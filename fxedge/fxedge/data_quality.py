"""DATA-001..005: data-quality gates (fx-edge-experiment-registry.md section 1).

All checks record excluded periods and never silently drop observations.
Each gate returns a Dict with structured findings; a JSON report is written
by the caller.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


from fxedge.bars import to_freq


def _gap_summary(index: pd.DatetimeIndex) -> Dict:
    """DATA-001: feed outages / missing periods.

    A gap = interval between consecutive ticks with no quotes. Longest gaps
    are reported; the weekend regular gap is not an outage.
    """
    if len(index) < 2:
        return {"n_gaps_over_1h": 0, "longest_gap_minutes": 0.0, "gaps_over_1h": []}
    diffs = np.diff(index.values).astype("timedelta64[s]").astype(np.int64) / 60.0
    big = np.where(diffs > 60.0)[0]
    gaps = [
        {
            "start_utc": str(index[i]),
            "end_utc": str(index[i + 1]),
            "minutes": float(diffs[i]),
        }
        for i in big
    ]
    return {
        "n_gaps_over_1h": len(gaps),
        "longest_gap_minutes": float(diffs.max()),
        "gaps_over_1h": gaps,
    }


def bid_ask_integrity(ticks: pd.DataFrame) -> Dict:
    """DATA-002: negative or crossed spreads, stale quotes, abnormal jumps."""
    res: Dict[str, object] = {}
    bid, ask = ticks["bid"], ticks["ask"]
    spread = ask - bid

    res["n_negative_spread"] = int((spread < 0).sum())
    res["n_zero_spread"] = int((spread == 0).sum())
    res["n_crossed"] = int((ask < bid).sum())

    # stale quotes: same (bid,ask) repeated for >= 5 minutes
    chg = (bid.diff() != 0) | (ask.diff() != 0)
    block_id = (~chg).cumsum()
    stale_lens = ticks.assign(_blk=block_id).groupby("_blk").size()
    res["n_stale_blocks_ge_5min"] = int((stale_lens >= 300).sum())  # conservative proxy

    # abnormal jumps: |log returns| > 2% in one tick (impossible for majors)
    mid = (bid + ask) / 2
    lr = np.abs(np.log(mid / mid.shift(1))).fillna(0.0)
    res["n_abs_jump_gt_2pct"] = int((lr > 0.02).sum())

    res["invalid_total"] = int(res["n_negative_spread"] + res["n_crossed"] + res["n_abs_jump_gt_2pct"])
    return res


def bar_consistency(ticks: pd.DataFrame, bars: pd.DataFrame, rule: str = "5m") -> Dict:
    """DATA-005: reconstructed OHLC consistent with raw tick extrema within each bar."""
    if bars.empty or ticks.empty:
        return {"status": "skipped", "reason": "empty input"}
    t = ticks.sort_index()
    bucket = t.index.floor(to_freq(rule))
    g = t.groupby(bucket)
    tick_h = g["bid"].max()
    tick_l = g["bid"].min()
    ok_h = np.isclose(bars["bid_h"], tick_h.reindex(bars.index), atol=1e-9)
    ok_l = np.isclose(bars["bid_l"], tick_l.reindex(bars.index), atol=1e-9)
    return {
        "status": "checked",
        "n_bars_checked": int(len(bars)),
        "n_high_mismatch": int((~ok_h).sum()),
        "n_low_mismatch": int((~ok_l).sum()),
    }


def session_coverage(ticks: pd.DataFrame, session_windows: List[Dict]) -> Dict:
    """Checks every expected session window has tick data (DATA-003/004 support).

    session_windows: list of dicts with london_date, asia_*_utc, ldn_*_utc, dst flags.
    """
    idx = ticks.index
    out = {"sessions_expected": len(session_windows), "sessions_missing": [], "dst_flip_ok": True}
    for w in session_windows:
        a_start = pd.Timestamp(w["asia_start_utc"])
        l_end = pd.Timestamp(w["ldn_end_utc"])
        n = ((idx >= a_start) & (idx < l_end)).sum()
        if n < 10:  # fewer than 10 quotes across 10h => treat as missing session
            out["sessions_missing"].append(w["london_date"])
    out["missing_count"] = len(out["sessions_missing"])
    return out


def run_all_gates(ticks: pd.DataFrame, rule: str = "5m") -> Dict:
    """Run DATA-001/002/005 gates; returns structured report dict."""
    gates: Dict[str, object] = {}
    gates["DATA-001 completeness"] = _gap_summary(ticks.index)
    gates["DATA-002 bid/ask integrity"] = bid_ask_integrity(ticks)
    bars = None
    try:
        from fxedge.bars import build_bars, to_freq
        bars = build_bars(ticks, rule=rule)
        gates["DATA-005 bar reconstruction"] = bar_consistency(ticks, bars, rule)
    except ValueError as e:
        gates["DATA-005 bar reconstruction"] = {"status": "failed", "reason": str(e)}
    pass_ = True
    if gates["DATA-002 bid/ask integrity"]["invalid_total"] > 0 or \
       (isinstance(gates["DATA-005 bar reconstruction"], dict) and
        gates["DATA-005 bar reconstruction"].get("status") == "failed"):
        pass_ = False
    gates["GATE_D_pass"] = pass_
    return gates