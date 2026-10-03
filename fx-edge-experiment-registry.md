# FX Edge Research — Complete Experiment Registry v1.0

**Program objective:** Identify robust FX edges that can support profitable discretionary, systematic, or algorithmic trading.

**Generation:** 1  
**Status:** Pre-registered  
**Rule:** Failed experiments remain permanently in the registry.

---

# 0. Global Frozen Definitions

Unless an experiment explicitly overrides them, use these definitions.

| Item | Definition |
|---|---|
| Primary universe | EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF |
| Secondary universe | EURGBP, EURJPY, GBPJPY, AUDJPY |
| Raw intraday data | Tick-level Bid/Ask |
| Raw timezone | UTC |
| London timezone | `Europe/London`, DST-aware |
| New York timezone | `America/New_York`, DST-aware |
| Daily FX close | 17:00 New York |
| Asia/pre-London range | 00:00–06:59 London time |
| London research window | 07:00–10:00 London time |
| Asia high | Maximum Bid during Asia window |
| Asia low | Minimum Bid during Asia window |
| Asia range | Asia high − Asia low |
| Compression lookback | Previous 60 valid sessions |
| Primary compression definition | Current Asia range ≤ 30th percentile of previous 60 Asia ranges |
| London range | Max price − min price during 07:00–10:00 |
| Expansion ratio | London range / Asia range |
| Expansion event 1 | Expansion ratio > 1.0 |
| Expansion event 2 | Expansion ratio > 1.5 |
| HTF trend baseline | Sign of previous completed 20-trading-day spot return |
| Intraday decision bars | 5-minute unless specified otherwise |
| Base transaction cost | Historical spread + commission + empirical/conservative slippage |
| OOS structure | Chronological 60% development / 20% validation / 20% final holdout |
| Parameter choice | Middle of robust plateau, never isolated maximum |
| Research currency | Returns and R-multiples; monetary P&L secondary |

---

# 1. Data and Infrastructure Experiments

These must pass before strategy results are trusted.

| ID | Experiment | Test | Pass Condition |
|---|---|---|---|
| DATA-001 | Tick completeness | Measure missing timestamps/days and feed outages | Missing periods identified and explicitly excluded |
| DATA-002 | Bid/Ask integrity | Detect negative spreads, crossed quotes, stale quotes, abnormal jumps | Invalid records quantified and cleaning rules frozen |
| DATA-003 | Session reconstruction | Reconstruct London and NY sessions using timezone databases | Manual spot checks match actual local clocks |
| DATA-004 | DST validation | Validate UK/US DST transition weeks separately | No one-hour session displacement |
| DATA-005 | Bar reconstruction | Build 1m/5m/15m bars from ticks | Reconstructed OHLC consistent with raw tick extrema |
| DATA-006 | Cross-feed replication | Compare major results on a second FX feed/broker where available | Structural results not dependent on one feed |
| DATA-007 | Spread distribution | Build pair/session spread distributions | Median, tails and event spreads documented |
| DATA-008 | Execution-cost dataset | Build empirical spread/slippage assumptions by pair/session | Cost model frozen before strategy testing |

**Gate D:** No edge family proceeds to final validation until DATA-001 through DATA-005 pass.

---

# 2. FX-LDN — Asia → London Structural Edge

This is the primary Phase I research branch.

The branch proceeds:

\[
Compression
\rightarrow
Expansion
\rightarrow
Direction
\rightarrow
TradableRule
\rightarrow
ICT/TTFMIncrement
\]

---

## 2.1 Structural Existence

| ID | Experiment | Frozen Test | Benchmark / Decision |
|---|---|---|---|
| FX-LDN-001 | Unconditional London behavior | Measure London range, absolute return and directional return across all valid sessions | Establish base distribution only |
| FX-LDN-002 | Compression → expansion | Compare expansion ratio when Asia range ≤30th percentile vs all sessions | Compression must increase expansion magnitude/probability |
| FX-LDN-003 | Expansion probability | Compare \(P(ER>1)\) and \(P(ER>1.5)\) compressed vs unconditional | Must show economically meaningful uplift |
| FX-LDN-004 | Forward volatility | Compare 15m, 30m, 60m, 180m absolute returns after 07:00 | Identify edge clock |
| FX-LDN-005 | Directional neutrality | Measure signed returns under compression with no direction filter | Determine whether compression alone predicts direction |
| FX-LDN-006 | Pair breadth | Repeat 001–005 separately for each primary pair | Effect cannot exist solely in one unexplained pair |
| FX-LDN-007 | Year breadth | Repeat by year | Effect not entirely one historical episode |
| FX-LDN-008 | Volatility regime | Split prior realized volatility into terciles | Identify regime dependency without retuning |

