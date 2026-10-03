# Experiment Outcomes — Generation 1 (index)

Result-only record. Methodology lives in the scripts (fxedge/fxedge/) and
specs; data lives in the (untracked) shard store; this directory holds only
what the registry §7 requires to persist: decisions, outcomes, provenance.

| ID | Experiment | Outcome | Key numbers | Entry |
|---|---|---|---|---|
| DATA-GATE | DATA-001..005 on 10y real ticks | **PASS — all 6 pairs** | 1.58B ticks, 720 shards, 0 missing months; 24,938 crossed quotes + 14 zero-bid rows cleaned (logged); bar reconstruction exact | [result](DATA_GATES.result.json) / [cleaning log](DATA_GATES.cleaning-log.json) |
| FX-LDN-001 | Unconditional London base rates | **Recorded** (no edge claim) | 16,052 sessions (2,663/pair); ER median 0.60–0.74 vs window-null 0.43; yearly P(ER>1.5) stable 0.045–0.062 | [entry](FX-LDN-001.entry.md) / [report](../../fxedge/runs/FX-LDN-001/report.json) |
| FX-LDN-002 | Compression → ER uplift | **Pass (relative only)** | ER median 0.82 vs 0.55; MW p<1e-300; boot CI [0.29, 0.36] | [entry](FX-LDN-002-004.entry.md) |
| FX-LDN-003 | P(ER>1) / P(ER>1.5) uplift | **Pass (relative only)** | 32.9% vs 10.8%; 10.8% vs 2.4%; z=33.7 | [entry](FX-LDN-002-004.entry.md) |
| FX-LDN-004 | Absolute \|R\| uplift | **FAIL — all pairs, all years** | \|R_60\|: 3.59bp vs 4.76bp; sign agreement 0/6; yearly deficit 10/10 | [entry](FX-LDN-002-004.entry.md) |
| **GATE L1 — compression branch** | | **MECHANICAL → TERMINATED** | London range on compressed days at 33rd pct of own history — denominator artifact; no tradable effect | [decision](FX-LDN-002-004.entry.md) |

## Branch status after Gate L1

- **Terminated:** compression→expansion (FX-LDN-008..015 not run; ladder member B3 dropped; ICT increments B5–B7 blocked by §19 — no foundation effect)
- **Surviving hypotheses (need new pre-registration):** session-handover breakout continuation (B0/B1/B2 + directional tests), mechanism = Osler stop-cluster continuation
- **Untouched branches:** FX-TREND (slow momentum), FX-FIX (fix/month-end flow)

## Provenance

- Universe: 6 registry majors (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF)
- Data: MT5 `CopyTicksRange` real ticks, MetaQuotes-Demo, 2016-11-01 → 2026-10-02
- Timestamps verified UTC (weekend gaps land Fri 23:59 → Mon 00:00 sharp)
- Frozen parameters: registry §0 (lookback 60, threshold 0.30, bootstrap B=2000/L=20, seed 42)
- Pre-registered exclusions held: no entries, no stops, no targets, no ICT concepts, no optimization in the base-rate/gate experiments