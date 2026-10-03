"""Bar construction from tick Bid/Ask data.

Registry section 0: derive bars ourselves; retain Bid OHLC, Ask OHLC where
practical, spread statistics, tick count. Data is UTC.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def to_freq(rule: str) -> str:
    """Registry bar labels use minutes ("5m"); pandas requires "5min"."""
    if rule.endswith("m") and not rule.endswith("min"):
        return rule[:-1] + "min"
    return rule


def build_bars(ticks: pd.DataFrame, rule: str = "5m", spread_cap_frac: float = 0.5) -> pd.DataFrame:
    """Aggregate tick Bid/Ask quotes into OHLC bars (UTC index).

    Parameters
    ----------
    ticks : DataFrame indexed by UTC timestamp with columns
        bid, ask, (optional) last.
    rule : bar grid label, e.g. "1m", "5m", "15m" (converted internally to "min").

    Returns
    -------
    DataFrame with columns:
        bid_o, bid_h, bid_l, bid_c, ask_c, mid_o, mid_h, mid_l, mid_c,
        spread_min, spread_med, spread_max, ticks
    """
    required = {"bid", "ask"}
    missing = required - set(ticks.columns)
    if missing:
        raise ValueError(f"ticks missing columns: {missing}")
    if ticks.empty:
        return pd.DataFrame()

    freq = to_freq(rule)
    df = ticks.sort_index()
    df = df[~df.index.duplicated(keep="last")]  # duplicate timestamps: keep last
    spread = df["ask"] - df["bid"]
    if (spread < 0).any():
        bad = spread[spread < 0]
        raise ValueError(f"negative spreads in source ticks ({len(bad)} rows); run data_quality first")
    df = df.assign(mid=(df["bid"] + df["ask"]) / 2, spread=spread)

    mid = df["mid"]
    spread_s = df["spread"]
    ticks_col = (
        df["last"].resample(freq).count()
        if "last" in df.columns
        else df["bid"].resample(freq).count()
    )

    out = pd.DataFrame({
        "bid_o": df["bid"].resample(freq).first(),
        "bid_h": df["bid"].resample(freq).max(),
        "bid_l": df["bid"].resample(freq).min(),
        "bid_c": df["bid"].resample(freq).last(),
        "ask_c": df["ask"].resample(freq).last(),
        "mid_o": mid.resample(freq).first(),
        "mid_h": mid.resample(freq).max(),
        "mid_l": mid.resample(freq).min(),
        "mid_c": mid.resample(freq).last(),
        "spread_min": spread_s.resample(freq).min(),
        "spread_med": spread_s.resample(freq).median(),
        "spread_max": spread_s.resample(freq).max(),
        "ticks": ticks_col,
    })
    # Drop bars with no ticks (weekends, gaps) but keep a marker.
    out["n_ticks"] = out["ticks"].fillna(0).astype(int)
    return out.dropna(subset=["bid_o", "bid_h", "bid_l", "bid_c"])


def window_range(bars: pd.DataFrame, start_utc: pd.Timestamp, end_utc: pd.Timestamp,
                 col: str = "bid_h", col_low: str = "bid_l") -> Optional[tuple]:
    """Max/Min of price over [start, end) using bars whose interval overlaps the window.

    Uses bar OHLC on 1m bars (registry decision bars are 5m; window boundaries
    are computed on the finest available bars). Returns (high, low) or None.
    """
    if bars.empty:
        return None
    m = (bars.index >= start_utc) & (bars.index < end_utc)
    sel = bars.loc[m, [col, col_low]]
    if sel.empty:
        return None
    return float(sel[col].max()), float(sel[col_low].min())


def window_close_or_last(bars: pd.DataFrame, ts_utc: pd.Timestamp,
                         col: str = "mid_c") -> Optional[float]:
    """Last close at or before ts_utc."""
    sel = bars.loc[bars.index <= ts_utc, col]
    if sel.empty:
        return None
    return float(sel.iloc[-1])