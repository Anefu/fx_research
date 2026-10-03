"""Coverage-bounded session computation (audit A2/A3).

Each session reports window coverage explicitly; forward returns are computed
only when both the origin quote and the horizon-end quote satisfy quote-age
bounds. Sessions failing coverage are marked invalid with a machine-readable
reason and are never silently dropped.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

MAX_QUOTE_AGE_MIN = 5.0  # audit A2: last quote must be fresher than this for any reading


def _last_within(df: pd.DataFrame, ts: pd.Timestamp, col: str):
    """Bar close at or before ts, requiring the bar to be fresh (bounded age)."""
    sel = df.loc[:ts, col]
    if sel.empty:
        return None
    v = sel.iloc[-1]
    age = (ts - sel.index[-1]).total_seconds() / 60.0
    if age > MAX_QUOTE_AGE_MIN:
        return None
    return float(v), age


def window_hilo(bars: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp,
                min_ticks_window: int = 30) -> Optional[Tuple[float, float]]:
    """High/low across 1m bars fully inside [start, end), with coverage floor.

    min_ticks_window: at least this many bar minutes present in a 7h (Asia,
    420 min) or 3h (London, 181 min) window; below => coverage failure.
    """
    if bars.empty:
        return None
    sel = bars.loc[(bars.index >= start) & (bars.index < end)]
    if len(sel) < min_ticks_window:
        return None
    return float(sel["bid_h"].max()), float(sel["bid_l"].min())


def forward_return(bars_1m: pd.DataFrame, t0: pd.Timestamp, minutes: int) -> Optional[float]:
    """Signed return over [t0 - 1m close, t0 + minutes - 1m close], both fresh."""
    a = _last_within(bars_1m, t0 - pd.Timedelta(minutes=1), "mid_c")
    if a is None:
        return None
    b = _last_within(bars_1m, t0 + pd.Timedelta(minutes=minutes) - pd.Timedelta(minutes=1), "mid_c")
    if b is None:
        return None
    if a[0] == 0 or not np.isfinite(a[0]) or not np.isfinite(b[0]):
        return None
    return float(b[0] / a[0] - 1.0)


def compute_sessions_coverage(ticks_month: pd.DataFrame, pair: str, frz,
                              engine, day_lo: date, day_hi: date) -> pd.DataFrame:
    """FX-LDN-001 session table for the ticks slice, with explicit coverage checks."""
    from fxedge.bars import build_bars
    if ticks_month.empty:
        return pd.DataFrame()
    bars_1m = build_bars(ticks_month, rule="1m")
    rows = []
    for asia, ldn, dst in engine.sessions_for_range(day_lo, day_hi):
        if asia.start_utc < ticks_month.index[0] or ldn.end_utc > ticks_month.index[-1]:
            # window edges outside this slice: another month's runner handles it
            edge = "next" if ldn.start_utc > ticks_month.index[-1] else "prev"
            continue
        a_start, a_end = pd.Timestamp(asia.start_utc), pd.Timestamp(asia.end_utc)
        l_start, l_end = pd.Timestamp(ldn.start_utc), pd.Timestamp(ldn.end_utc)
        aa = window_hilo(bars_1m, a_start, a_end, min_ticks_window=350)   # ~83% of 420 min
        ll = window_hilo(bars_1m, l_start, l_end, min_ticks_window=150)   # ~83% of 181 min
        base = {"pair": pair, "london_date": asia.london_date, "dst_summer": dst,
                "asia_hi": np.nan, "asia_lo": np.nan, "ldn_hi": np.nan, "ldn_lo": np.nan,
                "valid": False, "reason": ""}
        if aa is None or ll is None:
            base["reason"] = "window-coverage"
            rows.append(base)
            continue
        asia_range = aa[0] - aa[1]
        ldn_range = ll[0] - ll[1]
        if asia_range <= 0:
            base["reason"] = "zero-asia-range"
            rows.append(base)
            continue
        row = dict(base)
        row.update({"asia_hi": aa[0], "asia_lo": aa[1], "asia_range": asia_range,
                    "ldn_hi": ll[0], "ldn_lo": ll[1], "ldn_range": ldn_range,
                    "expansion_ratio": ldn_range / asia_range,
                    "valid": True, "reason": ""})
        t0 = l_start
        for h in frz.forward_horizons_min:
            r = forward_return(bars_1m, t0, h)
            row[f"r_{h}m"] = r if r is not None else np.nan
            row[f"absr_{h}m"] = abs(r) if r is not None else np.nan
            if r is None and "horizon-missing" not in row["reason"]:
                row["reason"] = "horizon-missing"
        rows.append(row)
    return pd.DataFrame(rows)


# keep the old name working for callers that don't need coverage semantics
compute_sessions = compute_sessions_coverage