# FX-LDN-001 — Registry Entry (pre-registered, frozen before data)

| Field | Value |
|---|---|
| Hypothesis | (none — baseline measurement only) |
| Economic mechanism | London session concentrates liquidity/flow; we measure unconditional levels, we do not yet claim an edge |
| Market universe | EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF (registry primary) |
| Signal definition | None. Session metrics only: AsiaRange, LondonRange, ExpansionRatio, R_h for h ∈ {15m, 30m, 60m, 180m} from 07:00 London |
| Parameters | Frozen registry §0: Asia 00:00–06:59, London 07:00–10:00 (Europe/London, DST-aware) |
| Entry rule | **None** — pre-registered exclusion |
| Exit rule | **None** — pre-registered exclusion |
| Benchmark | Self-reference: establishes the base distribution for FX-LDN-002+ |
| Cost assumptions | N/A (no trades) |
| Data period | Actual MT5 export coverage (filled after ingest) |
| Data source | MT5 `CopyTicksRange` export, meta: bid/ask, CHUNK=COPY_TICKS_INFO |
| Result | _filled from runs/FX-LDN-001/report.json_ |
| Decision | Pass / Fail / Modify (base-rate record only — neither pass nor fail) |
| Modification reason | n/a |

**Pre-registered exclusions (spec §8):** no entry rule, no stop loss, no
take profit, no ICT concepts, no optimization. This experiment may only
establish base rates. Any later reinterpretation of these numbers as a
"signal" requires a **new** experiment ID (FX-LDN-002+).