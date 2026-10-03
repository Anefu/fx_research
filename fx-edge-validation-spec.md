# Forex Edge Validation Specification v1.0

**Objective:** Develop, falsify, validate, and deploy repeatable FX trading edges that can be executed manually, systematically, or algorithmically.

The framework is designed to answer four separate questions:

\[
\boxed{
\text{Does the market effect exist?}
}
\]

\[
\boxed{
\text{Can it be converted into a profitable trading rule?}
}
\]

\[
\boxed{
\text{Does it survive realistic execution?}
}
\]

\[
\boxed{
\text{Can I execute it consistently?}
}
\]

A strategy is not considered an edge until all four have been addressed.

---

# 1. Research Philosophy

Every candidate must pass through:

\[
\boxed{
\text{Economic Mechanism}
\rightarrow
\text{Predictive Effect}
\rightarrow
\text{Trading Rule}
\rightarrow
\text{Robustness}
\rightarrow
\text{Execution}
\rightarrow
\text{Trader Validation}
\rightarrow
\text{Live Deployment}
}
\]

The order matters.

We do **not** begin with entries, stop losses, RR ratios, FVGs, CISD, candlestick patterns, or optimized parameters.

We first establish that the underlying market state predicts something useful.

---

# 2. Initial FX Research Universe

Start with liquid FX markets where transaction costs and data quality are relatively favorable.

### Primary majors

- EURUSD
- GBPUSD
- USDJPY
- AUDUSD
- USDCAD
- USDCHF

### Secondary crosses

After initial validation:

- EURGBP
- EURJPY
- GBPJPY
- AUDJPY

Do not expand the universe merely to increase the number of profitable backtests.

Every additional market must be economically relevant to the tested hypothesis.

---

# 3. Initial Edge Families

The first research program will focus on four FX hypotheses.

## FX-01 — Medium-Term Trend

Hypothesis:

\[
E[R_{t+h}\mid Trend_t] \neq 0
\]

Research whether persistent directional movement contains usable predictive information over days to months.

---

## FX-02 — Trend + Carry

Hypothesis:

Currencies with favorable:

\[
\text{Trend}
+
\text{Carry}
\]

should outperform currencies with unfavorable trend and carry.

Carry must be calculated using historical rate/forward information rather than today's broker swap applied retrospectively.

---

## FX-03 — Asia → London Expansion

Hypothesis:

A compressed pre-London trading range followed by the London liquidity transition produces a higher probability and/or magnitude of subsequent expansion than an unconditional session.

This is the primary intraday research project.

---

## FX-04 — Fix / Month-End Flow

Hypothesis:

Institutional benchmark execution and portfolio rebalancing create abnormal price behavior around defined fixing and month-end windows.

This is an event-study strategy and should be researched independently of ordinary technical analysis.

---

# 4. Strategy Classification

Every candidate must be classified before testing.

### Directional edge

Predicts:

\[
E[R_{t+h}|X]
\]

Example:

HTF trend predicts London breakout direction.

### Volatility edge

Predicts:

\[
E[|R_{t+h}||X]
\]

Example:

Asian compression predicts larger London-session range.

### Timing edge

Predicts when an existing directional effect becomes stronger.

Example:

Trend works better during London liquidity expansion.

### Execution edge

Improves entry/fill without improving the underlying forecast.

Example:

A pullback entry achieves better average price than immediate breakout execution.

These are not interchangeable.

A setup may have an excellent volatility edge but zero directional edge.

---

# 5. Data Specification

## 5.1 Intraday data

Preferred source:

**Tick-level Bid and Ask data from the broker/feed we are likely to trade.**

Store:

- UTC timestamp
- Bid
- Ask
- spread
- symbol
- quote source

Derive bars ourselves.

For every bar retain:

- Bid OHLC
- Ask OHLC where practical
- spread statistics
- tick count

---

## 5.2 Time conventions

All raw data:

\[
UTC
\]

Economic sessions converted dynamically using proper timezone rules.

London:

`Europe/London`

New York:

`America/New_York`

Do not hardcode London session times permanently in UTC because DST changes them.

---

# 6. Data Quality Tests

Before any strategy research:

Check for:

- missing days
- duplicate timestamps
- negative spreads
- impossible price jumps
- stale quotes
- weekend contamination
- DST errors
- feed interruptions
- symbol specification changes

