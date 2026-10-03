# Generation-1 Outcomes — v2 (corrected rerun after audit)

Supersedes the v1 outcomes in this directory. The v1 results contained a
confirmed session-sampling bug (duplicate month-ends via `MonthEnd`
arithmetic, truncated month ends, non-unique sessions, unrestricted
`asof()` lookups) and an invalid bootstrap (independent, per-group block
resampling). All Generation-1 London experiments were **rerun with the
corrected methodology**; the audit's proposed fixes are all implemented.

Rerun artifacts (untracked, regenerable):
- `fxedge/runs/FX-LDN-001-v2/` — corrected session table + manifest
- `fxedge/runs/FX-LDN-002-004-v2/` — corrected statistics

| ID | Experiment | Outcome (v2, corrected) | Key numbers |
|---|---|---|---|
| DATA-GATE | DATA-001..005, 10y real ticks | **PASS — all 6 pairs** | 1.57B ticks, 720 shards, 0 missing months; 24,938 crossed + 14 zero-bid rows removed (logged); bar reconstruction exact |
| FX-LDN-001 | Unconditional London base rates | **Recorded** | **14,935 unique (pair,date) sessions** [2,479–2,495 per pair; ≤2,589 weekday bound ✓]; 66 sessions excluded for window/horizon coverage (logged in manifest); ER median 0.60–0.74 |
| FX-LDN-002 | Compression → median ER uplift | **Holds (relative)** | median ER 0.81 vs 0.54; joint-block CI [0.12, 0.60]; mean diff CI [0.10, 0.64] |
| FX-LDN-003 | P(ER>1) uplift | **Holds (relative)** | comp−non = +0.212; CI [0.007, 0.544]; P(ER>1.5) CI crosses 0 |
| FX-LDN-004 | Absolute \|R\| uplift | **FAILS — confirmed under correct inference** | \|R_60\| diff −1.11bp, CI [−0.46, +0.14]bp (signs 0/6); \|R_180\| diff −1.84bp, CI [−0.83, +0.30]bp (signs 0/6) |
| **GATE L1** | compression→expansion branch | **MECHANICAL → TERMINATED (now with valid inference)** | ER uplift is a denominator artifact: London range on compressed days at 34th pct of own history (vs 57th non-compressed); absolute level 365bp vs 540bp |

## v1 → v2 deltas (what the fixes changed)

- **Session counts**: 2,663/pair (impossible, duplicated+truncated) → **unique 2,479–2,495/pair**, within the 2,589 weekday bound; 0 duplicate (pair,date) rows
- **ER effect**: direction and magnitude survive corrected inference (pooled MW still p≈0; joint CI positive)
- **|R| deficit**: persists under the joint date-block panel bootstrap — the v1 conclusion was directionally right, and now stands on valid statistics (0/6 pairs for uplift, CIs straddling 0 → no evidence of uplift)
- **Coverage exclusions**: 60-session warm-up + window-coverage floors (<83% of minutes) + 5-minute quote-age bound on forward-return endpoints; exclusions enumerated per month in the manifest

## Interpretation corrections (audit #4/#6)

1. **The 3/7 ≈ 0.43 "window null" was wrong.** Under a diffusion, high–low
   range scales with √time, so the matched-volatility null for a 3h window
   vs a 7h window is **√(3/7) ≈ 0.65** (equal-vol simulation median ≈ 0.652).
   The observed ER median of 0.60–0.74 is therefore **consistent with, not
   above, the diffusion null** — the earlier "London concentrates ~1.5×
   range per unit time" claim is **retracted**. FX-LDN-001's ER median
   carries no London-concentration evidence either way.
2. The v2 rejection of the compression hypothesis is **narrowly framed and
   provisional**: it rejects *this* pre-registered hypothesis (compressed
   Asia → larger subsequent absolute movement), not every
   compression-conditioned rule, and does not establish the order-flow
   mechanism. Intraday range ≠ endpoint returns: a session may travel far
   and close where it started — direction tests on intrawindow range are a
   separate hypothesis if ever registered.
3. **Exploratory status**: the full-period analysis is exploratory evidence
   for future hypotheses. Its final 20% has been **viewed** and can no
   longer be held out as untouched; any future confirmatory test must
   either collect new forward data or re-split with the holdout moved.

## Methodology (scripts, tracked)

- `fxedge/sessions_cov.py` — coverage-bounded session computation (windows ≥83% populated; forward-return endpoints bounded to ≤5min quote age)
- `fxedge/real_run_v2.py` — calendar-boundary-safe runner; one owner per (pair, london_date); month arithmetic on month-numbers only (no `MonthEnd`); store fingerprint + exclusion manifest
- `fxedge/shard_reader.py` — month-number pad arithmetic (fixes the 202312→1888203 bug class), uniform `utc_ms/bid/ask` column-store reading
- `fxedge/stream_ingest.py` — quote-level dedup on `(utc_ms, bid, ask)`; existing-shard merge fixed (`pd` import); never discards distinct quotes sharing a millisecond
- `fxedge/ldn_002_004_v2.py` — joint date-block panel bootstrap (B=2000, L=20 consecutive London dates, all 6 pairs jointly), median-keyed decision, NaN-poisoning guard

## Provenance

- Universe: 6 registry majors; MT5 `CopyTicksRange` real ticks (MetaQuotes-Demo)
- Frozen parameters unchanged: registry §0; bootstrap B=2000, block L=20 days, seed 42
- All reruns pre-declared the decision rule before results were read
- Committed: methodology + registry v2 entries; data and bulky run artifacts untracked