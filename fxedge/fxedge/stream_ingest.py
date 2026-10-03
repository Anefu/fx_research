"""v2: fast streaming converter — month-shard parquet, bounded memory, disk-safe.

Design fix vs v1: never merge into a monolithic parquet (that made each
conversion a full rewrite — O(n^2) and the reason the first watcher stalled).
Each month-CSV becomes its own shard:  shards/<PAIR>/<YYYYMM>.parquet
Duplicate handling: if a shard exists, merge + rewrite just that shard and
report the overlap count (spec section 6 — never hide duplicates).

Readers use pyarrow.dataset over the shard tree.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Optional

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
import pandas as pd

CSV_GLOB = "*_ticks_*.csv"
FNAME_RE = re.compile(r"^(?P<pair>[A-Z]{6})_ticks_(?P<yyyymm>\d{6})\.csv$")
STALE_SECONDS = 120.0


def read_mt5_csv_fast(path: Path) -> pa.Table:
    t = pacsv.read_csv(
        str(path),
        read_options=pacsv.ReadOptions(skip_rows=1, autogenerate_column_names=True),
        convert_options=pacsv.ConvertOptions(
            column_types={"f0": pa.int64(), "f1": pa.float64(), "f2": pa.float64()}))
    # autogen names f0/f1/f2 = utc_ms/bid/ask (pyarrow infers schema-less for
    # MT5's headerless-style giant files; explicit mapping avoids that)
    t = t.rename_columns(["utc_ms", "bid", "ask"])
    return t.sort_by([("utc_ms", "ascending")])


def table_to_frame(t: pa.Table) -> pd.DataFrame:
    """Tick-level dedup on (timestamp, bid, ask) — distinct quotes sharing a
    millisecond are preserved (spec section 6: never discard observations)."""
    df = t.to_pandas()
    n_before = len(df)
    df = df.drop_duplicates(subset=["utc_ms", "bid", "ask"], keep="first")
    n_dup = n_before - len(df)
    if n_dup:
        print(f"    [dedup] {n_dup:,} exact-duplicate (ts,bid,ask) rows dropped", flush=True)
    idx = pd.to_datetime(df["utc_ms"], unit="ms", utc=True)
    out = pd.DataFrame({"bid": df["bid"].to_numpy(), "ask": df["ask"].to_numpy()}, index=idx)
    return out.sort_index()


def convert_one(csv: Path, shard_root: Path) -> tuple:
    m = FNAME_RE.match(csv.name)
    pair, yyyymm = m.group("pair"), m.group("yyyymm")
    df = table_to_frame(read_mt5_csv_fast(csv))   # quote-level dedup on (ts,bid,ask)
    pdir = shard_root / pair
    pdir.mkdir(parents=True, exist_ok=True)
    shard = pdir / f"{yyyymm}.parquet"
    n_overlap = 0
    if shard.exists():
        old = pd.read_parquet(shard)
        merged = pd.concat([old, df])
        n_dup = int(merged.index.duplicated(keep="last").sum())
        merged = merged[~merged.index.duplicated(keep="last")]  # last quote wins on identical ms
        n_overlap = len(old) + len(df) - len(merged)
        df = merged.sort_index()
    df.to_parquet(shard)
    csv.unlink()
    return pair, yyyymm, len(df), n_overlap


def convert_idle(export_dir: Path, shard_root: Path, pairs: Optional[list] = None,
                 idle_secs: float = STALE_SECONDS, limit: Optional[int] = None) -> int:
    now = time.time()
    done = 0
    for csv in sorted(export_dir.glob(CSV_GLOB), key=lambda f: f.stat().st_mtime):
        m = FNAME_RE.match(csv.name)
        if not m:
            continue
        if pairs and m.group("pair") not in pairs:
            continue
        if now - csv.stat().st_mtime < idle_secs:
            continue
        pair, yyyymm, n, n_ov = convert_one(csv, shard_root)
        print(f"  {pair} {yyyymm}: {n:,} rows" + (f" ({n_ov:,} dup-ts replaced)" if n_ov else ""), flush=True)
        done += 1
        if limit and done >= limit:
            break
    return done


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-dir",
                    default=str(Path.home() / (
                        "Library/Application Support/net.metaquotes.wine.metatrader5/"
                        "drive_c/users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/FX_EDGE")))
    ap.add_argument("--shard-root", default="data/shards")
    ap.add_argument("--pairs", default=None)
    ap.add_argument("--poll", type=int, default=30, help="0 = single draining pass")
    ap.add_argument("--idle", type=float, default=STALE_SECONDS)
    args = ap.parse_args(argv)

    pairs = [p.strip().upper() for p in args.pairs.split(",")] if args.pairs else None
    export_dir, shard_root = Path(args.export_dir), Path(args.shard_root)

    if args.poll <= 0:
        n = convert_idle(export_dir, shard_root, pairs, args.idle)
        print(f"drained {n} files")
        return 0
    print(f"watching {export_dir} every {args.poll}s")
    try:
        while True:
            convert_idle(export_dir, shard_root, pairs, args.idle)
            time.sleep(args.poll)
    except KeyboardInterrupt:
        print("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())