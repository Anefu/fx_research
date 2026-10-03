"""CLI runner: quality gates + FX-LDN-001 over tick data.

Usage:
  python -m fxedge --data-root PATH [--pairs EURUSD,...] [--rule 5m]

Data layout expected (fxedge/data/fxedge/<PAIR>.parquet):
  tick files indexed by UTC datetime with columns bid, ask.

Produces:
  runs/quality_gates.json
  runs/FX-LDN-001/report.json
  runs/FX-LDN-001/sessions.parquet
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from fxedge.bars import build_bars
from fxedge.data_quality import run_all_gates
from fxedge.ldn_001 import run_ldn_001
from fxedge.registry import FRZ, REGISTRY_VERSION, validate_freeze
from fxedge.sessions import SessionEngine


def load_ticks(data_root: Path, pair: str) -> pd.DataFrame:
    path = data_root / f"{pair}.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        df.index = pd.to_datetime(df.index, utc=True)
        return df
    raise FileNotFoundError(
        f"missing tick file: {path}\n"
        "Generate synthetic demo data:  python -m fxedge.demo_data\n"
        "Or ingest a real MT5 export:    python -m fxedge.ingest_mt5"
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description="fxedge: DATA gates + FX-LDN-001")
    ap.add_argument("--data-root", default="data/fxedge")
    ap.add_argument("--pairs", default=",".join(FRZ.primary_universe))
    ap.add_argument("--rule", default="5m")
    args = ap.parse_args(argv)

    problems = validate_freeze()
    if problems:
        print("FATAL: frozen-registry inconsistency:", problems)
        return 2

    data_root = Path(args.data_root)
    pairs = [p.strip().upper() for p in args.pairs.split(",") if p.strip()]

    ticks_by_pair = {}
    for pair in pairs:
        try:
            ticks_by_pair[pair] = load_ticks(data_root, pair)
            print(f"loaded {pair}: {len(ticks_by_pair[pair]):,} ticks")
        except FileNotFoundError as e:
            msg = str(e)
            print(f"  {pair}: {msg.splitlines()[0]}")

    if not ticks_by_pair:
        print("No data loaded. Generate synthetic demo data first:")
        print("  python -m fxedge.demo_data")
        return 1

    gates = {}
    for pair, ticks in ticks_by_pair.items():
        gates[pair] = run_all_gates(ticks, rule=args.rule)
        print(f"DATA gates {pair}: GATE_D_pass={gates[pair]['GATE_D_pass']} "
              f"(invalid={gates[pair]['DATA-002 bid/ask integrity']['invalid_total']})")

    out = Path("runs")
    out.mkdir(parents=True, exist_ok=True)
    (out / "quality_gates.json").write_text(json.dumps(gates, indent=2, default=str))

    report, sessions = run_ldn_001(ticks_by_pair, FRZ)
    print(json.dumps(report["pooled"], indent=2, default=str))
    print(f"\nFX-LDN-001 complete: {len(sessions)} sessions, "
          f"{int(sessions['valid'].sum())} valid. Reports in runs/FX-LDN-001/")
    return 0


if __name__ == "__main__":
    sys.exit(main())