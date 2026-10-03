"""Canonical tick-frame schema — single source of truth for all writers/readers.

Representation (audit round-3 fix):
    pandas DataFrame, index = UTC DatetimeIndex (ns) (+ optional `_seq`),
    columns = [bid, ask]; storage = column store (utc_ms, seq, bid, ask).

- Same-millisecond DISTINCT quotes are preserved everywhere — dedup drops
  only exact (ts, bid, ask) records (identical repeated feeds).
- Chronological source ORDER is preserved: `_seq` is assigned at ingest
  (arrival order) and every sort is on (ts, _seq). Same-ms quotes keep their
  arrival sequence, so bar 'first'/'last' reflect the true source order
  instead of price-order (audit #1 fix).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

TICK_COLUMNS = ["bid", "ask"]
SEQ_COL = "_seq"


def with_seq(df: pd.DataFrame, start: int = 0) -> pd.DataFrame:
    """Assign monotone sequence numbers to a tick frame (arrival order)."""
    out = df.copy()
    out[SEQ_COL] = np.arange(start, start + len(out), dtype="int64")
    return out


import numpy as np  # noqa: E402


def tick_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """Drop only exact duplicate records (ts, bid, ask); keep arrival order.

    Never reorders by price. If `_seq` is absent it is assigned from current
    row order (a stable no-op ordering), so downstream sorts stay causal.
    """
    n_before = len(df)
    name = df.index.name
    reset = df.reset_index()
    idx_col = reset.columns[0]
    subset = [idx_col, "bid", "ask"]
    # dedup with keep=first under (ts, bid, ask): identical records are genuine repeats
    reset = reset.drop_duplicates(subset=subset, keep="first")
    if len(reset) < n_before:
        print(f"    [tick-dedup] {n_before - len(reset):,} exact duplicate records dropped")
    # stable causal order: ts then arrival seq (never price!)
    if SEQ_COL not in reset.columns:
        reset[SEQ_COL] = np.arange(len(reset), dtype="int64")
    reset = reset.sort_values([idx_col, SEQ_COL], kind="mergesort")
    out = reset.set_index(idx_col)
    out.index.name = name
    return out


def to_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Column-store layout: utc_ms (int64 ms), seq, bid, ask — no index."""
    if isinstance(df.index, pd.DatetimeIndex):
        ms = df.index.asi8 // 1_000_000
    else:
        ms = df["utc_ms"]
    seq = df[SEQ_COL].to_numpy() if SEQ_COL in df.columns else np.arange(len(df), dtype="int64")
    out = pd.DataFrame({"utc_ms": pd.Series(ms).astype("int64").to_numpy(),
                        "seq": seq.astype("int64"),
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
    pq.write_table(pa.Table.from_pandas(to_storage(tick_dedup(df))), path)


def read_shard(path: Path) -> pd.DataFrame:
    """Canonical shard -> tick frame. Accepts legacy layouts (seq becomes
    arrival order within the shard — flagged for reproducibility)."""
    return from_storage(pq.read_table(path).to_pandas())


def read_mt5_csv_frame(path) -> pd.DataFrame:
    """MT5 export CSV (utc_ms,bid,ask) -> canonical tick frame.

    Arrival order = row order in the export file (chronological source order).
    Quote-level dedup drops only exact (ts,bid,ask) repeats.
    """
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
    return with_seq(tick_dedup(out.sort_index()))


def normalize_store(root: Path) -> int:
    """One-time migration: rewrite every shard under the current canonical
    (seq, bid, ask) layout; returns count rewritten."""
    n = 0
    for pdir in sorted(root.glob("*")):
        for shard in sorted(pdir.glob("*.parquet")):
            try:
                df = read_shard(shard)
                if SEQ_COL not in df.columns:
                    df = with_seq(df)
                write_shard(df, shard)
                n += 1
            except Exception as e:
                print(f"    [normalize] {shard}: {e}")
    return n