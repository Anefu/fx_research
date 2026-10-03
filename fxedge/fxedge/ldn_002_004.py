"""FX-LDN-002/003/004 — Gate L1: does compression predict expansion?

Pre-registered tests (fx-edge-experiment-registry.md section 2.1):
  FX-LDN-002  ER when Asia range <= 30th pct of prev 60 valid sessions vs ALL sessions
  FX-LDN-003  P(ER>1), P(ER>1.5): compressed vs all/uncompressed
  FX-LDN-004  |R| at 15/30/60/180m after 07:00 London: compressed vs uncompressed

Honesty design (applied at gate time, stated up front):
  ER-based tests (002/003) are mechanically inflated when the Asia range is
  small (small denominator). FX-LDN-004 uses absolute forward returns and is
  therefore the confound-free arbiter of "greater subsequent movement".
  Additional diagnostic (not pre-registered, clearly labeled): today's
  London range percentile within the previous 60 London windows, compressed
  vs not — if compressed ≈ 0.5, the "expansion" is pure denominator effect.

Decision rule applied for Gate L1 (stated before results):
  - MW-U rank test p < 0.05 AND block-bootstrap CI excludes 0 for the
    pooled effect, AND >= 5/6 pairs share the sign, for BOTH the ER effect
    (002/003) and the absolute-|R| effect (004).
  - If ER passes but |R| does not: compression is judged mechanical.
"""
from __future__ import annotations

import json
from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

LOOKBACK = 60
THRESHOLD = 0.30
HORIZONS = [15, 30, 60, 180]
SEED = 42
B_BOOT = 2000
BLOCK = 20


def add_flags(v: pd.DataFrame) -> pd.DataFrame:
    """Per pair: rolling percentile of today's Asia range within previous
    60 valid sessions (mid-rank for ties), plus compressed flag."""
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
        # diagnostic: London-range percentile (same construction, London side)
        lr = g["ldn_range"].to_numpy()
        lpct = np.full(len(g), np.nan)
        for i in range(LOOKBACK, len(g)):
            w = lr[i - LOOKBACK:i]
            lpct[i] = ((w < lr[i]).sum() + 0.5 * (w == lr[i]).sum()) / LOOKBACK
        g["ldn_pct"] = lpct
        outs.append(g)
    return pd.concat(outs, ignore_index=True)


def mw_u_p(a: np.ndarray, b: np.ndarray):
    """Mann-Whitney U with normal approximation, two-sided."""
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    n1, n2 = len(a), len(b)
    if n1 < 20 or n2 < 20:
        return None
    ranks = pd.Series(np.concatenate([a, b])).rank().to_numpy()
    u1 = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sigma = sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u1 - mu) / sigma
    return {"u": float(u1), "z": float(z), "p": float(erfc(abs(z) / sqrt(2))),
            "n1": int(n1), "n2": int(n2)}


def block_boot_ci(a: np.ndarray, b: np.ndarray, B=B_BOOT, L=BLOCK, seed=SEED):
    """Moving-block bootstrap CI for (mean(a) - mean(b))."""
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    rng = np.random.default_rng(seed)

    def draw(x):
        starts = rng.integers(0, len(x) - L + 1, size=int(np.ceil(len(x) / L)))
        idx = np.concatenate([np.arange(s, s + L) for s in starts])[:len(x)]
        return x[idx]

    diffs = np.empty(B)
    for k in range(B):
        diffs[k] = draw(a).mean() - draw(b).mean()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"diff_mean": float(a.mean() - b.mean()), "ci95": [float(lo), float(hi)],
            "excludes_zero": bool(lo > 0 or hi < 0)}