Record all excluded periods.

Never silently clean losing observations.

---

# 7. Experiment Registry

Every experiment gets a permanent ID.

Examples:

`FX-LDN-001`

`FX-LDN-002`

`FX-TREND-001`

For every experiment record:

| Field | Required |
|---|---|
| Hypothesis | Yes |
| Economic mechanism | Yes |
| Market universe | Yes |
| Signal definition | Yes |
| Parameters | Yes |
| Entry rule | If applicable |
| Exit rule | If applicable |
| Benchmark | Yes |
| Cost assumptions | Yes |
| Data period | Yes |
| Result | Yes |
| Decision | Pass / Fail / Modify |
| Modification reason | If modified |

Failed experiments remain in the registry.

They are not deleted.

This allows us to measure how many hypotheses were actually tested.

---

# 8. Rule Against Backtest Storytelling

Every change must be made **before** observing the next test sample.

Forbidden process:

> Backtest → inspect losses → change rule → retest same data repeatedly.

Allowed process:

> Development data → formulate modification → freeze modification → evaluate on unseen validation data.

Every modification creates a new strategy version.

Example:

`FX-LDN-004`

becomes:

`FX-LDN-005`

rather than silently rewriting FX-LDN-004.

---

# 9. Stripped Benchmark Framework

Every complex strategy must beat its simpler predecessor.

For our London research:

### B0 — Null

Equivalent holding period during randomly selected comparable periods.

### B1 — London breakout

No Asian information.

### B2 — Asia-range breakout

Trade break of the pre-London range.

### B3 — Compression

\[
B2+\text{Asian compression}
\]

### B4 — Higher-timeframe direction

\[
B3+\text{HTF direction}
\]

### B5 — Liquidity sweep

\[
B4+\text{sweep}
\]

### B6 — CISD

\[
B5+\text{CISD}
\]

### B7 — FVG / POI

\[
B6+\text{FVG/POI}
\]

Each layer must show incremental benefit.

If:

\[
Performance(B7)\approx Performance(B4)
\]

then B5–B7 provide no demonstrated edge.

Remove them.

---

# 10. Predictive Research Before Strategy Construction

Before using stops or profit targets, measure forward returns.

For every signal \(X\):

\[
E[R_{5m}|X]
\]

\[
E[R_{15m}|X]
\]

\[
E[R_{30m}|X]
\]

\[
E[R_{60m}|X]
\]

\[
E[R_{session}|X]
\]

Also measure:

\[
E[|R_{h}||X]
\]

This tells us whether the signal predicts:

- direction;
- volatility;
- both;
- neither.

Only then construct an execution rule.

---

# 11. Canonical Asia → London Research Definition

We need one starting definition rather than searching hundreds.

Initial pre-registered version:

### Pre-London range

London local time:

\[
00{:}00-06{:}59
\]

Record:

\[
H_A=\text{Asia High}
\]

\[
L_A=\text{Asia Low}
\]

\[
Range_A=H_A-L_A
\]

### London observation window

Initial:

\[
07{:}00-10{:}00
\]

We later test modest shifts around these values as robustness checks.

We do not initially optimize the exact minutes.

---

# 12. Compression Definition

Do not use an arbitrary fixed pip value.

Normalize the Asian range.

Example:

\[
Compression_t=
\frac{Range_{Asia,t}}
{\text{Median}(Range_{Asia,t-60:t-1})}
\]

Alternative:

percentile rank of today's Asian range relative to the previous 60 sessions.

Example hypothesis:

\[
CompressionPercentile <30\%
\]

The 30% value is not assumed optimal.

We later examine a plateau around:

\[
20,\ 25,\ 30,\ 35,\ 40\%
\]

---

# 13. Expansion Measurement

Measure:

\[
Expansion=
\frac{LondonRange}
{AsiaRange}
\]

Also:

\[
P(LondonRange > AsiaRange)
\]

and:

\[
P(LondonRange >1.5\times AsiaRange)
\]

Compare compressed vs non-compressed sessions.

If compression does not predict expansion:

**stop the research branch.**

There is no reason to optimize entries.

---

# 14. Directional Testing

If expansion exists, investigate direction.

Possible predictors:

- prior-day direction
- D1 momentum
- H4 momentum
- distance from prior-day high/low
- Asia closing location
- breakout side

