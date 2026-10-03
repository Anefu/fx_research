"""Calendar-boundary-safe FX-LDN runner v2 — audit fixes A1/A3.

Processes one London-calendar day at a time over a padded tick slice, so
month-end sessions never duplicate or truncate. Enforces uniqueness of
(pair, london_date). Requires data coverage; empty/failed mandatory checks
block downstream. Writes a run manifest with input fingerprints.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from fxedge.registry import FRZ, REGISTRY_VERSION
from fxedge.sessions import SessionEngine
from fxedge.shard_reader import read_pair, shard_root_default
from fxedge.sessions_cov import compute_sessions_coverage

UTC = "UTC"


def month_bounds(ym: int) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Explicit month boundaries (no pandas MonthEnd arithmetic)."""
    y, m = divmod(ym, 100)
    start = pd.Timestamp(f"{y:04d}-{m:02d}-01", tz="UTC")
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    end = pd.Timestamp(f"{ny:04d}-{nm:02d}-01", tz="UTC") - pd.Timedelta(microseconds=1)
    return start, end


def padded_read_days(pair: str, ym: int, root: Path, pad_days: int = 2) -> pd.DataFrame:
    """One month's ticks + pad_days on each side (for London windows near
    UTC-shard edges). Callers slice per-day windows from this."""
    s0, e1 = month_bounds(ym)
    s = s0 - pd.Timedelta(days=pad_days)
    e = e1 + pd.Timedelta(days=pad_days)
    return read_pair(pair, s, e, root)


def sha256_file(p: Path, n_bytes: Optional[int] = None) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        if n_bytes:
            h.update(f.read(n_bytes))
        else:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()


def fingerprint_store(root: Path) -> Dict:
    """Per-pair: shard count, span, byte sizes, sampled hashes."""
    inv = {}
    for pdir in sorted(root.glob("*")):
        if not pdir.is_dir():
            continue
        shards = sorted(pdir.glob("*.parquet"))
        if not shards:
            continue
        yms = sorted(int(m) for m in [re.match(r"^(\d{6})", s.stem).group(1) for s in shards])
        inv[pdir.name] = {
            "n_shards": len(shards),
            "first_month": yms[0],
            "last_month": yms[-1],
            "bytes_total": sum(s.stat().st_size for s in shards),
            "hash_first_shard_head": sha256_file(shards[0], 1 << 16),
            "hash_last_shard_head": sha256_file(shards[-1], 1 << 16),
        }
    return inv


def run_ldn_001_v2(out_dir=None, root=None, pairs=None) -> pd.DataFrame:
    root = root or shard_root_default()
    out_dir = Path(out_dir or "runs/FX-LDN-001-v2")
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = SessionEngine(FRZ)
    all_parts = []
    manifest = {
        "runner": "fxedge.real_run_v2.run_ldn_001_v2",
        "registry_version": REGISTRY_VERSION,
        "frozen": {"asia": f"{FRZ.asia_start}-{FRZ.asia_end}", "london": f"{FRZ.london_window_start}-{FRZ.london_window_end}"},
        "store_fingerprint": None,
        "exclusions": {},
        "unique_sessions": {},
    }
    manifest["store_fingerprint"] = fingerprint_store(root)

    for pair in (pairs or FRZ.primary_universe):
        print(f"{pair}: ...", end=" ", flush=True)
        # month list for this pair
        months = sorted(int(re.match(r"^(\d{6})", p.stem).group(1))
                        for p in (root / pair).glob("*.parquet"))
        pair_rows = []
        exclusions = {}
        for ym in months:
            # determine days this month's runner owns: the London-local days whose
            # Asia window starts inside the month (00:00 London) — mapped to UTC days.
            s0, _ = month_bounds(ym)
            days = []
            for d in pd.date_range(s0, periods=32 + 2, freq="D").date:
                r = engine.asia_and_london(d)
                if r is None:
                    continue
                if s0 <= r[0].start_utc < month_bounds(ym)[1]:
                    days.append(d)
            if not days:
                continue
            lo, hi = min(days), max(days)
            df = padded_read_days(pair, ym, root)
            if df.empty:
                exclusions[str(ym)] = "no-ticks-in-padded-window"
                continue
            # feed only the padded tick window for the owned days
            a1 = engine.asia_and_london(lo)[0]
            a2 = engine.asia_and_london(hi)[1]
            sl = df.loc[pd.Timestamp(a1.start_utc) - pd.Timedelta(minutes=5):
                        pd.Timestamp(a2.end_utc) + pd.Timedelta(minutes=5)]
            if sl.empty:
                exclusions[str(ym)] = "no-ticks-adjacent"
                continue
            sess = compute_sessions_coverage(sl, pair, FRZ, engine, lo, hi)
            if sess.empty:
                exclusions[str(ym)] = "no-sessions-computed"
                continue
            # split valid / invalid
            inv = sess[~sess["valid"]]
            if len(inv):
                for reason, n in inv["reason"].value_counts().items():
                    exclusions[f"{ym}:{reason}"] = int(n)
            pair_rows.append(sess[sess["valid"]])

        if not pair_rows:
            manifest["unique_sessions"][pair] = 0
            manifest["exclusions"][pair] = exclusions
            print("EMPTY — downstream blocked")
            continue

        pv = pd.concat(pair_rows, ignore_index=True)
        # enforce uniqueness of (pair, london_date) — audit A1
        n_before = len(pv)
        pv = pv.drop_duplicates(subset=["pair", "london_date"], keep="first").sort_values("london_date")
        if len(pv) != n_before:
            exclusions["duplicate-london_dates"] = n_before - len(pv)
        manifest["unique_sessions"][pair] = int(len(pv))
        manifest["exclusions"][pair] = exclusions
        all_parts.append(pv)
        print(f"{len(pv)} unique valid sessions ({n_before} pre-dedup)")

    sessions = pd.concat(all_parts, ignore_index=True) if all_parts else pd.DataFrame()
    manifest["total_unique_valid"] = int(len(sessions))
    sessions.to_parquet(out_dir / "sessions.parquet")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print("wrote", out_dir)
    return sessions


if __name__ == "__main__":
    args = sys.argv[1:]
    pairs = args[0].split(",") if args else None
    run_ldn_001_v2(pairs=pairs)