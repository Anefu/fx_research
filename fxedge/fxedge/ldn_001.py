"""FX-LDN-001 — Unconditional London-session behavior (pre-registered).

Registry section 20, verbatim in intent:
  Universe: FRZ.primary_universe (6 pairs)
  Asia window:    00:00-06:59 Europe/London (inclusive)  -> [00:00, 07:00)
  London window:  07:00-10:00 Europe/London (inclusive)  -> [07:00, 10:01)
  For each session:
      AsiaRange, LondonRange, ExpansionRatio = LondonRange / AsiaRange
      R_15m, R_30m, R_60m, R_180m measured from 07:00 London close onward
      |R_h| versions
      I(ER > 1), I(ER > 1.5)
  No entry rule. No stops. No targets. No ICT concepts. No optimization.

Output: FX-LDN-001 base-rate report (per pair + pooled), written to runs/.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from fxedge.bars import build_bars
from fxedge.sessions import SessionEngine

UTC = "UTC"


def _window_hilo(bars: pd.DataFrame, start_utc: pd.Timestamp, end_utc: pd.Timestamp,
                 col_h: str, col_l: str) -> Optional[tuple]:
    """High/low across 1m bars whose *interval* overlaps [start, end).

    Bars are labeled by interval start; a 1m bar starting at t covers [t, t+1m).
    We select bars with start >= start_utc and start + 1m <= end_utc, i.e. fully
    inside the window. Window boundaries are minute stamps, so this is exact.
    """
    if bars.empty:
        return None
    sel = bars.loc[(bars.index >= start_utc) & (bars.index < end_utc)]
    if sel.empty:
        return None
    return float(sel[col_h].max()), float(sel[col_l].min())


def _forward_return(bars: pd.DataFrame, t0: pd.Timestamp, minutes: int,
                    from_col: str = "mid_c", to_col: str = "mid_c") -> Optional[float]:
    """PnL-in-pips-free signed return in price units: close(t0 + minutes) / close(t0) - 1.

    Uses the bar labeled exactly t0 + minutes - 1m on 1m bars (close of that bar
    is the price at t0 + minutes). Price units are the pair's own (not pips).
    """
    t1 = t0 + pd.Timedelta(minutes=minutes)
    a = bars[from_col].asof(pd.Timestamp(t0 - pd.Timedelta(minutes=1)))
    b = bars[to_col].asof(pd.Timestamp(t1 - pd.Timedelta(minutes=1)))
    if a is None or b is None or not np.isfinite(a) or not np.isfinite(b) or a == 0:
        return None
    return float(b / a - 1.0)


def compute_sessions(ticks: pd.DataFrame, pair: str, frz, engine: SessionEngine,
                     first_day: date, last_day: date) -> pd.DataFrame:
    """Build the FX-LDN-001 per-session table for one pair. Needs 1m bars."""
    bars_1m = build_bars(ticks, rule="1m")
    rows = []
    for asia, ldn, dst in engine.sessions_for_range(first_day, last_day):
        a_start = pd.Timestamp(asia.start_utc)
        a_end = pd.Timestamp(asia.end_utc)
        l_start = pd.Timestamp(ldn.start_utc)
        l_end = pd.Timestamp(ldn.end_utc)
        in_range = (bars_1m.index >= a_start) & (bars_1m.index < l_end)
        n_ticks = int(in_range.sum())
        if n_ticks < 10:
            rows.append({"pair": pair, "london_date": asia.london_date, "valid": False,
                         "reason": "no-data", "dst_summer": dst, "weekday": asia.london_date})
            continue
        aa = _window_hilo(bars_1m, a_start, a_end, "bid_h", "bid_l")
        ll = _window_hilo(bars_1m, l_start, l_end, "bid_h", "bid_l")
        if aa is None or ll is None:
            rows.append({"pair": pair, "london_date": asia.london_date, "valid": False,
                         "reason": "missing-window-data", "dst_summer": dst})
            continue
        asia_range = aa[0] - aa[1]
        ldn_range = ll[0] - ll[1]
        if asia_range <= 0:
            rows.append({"pair": pair, "london_date": asia.london_date, "valid": False,
                         "reason": "zero-asia-range", "dst_summer": dst})
            continue
        er = ldn_range / asia_range
        t0 = l_start
        row = {
            "pair": pair,
            "london_date": asia.london_date,
            "valid": True,
            "reason": "",
            "dst_summer": bool(dst),
            "asia_high": aa[0], "asia_low": aa[1], "asia_range": asia_range,
            "ldn_high": ll[0], "ldn_low": ll[1], "ldn_range": ldn_range,
            "expansion_ratio": er,
            "er_gt_1": int(er > 1.0),
            "er_gt_15": int(er > 1.5),
        }
        for h in frz.forward_horizons_min:
            r = _forward_return(bars_1m, t0, h)
            row[f"r_{h}m"] = r if r is not None else np.nan
            row[f"absr_{h}m"] = abs(r) if r is not None else np.nan
        rows.append(row)
    df = pd.DataFrame(rows)
    return df


def _stats(v: pd.Series) -> dict:
    v = pd.Series(v).dropna().astype(float)
    if v.empty:
        return {"n": 0}
    return {
        "n": int(len(v)),
        "mean": float(v.mean()),
        "median": float(v.median()),
        "std": float(v.std(ddof=1)) if len(v) > 1 else None,
        "p10": float(v.quantile(0.10)),
        "p25": float(v.quantile(0.25)),
        "p75": float(v.quantile(0.75)),
        "p90": float(v.quantile(0.90)),
    }


def _yearly_breakdown(df: pd.DataFrame, col: str) -> Dict[str, dict]:
    out = {}
    for y, g in df.groupby(df["london_date"].str[:4]):
        out[y] = _stats(g[col])
    return out


def run_ldn_001(ticks_by_pair: Dict[str, pd.DataFrame], frz) -> Dict:
    """Run the full pre-registered FX-LDN-001 for every pair in `ticks_by_pair`.

    Returns a nested report dict; also writes runs/FX-LDN-001/report.json,
    sessions.parquet, and a markdown summary next to this package.
    """
    engine = SessionEngine(frz)
    all_dates = []
    for pair, ticks in ticks_by_pair.items():
        all_dates.append(ticks.index.min())
        all_dates.append(ticks.index.max())
    first_day = pd.Timestamp(min(all_dates)).tz_convert(UTC).date() if min(all_dates).tzinfo else pd.Timestamp(min(all_dates)).date()
    last_day = pd.Timestamp(max(all_dates)).tz_convert(UTC).date() if max(all_dates).tzinfo else pd.Timestamp(max(all_dates)).date()

    tables = {}
    for pair, ticks in ticks_by_pair.items():
        tables[pair] = compute_sessions(ticks, pair, frz, engine, first_day, last_day)
    sessions = pd.concat(tables.values(), ignore_index=True)
    valid = sessions[sessions["valid"] == True].copy()

    cols_ranges = ["asia_range", "ldn_range", "expansion_ratio"]
    cols_abs = [f"absr_{h}m" for h in frz.forward_horizons_min]
    cols_dir = [f"r_{h}m" for h in frz.forward_horizons_min]

    report = {
        "experiment": "FX-LDN-001",
        "registry_version": "1.0",
        "universe": list(ticks_by_pair.keys()),
        "data_period": {"first_day": str(first_day), "last_day": str(last_day)},
        "frozen": {
            "asia_window": f"{frz.asia_start}-{frz.asia_end} Europe/London (inclusive)",
            "london_window": f"{frz.london_window_start}-{frz.london_window_end} Europe/London (inclusive)",
            "expansion_events": {">1.0": frz.expansion_event_1, ">1.5": frz.expansion_event_2},
            "forward_horizons_min": list(frz.forward_horizons_min),
        },
        "per_pair": {},
        "pooled": {},
        "yearly_by_pair": {},
    }

    for pair in ticks_by_pair:
        pv = valid[valid["pair"] == pair]
        pv_invalid = int(sessions[(sessions["pair"] == pair) & (sessions["valid"] == False)].shape[0])
        r = {"sessions_valid": int(len(pv)), "sessions_invalid": pv_invalid}
        for c in cols_ranges:
            r[c] = _stats(pv[c])
        r["p_er_gt_1"] = float(pv["er_gt_1"].mean()) if len(pv) else None
        r["p_er_gt_15"] = float(pv["er_gt_15"].mean()) if len(pv) else None
        for c in cols_abs + cols_dir:
            r[c] = _stats(pv[c])
        r["dst_summer_share"] = float(pv["dst_summer"].mean()) if len(pv) else None
        report["per_pair"][pair] = r

    for c in cols_ranges:
        report["pooled"][c] = _stats(valid[c])
    report["pooled"]["p_er_gt_1"] = float(valid["er_gt_1"].mean()) if len(valid) else None
    report["pooled"]["p_er_gt_15"] = float(valid["er_gt_15"].mean()) if len(valid) else None
    for c in cols_abs + cols_dir:
        report["pooled"][c] = _stats(valid[c])

    for pair in ticks_by_pair:
        report["yearly_by_pair"][pair] = {y: _stats(g[c]) for y, g in
                                          valid[valid["pair"] == pair].groupby(valid["london_date"].str[:4])
                                          for c in ["expansion_ratio"]}

    out_dir = Path("runs") / "FX-LDN-001"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, default=str))
    sessions.to_parquet(out_dir / "sessions.parquet")
    return report, sessions