**Gate L1:** If compression does not predict greater subsequent movement in FX-LDN-002/003/004, terminate the compression branch. Do not optimize entries.

---

## 2.2 Compression Robustness

Run only if Gate L1 passes.

| ID | Experiment | Frozen Test | Purpose |
|---|---|---|---|
| FX-LDN-009 | Percentile plateau | Compression thresholds 20/25/30/35/40% | Require broad plateau |
| FX-LDN-010 | Lookback robustness | 40/60/90/120 prior sessions | Test dependence on 60-day normalization |
| FX-LDN-011 | Ratio definition | Asia range / rolling median instead of percentile | Check whether effect depends on normalization method |
| FX-LDN-012 | ATR normalization | Asia range relative to recent daily ATR | Independent volatility normalization |
| FX-LDN-013 | Asia-window perturbation | Shift start/end by ±30 minutes | Test clock fragility |
| FX-LDN-014 | London-window perturbation | Shift entry/measurement window by ±30 minutes | Test clock fragility |
| FX-LDN-015 | DST split | UK summer vs winter clocks | Ensure true London effect rather than UTC artifact |

**Gate L2:** The effect must persist across reasonable neighboring definitions.

---

# 3. FX-LDN Directional Edge

Only run after the volatility/expansion effect is understood.

## 3.1 Basic Direction Tests

| ID | Experiment | Frozen Test | Benchmark |
|---|---|---|---|
| FX-LDN-016 | Breakout direction | Does first break of Asia high/low predict subsequent London direction? | Unconditional signed return |
| FX-LDN-017 | 20D HTF direction | Condition London move on sign of prior 20D spot return | FX-LDN-016 |
| FX-LDN-018 | HTF lookback plateau | 5/10/20/40/60 trading-day momentum | Require directional plateau |
| FX-LDN-019 | Prior-day direction | Condition on previous daily return sign | No filter |
| FX-LDN-020 | Asia closing location | Normalize 07:00 price within Asia range | Test whether range location predicts breakout side |
| FX-LDN-021 | Prior-day range location | Price relative to previous high/low/midpoint | Test structural location information |
| FX-LDN-022 | Combined directional state | Combine only features that independently survived 017–021 | Must beat best single feature |

**Gate L3:** There must be demonstrated directional information before building a directional trading strategy.

If only volatility prediction survives, redesign this branch as a volatility/expansion strategy rather than forcing direction.

---

# 4. FX-LDN Stripped Strategy Ladder

This is the formal B0–B7 sequence.

Every model inherits identical cost assumptions and evaluation windows.

| Model | Experiment ID | Strategy |
|---|---|---|
| B0 | FX-LDN-023 | Random comparable-time breakout/control with matched trade frequency and holding period |
| B1 | FX-LDN-024 | Generic London breakout; no Asia compression |
| B2 | FX-LDN-025 | Asia-range breakout during London |
| B3 | FX-LDN-026 | B2 + Asia compression |
| B4 | FX-LDN-027 | B3 + validated HTF directional filter |
| B5 | FX-LDN-028 | B4 + opposite-side liquidity sweep |
| B6 | FX-LDN-029 | B5 + CISD |
| B7 | FX-LDN-030 | B6 + FVG pullback |

The comparison is always:

\[
\Delta_n =
Performance(B_n)-Performance(B_{n-1})
\]

Complexity survives only if \(\Delta_n\) is robustly useful.

---

# 5. Machine-Readable ICT / TTFM Definitions

These are hypotheses, not assumed truths.

## FX-LDN-028 — Sweep

For a **long** candidate:

1. B4 conditions are already satisfied.
2. Price trades below the Asia low by at least:

\[
0.05\times AsiaRange
\]

3. Within the next three completed 5m candles, a candle closes back above the Asia low.
4. Only the first qualifying sweep per session is eligible.

Reverse symmetrically for shorts.

Test alternative sweep magnitudes only after the frozen baseline result is known.

---

## FX-LDN-029 — CISD

For a long after a valid sell-side sweep:

1. Identify the bearish 5m candle containing the lowest low of the sweep sequence.
2. CISD occurs when a subsequent completed 5m candle closes above that candle's open.
3. Maximum waiting window: six completed 5m bars after the sweep.

Reverse for shorts.

B6 must beat B5.

