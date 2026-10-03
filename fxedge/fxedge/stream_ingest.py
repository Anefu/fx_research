"""v3: streaming converter — month-shard parquet via canonical tick_schema.

Canonical schema everywhere (audit #2): initial ingest, existing-shard merge,
and shard writing all go through fxedge.tick_schema, which preserves
distinct same-millisecond quotes (dedup only exact (ts,bid,ask) records —
audit #3) and always writes the column-store layout the reader expects.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

import fxedge.tick_schema as ts

CSV_GLOB = "*_ticks_*.csv"
FNAME_RE = re.compile(r"^(?P<pair>[A-Z]{6})_ticks_(?P<yyyymm>\d{6})\.csv$")
STALE_SECONDS = 120.0


def convert_one(csv: Path, shard_root: Path) -> tuple:
    """Month-CSV -> canonical shard.

    Refresh semantics (audit round-4): existing shard rows keep their seq
    identity; re-transmitted (overlapping) records are dropped from the
    incoming frame; new source rows get fresh disjoint seq numbers.
    """
    import fxedge.tick_schema as ts_
    m = FNAME_RE.match(csv.name)
    pair, yyyymm = m.group("pair"), m.group("yyyymm")
    df = ts.read_mt5_csv_frame(csv)
    pdir = shard_root / pair
    pdir.mkdir(parents=True, exist_ok=True)
    shard = pdir / f"{yyyymm}.parquet"
    n_overlap = 0
    if shard.exists():
        old = ts.read_shard(shard)
        df, _wm = ts_.merge_refresh(old, df)
        n_overlap = len(old) + len(df) - len(old) - _count_new(old, df)
        df = df
    ts.write_shard(df, shard)
    csv.unlink()
    return pair, yyyymm, len(df), n_overlap


def _count_new(old, merged):
    return len(merged) - len(old)


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
        print(f"  {pair} {yyyymm}: {n:,} rows" + (f" ({n_ov:,} duplicate records dropped)" if n_ov else ""), flush=True)
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