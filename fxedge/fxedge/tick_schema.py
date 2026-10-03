"""Canonical tick-frame schema — single source of truth for all writers/readers.

Every producer (initial ingest, shard merge, normalization) and consumer
(reader, gates, experiments) uses these functions. One representation
everywhere:

    pandas DataFrame, index = UTC DatetimeIndex (ns), columns = [bid, ask]
    PLUS round-trippable storage via to_storage()/from_storage().

Same-millisecond distinct quotes are preserved everywhere: dedup only drops
genuine repeated records — identical (ts, bid, ask) triples — never distinct
quotes that share a timestamp (audit #3).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

TICK_COLUMNS = ["bid", "ask"]


def tick_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """Drop only exact duplicate records (ts, bid, ask).

    Distinct quotes sharing a millisecond survive (keep the natural order:
    sorted by price within each millisecond for deterministic bar O/C).
    """
    n_before = len(df)
    name = df.index.name
    reset = df.reset_index()
    idx_col = reset.columns[0]
    reset = reset.drop_duplicates(subset=[idx_col, "bid", "ask"], keep="first")
    if len(reset) < n_before:
        dropped = n_before - len(reset)
        if dropped > 0:
            print(f"    [tick-dedup] {dropped:,} exact duplicate records dropped")
    # deterministic within-ms ordering: ascending (bid, ask) so bar 'first'/'last'
    # picks are stable regardless of arrival order
    reset = reset.sort_values([idx_col, "bid", "ask"], kind="mergesort")
    out = reset.set_index(idx_col)
    out.index.name = name
    return out


def to_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Column-store layout: utc_ms (int64 ms), bid, ask — no index."""
    if isinstance(df.index, pd.DatetimeIndex):
        ms = df.index.asi8 // 1_000_000
    else:
        ms = df["utc_ms"]
    out = pd.DataFrame({"utc_ms": ms.astype("int64"),
                        "bid": df["bid"].to_numpy(),
                        "ask": df["ask"].to_numpy()})
    return out.reset_index(drop=True)


def from_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Storage layout -> canonical tick frame (UTC DatetimeIndex)."""
    if "utc_ms" in df.columns:
        idx = pd.to_datetime(pd.to_numeric(df["utc_ms"], errors="coerce"),
                             unit="ms", utc=True)
        out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()},
                           index=idx)
    elif isinstance(df.index, pd.DatetimeIndex):
        out = df[TICK_COLUMNS].copy()
    else:
        raise ValueError(f"cannot interpret tick frame: columns={df.columns.tolist()}")
    out.index.name = None
    return out


def write_shard(df: pd.DataFrame, path: Path) -> None:
    """Tick frame -> canonical column-store parquet shard."""
    pq.write_table(pa.Table.from_pandas(to_storage(tick_dedup(df))), path)


def read_shard(path: Path) -> pd.DataFrame:
    """Canonical shard -> tick frame (UTC DatetimeIndex). Accepts both layouts
    for backward compatibility with pre-normalization shards."""
    return from_storage(pq.read_table(path).to_pandas())


def read_mt5_csv_frame(path) -> pd.DataFrame:
    """MT5 export CSV (utc_ms,bid,ask) -> canonical tick frame, quote-level dedup."""
    import pyarrow.csv as pacsv
    import pyarrow._compute  # noqa: F401
    t = pacsv.read_csv(
        str(path),
        read_options=pacsv.ReadOptions(skip_rows=1, autogenerate_column_names=True),
        convert_options=pacsv.ConvertOptions(
            column_types={"f0": pa.int64(), "f1": pa.float64(), "f2": pa.float64()}))
    t = t.rename_columns(["utc_ms", "bid", "ask"])
    df = t.to_pandas()
    idx = pd.to_datetime(df["utc_ms"], unit="ms", utc=True)
    out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()}, index=idx)
    return tick_dedup(out.sort_index())