---

## FX-LDN-030 — FVG

For a long:

A bullish three-candle imbalance exists when:

\[
Low_{3}>High_{1}
\]

after valid CISD.

Entry candidate occurs when price subsequently retraces into the FVG within six completed 5m bars.

Primary entry point:

\[
FVG_{mid}=
\frac{High_1+Low_3}{2}
\]

Reverse for shorts.

B7 must beat B6.

If it does not, FVG is removed.

---

# 6. Additional Entry-Pattern Experiments

Run only if B4 itself is profitable/robust.

| ID | Experiment | Comparison |
|---|---|---|
| FX-LDN-031 | Breakout market entry | Immediate execution on qualifying breakout |
| FX-LDN-032 | Breakout-close entry | Wait for 5m candle close beyond boundary |
| FX-LDN-033 | Retest entry | Require return to broken boundary |
| FX-LDN-034 | Sweep-only entry | B4 + sweep without CISD |
| FX-LDN-035 | CISD without FVG | Direct entry on CISD confirmation |
| FX-LDN-036 | FVG midpoint | B7 baseline |
| FX-LDN-037 | Order-block candidate | Machine-readable last-opposing-candle definition; must beat B4 separately |

These experiments determine **execution efficiency**, not the underlying economic mechanism.

---

# 7. Exit Experiments

Run against the best frozen entry model, without changing the signal.

| ID | Experiment | Frozen Comparison |
|---|---|---|
| FX-LDN-038 | Time exit | Close at 10:00 London |
| FX-LDN-039 | 1R target | Fixed 1R target |
| FX-LDN-040 | 2R target | Fixed 2R target |
| FX-LDN-041 | Opposite range boundary | Structural target |
| FX-LDN-042 | ATR/range target | Target proportional to Asia range |
| FX-LDN-043 | Trailing stop | Mechanical trailing rule |
| FX-LDN-044 | Partial + runner | Compare with full-position exit |
| FX-LDN-045 | Break-even at 0.5R | Compare with no BE |
| FX-LDN-046 | Break-even at 1R | Compare with no BE |

Do not choose exits solely on CAGR.

Evaluate expectancy, skew, drawdown and execution burden.

---

# 8. London Cost and Execution Stress

| ID | Experiment | Test |
|---|---|---|
| FX-LDN-047 | Base costs | Historical spread + base slippage |
| FX-LDN-048 | 1.25× costs | Increase total friction 25% |
| FX-LDN-049 | 1.50× costs | Increase friction 50% |
| FX-LDN-050 | 2.00× costs | Double friction |
| FX-LDN-051 | Stop slippage stress | Increase adverse stop fills |
| FX-LDN-052 | Breakout slippage stress | Increase breakout-entry slippage |
| FX-LDN-053 | Spread-tail test | Use upper-decile observed spreads |
| FX-LDN-054 | Latency stress | Delay market execution mechanically |

---

# 9. News Interaction

News is classified, not automatically excluded.

| ID | Experiment | Test |
|---|---|---|
| FX-LDN-055 | Major-news split | Compare major scheduled-release days vs normal days |
| FX-LDN-056 | News ±30m | Signals within ±30m of major release |
| FX-LDN-057 | News ±60m | Signals within ±60m |
| FX-LDN-058 | News cost effect | Determine whether degradation comes from prediction or execution |
| FX-LDN-059 | News exclusion | Test exclusion only after 055–058 establish justification |

---

# 10. London Final Robustness

| ID | Experiment | Requirement |
|---|---|---|
| FX-LDN-060 | Walk-forward | Positive aggregate out-of-sample behavior |
| FX-LDN-061 | Final untouched holdout | Frozen strategy only |
| FX-LDN-062 | Pair leave-one-out | Recalculate portfolio excluding each pair individually |
| FX-LDN-063 | Year leave-one-out | Exclude each year individually |
| FX-LDN-064 | Parameter perturbation | Neighboring parameters remain viable |
| FX-LDN-065 | Block bootstrap | Confidence intervals for expectancy and Sharpe |
| FX-LDN-066 | Monte Carlo sequence | Drawdown and losing-streak distribution |
| FX-LDN-067 | Deflated Sharpe | Adjust for strategy-selection count |
| FX-LDN-068 | PBO | Estimate backtest-overfitting probability |

**Gate L4:** Only after this gate does the London model become a validated research edge.

---

# 11. FX-TREND — Slow Trend Edge

Canonical baseline:

\[
Signal_t=\operatorname{sign}(P_t/P_{t-63}-1)
\]

