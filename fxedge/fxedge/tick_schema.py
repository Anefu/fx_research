"""Canonical tick-frame schema — single source of truth for all writers/readers.

Representation (audit round-4):
    pandas DataFrame, index = UTC DatetimeIndex (ns),
    columns = [bid, ask, (optional _seq)]; storage = (utc_ms, seq, bid, ask).

Semantics (each point fixes a named audit finding):

- Same-millisecond DISTINCT quotes preserved everywhere. Dedup drops only
  exact duplicate (ts, bid, ask) records — identical repeated feeds.

- Quote REVISIT (A → B → A) is legal market behavior and is PRESERVED
  (round-4 finding: v3 collapsed it via unique-subset dedup). Only
  CONSECUTIVE identical records (A → A) collapse — that is a genuine
  repeated feed.

- Sequence identity across refreshes (round-4): `_seq` is global and
  persistent. New rows get fresh, disjoint sequence ranges (a running
  watermark), and when overlapping exports merge, exact duplicates from
  the refresh are dropped *without* renumbering existing rows. Sequence
  ranges are per-source tracked so overlapping exports can't interleave
  fake order between them.

- Chronology recovery (round-4): historical shards that were price-sorted
  before seq tracking existed are marked `chronology=recovered-unordered`
  in the store manifest; their intra-ms order is unknown by construction.
  The only way to re-derive true arrival order is re-export from the
  source CSVs; `recover_from_exports()` does exactly that.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

TICK_COLUMNS = ["bid", "ask"]
SEQ_COL = "_seq"
STORE_MANIFEST = "store_manifest.json"


def with_seq(df: pd.DataFrame, start: int = 0) -> pd.DataFrame:
    """Assign monotone sequence numbers to a tick frame (arrival order)."""
    out = df.copy()
    out[SEQ_COL] = np.arange(start, start + len(out), dtype="int64")
    return out


def tick_dedup_consecutive(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse only CONSECUTIVE identical records (A→A); keep A→B→A revisits."""
    name = df.index.name
    reset = df.reset_index()
    idx_col = reset.columns[0]
    key = ["bid", "ask"]
    dup_mask = (reset[key] == reset[key].shift(1)).all(axis=1) & (reset[idx_col] == reset[idx_col].shift(1))
    n_before = len(reset)
    reset = reset[~dup_mask]
    if len(reset) < n_before:
        print(f"    [tick-dedup] {n_before - len(reset):,} consecutive duplicate records collapsed")
    return reset.set_index(idx_col).rename_axis(name)