Each must be tested separately before combining them.

Example:

\[
P(
UpwardExpansion
|
Compression,
HTFUptrend
)
\]

versus:

\[
P(
UpwardExpansion
|
Compression
)
\]

That difference represents the incremental value of HTF direction.

---

# 15. ICT / TheStrat Treatment

These are **candidate features**, not assumed edges.

Examples:

- sweep
- CISD
- FVG
- order block
- POI
- 2-1-2
- 3-2 continuation

They enter research only after the structural hypothesis works.

Every concept must have a precise machine-readable definition.

For example, a "sweep" cannot remain:

> Price grabbed liquidity.

It must become something like:

> Price trades at least X points above the previous range high and subsequently closes back inside the range within N bars.

Different definitions may be tested, but each counts as a separate experiment.

---

# 16. Development / Validation Structure

Never randomly shuffle financial data.

Use chronological validation.

Suggested architecture:

### Development

First approximately:

\[
60\%
\]

Used for:

- hypothesis development
- exploratory work
- feature discovery

### Validation

Next:

\[
20\%
\]

Used to select among already-defined versions.

### Final Holdout

Last:

\[
20\%
\]

Completely untouched until strategy specification is frozen.

Once the holdout is viewed, it can never again be considered untouched.

---

# 17. Walk-Forward Testing

Within development + validation data use anchored or rolling walk-forward testing.

Example:

\[
Train_1\rightarrow Test_1
\]

\[
Train_2\rightarrow Test_2
\]

\[
Train_3\rightarrow Test_3
\]

Combine only the test-period returns to form the walk-forward equity curve.

We care much more about this curve than the in-sample equity curve.

---

# 18. Cross-Pair Validation

For hypotheses claiming general FX behavior, test across multiple pairs.

Record each pair separately.

Measure:

- number of signals
- expectancy
- profit factor
- average winner
- average loser
- maximum drawdown
- Sharpe/Sortino
- cost per trade
- MAE
- MFE

A strategy does not need to be profitable on every pair.

But a supposedly general structural effect should not rely completely on one instrument.

---

# 19. Contribution Concentration

Calculate:

\[
Contribution_i=
\frac{PnL_i}
{TotalPnL}
\]

If one pair produces most of the result, investigate whether:

1. the economic mechanism is genuinely pair-specific; or
2. the portfolio result is actually one lucky backtest.

Do not hide concentration inside aggregate statistics.

---

# 20. Year-by-Year Validation

Report every calendar year independently.

Example:

| Year | Trades | Expectancy | PF | DD |
|---|---:|---:|---:|---:|
| 2019 | | | | |
| 2020 | | | | |
| 2021 | | | | |
| 2022 | | | | |
| 2023 | | | | |
| 2024 | | | | |
| 2025 | | | | |
| 2026 | | | | |

We are looking for economic persistence, not identical annual returns.

---

# 21. Regime Analysis

Without changing the strategy, segment performance by:

### Volatility

- low
- medium
- high

### Trend environment

- directional
- neutral
- reversal-heavy

### Session

- London DST
- London non-DST

### Macro environment

Where relevant:

- tightening
- easing
- crisis/stress

### Direction

- long
- short

### Currency

Aggregate exposure by currency, not merely pair.

---

# 22. Parameter Robustness

Never select the single highest-performing parameter.

Suppose compression threshold is tested at:

\[
20,25,30,35,40\%
\]

Healthy result:

\[
0.8,\ 0.9,\ 1.0,\ 0.95,\ 0.83
\]

Fragile result:

\[
0.1,\ 0.2,\ 1.8,\ -0.1,\ 0.0
\]

The first suggests a plateau.

The second suggests optimization noise.

Choose parameters from the center of stable regions.

---

# 23. Sensitivity Testing

Every important parameter should be perturbed.

For example:

### Time window

Shift ±15–30 minutes.

### Stop

\[
0.8,\ 1.0,\ 1.2
\]

times the baseline distance.

### Holding period

Test modestly earlier and later exits.

### Compression threshold

Neighboring percentiles.

### Trend lookback

Neighboring periods.

If minor changes destroy performance, reject or downgrade the strategy.

---

# 24. Transaction-Cost Model

Every backtest must include:

