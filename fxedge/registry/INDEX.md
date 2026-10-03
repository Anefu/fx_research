# Generation-1 Outcomes — v2 (corrected reruns, valid inference)

Audits: v1 superseded (sampling bug); v2-interim superseded (single-block bootstrap); v3 = round-3 audit fixes (causal same-ms ordering in bars, disjoint-block length guarantee, precondition gate, JSON-generated entries, provenance binding).
Current entries carry valid session accounting (unique dates, exclusions recorded)
and valid joint-panel inference. Failed experiments retained permanently (registry §7).

| ID | Experiment | Outcome | Key numbers | Entry |
|---|---|---|---|---|
| DATA-GATE | DATA-001..005 on 10y real ticks | **PASS — all 6 pairs** | 1.57B ticks, 720 shards, 24,938 crossed + 14 zero-bid quotes removed (logged); bar reconstruction exact | [result](DATA_GATES.result.json) / [cleaning log](DATA_GATES.cleaning-log.json) |
| FX-LDN-001 | Unconditional base rates | **Recorded** | 14,935 unique sessions (2,479–2,495/pair; 2,609 expected incl. holidays; 719 exclusions with reasons: 474 out-of-slice, 245 window-coverage); reconciliation exact (valid+excluded=expected per pair) | [entry](FX-LDN-001-v2.entry.md) / [result JSON](FX-LDN-001-v2.result.json) |
| FX-LDN-002 | Compression → median ER | **Holds** | 0.81 vs 0.54; CI [0.241, 0.291] | [v3 entry](FX-LDN-002-004-v2.entry.md) |
| FX-LDN-003 | P(ER>1)/P(ER>1.5) | **Holds** | +0.212 [0.187, 0.236]; +0.076 [0.063, 0.090] | [v2 entry](FX-LDN-002-004-v2.entry.md) |
| FX-LDN-004 | Absolute \|R\| uplift | **FAILS — significantly NEGATIVE** | \|R_60\| −1.11 bp, CI [−1.41, −0.83] bp; 0/6 pairs; \|R_180\| also negative | [v2 entry](FX-LDN-002-004-v2.entry.md) |
| **GATE L1** | compression branch | **MECHANICAL → TERMINATED** (valid inference, stability-checked) | Compression predicts the *absence* of movement: quiet Asia → quiet London, not an expansion release | [decision](FX-LDN-002-004-v2.entry.md) |

## Interpretation register
- **√-time null stands**: ER median 0.60–0.74 vs diffusion null ≈0.65 ⇒ no London-concentration claim
- **Rejection scope**: this pre-registered hypothesis only; mechanism not established; range ≠ endpoint return
- **Exploratory status**: full historical period viewed; any confirmatory rerun needs new forward data or a fresh holdout split

## Branch status
- **Terminated:** compression→expansion (FX-LDN-009..015 skipped; ladder B3 dropped; B5–B7 blocked)
- **Next (need pre-registration):** B0/B1/B2 + directional tests (session-handover breakout); FX-TREND; FX-FIX

## Methodology (tracked scripts)
`sessions_cov.py` (coverage/eligibility) · `real_run_v2.py` (calendar-safe runner + manifest) ·
`shard_reader.py` + `tick_schema.py` (canonical schema, same-ms distinct quotes preserved) ·
`ldn_002_004_v2.py` (joint disjoint-block bootstrap) · original registry + spec documents