measured from completed 17:00 NY daily closes.

Initial forward horizon:

\[
21\ trading\ days
\]

---

| ID | Experiment | Test |
|---|---|---|
| FX-TRD-001 | 63D momentum effect | Prior 63D return vs next 21D spot return |
| FX-TRD-002 | Long/short symmetry | Positive vs negative trend separately |
| FX-TRD-003 | Pair breadth | Per-pair results |
| FX-TRD-004 | Currency breadth | Decompose results by underlying currency |
| FX-TRD-005 | Lookback plateau | 21/63/126/252 days |
| FX-TRD-006 | Holding horizon | 5/21/63 days |
| FX-TRD-007 | Signal strength | Magnitude/rank of trend vs future return |
| FX-TRD-008 | Volatility regime | Low/mid/high realized vol |
| FX-TRD-009 | Trend regime stability | Year-by-year |
| FX-TRD-010 | Cost inclusion | Spread + financing + turnover |
| FX-TRD-011 | Weekly rebalance | Frozen weekly implementation |
| FX-TRD-012 | Monthly rebalance | Compare with weekly |
| FX-TRD-013 | Vol scaling | Trend alone vs inverse-vol-scaled trend |
| FX-TRD-014 | Constant exposure control | Test whether vol scaling itself drives result |
| FX-TRD-015 | Cross-sectional trend rank | Strongest vs weakest currencies |
| FX-TRD-016 | Pair-level vs currency-level | Compare direct pair signals with constructed currency ranks |
| FX-TRD-017 | Walk-forward | Chronological validation |
| FX-TRD-018 | Final holdout | Frozen strategy |
| FX-TRD-019 | Cost stress | 1×/1.5×/2× costs |
| FX-TRD-020 | Bootstrap/Monte Carlo | Statistical/tail robustness |

**Gate T:** Trend must demonstrate positive OOS expectancy before carry is allowed to "rescue" it.

---

# 12. FX-CARRY — Carry Edge

Carry requires historical interest-rate/forward-point data.

Do not use today's MT5 swap retrospectively.

Primary research horizon:

monthly.

---

| ID | Experiment | Test |
|---|---|---|
| FX-CAR-001 | Rate differential effect | Current short-rate differential vs next-month FX return |
| FX-CAR-002 | Forward premium effect | Historical 1M forward premium vs subsequent return |
| FX-CAR-003 | Cross-sectional rank | High-carry vs low-carry currencies |
| FX-CAR-004 | Pair breadth | Performance by currency pair |
| FX-CAR-005 | Carry tails | Loss distribution during stress events |
| FX-CAR-006 | Volatility regime | Carry behavior by realized-vol tercile |
| FX-CAR-007 | Risk-off sensitivity | Carry performance during broad risk shocks |
| FX-CAR-008 | Funding-currency asymmetry | JPY/CHF/USD-funded exposures separately |
| FX-CAR-009 | Monthly rebalance | Canonical implementation |
| FX-CAR-010 | Cost/financing model | Historical forward/swap economics net of broker markup |
| FX-CAR-011 | Walk-forward | OOS validation |
| FX-CAR-012 | Final holdout | Frozen carry strategy |

**Gate C1:** Carry must stand on its own before combining with trend.

---

# 13. FX Trend + Carry

Only run if both individual families have credible evidence.

| ID | Experiment | Test |
|---|---|---|
| FX-TC-001 | Agreement state | Trend+ / Carry+ vs conflicting states |
| FX-TC-002 | Trend− / Carry− | Short-side symmetric case |
| FX-TC-003 | Conflict analysis | Trend+Carry− and Trend−Carry+ |
| FX-TC-004 | Equal-weight score | 50% trend rank + 50% carry rank |
| FX-TC-005 | Weight plateau | 25/75, 50/50, 75/25 |
| FX-TC-006 | Filter model | Carry used only as trend filter |
| FX-TC-007 | Trend used as carry filter | Reverse architecture |
| FX-TC-008 | Vol scaling | Raw vs vol-scaled combined portfolio |
| FX-TC-009 | Currency exposure cap | Limit concentration in common funding currencies |
| FX-TC-010 | Rebalance frequency | Weekly vs monthly |
| FX-TC-011 | Pair leave-one-out | Concentration robustness |
| FX-TC-012 | Walk-forward | OOS |
| FX-TC-013 | Final holdout | Frozen combined model |
| FX-TC-014 | Correlation benefit | Does combination outperform component diversification mechanically? |