\[
NetPnL
=
GrossPnL
-
Spread
-
Commission
-
Slippage
-
Financing
\]

Use actual historical Bid/Ask where possible.

For longs:

entry effectively occurs at Ask.

Exit occurs at Bid.

Reverse for shorts.

Never backtest intraday FX exclusively using mid-price candles.

---

# 25. Cost Stress Testing

Test:

### Base

\[
1.0\times Cost
\]

### Moderate

\[
1.25\times Cost
\]

### Severe

\[
1.5\times Cost
\]

### Extreme

\[
2.0\times Cost
\]

A serious intraday strategy should not immediately collapse under a modest increase in execution costs.

Record:

\[
EdgeToCost=
\frac{GrossExpectancy}
{AverageCost}
\]

Higher is better.

An edge that earns 0.7 pip before paying 0.6 pip is not attractive even if the historical backtest remains slightly positive.

---

# 26. Slippage Model

Slippage should depend on conditions.

At minimum distinguish:

- ordinary market entry
- breakout entry
- stop-loss execution
- high-volatility event
- thin-liquidity periods

Stops generally deserve more pessimistic assumptions than passive exits.

Run Monte Carlo or empirical slippage distributions rather than assuming every fill occurs exactly at the trigger.

---

# 27. News Handling

Do not initially remove news periods merely because they create losses.

First classify them.

Measure strategy performance:

- around major releases;
- away from releases.

Possible outcomes:

1. News destroys the edge.
2. News strengthens the edge.
3. News changes only execution costs.
4. News makes no meaningful difference.

Only introduce a news filter when evidence supports it.

---

# 28. Core Performance Metrics

For every strategy calculate:

\[
Expectancy =
P(W)\overline{W}
-
P(L)\overline{L}
-
Costs
\]

Also report:

- total trades
- average trade
- median trade
- win rate
- average winner
- average loser
- payoff ratio
- profit factor
- Sharpe
- Sortino
- max drawdown
- expected shortfall
- skew
- recovery factor
- MAE
- MFE
- turnover
- average holding period
- average spread
- average slippage

Win rate alone has almost no meaning.

---

# 29. R-Multiple Reporting

For manual and systematic intraday trading, normalize results into:

\[
R=
\frac{TradePnL}
{InitialRisk}
\]

Record:

- mean R
- median R
- standard deviation of R
- average positive R
- average negative R
- maximum consecutive losses

This allows comparison across pairs and position sizes.

---

# 30. Confidence Intervals

Do not treat estimated expectancy as exact.

Bootstrap the trade series.

Prefer block/bootstrap methods when observations may be serially dependent.

Estimate confidence intervals for:

- expectancy
- Sharpe
- drawdown
- profit factor where feasible

The central question becomes:

> How uncertain is our estimate of the edge?

rather than:

> Is the backtest positive?

---

# 31. Multiple-Testing Control

Record every experiment.

The more configurations tested, the less impressive the best result becomes.

For mature strategies calculate where practical:

- Deflated Sharpe Ratio
- Probability of Backtest Overfitting
- bootstrap significance against the stripped benchmark

A strategy found after 300 failed configurations gets a higher evidentiary hurdle than one specified almost entirely beforehand.

---

# 32. Monte Carlo Analysis

Generate alternate paths through:

- trade resampling
- return-block resampling
- randomized slippage
- sequence reshuffling where appropriate

Estimate distributions for:

- max drawdown
- losing streak
- annual return
- recovery time

Do not size using the historical max drawdown alone.

---

# 33. Research Pass Conditions

A candidate becomes a **validated research edge** when:

### Mechanism

There is a plausible economic reason for the effect.

### Signal

The underlying state predicts something before stops/targets are optimized.

### Benchmark

It beats a stripped baseline.

### OOS

Net expectancy remains positive out of sample.

### Breadth

Performance is not obviously one pair/year accident unless the economic hypothesis is explicitly pair-specific.

### Parameters

A reasonable robustness plateau exists.

### Costs

The edge survives realistic costs and meaningful stress.

### Selection

Results remain credible given the number of variants tested.

Failure of the first four generally kills the strategy.

---

# 34. Trading Rule Construction

Only after the predictive effect survives do we construct the trading system.

Define:

- eligible pairs
- eligible session
- setup conditions
- direction
- trigger
- order type
- stop
- exit
- maximum holding period
- invalidation
- news handling
- position sizing

