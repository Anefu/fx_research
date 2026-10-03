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
    """Joint date-block bootstrap over the 6-pair panel — MULTI-BLOCK version.

    Classical moving-block bootstrap with a DISJOINT partition: the sample is
    partitioned into ceil(n_dates/L) contiguous non-overlapping blocks; each
    replicate resamples those blocks independently with replacement,
    concatenates, and truncates to n_dates (audit fix: v2 drew ONE block and
    tiled it). The joint panel (6 pairs per date) is carried through draws,
    preserving same-date cross-pair dependence and temporal spacing.
    """
    rng = np.random.default_rng(seed)
    dates = np.sort(panel.index.get_level_values(0).unique().to_numpy())
    n_dates = len(dates)
    edges = list(range(0, n_dates, L))
    blocks = [(e, min(e + L, n_dates)) for e in edges]
    n_blocks = len(blocks)
    by_date = {d: sub for d, sub in panel.groupby(level=0)}

    def stat(draw_dates) -> dict:
        pieces = [by_date[d].assign(_b=i) for i, d in enumerate(draw_dates)]
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
    boot = {k: np.empty(B) for k in point}
    nan_ct = {k: 0 for k in point}
    for b in range(B):
        picks = rng.integers(0, n_blocks, size=n_blocks)     # independent block resample
        dd = np.concatenate([np.arange(*blocks[p]) for p in picks])
        # audit #3: guarantee replicate length — keep drawing until n_dates
        while len(dd) < n_dates:
            p2 = rng.integers(0, n_blocks)
            dd = np.concatenate([dd, np.arange(*blocks[p2])])
        dd = dd[:n_dates]
        assert len(dd) == n_dates, "replicate length mismatch"
        st = stat(dates[np.sort(dd)])                        # positions -> labels (sorted ⇒ deterministic)
        for k in point:
            v = st[k]
            if np.isfinite(v):
                boot[k][b] = v
            else:
                nan_ct[k] += 1
                boot[k][b] = np.nan

    result = {"point": point, "ci95": {}, "excludes_zero": {}, "n_valid_draws": {},
              "blocks_per_replicate": n_blocks}
    for k in point:
        valid = boot[k][np.isfinite(boot[k])]
        result["n_valid_draws"][k] = int(len(valid))
        if len(valid) < max(100, int(0.9 * B)):
            result["ci95"][k] = None
            result["excludes_zero"][k] = None
            continue
        lo, hi = np.percentile(valid, [2.5, 97.5])
        result["ci95"][k] = [float(lo), float(hi)]
        result["excludes_zero"][k] = bool(lo > 0 or hi < 0)
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


