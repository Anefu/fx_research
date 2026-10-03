"""DATA gates + FX-LDN-001 on the real MT5 tick store (shards), streaming per pair.

Memory note: 10y of ticks per pair is ~300M rows; gates and FX-LDN-001 both
run month-by-month per pair (shard-wise), so peak RAM stays bounded.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from fxedge.snapshot import snapshot_id, reject_mismatch, expected_months
from fxedge.bars import build_bars
from fxedge.data_quality import _gap_summary, bid_ask_integrity
from fxedge.ldn_001 import compute_sessions
from fxedge.registry import FRZ, REGISTRY_VERSION
from fxedge.sessions import SessionEngine
from fxedge.shard_reader import read_pair, shard_root_default

UTC = "UTC"


def month_bounds(ym: int):
    """Explicit calendar-month boundaries (audit round-4 fix #3: no MonthEnd)."""
    y, m = divmod(ym, 100)
    start = pd.Timestamp(f"{y:04d}-{m:02d}-01", tz="UTC")
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    end = pd.Timestamp(f"{ny:04d}-{nm:02d}-01", tz="UTC") - pd.Timedelta(microseconds=1)
    return start, end


def gates_for_pair(pair: str, root: Path, months: list) -> dict:
    """DATA-001/002/005 over the pair's tick history, per shard group.

    Audit round-4: calendar bounds via month_bounds(); empty months are
    counted as missing coverage, and a pair with zero checked bars fails
    the gate (no silent PASS on empty stores).
    """
    res = {"negative_spread": 0, "jump_gt_2pct": 0, "bars_checked": 0, "high_mismatch": 0, "flat_mismatch": 0,
           "total_ticks": 0, "longest_gap_min": 0.0, "months_missing": []}
    for ym in months:
        s, e = month_bounds(ym)
        df = read_pair(pair, s, e, root)
        if df.empty:
            res["months_missing"].append(str(ym))
            continue
        res["total_ticks"] += len(df)
        # DATA-002 (vectorized on the shard)
        spread = df["ask"] - df["bid"]
        res["negative_spread"] += int((spread < 0).sum())
        mid = (df["bid"] + df["ask"]) / 2
        lr = np.abs(np.log(mid / mid.shift(1))).replace([np.inf, -np.inf], np.nan).fillna(0.0)
        res["jump_gt_2pct"] += int((lr > 0.02).sum())
        # DATA-005: bar extrema vs ticks, via identical resampler on both
        from fxedge.bars import to_freq
        bars5 = build_bars(df, rule="5m")
        freq = to_freq("5m")
        gmax = df["bid"].resample(freq).max()
        gmin = df["bid"].resample(freq).min()
        common = bars5.index.intersection(gmax.index)
        mis_h = int((~np.isclose(gmax.reindex(common).to_numpy(),
                                 bars5.loc[common, "bid_h"].to_numpy())).sum())
        mis_l = int((~np.isclose(gmin.reindex(common).to_numpy(),
                                 bars5.loc[common, "bid_l"].to_numpy())).sum())
        res["high_mismatch"] += mis_h
        res["flat_mismatch"] += mis_l
        res["bars_checked"] += len(common)
        # DATA-001: longest within-month gap
        diffs = np.diff(df.index.values).astype("timedelta64[m]").astype(np.float64)
        if len(diffs):
            res["longest_gap_min"] = max(res["longest_gap_min"], float(np.nanmax(diffs)))
    return res


def run(pair_list=None, root=None, out_dir=None, start_month=None, end_month=None):
    root = Path(root or shard_root_default()).resolve()
    out_dir = Path(out_dir or "runs/DATA_GATES")
    out_dir.mkdir(parents=True, exist_ok=True)
    before = snapshot_id(root)
    months = expected_months(root, start_month, end_month)
    report = {"registry_version": REGISTRY_VERSION, "pairs": {},
              "store_root": str(root), "store_fingerprint": before, "expected_months": months}
    for pair in (pair_list or FRZ.primary_universe):
        pdir = root / pair
        r = gates_for_pair(pair, root, months)
        r["DATA_pass"] = (r["negative_spread"] == 0 and r["jump_gt_2pct"] == 0 and
                          r["high_mismatch"] == 0 and r["flat_mismatch"] == 0 and
                          r["bars_checked"] > 0 and r["total_ticks"] > 0 and len(r["months_missing"]) == 0)
        report["pairs"][pair] = r
        print(f"{pair}: ticks={r['total_ticks']:,} neg-spread={r['negative_spread']} "
              f"jump2%={r['jump_gt_2pct']} bar-mismatch(h/l)={r['high_mismatch']}/{r['flat_mismatch']} "
              f"longest-gap={r['longest_gap_min']:.0f}min -> PASS={r['DATA_pass']}", flush=True)
    if before["pairs"]:
        reject_mismatch(before, snapshot_id(root), "DATA store changed during run")
    (out_dir / "data_gates.json").write_text(json.dumps(report, indent=2))
    print("saved:", out_dir / "data_gates.json")
    return report


def run_ldn_001_all(out_dir=None):
    """FX-LDN-001 over the full real history — per-month streaming.

    For each pair: read one month shard, build 1m bars for that month, feed
    compute_sessions just that month's slice, append. Bounded memory; the
    earlier full-slice version stalled on repeated full-history bar builds.
    """
    root = shard_root_default()
    out_dir = Path(out_dir or "runs/FX-LDN-001")
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = SessionEngine(FRZ)
    parts = []

    for pair in FRZ.primary_universe:
        print(f"{pair}: computing sessions (per-month)...", flush=True)
        pair_rows = []
        months = sorted(int(m.stem) for m in (root / pair).glob("*.parquet"))
        for ym in months:
            df = read_pair(pair, pd.Timestamp(str(ym) + "01", tz="UTC"),
                           pd.Timestamp(str(ym) + "28", tz="UTC") + pd.offsets.MonthEnd(1), root)
            if df.empty:
                continue
            first_day = df.index[0].date()
            last_day = df.index[-1].date()
            sess = compute_sessions(df, pair, FRZ, engine, first_day, last_day)
            pair_rows.append(sess)
        sess_pair = pd.concat(pair_rows, ignore_index=True)
        n_valid = int(sess_pair["valid"].sum()) if "valid" in sess_pair else 0
        print(f"{pair}: {n_valid} valid sessions ({len(sess_pair)} rows)", flush=True)
        parts.append(sess_pair)

    sessions = pd.concat(parts, ignore_index=True)
    sessions.to_parquet(out_dir / "sessions.parquet")
    print("wrote", out_dir / "sessions.parquet", f"({len(sessions)} session rows)", flush=True)
    return sessions


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "gates":
        run()
    elif args and args[0] == "ldn001":
        run_ldn_001_all()
    else:
        print("usage: python -m fxedge.real_run [gates|ldn001]")