Every rule should be observable in real time.

No rule may depend on knowing what happened later.

---

# 35. Entry Optimization Comes Late

Once the structural edge works, compare execution methods.

Example:

Structural edge:

\[
Compression
+
London
+
HTFDirection
\]

Possible entries:

- range breakout
- breakout + retest
- sweep reversal
- CISD
- FVG pullback
- market order

Now we ask:

> Which execution method extracts the structural edge most efficiently?

This prevents us from mistaking execution terminology for the actual source of P&L.

---

# 36. Exit Research

Test exits independently.

Start with deliberately simple exits:

### Time exit

Example:

close at a fixed London time.

### Opposite-range exit

### Volatility stop

### Structural invalidation

### Fixed R target

Only add sophisticated trade management if it produces genuine incremental improvement.

---

# 37. Partial Profits

Do not assume partial profit taking improves a strategy.

Compare:

\[
FullExit
\]

against:

\[
Partial+Runner
\]

using identical entries.

Judge on:

- expectancy
- drawdown
- skew
- psychological/execution consistency

Partials may reduce volatility while also reducing expectancy.

That is an empirical question.

---

# 38. Break-Even Stops

Treat break-even movement as another strategy feature.

Compare:

- no BE
- BE at 0.5R
- BE at 1R
- structure-based BE

Measure how often BE prevents a full loss versus destroys a subsequent winner.

Do not call BE "risk-free."

---

# 39. Position Sizing Validation

Position sizing is applied after the edge exists.

Initial research uses constant risk or constant volatility.

Then compare:

- fixed fractional
- volatility scaling
- portfolio-level risk targeting

Sizing must never rescue a negative-expectancy signal.

---

# 40. Currency Exposure Aggregation

FX positions must be decomposed into currencies.

Example:

Long EURUSD

and

Long GBPUSD

are both partly:

\[
Short\ USD
\]

Therefore portfolio risk must be calculated by currency factor, not just by pair.

Aggregate:

- USD
- EUR
- GBP
- JPY
- AUD
- CAD
- CHF

exposures.

---

# 41. Correlation Risk

Measure:

- signal correlation
- trade-return correlation
- daily P&L correlation
- drawdown overlap

EURUSD and GBPUSD strategies may appear separate while actually expressing nearly identical USD exposure.

---

# 42. Manual and Algorithmic Paths

Once a trading rule is frozen, validation splits.

\[
\boxed{
ValidatedEdge
\rightarrow
\begin{cases}
ManualExecution\\
AlgorithmicExecution
\end{cases}
}
\]

The underlying edge must remain the same.

---

# 43. Manual Trading Validation

Manual trading is treated as another model.

The human trader is effectively adding:

\[
DiscretionaryFilter
\]

to the mechanical signal.

Therefore discretion must demonstrate value.

---

# 44. Manual Setup Checklist

Every setup should be reducible to a checklist.

Example:

### FX-LDN

- Eligible pair?
- Correct session?
- Asia range completed?
- Compression condition satisfied?
- Directional condition satisfied?
- Trigger occurred?
- Spread acceptable?
- News condition satisfied?
- Stop location valid?
- Position size valid?

If discretionary judgement remains, define it explicitly.

---

# 45. Consistency Test

Take a historical set of charts.

Mark decisions without future information.

After a meaningful gap, independently repeat the classification.

Measure:

\[
Consistency=
\frac{SameDecision}
{TotalDecisions}
\]

If you cannot repeatedly identify the same setups, the rule is not yet sufficiently defined for reliable manual execution.

---

# 46. Blind Replay Test

Use unseen historical sessions.

Future candles must be hidden.

For every potential trade, record **before revealing subsequent prices**:

- trade / no trade
- direction
- entry
- stop
- target/exit plan
- confidence if desired
- reason

Then reveal the future.

No retroactive chart interpretation.

---

# 47. Manual Baseline Comparison

Compare the trader against the mechanical strategy.

Mechanical system:

\[
M
\]

Manual-filtered system:

\[
M+D
\]

Evaluate:

\[
\Delta E=
E[M+D]-E[M]
\]

If discretionary filtering consistently reduces expectancy, the manual filter should be removed.

If it improves expectancy robustly, discretion may be a genuine second edge.

---

# 48. Execution-Adherence Metric

