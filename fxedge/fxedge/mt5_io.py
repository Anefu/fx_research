"""MT5 CSV tick loader for FX Edge Research.

Consumes the output of mt5/ExportTicksFromMT5.mq5:
  Common\\Files\\FX_EDGE\\<PAIR>_ticks_<YYYYMM>.csv
with header + rows: utc_ms, bid, ask  (MT5 time_msc is UTC in MQL5 FileWrite)

Produces the canonical fxedge schema: UTC-indexed DataFrame with columns
bid, ask. Output is written as data/fxedge/<PAIR>.parquet (loader layout).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

CSV_GLOB = "*_ticks_*.csv"
FNAME_RE = re.compile(r"^(?P<pair>[A-Z]{6})_ticks_(?P<yyyymm>\d{6})\.csv$")


def read_mt5_csv(path: Path) -> pd.DataFrame:
    """One month-file -> UTC-indexed bid/ask frame.

    MT5 CSV (FILE_CSV with comma) rows: utc_ms, bid, ask. Header row is
    written by the script; skip it if present. Numeric coercion is strict:
    unparseable rows are reported, not silently dropped.
    """
    df = pd.read_csv(path, header=None, names=["utc_ms", "bid", "ask"],
                     skiprows=1, dtype={"utc_ms": "int64", "bid": "float64", "ask": "float64"},
                     on_bad_lines="warn")
    df = df.dropna(subset=["utc_ms"])
    idx = pd.to_datetime(df["utc_ms"], unit="ms", utc=True)
    out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()}, index=idx)
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def pair_from_filename(name: str) -> Optional[str]:
    m = FNAME_RE.match(name)
    return m.group("pair") if m else None


def load_export_dir(export_dir: Path, pairs: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    """Load every *_ticks_YYYYMM.csv in `export_dir`, concatenate per pair."""
    if not export_dir.exists():
        raise FileNotFoundError(f"MT5 export dir not found: {export_dir}")
    by_pair: Dict[str, List[pd.DataFrame]] = {}
    files = sorted(export_dir.glob(CSV_GLOB))
    if not files:
        raise FileNotFoundError(f"no *_ticks_*.csv files in {export_dir}")
    for f in files:
        pair = pair_from_filename(f.name)
        if pair is None:
            continue
        if pairs and pair not in pairs:
            continue
        by_pair.setdefault(pair, []).append(read_mt5_csv(f))
    return {p: pd.concat(v).sort_index() for p, v in by_pair.items()}


def to_parquet_store(frames: Dict[str, pd.DataFrame], out_dir: Path) -> Dict[str, Path]:
    """Write each pair to canonical fxedge layout: <out_dir>/<PAIR>.parquet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for pair, df in frames.items():
        p = out_dir / f"{pair}.parquet"
        df.to_parquet(p)
        written[pair] = p
    return written


def ingest(export_dir: Path, out_dir: Path = Path("data/fxedge"),
           pairs: Optional[List[str]] = None) -> Dict[str, Path]:
    """MT5 Common\\Files\\FX_EDGE -> canonical parquet store. Returns files written."""
    frames = load_export_dir(export_dir, pairs)
    return to_parquet_store(frames, out_dir)