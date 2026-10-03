"""Synthetic tick data generator for pipeline validation (NOT research data).

Produces deterministic, physically plausible FX ticks for the frozen registry
universe. Two regimes are built in so every downstream check has known
expectations:

  - normal sessions: volatility w = 1.0
  - compressed-then-expanded sessions (Fridays): Asia noise shrinks by kComp
    while the 08:00 London "expansion burst" is larger, so
    E[LondonRange/AsiaRange | compressed] > E[ER | all] by construction.

Windows and DST follow Section 0 of the registry; the generator quotes ticks
every 30 seconds (2 ticks/minute) during the whole week so every session
window is fully populated and Sunday contamination is impossible.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from fxedge.registry import FRZ
from fxedge.sessions import SessionEngine

UTC = timezone.utc

PIPS: dict = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "AUDUSD": 0.0001,
    "USDJPY": 0.01, "USDCAD": 0.0001, "USDCHF": 0.0001,
}
LEVELS: dict = {
    "EURUSD": 1.10, "GBPUSD": 1.27, "USDJPY": 150.0,
    "AUDUSD": 0.66, "USDCAD": 1.35, "USDCHF": 0.92,
}
BASE_SPREAD: dict = {
    "EURUSD": 0.6, "GBPUSD": 0.9, "USDJPY": 0.7,
    "AUDUSD": 0.9, "USDCAD": 1.5, "USDCHF": 1.1,  # in pips
}


def generate_pair(pair: str, first_day: date, last_day: date, seed: int,
                  comp_frac: float = 0.30) -> pd.DataFrame:
    """One synthetic series in UTC index with bid/ask columns."""
    rng = np.random.default_rng(seed)
    engine = SessionEngine(FRZ)
    pip = PIPS[pair]
    level = LEVELS[pair]
    spread_pips = BASE_SPREAD[pair]

    ts = []
    bid = []
    d = first_day
    price = level
    while d <= last_day:
        r = engine.asia_and_london(d)
        if r is not None:
            asia, ldn, dst = r
            is_friday = d.weekday() == 4
            comp = is_friday and (rng.random() < comp_frac)  # Friday => compressed Asia + expansion

            k_asis = 0.35 if comp else 1.0   # compressed Asia noise
            burst = 4.0 if comp else 1.0     # larger London burst on compressed days

            # Asia window ticks: 30-second grid
            n_asia = int((asia.end_utc - asia.start_utc).total_seconds() // 30)
            for i in range(n_asia):
                t = asia.start_utc + timedelta(seconds=30 * i)
                sigma_pips = 0.25 * k_asis
                price += rng.normal(0.0, sigma_pips * pip)
                bid.append(price - (spread_pips / 2) * pip)
                ts.append(t)
            # London window ticks + one 08:00 burst
            n_ldn = int((ldn.end_utc - ldn.start_utc).total_seconds() // 30)
            for i in range(n_ldn):
                t = ldn.start_utc + timedelta(seconds=30 * i)
                sigma_pips = 0.25 * burst if t.hour == 8 else 0.55
                price += rng.normal(0.0, sigma_pips * pip)
                bid.append(price - (spread_pips / 2) * pip)
                ts.append(t)
        d += timedelta(days=1)

    bid_arr = np.asarray(bid)
    ask_arr = bid_arr + spread_pips * pip
    idx = pd.DatetimeIndex(pd.to_datetime(ts, utc=True), name=None)
    df = pd.DataFrame({"bid": bid_arr, "ask": ask_arr}, index=idx)
    return df[~df.index.duplicated(keep="last")].sort_index()


def generate(first_day: date, last_day: date, out_dir: Path = Path("data/fxedge")) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, pair in enumerate(FRZ.primary_universe):
        df = generate_pair(pair, first_day, last_day, seed=42 + i)
        df.to_parquet(out_dir / f"{pair}.parquet")
        print(f"generated {pair}: {len(df):,} ticks")


if __name__ == "__main__":
    from datetime import date as D
    generate(D(2022, 1, 3), D(2023, 12, 29))