def two_prop(x1: int, n1: int, x2: int, n2: int):
    p1, p2, p = x1 / n1, x2 / n2, (x1 + x2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    return {"p_comp": p1, "p_non": p2, "z": float(z), "p": float(erfc(abs(z) / sqrt(2)))}


def summarize(v_flagged: pd.DataFrame) -> dict:
    c = v_flagged[v_flagged["compressed"]]
    n = v_flagged[~v_flagged["compressed"]]
    out = {"n_compressed": len(c), "n_noncompressed": len(n)}

    # FX-LDN-002: ER uplift (also vs ALL, as pre-registered)
    all_er = v_flagged["expansion_ratio"].dropna().to_numpy()
    out["ER"] = {
        "median_compressed": float(c["expansion_ratio"].median()),
        "median_non": float(n["expansion_ratio"].median()),
        "median_all": float(np.median(all_er)),
        "mw": mw_u_p(c["expansion_ratio"].to_numpy(), n["expansion_ratio"].to_numpy()),
        "boot": block_boot_ci(c["expansion_ratio"].to_numpy(), n["expansion_ratio"].to_numpy()),
    }
    # FX-LDN-003: P(ER>1), P(ER>1.5)
    out["PROB"] = {
        "er_gt_1": two_prop(int((c["expansion_ratio"] > 1).sum()), len(c),
                            int((n["expansion_ratio"] > 1).sum()), len(n)),
        "er_gt_15": two_prop(int((c["expansion_ratio"] > 1.5).sum()), len(c),
                             int((n["expansion_ratio"] > 1.5).sum()), len(n)),
    }
    # FX-LDN-004: absolute forward returns (bp)
    absr = {}
    for h in HORIZONS:
        col = f"absr_{h}m"
        res = {
            "mean_bp_comp": float(c[col].mean() * 1e4),
            "mean_bp_non": float(n[col].mean() * 1e4),
            "mw": mw_u_p(c[col].to_numpy(), n[col].to_numpy()),
        }
        if h in (60, 180):
            res["boot"] = block_boot_ci(c[col].to_numpy(), n[col].to_numpy())
        absr[f"h{h}"] = res
    out["ABSR"] = absr
    # diagnostic: London-range percentile, compressed vs not
    out["DIAG_LDN_PCT"] = {
        "median_pct_compressed": float(c["ldn_pct"].median()),
        "median_pct_non": float(n["ldn_pct"].median()),
        "mw": mw_u_p(c["ldn_pct"].to_numpy(), n["ldn_pct"].to_numpy()),
    }
    out["DIAG_LDN_RANGE_BP"] = {
        "mean_comp": float(c["ldn_range"].mean() * 1e4),
        "mean_non": float(n["ldn_range"].mean() * 1e4),
    }
    return out


def per_pair_sign_table(v_flagged: pd.DataFrame, col: str) -> dict:
    """Direction consistency: sign of (compressed mean - non mean) per pair."""
    signs = {}
    for pair, g in v_flagged.groupby("pair"):
        cc = g[g["compressed"]][col].dropna()
        nn = g[~g["compressed"]][col].dropna()
        signs[pair] = float(cc.mean() - nn.mean())
    pos = sum(1 for s in signs.values() if s > 0)
    return {"signs": signs, "n_positive": pos, "n_pairs": len(signs)}


def yearly_stability(v_flagged: pd.DataFrame, col: str = "absr_60m") -> list:
    rows = []
    for y, g in v_flagged.groupby(g_flagged_year(v_flagged)):
        cc, nn = g[g["compressed"]][col].dropna(), g[~g["compressed"]][col].dropna()
        rows.append({"year": y, "diff_mean_bp": float((cc.mean() - nn.mean()) * 1e4),
                     "n_comp": len(cc), "n_non": len(nn)})
    return rows


def g_flagged_year(x: pd.DataFrame):
    return x["london_date"].str[:4]


def main(out_root: str = "runs"):
    sess = pd.read_parquet(Path(out_root) / "FX-LDN-001" / "sessions.parquet")
    v = sess[sess["valid"] == True].copy()
    v = add_flags(v)
    flagged = v.dropna(subset=["comp_pct"])  # warm-up excluded (60-session rule)

    report = {
        "registry_version": "1.0",
        "experiments": ["FX-LDN-002", "FX-LDN-003", "FX-LDN-004"],
        "frozen": {"lookback": LOOKBACK, "threshold": THRESHOLD, "block": BLOCK,
                   "boot_B": B_BOOT, "seed": SEED},
        "decision_rule_stated_before_results":
            "Gate L1 requires ER uplift (002/003) AND absolute-|R| uplift (004): "
            "MW p<0.05 + block-bootstrap CI excl. 0 + >=5/6 pair sign agreement. "
            "If ER passes but |R| fails, compression is mechanical.",
        "pooled": summarize(flagged),
        "ABSR_60m_signs": per_pair_sign_table(flagged, "absr_60m"),
        "ABSR_180m_signs": per_pair_sign_table(flagged, "absr_180m"),
        "ER_signs": per_pair_sign_table(flagged, "expansion_ratio"),
        "yearly_ABSR_60m": yearly_stability(flagged, "absr_60m"),
        "dst_split_ABSR_60m": {},
    }
    for tag, sel in [("summer", flagged["dst_summer"] == True), ("winter", flagged["dst_summer"] == False)]:
        cc = flagged[sel & flagged["compressed"]]["absr_60m"].dropna()
        nn = flagged[sel & ~flagged["compressed"]]["absr_60m"].dropna()
        report["dst_split_ABSR_60m"][tag] = {"diff_bp": float((cc.mean() - nn.mean()) * 1e4),
                                             "n_comp": len(cc), "n_non": len(nn)}

    # ------- Gate L1 decision, applied mechanically -------
    pooled = report["pooled"]
    checks = []
    for key, name in [("ER", "FX-LDN-002"), ("ABSR_h60", None), ("ABSR_h180", None)]:
        pass
    def check(res, sign_table):
        mw_ok = res.get("mw") and res["mw"]["p"] < 0.05
        boot = res.get("boot")
        boot_ok = (not boot) or boot["excludes_zero"]
        st = sign_table or {"n_positive": 6, "n_pairs": 6}
        cons_ok = st["n_positive"] >= 5
        return bool(mw_ok and boot_ok and cons_ok)
    checks.append(("FX-LDN-002 ER", check(pooled["ER"], report["ER_signs"])))
    checks.append(("FX-LDN-003 P(ER>1)", pooled["PROB"]["er_gt_1"]["p"] < 0.05))
    checks.append(("FX-LDN-003 P(ER>1.5)", pooled["PROB"]["er_gt_15"]["p"] < 0.05))
    checks.append(("FX-LDN-004 |R_60m|", check(pooled["ABSR"]["h60"], report["ABSR_60m_signs"])))
    checks.append(("FX-LDN-004 |R_180m|", check(pooled["ABSR"]["h180"], report["ABSR_180m_signs"])))
    report["gate_checks"] = [{"test": t, "pass": p} for t, p in checks]
    er_pass = checks[0][1] and checks[1][1] and checks[2][1]
    absr_pass = checks[3][1] and checks[4][1]
    if er_pass and absr_pass:
        report["gate_L1_decision"] = "PASS — proceed to L2 robustness (FX-LDN-008..015)"
    elif er_pass and not absr_pass:
        report["gate_L1_decision"] = (
            "MECHANICAL — ER uplift without absolute-range uplift; "
            "re-aim as relative-range phenomenon, do NOT build directional entries")
    else:
        report["gate_L1_decision"] = "FAIL — terminate compression branch"

    root = Path(out_root)
    out_dir = root / "FX-LDN-002-004"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, default=str))
    flagged.to_parquet(out_dir / "sessions_flagged.parquet")
    print("decision:", report["gate_L1_decision"])
    print("saved:", out_dir)
    return report


if __name__ == "__main__":
    main()