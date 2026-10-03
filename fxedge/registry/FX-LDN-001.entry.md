# FX-LDN-001 — Registry Entry (filled)

| Field | Value |
|---|---|
| Hypothesis | (none — baseline measurement only) |
| Economic mechanism | London session concentrates liquidity/flow; unconditional levels measured, no edge claimed |
| Market universe | EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF (registry primary) |
| Signal definition | None. Session metrics only: AsiaRange, LondonRange, ExpansionRatio, R_h for h ∈ {15m, 30m, 60m, 180m} from 07:00 London |
| Parameters | Frozen registry §0: Asia 00:00–06:59, London 07:00–10:00 (Europe/London, DST-aware) |
| Entry rule | **None** — pre-registered exclusion (held) |
| Exit rule | **None** — pre-registered exclusion (held) |
| Benchmark | Establishes base distribution for FX-LDN-002+ |
| Cost assumptions | N/A (no trades) |
| Data period | **2016-11-01 → 2026-10-02** (MetaQuotes-Demo real ticks; DST-aware London windows) |
| Data source | MT5 `CopyTicksRange` (COPY_TICKS_INFO), exported via ExportTicksFromMT5.mq5 v1.04, streamed to month-shard parquet store; DATA gates passed pre-computation |
| Result | **16,052 session rows (2,663 valid sessions/pair × 6 pairs, 0 invalid).** Pooled: P(ER>1) 0.18–0.29 by pair; ER median 0.60–0.74. Yearly ER>1.5 probabilities stable at 0.045–0.062 with no single-year dependence. Forward |R_60m| ~7bp mean (AUDUSD) down to ~3.2bp (USDCAD). Full numbers in runs/FX-LDN-001/report.json |
| Decision | **Recorded — base rate established.** No trading claim made or permitted from this entry |
| Modification reason | n/a |

## Key measurement note (pre-registered interpretation, added at record time)

The Asia window is 7 hours and the London observation window is 3 hours.
**The window-ratio null is 3/7 ≈ 0.43.** The observed ER median of 0.60–0.74
is therefore **above** the uniform-accumulation null — London concentrates
~1.4–1.7× the range per unit time. The `P(ER>1)` statistics (~18–29%) only
look "low" against the naive ER=1 reading; they must be compared against the
0.43-window null in FX-LDN-002/003, or the compression uplift test will be
mis-specified.

## Data-quality provenance (DATA gate record)

- 1.58B ticks ingested, 720 monthly shards, zero missing months in span
- Crossed quotes (ask<bid): 24,938 rows removed — concentrated in 2017-09/10
  feed glitches; log: `runs/DATA_GATES/crossed_quotes_cleaning.json`
- Zero-bid impossible quotes: 14 rows removed (2017 holiday sessions)
- Bar reconstruction (DATA-005): exact — 0 mismatches across all pairs
- Timestamps verified UTC (weekend gaps land Fri 23:59 → Mon 00:00 UTC sharp)
- Synthetic-contamination incident: 627,519 demo rows purged; purge verified
  per-month against the deterministic generator's expected counts (all OK)
- Gates report: `runs/DATA_GATES/data_gates.json` — **all 6 pairs PASS**

**Pre-registered exclusions (spec §8) unchanged:** no entry rule, no stop
loss, no take profit, no ICT concepts, no optimization. Any reinterpretation
of these numbers as a signal requires a new experiment ID (FX-LDN-002+).