For live/demo manual trading:

\[
Adherence=
\frac{TradesExecutedAccordingToPlan}
{TotalTrades}
\]

Track separately:

- valid signals taken
- valid signals skipped
- invalid trades taken
- exit violations
- sizing violations

Do not mix strategy failure with trader-process failure.

---

# 49. Manual Trade Journal

Every trade gets:

- trade ID
- strategy version
- pair
- date/time
- signal
- screenshot before entry
- planned entry
- actual entry
- stop
- planned exit
- actual exit
- spread
- slippage
- position size
- MAE
- MFE
- P&L
- R multiple
- rule adherence
- discretionary modification
- short note

Journal design should serve analysis rather than storytelling.

---

# 50. Algorithmic Validation Path

For automation:

\[
PythonResearchModel
\rightarrow
MQL5Implementation
\rightarrow
ParityTest
\rightarrow
MT5RealTickBacktest
\rightarrow
ForwardDemo
\rightarrow
Live
\]

---

# 51. Python → MQL5 Parity Test

Before evaluating MT5 performance, verify the EA generates the same signals as the research model.

For selected periods compare trade by trade:

- signal timestamp
- direction
- trigger
- stop
- exit
- position size

Any difference must be understood.

We should be able to reconcile virtually every discrepancy.

---

# 52. MT5's Role

MT5 becomes the execution-validation environment.

Use:

**Every tick based on real ticks** where available.

Validate:

- Bid/Ask behavior
- spread
- order triggering
- stop execution
- commissions
- broker symbol specifications
- latency sensitivity
- portfolio interaction

Do not rely on simplified OHLC testing for final intraday validation.

---

# 53. MT5 Is Not the Primary Research Engine

Python should remain the main environment for:

- conditional-return analysis
- event studies
- cross-sectional work
- bootstrapping
- walk-forward analysis
- regime analysis
- parameter surfaces
- experiment tracking
- Monte Carlo analysis

MT5 answers:

> Would the frozen strategy have executed realistically through this broker/feed?

Python answers:

> Is the hypothesis actually supported by the data?

---

# 54. Demo Forward Validation

Once historical testing is complete:

Freeze the strategy.

Do not optimize during the forward test.

Collect:

- every valid signal
- theoretical fill
- actual fill
- spread
- slippage
- execution errors
- strategy P&L

Compare forward behavior with the OOS distribution.

---

# 55. Shadow Trading

For manual strategies, simultaneously record:

### System signal

What the frozen strategy said.

### Trader action

What you actually did.

This allows:

\[
SystemEdge
\]

and:

\[
TraderValueAdded
\]

to be measured separately.

This is essential if the long-term objective may involve both discretionary and algorithmic trading.

---

# 56. Live Deployment Ladder

A strategy should move through stages:

### Stage 0 — Research

No capital.

### Stage 1 — Replay

Manual or algorithmic historical execution.

### Stage 2 — Demo / shadow

Current markets, zero capital.

### Stage 3 — Micro-live

Very small risk.

Objective:

validate fills, behavior, and operational process.

### Stage 4 — Validated live

Increase risk only after realized behavior remains consistent with validated expectations.

### Stage 5 — Portfolio allocation

Strategy receives a meaningful risk budget alongside other independent edges.

---

# 57. Risk During Initial Live Validation

Initial live size should be small enough that the purpose remains **information gathering**, not income generation.

The first question is:

> Does real execution reproduce the validated system?

not:

> How much can I make this month?

Scale only once:

- signal behavior;
- costs;
- adherence;
- drawdown;
- expectancy

are consistent with expectations.

---

# 58. Edge Health Monitoring

Once live, maintain rolling metrics.

Track:

- last 20 trades
- last 50 trades
- last 100 trades
- rolling expectancy
- rolling PF
- rolling cost
- rolling slippage
- rolling drawdown
- setup frequency

Compare live metrics against the backtest distribution.

---

# 59. Edge-Decay Trigger

Do not declare an edge dead merely because of a losing streak.

Use simulations from the validated strategy to establish expected ranges.

Trigger investigation when:

- drawdown enters an historically/modelled extreme tail;
- expectancy materially deviates from its expected range;
- transaction costs structurally increase;
- signal frequency materially changes;
- underlying market structure changes.

Investigation does not mean immediate optimization.