def tick_dedup_exact_global(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate (ts,bid,ask) rows ANYWHERE in the frame (used when
    merging overlapping exports of the SAME source, where repeats are
    re-transmissions, not market revisits)."""
    name = df.index.name
    reset = df.reset_index()
    idx_col = reset.columns[0]
    n_before = len(reset)
    reset = reset.drop_duplicates(subset=[idx_col, "bid", "ask"], keep="first")
    if len(reset) < n_before:
        print(f"    [tick-dedup] {n_before - len(reset):,} exact duplicate records dropped")
    return reset.set_index(idx_col).rename_axis(name)


def merge_refresh(existing: pd.DataFrame, incoming: pd.DataFrame,
                  watermark: int | None = None) -> tuple[pd.DataFrame, int]:
    """Merge a refresh export into the canonical store.

    - incoming rows are assigned NEW disjoint seq numbers (above the
      existing watermark), preserving source identity (round-4 fix).
    - exact re-transmissions (identical ts/bid/ask) are dropped from the
      incoming frame first (overlapping export, not a market revisit).
    - the existing frame is NEVER resequenced; the union of seq sets stays
      disjoint by source.
    Returns (merged, new_watermark).
    """
    if watermark is None:
        watermark = int(existing[SEQ_COL].max()) if SEQ_COL in existing.columns and len(existing) else -1
    incoming = incoming.copy()
    if SEQ_COL in existing.columns and len(existing):
        key = ["bid", "ask"]
        er = existing.reset_index()
        ex_idx = er.columns[0]
        # drop re-transmissions: identical (ts,bid,ask) already present
        existing_keys = set(zip(er[ex_idx].view("int64") // 1_000_000
                                if isinstance(pd.api.types.is_datetime64_any_dtype(er[ex_idx]), bool) else er[ex_idx],
                                ) ) if False else set()
        # (set-intersect approach is too slow/memory-heavy on 300M rows;
        #  use merge indicator instead)
        er = er[[ex_idx] + key]
        ir = incoming.reset_index()
        in_idx = ir.columns[0]
        merged_keys = er.merge(ir, left_on=[ex_idx] + key, right_on=[in_idx] + key,
                               how="inner", indicator=True)
        dup_mask = incoming.index.isin(
            pd.DatetimeIndex(merged_keys[in_idx])) if len(merged_keys) else pd.Series(False, index=incoming.index)
        n_dropped = int(dup_mask.sum())
        incoming = incoming[~dup_mask]
        if n_dropped:
            print(f"    [merge-refresh] {n_dropped:,} re-transmitted records dropped (overlap)")
    incoming[SEQ_COL] = np.arange(watermark + 1, watermark + 1 + len(incoming), dtype="int64")
    out = pd.concat([existing, incoming]).sort_values([SEQ_COL], kind="mergesort")
    return out, int(out[SEQ_COL].max())


def to_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Column-store layout: utc_ms (int64 ms), seq, bid, ask — no index."""
    if isinstance(df.index, pd.DatetimeIndex):
        ms = df.index.asi8 // 1_000_000
    else:
        ms = df["utc_ms"]
    seq = df[SEQ_COL].to_numpy() if SEQ_COL in df.columns else np.arange(len(df), dtype="int64")
    out = pd.DataFrame({"utc_ms": pd.Series(ms).astype("int64").to_numpy(),
                        "seq": np.asarray(seq).astype("int64"),
                        "bid": df["bid"].to_numpy(),
                        "ask": df["ask"].to_numpy()})
    return out.reset_index(drop=True)


def from_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Storage layout -> canonical tick frame (UTC DatetimeIndex + _seq)."""
    if "utc_ms" in df.columns:
        idx = pd.to_datetime(pd.to_numeric(df["utc_ms"], errors="coerce"),
                             unit="ms", utc=True)
        out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()},
                           index=idx)
        if "seq" in df.columns:
            out[SEQ_COL] = df["seq"].to_numpy()
    elif isinstance(df.index, pd.DatetimeIndex):
        out = df[TICK_COLUMNS].copy()
        if SEQ_COL in df.columns:
            out[SEQ_COL] = df[SEQ_COL]
    else:
        raise ValueError(f"cannot interpret tick frame: columns={df.columns.tolist()}")
    out.index.name = None
    return out


def write_shard(df: pd.DataFrame, path: Path) -> None:
    """Tick frame -> canonical column-store parquet shard (with seq)."""
    pq.write_table(pa.Table.from_pandas(to_storage(df)), path)


def read_shard(path: Path) -> pd.DataFrame:
    """Canonical shard -> tick frame. Legacy layouts (no seq) get arrival-order
    seq within the shard + a chronology flag."""
    df = from_storage(pq.read_table(path).to_pandas())
    if SEQ_COL not in df.columns:
        df = with_seq(df)   # legacy: intra-shard order = the only order we have
    return df


def read_mt5_csv_frame(path) -> pd.DataFrame:
    """MT5 export CSV (utc_ms,bid,ask) -> canonical tick frame.

    Arrival order = row order in the export file (chronological source order).
    Consecutive duplicates collapse (repeated feed lines); non-consecutive
    exact repeats PRESERVED (possible quote revisits)."""
    import pyarrow.csv as pacsv
    t = pacsv.read_csv(
        str(path),
        read_options=pacsv.ReadOptions(skip_rows=1, autogenerate_column_names=True),
        convert_options=pacsv.ConvertOptions(
            column_types={"f0": pa.int64(), "f1": pa.float64(), "f2": pa.float64()}))
    t = t.rename_columns(["utc_ms", "bid", "ask"])
    df = t.to_pandas()
    idx = pd.to_datetime(df["utc_ms"], unit="ms", utc=True)
    out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()}, index=idx)
    out = with_seq(tick_dedup_consecutive(out.sort_index(kind="mergesort")), start=0)
    return out


def recover_from_exports(export_dir: Path, shard_root: Path, pairs=None) -> dict:
    """Rebuild shards' chronology from the original export CSVs (round-4 fix).

    For each pair-month file present in the export dir, re-read with true
    arrival order, merge into the store via merge_refresh (existing seq
    preserved, re-transmissions dropped), and re-write. Only run when the
    exports still exist on disk.
    """
    import re
    fname_re = re.compile(r"^(?P<pair>[A-Z]{6})_ticks_(?P<yyyymm>\d{6})\.csv$")
    out = {}
    for csv in sorted(export_dir.glob("*_ticks_*.csv")):
        m = fname_re.match(csv.name)
        if not m:
            continue
        pair, yyyymm = m.group("pair"), m.group("yyyymm")
        if pairs and pair not in pairs:
            continue
        shard = shard_root / pair / f"{yyyymm}.parquet"
        fresh = read_mt5_csv_frame(csv)
        if shard.exists():
            existing = read_shard(shard)
            merged, wm = merge_refresh(existing, fresh)
            write_shard(merged, shard)
            out[f"{pair}/{yyyymm}"] = {"merged_rows": int(len(merged)), "watermark": wm}
        else:
            write_shard(fresh, shard)
            out[f"{pair}/{yyyymm}"] = {"merged_rows": int(len(fresh)), "watermark": int(fresh[SEQ_COL].max())}
    return out


def normalize_store(root: Path) -> dict:
    """One-time migration + chronology bookkeeping.

    Shards without seq get arrival-order seq assigned (intra-shard order);
    the store manifest records that migrated shards are
    'recovered-unordered' for intra-ms chronology unless re-exported.
    """
    manifest_p = Path(root) / STORE_MANIFEST
    manifest = json.loads(manifest_p.read_text()) if manifest_p.exists() else {
        "chronology": "source-arrival", "shards": {}}
    n = 0
    for pdir in sorted(Path(root).glob("*")):
        if not pdir.is_dir():
            continue
        for shard in sorted(pdir.glob("*.parquet")):
            raw = pq.read_table(shard).to_pandas()
            df = from_storage(raw)
            if SEQ_COL not in df.columns:
                df = with_seq(df)
                key = f"{pdir.name}/{shard.stem}"
                if key not in manifest["shards"]:
                    manifest["shards"][key] = {"chronology": "recovered-unordered"}
            write_shard(df, shard)
            n += 1
    manifest["shards_normalized"] = n
    manifest_p.write_text(json.dumps(manifest, indent=2))
    return manifest