The combined model must beat the best individual component **after accounting for complexity and correlation**.

---

# 14. FX-FIX — London Fix / Month-End Flow

Event time:

\[
t=0=16{:}00\ London
\]

Measure windows:

\[
[-120,-60]
\]

\[
[-60,-30]
\]

\[
[-30,0]
\]

\[
[0,+30]
\]

\[
[+30,+60]
\]

minutes.

---

| ID | Experiment | Test |
|---|---|---|
| FX-FIX-001 | Normal-day fix profile | Intraday return/volatility around 16:00 |
| FX-FIX-002 | Month-end profile | Month-end vs ordinary days |
| FX-FIX-003 | Quarter-end profile | Quarter-end vs ordinary month-end |
| FX-FIX-004 | Pre-fix momentum | Return continuation into fix |
| FX-FIX-005 | Post-fix reversal | Reversal after benchmark execution |
| FX-FIX-006 | Pre/post relationship | Large pre-fix move → subsequent reversal? |
| FX-FIX-007 | Pair breadth | Per-pair event response |
| FX-FIX-008 | Volatility regime | Calm vs high-volatility months |
| FX-FIX-009 | Month-return proxy | Condition on prior monthly currency move |
| FX-FIX-010 | Portfolio-rebalance proxy | Construct simple equity/bond relative-performance pressure proxy |
| FX-FIX-011 | External rebalance estimate | Use independent published estimate if reliable data available |
| FX-FIX-012 | Directional strategy | Frozen event-entry rule |
| FX-FIX-013 | Reversal strategy | Frozen post-fix rule |
| FX-FIX-014 | Spread/slippage | Fix-window execution costs |
| FX-FIX-015 | Cost stress | 1×/1.5×/2× |
| FX-FIX-016 | Walk-forward | Chronological OOS |
| FX-FIX-017 | Final holdout | Frozen rule |

---

# 15. Portfolio-Level Experiments

Only validated individual strategies enter this stage.

| ID | Experiment | Test |
|---|---|---|
| FX-PORT-001 | Return correlation | Strategy daily/trade P&L correlation |
| FX-PORT-002 | Drawdown overlap | Whether strategies fail simultaneously |
| FX-PORT-003 | Currency factor exposure | Aggregate USD/EUR/GBP/JPY/AUD/CAD/CHF exposure |
| FX-PORT-004 | Equal-risk portfolio | Equalize ex-ante volatility contribution |
| FX-PORT-005 | Exposure caps | Currency and gross-risk limits |
| FX-PORT-006 | Slow + intraday combination | Trend/carry plus London edge |
| FX-PORT-007 | Fix diversification | Incremental contribution of fix strategy |
| FX-PORT-008 | Crisis simulation | Historical and bootstrap joint stress |
| FX-PORT-009 | Portfolio cost stress | Combined realistic trading costs |
| FX-PORT-010 | Portfolio final holdout | No re-optimization |

---

# 16. Manual Execution Validation

Every strategy that may be traded discretionarily must undergo this branch.

| ID | Experiment | Test |
|---|---|---|
| FX-MAN-001 | Setup identification consistency | Reclassify same hidden charts twice |
| FX-MAN-002 | Blind replay | Trade unseen sessions candle-by-candle |
| FX-MAN-003 | Signal capture | Percentage of mechanical valid setups identified manually |
| FX-MAN-004 | False positives | Manual trades without system-valid signal |
| FX-MAN-005 | Entry slippage | Manual entry vs mechanical theoretical entry |
| FX-MAN-006 | Exit deviation | Manual vs frozen planned exit |
| FX-MAN-007 | Discretion value added | Mechanical \(M\) vs manual \(M+D\) |
| FX-MAN-008 | Skip value | Were skipped mechanical trades actually worse? |
| FX-MAN-009 | Override value | Did discretionary overrides add expectancy? |
| FX-MAN-010 | Confidence score | Does subjective confidence predict outcome? |
| FX-MAN-011 | Rule adherence | Valid execution percentage |
| FX-MAN-012 | Demo sample | Forward manual sample |
| FX-MAN-013 | Manual OOS expectancy | Compare against historical expected range |

If discretion cannot demonstrate value, remove it rather than defend it narratively.

---

# 17. Algorithmic Execution Validation

