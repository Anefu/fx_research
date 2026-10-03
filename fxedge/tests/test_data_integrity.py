"""Regression tests use real CSV and Parquet files, with tiny tick stores."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from fxedge import tick_schema as ts, snapshot, real_run, real_run_v2
from fxedge.stream_ingest import convert_one
from fxedge.ldn_002_004_v2 import preconditions
from fxedge.registry import FRZ


def frame(prices, times=None):
    times = times or ['2026-01-05T07:00:00Z'] * len(prices)
    return ts.with_seq(pd.DataFrame({'bid': prices, 'ask': [p + .0001 for p in prices]},
                                    index=pd.to_datetime(times, utc=True)))


def export(path, ticks):
    ts.to_storage(ticks)[['utc_ms', 'bid', 'ask']].to_csv(path, index=False)


class TickTests(unittest.TestCase):
    def test_same_millisecond_refresh_preserves_revisit(self):
        merged, wm = ts.merge_refresh(frame([1.1]), frame([1.1, 1.1001, 1.1]))
        self.assertEqual(merged.bid.tolist(), [1.1, 1.1001, 1.1])
        self.assertEqual(wm, 2)
        self.assertEqual(merged._seq.tolist(), [0, 1, 2])
        again, _ = ts.merge_refresh(merged, frame([1.1, 1.1001, 1.1]))
        pd.testing.assert_frame_equal(again, merged)

    def test_conflicting_order_is_rejected(self):
        with self.assertRaises(ValueError):
            ts.merge_refresh(frame([1.1002, 1.1]), frame([1.1, 1.1001]))

    def test_append_and_empty(self):
        new = frame([1.2], ['2026-01-05T07:00:01Z'])
        merged, _ = ts.merge_refresh(frame([1.1]), new, watermark=10)
        self.assertEqual(merged._seq.tolist(), [0, 11])
        empty, wm = ts.merge_refresh(frame([]), frame([]))
        self.assertTrue(empty.empty)
        self.assertEqual(wm, -1)

    def test_overlap_count_and_csv_retained_on_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'EURUSD').mkdir()
            shard = root/'EURUSD/202601.parquet'
            ts.write_shard(frame([1.1]), shard)
            csv = root/'EURUSD_ticks_202601.csv'
            export(csv, frame([1.1, 1.1001, 1.1]))
            self.assertEqual(convert_one(csv, root)[2:], (3, 1))
            export(csv, frame([1.1, 1.1002]))
            with self.assertRaises(ValueError):
                convert_one(csv, root)
            self.assertTrue(csv.exists())
            self.assertEqual(len(ts.read_shard(shard)), 3)

    def test_recovery_replaces_order_and_rejects_partial_export(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'EURUSD').mkdir()
            shard = root/'EURUSD/202601.parquet'
            ts.write_shard(frame([1.1, 1.1001, 1.1002]), shard)
            csv = root/'EURUSD_ticks_202601.csv'
            export(csv, frame([1.1002, 1.1, 1.1001]))
            ts.recover_from_exports(root, root)
            self.assertEqual(ts.read_shard(shard).bid.tolist(), [1.1002, 1.1, 1.1001])
            export(csv, frame([1.1]))
            with self.assertRaises(ValueError):
                ts.recover_from_exports(root, root)
            self.assertEqual(len(ts.read_shard(shard)), 3)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'store'; self.root.mkdir()
        self.runs = Path(self.tmp.name)/'runs'
        self.base = self.runs/'FX-LDN-001-v2'; self.base.mkdir(parents=True)
        self.gates_dir = self.runs/'DATA_GATES'; self.gates_dir.mkdir()
        for pair in FRZ.primary_universe:
            (self.root/pair).mkdir()
            ts.write_shard(frame([1.1]), self.root/pair/'202601.parquet')
        sess = pd.DataFrame([{'pair': p, 'london_date': '2026-01-05', 'valid': True}
                             for p in FRZ.primary_universe])
        sess.to_parquet(self.base/'sessions.parquet')
        snap = snapshot.snapshot_id(self.root)
        self.manifest = {'unique_sessions': dict.fromkeys(FRZ.primary_universe, 1),
                         'universe_complete': True, 'store_root': str(self.root),
                         'store_fingerprint': snap, 'expected_months': [202601],
                         'sessions_sha256': snapshot._sha256_file(self.base/'sessions.parquet')}
        self.gates = {'store_root': str(self.root), 'store_fingerprint': snap,
                      'expected_months': [202601], 'pairs': {
                          p: {'DATA_pass': True, 'total_ticks': 1, 'bars_checked': 1, 'months_missing': []}
                          for p in FRZ.primary_universe}}
        self.save()

    def save(self):
        (self.base/'manifest.json').write_text(json.dumps(self.manifest))
        (self.gates_dir/'data_gates.json').write_text(json.dumps(self.gates))

    def test_valid_bound_run(self):
        self.assertTrue(preconditions(self.runs)['promotable'])

    def test_missing_binding(self):
        del self.gates['store_fingerprint']; self.save()
        with self.assertRaises(RuntimeError): preconditions(self.runs)

    def test_quality_snapshot_mismatch(self):
        self.gates['store_fingerprint'] = {'snapshot_id': 'wrong', 'pairs': {}}; self.save()
        with self.assertRaises(RuntimeError): preconditions(self.runs)

    def test_live_store_change_without_saved_manifest(self):
        ts.write_shard(frame([1.1001]), self.root/'EURUSD/202601.parquet')
        with self.assertRaises(RuntimeError): preconditions(self.runs)

    def test_zero_coverage_cannot_pass(self):
        self.gates['pairs']['EURUSD']['total_ticks'] = 0; self.save()
        with self.assertRaises(RuntimeError): preconditions(self.runs)

    def test_zero_bars_cannot_pass(self):
        self.gates['pairs']['EURUSD']['bars_checked'] = 0; self.save()
        with self.assertRaises(RuntimeError): preconditions(self.runs)

    def test_unresolved_chronology_blocks_inference(self):
        (self.root/snapshot.STORE_MANIFEST).write_text(json.dumps({
            'shards': {'EURUSD/202601': {'chronology': 'recovered-unordered'}}}))
        with self.assertRaises(RuntimeError): preconditions(self.runs)

    def test_renderer_requires_binding(self):
        from fxedge.provenance import render_ldn_001_entry
        result = self.base/'result.json'; result.write_text('{}')
        with self.assertRaises(RuntimeError):
            render_ldn_001_entry(self.base/'manifest.json', result, self.base/'entry.md')
        self.assertFalse((self.base/'entry.md').exists())

    def test_table_tampering(self):
        p = self.base/'sessions.parquet'; df = pd.read_parquet(p)
        df['london_date'] = '2026-01-06'; df.to_parquet(p)
        with self.assertRaises(RuntimeError): preconditions(self.runs)

    def test_missing_whole_month_fails_quality_and_sessions(self):
        for pair in FRZ.primary_universe:
            ts.write_shard(frame([1.1], ['2026-03-05T07:00:00Z']), self.root/pair/'202603.parquet')
        report = real_run.run(root=self.root, out_dir=self.gates_dir)
        for pair in FRZ.primary_universe:
            self.assertFalse(report['pairs'][pair]['DATA_pass'])
            self.assertEqual(report['pairs'][pair]['months_missing'], ['202602'])
        with patch.object(real_run_v2, 'compute_sessions_coverage', return_value=pd.DataFrame()):
            real_run_v2.run_ldn_001_v2(root=self.root, out_dir=self.base)
        manifest = json.loads((self.base/'manifest.json').read_text())
        self.assertFalse(manifest['universe_complete'])
        self.assertEqual(manifest['months_missing']['EURUSD'], [202602])

    def test_inventory_mismatch_rejected(self):
        bad = dict(self.manifest['store_fingerprint']); bad['pairs'] = {}
        with self.assertRaises(RuntimeError):
            snapshot.reject_mismatch(bad, self.manifest['store_fingerprint'], 'test')

    def test_explicit_calendar_span(self):
        self.assertEqual(snapshot.expected_months(self.root, 202512, 202602), [202512, 202601, 202602])
        with self.assertRaises(ValueError): snapshot.expected_months(self.root, 202602, 202601)


if __name__ == '__main__':
    unittest.main()
