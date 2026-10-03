"""Shard-store reader: pyarrow.dataset over month-shard parquet trees.

Canonical store layout (built by fxedge.stream_ingest v2):
    data/shards/<PAIR>/<YYYYMM>.parquet   (UTC-indexed bid/ask frames)

The month-shard design exists so any date range can be served with bounded
memory and no full rewrites.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pyarrow.dataset as pads

SHARD_RE = re.compile(r"^(\d{6})\.parquet$")


def shard_root_default() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "shards"


def month_key(ts: pd.Timestamp) -> int:
    return ts.year * 100 + ts.month


def shard_months(pair_dir: Path) -> List[int]:
    out = []
    for p in pair_dir.glob("*.parquet"):
        m = SHARD_RE.match(p.name)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def months_for_range(start: pd.Timestamp, end: pd.Timestamp) -> List[int]:
    k0, k1 = month_key(start), month_key(end)
    out, k = [], k0
    while k <= k1:
        out.append(k)
        y, m = divmod(k, 100)
        m += 1
        if m > 12:
            y, m = y + 1, 1
        k = y * 100 + m
    return out


def read_pair(pair: str, start: Optional[pd.Timestamp] = None,
              end: Optional[pd.Timestamp] = None,
              root: Optional[Path] = None) -> pd.DataFrame:
    """Read one pair's shard tree for [start, end] (UTC, inclusive), as bid/ask frame.

    Reads only the shards overlapping the range — bounded memory.
    """
    root = root or shard_root_default()
    pdir = root / pair
    if not pdir.exists():
        raise FileNotFoundError(f"no shard dir for {pair}: {pdir}")

    if start is None or end is None:
        months = shard_months(pdir)                      # full history
    else:
        months = [m for m in months_for_range(start, end) if m in set(shard_months(pdir))]

    if not months:
        return pd.DataFrame(columns=["bid", "ask"], index=pd.DatetimeIndex([], tz="UTC"))

    files = [pdir / f"{m}.parquet" for m in months]
    ds = pads.dataset([str(f) for f in files], format="parquet")
    table = ds.to_table()
    df = table.to_pandas()
    if "utc_ms" in df.columns:
        idx = pd.to_datetime(df["utc_ms"], unit="ms", utc=True)
        out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()}, index=idx)
    else:
        # shard already parsed (tz-aware index, bid/ask columns)
        out = df[["bid", "ask"]]
    out = out[~out.index.duplicated(keep="last")].sort_index()
    if out.index.tz is None:
        out.index = out.index.tz_localize("UTC")
    out.index.name = None
    if start is not None:
        out = out[out.index >= start]
    if end is not None:
        out = out[out.index <= end]
    return out


def inventory(root: Optional[Path] = None) -> pd.DataFrame:
    """Per-pair shard inventory: span, count, missing months inside span."""
    root = root or shard_root_default()
    rows = []
    for pdir in sorted(root.glob("*")):
        if not pdir.is_dir():
            continue
        months = shard_months(pdir)
        if not months:
            continue
        span = months_for_range(pd.Timestamp(str(months[0]) + "01"), pd.Timestamp(str(months[-1]) + "28"))
        missing = [m for m in span if m not in set(months)]
        rows.append({
            "pair": pdir.name,
            "n_shards": len(months),
            "first_month": months[0],
            "last_month": months[-1],
            "missing_in_span": missing,
        })
    return pd.DataFrame(rows)