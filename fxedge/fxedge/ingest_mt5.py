"""Ingest MT5 tick export (Common\\Files\\FX_EDGE) into the canonical parquet store.

Usage:
  python -m fxedge.ingest_mt5 [--export-dir PATH] [--out-dir PATH] [--pairs EURUSD,...]

Default export dir is auto-detected from the MetaQuotes wine install:
  ~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/
      users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files/FX_EDGE
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fxedge.mt5_io import ingest

WINE_COMMON_FILES = Path.home() / (
    "Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/"
    "users/user/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
)


def default_export_dir() -> Path:
    return WINE_COMMON_FILES / "FX_EDGE"


def main(argv=None):
    ap = argparse.ArgumentParser(description="ingest MT5 tick export")
    ap.add_argument("--export-dir", default=str(default_export_dir()))
    ap.add_argument("--out-dir", default="data/fxedge")
    ap.add_argument("--pairs", default=None, help="comma list to filter, else all found")
    args = ap.parse_args(argv)

    pairs = [p.strip().upper() for p in args.pairs.split(",")] if args.pairs else None
    try:
        written = ingest(Path(args.export_dir), Path(args.out_dir), pairs)
    except FileNotFoundError as e:
        print(f"nothing ingested: {e}")
        return 1
    for pair, path in written.items():
        n = len(__import__("pandas").read_parquet(path))
        print(f"ingested {pair}: {n:,} ticks -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())