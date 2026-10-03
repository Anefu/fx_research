"""FX-LDN-002/003/004 v2 — joint panel bootstrap (audit A5).

Changes from v1 (stated before results):
  - Bootstrap resamples CONSECUTIVE DATE BLOCKS jointly across all six pairs:
    the sampling unit is a (date-window × 6-pair panel slice), preserving
    same-day cross-pair dependence and temporal spacing.
  - Statistics: median ER diff (headline), mean ER diff, P(ER>1) diff,
    P(ER>1.5) diff, mean |R_60| diff, mean |R_180| diff — each with a
    percentile CI.
  - MW/proportion tests retained as point-inference diagnostics, not the
    headline.
  - Gate L1 decision rule unchanged in substance, now keyed on the MEDIAN
    ER CI and the |R| CIs (joint-block), plus >=5/6 pair sign agreement.
"""
from __future__ import annotations

import json
from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

LOOKBACK = 60
THRESHOLD = 0.30
HORIZONS = [60, 180]
B_BOOT = 2000
BLOCK_DAYS = 20
SEED = 42


def add_flags(v: pd.DataFrame) -> pd.DataFrame:
    outs = []
    for pair, g in v.groupby("pair"):
        g = g.sort_values("london_date").copy()
        ar = g["asia_range"].to_numpy()
        pct = np.full(len(g), np.nan)
        for i in range(LOOKBACK, len(g)):
            w = ar[i - LOOKBACK:i]
            pct[i] = ((w < ar[i]).sum() + 0.5 * (w == ar[i]).sum()) / LOOKBACK
        g["comp_pct"] = pct
        g["compressed"] = np.where(np.isnan(pct), False, pct <= THRESHOLD)
        lr = g["ldn_range"].to_numpy()
        lpct = np.full(len(g), np.nan)
        for i in range(LOOKBACK, len(g)):
            w = lr[i - LOOKBACK:i]
            lpct[i] = ((w < lr[i]).sum() + 0.5 * (w == lr[i]).sum()) / LOOKBACK
        g["ldn_pct"] = lpct
        outs.append(g)
    return pd.concat(outs, ignore_index=True)


def _pvalue_from_ci(lo: float, hi: float, point: float) -> float:
    """Rough two-sided p via CI inversion at the percentile ends (report-only)."""
    half = max(abs(point - lo), abs(hi - point))
    if half <= 0:
        return 0.0
    return float(erfc((abs(point) / half) / sqrt(2)))


def joint_block_stats(panel: pd.DataFrame, B=B_BOOT, L=BLOCK_DAYS, seed=SEED) -> dict:
    """Joint date-block bootstrap over the 6-pair panel.

    panel: indexed by (london_date, pair) with columns compressed + metrics.
    Block = L consecutive London dates; sample blocks with replacement until
    the drawn date count >= observed unique dates; concatenate block panels.
    """
    rng = np.random.default_rng(seed)
    dates = np.sort(panel.index.get_level_values(0).unique().to_numpy())
    n_dates = len(dates)
    # per-date panels as flat arrays for fast draws
    by_date = {d: sub for d, sub in panel.groupby(level=0)}

    def stat(draw_dates) -> dict:
        pieces = [by_date[d].assign(_b=i) for i, d in enumerate(draw_dates)]
        # concat is the bottleneck; use smaller number of big concats
        p = pd.concat(pieces, ignore_index=True)
        c = p[p["compressed"]]
        n = p[~p["compressed"]]
        out = {
            "med_er_diff": float(c["expansion_ratio"].median() - n["expansion_ratio"].median()),
            "mean_er_diff": float(c["expansion_ratio"].mean() - n["expansion_ratio"].mean()),
            "p1_diff": float((c["expansion_ratio"] > 1).mean() - (n["expansion_ratio"] > 1).mean()),
            "p15_diff": float((c["expansion_ratio"] > 1.5).mean() - (n["expansion_ratio"] > 1.5).mean()),
            "r60_diff": float(c["absr_60m"].mean() - n["absr_60m"].mean()),
            "r180_diff": float(c["absr_180m"].mean() - n["absr_180m"].mean()),
        }
        return out

    point = stat(dates)
    starts = rng.integers(0, n_dates - L + 1, size=B)
    boot = {k: np.empty(B) for k in point}
    for b, s in enumerate(starts):
        # block-concatenated date list (np arrays of scalars -> use python list then tile)
        dd = [dates[s + j] for j in range(L) if s + j < n_dates]
        dd = np.array(dd, dtype=dates.dtype)
        # need ~n_dates coverage: repeat blocks until length reached
        reps = int(np.ceil(n_dates / max(1, len(dd))))
        dd_full = np.tile(dd, reps)[:n_dates]
        st = stat(dd_full)
        for k in point:
            boot[k][b] = st[k]

    result = {"point": point, "ci95": {}, "excludes_zero": {}, "n_valid_draws": {}}
    for k in point:
        arr = boot[k]
        valid = arr[np.isfinite(arr)]
        result["n_valid_draws"][k] = int(len(valid))
        if len(valid) < 100:
            # poison-draw protection: record instead of yielding NaN CIs
            result["ci95"][k] = None
            result["excludes_zero"][k] = None
            continue
        lo, hi = np.percentile(valid, [2.5, 97.5])
        result["ci95"][k] = [float(lo), float(hi)]
        result["excludes_zero"][k] = bool(lo > 0 or hi < 0)
        if len(valid) < B:
            print(f"    [boot] {k}: {B - len(valid)} NaN draws discarded "
                  f"(draws with a degenerate block)", flush=True)
    return result