---

# 60. Never Re-Optimize Live Losses Immediately

When performance deteriorates:

1. freeze the current version;
2. diagnose;
3. identify a new hypothesis;
4. test it separately;
5. forward validate it;
6. only then consider replacing the current model.

Otherwise every drawdown turns into curve-fitting.

---

# 61. Strategy Maturity Levels

## Level 0 — Idea

Economic hypothesis only.

## Level 1 — Statistical Effect

Conditional behavior exists.

## Level 2 — Tradable Edge

Net positive after realistic execution.

## Level 3 — Robust Edge

Survives OOS, regimes, neighboring parameters and costs.

## Level 4 — Executable Edge

Manual or algorithmic implementation behaves as expected.

## Level 5 — Live Edge

Current-market performance remains compatible with validation.

## Level 6 — Portfolio Edge

Adds useful return after considering correlation with existing strategies.

Only Levels 4–6 deserve trading capital.

---

# 62. Required Research Report for Every Edge

Every candidate eventually receives a one-page scorecard containing:

### Thesis

Why should the edge exist?

### Payer

Who is transferring value?

### Clock

When should it occur?

### Signal

What observable state identifies it?

### Benchmark

What simpler strategy must it beat?

### Sample

How much data was used?

### OOS result

What happened on unseen data?

### Cost result

What happens after realistic costs?

### Robustness

Does the effect survive parameter and regime changes?

### Failure modes

When does it lose?

### Execution

Manual / systematic / automated?

### Status

Reject / Research / Validate / Deploy.

---

# 63. Pass / Fail Decision Tree

For every idea:

### Question 1

Does the underlying conditional effect exist?

**No → Reject.**

**Yes → Continue.**

### Question 2

Does it beat the stripped benchmark?

**No → Remove the unnecessary feature.**

**Yes → Continue.**

### Question 3

Does it survive OOS?

**No → Reject or return to hypothesis formation.**

### Question 4

Does it survive realistic costs?

**No → Reject as untradable.**

### Question 5

Is it robust across reasonable neighboring specifications?

**No → Reject as fragile.**

### Question 6

Can it be implemented consistently?

**No → simplify the rules.**

### Question 7

Does current forward performance behave within expected ranges?

**No → investigate before deploying meaningful capital.**

### Question 8

Does it improve the portfolio after correlations?

**No → it may still be a real edge, but it does not deserve additional portfolio risk.**

---

# 64. What Counts as Success

The target is not:

- 80% win rate;
- a perfect equity curve;
- dozens of setups;
- one huge backtest CAGR.

The target is:

\[
\boxed{
Positive\ Net\ Expectancy
}
\]

that survives:

\[
\boxed{
Different\ Samples
+
Different\ Regimes
+
Realistic\ Costs
+
Real\ Execution
}
\]

and can be repeated by either:

\[
\boxed{
Code
}
\]

or:

\[
\boxed{
A\ disciplined\ human\ process
}
\]

---

# 65. Recommended Research Sequence

We should proceed in this order:

### Phase I — Intraday structural edge

**FX-03 Asia → London**

Research:

\[
Compression
\rightarrow
Expansion
\rightarrow
Direction
\rightarrow
Execution
\]

This directly connects to the style of trading already being developed.

---

### Phase II — Slow FX edge

**FX-01 Trend**

Establish a low-frequency structural benchmark.

---

### Phase III — Carry

**FX-02 Trend + Carry**

Test whether combining the two creates better portfolio characteristics.

---

### Phase IV — Institutional flow

**FX-04 Fix / Month-End**

Develop a second independent intraday mechanism.

---

# 66. Desired End State

The objective is not one magical strategy.

The eventual FX book could contain:

### Slow Engine

\[
Trend + Carry
\]

### Intraday Engine 1

\[
London\ Liquidity/Expansion
\]

### Intraday Engine 2

\[
Benchmark/Rebalancing\ Flow
\]

Each should have a genuinely different economic mechanism.

Only after the individual edges are validated should they be combined.

---

# 67. The Rule That Governs the Entire Project

For every trading concept:

> **Identify the economic mechanism. Demonstrate the statistical effect. Beat the stripped benchmark. Survive unseen data. Survive real costs. Prove you can execute it. Then risk capital.**

Anything that fails one of those stages remains research—not an edge.