| ID | Experiment | Test |
|---|---|---|
| FX-ALG-001 | Python signal freeze | Produce canonical signal log |
| FX-ALG-002 | MQL5 implementation | Reimplement exact rules |
| FX-ALG-003 | Signal parity | Python vs MT5 timestamps/directions |
| FX-ALG-004 | Entry parity | Order price comparison |
| FX-ALG-005 | Exit parity | Exit/stop comparison |
| FX-ALG-006 | Position-size parity | Identical risk calculations |
| FX-ALG-007 | MT5 real-tick test | Every-tick-real-ticks mode |
| FX-ALG-008 | Broker spread test | Native historical spread |
| FX-ALG-009 | Delay stress | Artificial execution delay |
| FX-ALG-010 | Multi-pair test | Simultaneous positions |
| FX-ALG-011 | Demo forward | Live market, no capital |
| FX-ALG-012 | Forward/backtest comparison | Signal rate, costs and expectancy |

---

# 18. Live Validation Experiments

These do not begin until historical and forward gates pass.

| ID | Experiment | Test |
|---|---|---|
| FX-LIVE-001 | Micro-live fills | Actual spread/slippage vs model |
| FX-LIVE-002 | Signal parity | Live signal generation vs frozen rules |
| FX-LIVE-003 | Operational reliability | Missed/duplicated/order-error rate |
| FX-LIVE-004 | 20-trade health check | Compare with simulated distribution |
| FX-LIVE-005 | 50-trade health check | Same |
| FX-LIVE-006 | 100-trade health check | Same |
| FX-LIVE-007 | Drawdown percentile | Current DD vs expected distribution |
| FX-LIVE-008 | Cost drift | Actual vs assumed friction |
| FX-LIVE-009 | Signal-frequency drift | Current vs historical |
| FX-LIVE-010 | Strategy-decay review | Formal investigation only if statistical trigger breached |

---

# 19. Research Dependency Map

The experiments are not intended to be run as one giant optimization exercise.

The dependency structure is:

\[
DATA
\]

↓

\[
FX\text{-}LDN\text{-}001\text{–}008
\]

↓

\[
\boxed{\text{Does compression predict expansion?}}
\]

If no:

\[
\text{Kill compression branch}
\]

If yes:

\[
LDN\ Robustness
\rightarrow
Directional\ Tests
\rightarrow
B0\text{–}B4
\]

↓

\[
\boxed{\text{Is B4 profitable and robust?}}
\]

If no:

\[
\text{Do not test ICT complexity}
\]

If yes:

\[
B5
\rightarrow
B6
\rightarrow
B7
\]

Each survives only if incremental.

Then:

\[
Execution
\rightarrow
Costs
\rightarrow
OOS
\rightarrow
Manual/Algo
\rightarrow
Forward
\rightarrow
Live
\]

In parallel:

\[
Trend
\rightarrow
Carry
\rightarrow
Trend+Carry
\]

and:

\[
Fix\ Flow
\]

Only validated branches enter the portfolio stage.

---

# 20. First Experiment to Run

The first actual registered experiment is:

## FX-LDN-001

**Question**

What is the unconditional distribution of London-session price behavior?

**Universe**

EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF.

**Asia window**

00:00–06:59 Europe/London.

**London window**

07:00–10:00 Europe/London.

**For each session calculate**

\[
AsiaRange
\]

\[
LondonRange
\]

\[
ExpansionRatio=
\frac{LondonRange}{AsiaRange}
\]

\[
R_{15m},R_{30m},R_{60m},R_{180m}
\]

\[
|R_{15m}|,|R_{30m}|,|R_{60m}|,|R_{180m}|
\]

Also calculate:

\[
I(ExpansionRatio>1)
\]

and:

\[
I(ExpansionRatio>1.5)
\]

**No entry rule.**

**No stop loss.**

**No take profit.**

**No ICT concepts.**

**No optimization.**

The purpose is simply to establish the base rate against which FX-LDN-002 and every subsequent claim will be measured.

---

# 21. Total Generation-1 Research Scope

This registry contains five distinct levels of research:

**Market effects**
→ Does predictable behavior exist?

**Trading conversion**
→ Can that behavior produce positive expectancy?

**Incremental complexity**
→ Does each additional rule improve the simpler system?

**Execution**
→ Does the edge survive spreads, slippage and real order mechanics?

**Human/system implementation**
→ Can either a trader or algorithm reproduce it consistently?

The standard for promotion remains:

\[
\boxed{
Economic\ Mechanism
+
Predictive\ Effect
+
Incremental\ Value
+
OOS\ Robustness
+
Execution\ Realism
+
Repeatability
}
\]

Only strategies satisfying all six qualify as deployable edges.