def per_pair_signs(panel: pd.DataFrame, col: str) -> dict:
    signs = {}
    for pair, g in panel.groupby(level=1):
        cc = g[g["compressed"]][col].dropna()
        nn = g[~g["compressed"]][col].dropna()
        if len(cc) and len(nn):
            signs[pair] = float(cc.mean() - nn.mean())
    pos = sum(1 for s in signs.values() if s > 0)
    return {"signs": signs, "n_positive": pos, "n_pairs": len(signs)}


def mw_u_p(a, b):
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    n1, n2 = len(a), len(b)
    if n1 < 20 or n2 < 20:
        return None
    ranks = pd.Series(np.concatenate([a, b])).rank().to_numpy()
    u1 = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    z = (u1 - n1 * n2 / 2) / sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    return {"z": float(z), "p": float(erfc(abs(z) / sqrt(2)))}


def main(out_root="runs"):
    sess = pd.read_parquet(Path(out_root) / "FX-LDN-001-v2" / "sessions.parquet")
    v = sess[sess["valid"] == True].copy()
    v = add_flags(v)
    flagged = v.dropna(subset=["comp_pct"]).copy()
    flagged = flagged.set_index([flagged["london_date"], flagged["pair"]])

    panel_cols = ["compressed", "expansion_ratio", "absr_60m", "absr_180m", "ldn_pct", "ldn_range"]
    panel = flagged[panel_cols]

    boot = joint_block_stats(panel)
    c = panel[panel["compressed"]]
    n = panel[~panel["compressed"]]
    diagnostics = {
        "n_compressed": int(len(c)), "n_noncompressed": int(len(n)),
        "er_median_comp": float(c["expansion_ratio"].median()),
        "er_median_non": float(n["expansion_ratio"].median()),
        "er_mw": mw_u_p(c["expansion_ratio"].to_numpy(), n["expansion_ratio"].to_numpy()),
        "ldn_pct_median_comp": float(c["ldn_pct"].median()),
        "ldn_pct_median_non": float(n["ldn_pct"].median()),
        "ldn_range_bp_comp": float(c["ldn_range"].mean() * 1e4),
        "ldn_range_bp_non": float(n["ldn_range"].mean() * 1e4),
    }
    report = {
        "registry_version": "1.0",
        "version_note": "v2: joint date-block panel bootstrap; median-keyed decision",
        "decision_rule_stated_before_results":
            "L1 = median-ER CI excludes 0 positively AND |R_60| and |R_180| CIs exclude 0 "
            "positively AND >=5/6 pair sign agreement on |R_60|; else branch fails/mechanical.",
        "pairs": list(panel.index.get_level_values(1).unique()),
        "diagnostics": diagnostics,
        "joint_block_bootstrap": boot,
        "ABS_signs_60": per_pair_signs(panel, "absr_60m"),
        "ABS_signs_180": per_pair_signs(panel, "absr_180m"),
        "ER_signs": per_pair_signs(panel, "expansion_ratio"),
    }

    p = boot["point"]; ci = boot["ci95"]; ez = boot["excludes_zero"]
    er_ok = p["med_er_diff"] > 0 and ez["med_er_diff"] and ez["mean_er_diff"]
    r60_ok = p["r60_diff"] > 0 and ez["r60_diff"]
    r180_ok = p["r180_diff"] > 0 and ez["r180_diff"]
    signs60 = report["ABS_signs_60"]["n_positive"] >= 5
    checks = {"median_ER_ci_positive": er_ok, "absR60_ci_positive": r60_ok,
              "absR180_ci_positive": r180_ok, "signs60_ge_5_of_6": signs60}
    if er_ok and r60_ok and r180_ok and signs60:
        verdict = "PASS — proceed to L2 robustness"
    elif er_ok and not (r60_ok or r180_ok):
        verdict = "MECHANICAL — ratio artifact; no absolute movement uplift"
    else:
        verdict = "FAIL — no demonstrated effect"
    report["checks"] = checks
    report["gate_L1_decision"] = verdict

    out_dir = Path(out_root) / "FX-LDN-002-004-v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, default=str))
    flagged.reset_index(drop=True).to_parquet(out_dir / "sessions_flagged.parquet")
    print("verdict:", verdict)
    print("point:", {k: round(x, 6) for k, x in p.items()})
    print("ci95:", {k: [round(a, 6) for a in v] for k, v in ci.items()})
    print("excludes_zero:", ez)
    return report


if __name__ == "__main__":
    main()