def preconditions(out_root="runs", required_universe=None, root=None) -> dict:
    """Precondition gate (audit rounds 3+4).

    Hard requirements before ANY inference:
      1. FX-LDN-001-v2 manifest exists
      2. Required universe == FRZ.primary_universe (promotion gate; a
         narrower run may only be allowed by explicitly passing
         required_universe, and the result is then marked non-promotable)
      3. The SESSION TABLE's actual pairs == the required universe, and
         table counts agree with manifest counts (audit: five-pair table
         under a six-pair manifest previously slipped through)
      4. manifest universe_complete=True and zero-requested-missing
      5. DATA gates PASS for every required pair (with coverage>0)
      6. (pair, london_date) uniqueness in the table
      7. store snapshot agreement between manifest and store_manifest.json
    """
    from fxedge.registry import FRZ
    base = Path(out_root)
    manifest_path = base / "FX-LDN-001-v2" / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("precondition: FX-LDN-001-v2 manifest.json missing — run the base-rate runner first")
    m = json.loads(manifest_path.read_text())

    # 1. Universe: for promotion, the frozen registry universe is REQUIRED.
    promotable = required_universe is None
    required = [p.upper() for p in (required_universe if required_universe is not None
                                    else FRZ.primary_universe)]
    missing = [p for p in required if m["unique_sessions"].get(p, 0) <= 0]
    if missing:
        raise RuntimeError(f"precondition: universe incomplete — no valid data for {missing}; "
                           f"refusing inference (subset runs must be explicitly declared and are non-promotable)")
    if not m.get("universe_complete", False):
        raise RuntimeError("precondition: manifest universe_complete=False — inference blocked")

    # 2. Table↔manifest reconciliation (audit #1: trust the ACTUAL table)
    sess = pd.read_parquet(base / "FX-LDN-001-v2" / "sessions.parquet")
    if sess.duplicated(["pair", "london_date"]).any():
        raise RuntimeError("precondition: duplicate (pair, london_date) rows — session accounting invalid")
    actual_pairs = [p for p, n in sess[sess["valid"] == True]["pair"].value_counts().items() if n > 0]
    if required_universe is None and set(actual_pairs) != set(required):
        raise RuntimeError("precondition: session table universe differs from frozen universe")
    absent = [p for p in required if p not in actual_pairs]
    if absent:
        raise RuntimeError(f"precondition: session table missing required pairs {absent} "
                           f"(manifest/table disagreement)")
    for p in required:
        table_n = int(((sess["pair"] == p) & (sess["valid"] == True)).sum())
        manifest_n = int(m["unique_sessions"].get(p, 0))
        if table_n != manifest_n:
            raise RuntimeError(f"precondition: {p} count mismatch — table {table_n} vs manifest {manifest_n}")

    # 3. DATA gates PASS with positive coverage for every required pair
    gates_path = base / "DATA_GATES" / "data_gates.json"
    if not gates_path.exists():
        raise RuntimeError("precondition: DATA_GATES/data_gates.json missing — DATA gates not run")
    g = json.loads(gates_path.read_text())
    for p in required:
        pg = g["pairs"].get(p)
        if (not pg or not pg.get("DATA_pass") or pg.get("total_ticks", 0) <= 0
                or pg.get("bars_checked", 0) <= 0 or pg.get("months_missing")):
            raise RuntimeError(f"precondition: DATA gate FAIL or missing for {p} — inference blocked")

    # 4. Store snapshot agreement (audit #4: one data identity across artifacts)
    import fxedge.snapshot as snap
    if not m.get("store_root") or not g.get("store_root"):
        raise RuntimeError("precondition: store_root binding missing; rerun sessions and DATA gates")
    store_root = Path(root or m["store_root"]).resolve()
    if store_root != Path(m["store_root"]).resolve() or store_root != Path(g["store_root"]).resolve():
        raise RuntimeError("precondition: artifacts reference different stores")
    live = snap.snapshot_id(store_root)
    snap.reject_mismatch(m.get("store_fingerprint", {}), live, "sessions-vs-live-store")
    snap.reject_mismatch(g.get("store_fingerprint", {}), live, "DATA-vs-live-store")
    if not m.get("expected_months") or m["expected_months"] != g.get("expected_months"):
        raise RuntimeError("precondition: expected month coverage missing or differs")
    if any(m.get("months_missing", {}).values()):
        raise RuntimeError("precondition: session months missing")
    session_path = base / "FX-LDN-001-v2" / "sessions.parquet"
    if m.get("sessions_sha256") != snap._sha256_file(session_path):
        raise RuntimeError("precondition: session table binding missing or changed")
    mp = store_root / snap.STORE_MANIFEST
    if mp.exists():
        metadata = json.loads(mp.read_text())
        if any(v.get("chronology") == "recovered-unordered" for v in metadata.get("shards", {}).values()):
            raise RuntimeError("precondition: unresolved source chronology; recover from exports")
        if metadata.get("snapshot_id"):
            snap.reject_mismatch(metadata, live, "saved-store-vs-live-store")

    return {"manifest": m, "required_universe": required, "gates": g,
            "promotable": bool(promotable and set(required) == set(FRZ.primary_universe)),
            "n_valid": int(sess["valid"].sum())}


def main(out_root="runs"):
    pre = preconditions(out_root)          # audit #2: hard gate before any inference
    sess = pd.read_parquet(Path(out_root) / "FX-LDN-001-v2" / "sessions.parquet")
    v = sess[sess["valid"] == True].copy()
    v = add_flags(v)
    flagged = v.dropna(subset=["comp_pct"]).copy()
    flagged = flagged.set_index([flagged["london_date"], flagged["pair"]])

    panel_cols = ["compressed", "expansion_ratio", "absr_60m", "absr_180m", "ldn_pct", "ldn_range"]
    panel = flagged[panel_cols]

    boot = joint_block_stats(panel)
    # relative-range diagnostics need the hi/lo columns (kept in flagged, not panel)
    # flagged has 'pair' as index level AND column — reset to a flat frame first
    flat = flagged.reset_index(drop=True)
    c = flat[flat["compressed"]]
    n = flat[~flat["compressed"]]
    panel_c = panel[panel["compressed"]]
    panel_n = panel[~panel["compressed"]]
    diagnostics = {
        "n_compressed": int(len(panel_c)), "n_noncompressed": int(len(panel_n)),
        "er_median_comp": float(panel_c["expansion_ratio"].median()),
        "er_median_non": float(panel_n["expansion_ratio"].median()),
        "er_mw": mw_u_p(panel_c["expansion_ratio"].to_numpy(), panel_n["expansion_ratio"].to_numpy()),
        "ldn_pct_median_comp": float(panel_c["ldn_pct"].median()),
        "ldn_pct_median_non": float(panel_n["ldn_pct"].median()),
        # AUDIT #5 fix: relative range = range / mid-price, in bp; per-pair mean then pooled average
        "ldn_rel_range_bp_comp": float(
            c.assign(rr=lambda g: g["ldn_range"] / (g["ldn_hi"] + g["ldn_lo"]) * 2 * 1e4)
            .groupby("pair")["rr"].mean().mean()),
        "ldn_rel_range_bp_non": float(
            n.assign(rr=lambda g: g["ldn_range"] / (g["ldn_hi"] + g["ldn_lo"]) * 2 * 1e4)
            .groupby("pair")["rr"].mean().mean()),
    }
    report = {
        "registry_version": "1.0",
        "store_fingerprint": pre["manifest"]["store_fingerprint"],
        "promotable": pre["promotable"],
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