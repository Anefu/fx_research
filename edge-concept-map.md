# Edge Concept Map — Core Concepts for FX, Futures, and Equity Options

**Date:** 2026-10-02

Distilled from the FX daily-strategy research, intraday FX candidates, intraday options candidates, and TheStrat/TTFM + ICT-primitives grading.

The purpose is not to collect setups. It is to identify **repeatable economic transfers** that survive stripped benchmarks, realistic costs, and publication decay.

---

# Part A — Shared Framework

## A1. Edge begins with an economic transfer

For any proposed edge, identify:

1. **Who is on the other side?**
2. **Why are they willing or required to transact?**
3. **Why does the transfer persist despite competition?**
4. **When does it occur?**

Recurring counterparties include:

- **Hedgers** — transferring price or volatility risk
- **Mandate-bound actors** — benchmark fixes, rebalances, rolls
- **Liquidity demanders** — stops, margin calls, urgent execution
- **Behaviorally constrained actors** — underreaction, herding, attention effects

A counterparty does not need to be irrational or literally unable to stop. Persistence can come from mandates, risk-transfer demand, institutional constraints, recurring liquidity needs, or slow behavioral adjustment.

The strongest edges have a clear economic reason to survive publication.

---

## A2. Separate signal, premium, and risk engineering

Do not treat these as interchangeable.

### Signal
Information that predicts the future distribution or direction of returns.

Examples:
- trend
- reversal
- breakout
- valuation
- order-flow imbalance

### Premium
Compensation for carrying risk or accommodating another participant.

Examples:
- carry
- volatility risk premium
- commodity term-structure premia
- liquidity provision

### Risk engineering
How the raw return stream is transformed.

Examples:
- volatility targeting
- position sizing
- stops
- leverage limits
- diversification

Risk engineering can materially improve drawdowns, tails, and sometimes Sharpe, but it does not automatically create the underlying economic edge.

---

## A3. Premium families

Most candidates fall into a small number of families:

1. **Risk-transfer premia**
   - trend
   - carry
   - volatility risk premium

2. **Structural-flow premia**
   - benchmark fixes
   - month-end rebalancing
   - futures rolls
   - opening/closing auctions

3. **Behavioral effects**
   - underreaction
   - short-horizon reversal
   - attention-driven gaps

4. **Liquidity effects**
   - stop cascades
   - margin liquidation
   - temporary price pressure

5. **Calendar/event effects**
   - scheduled macro announcements
   - earnings
   - expiry
   - uncertainty resolution

The taxonomy matters because genuine diversification should come primarily **across economic mechanisms**, not from combining multiple indicators that express the same exposure.

---

## A4. The trend-rule equivalence principle

Momentum, moving-average rules, breakouts, and related trend filters often capture highly similar directional exposures.

Therefore:

> Do not count rule variants as separate edges until their return streams are demonstrably independent.

The same applies to discretionary stacks.

If:
- FVG
- order block
- POI
- retracement entry

all reduce to “enter a pullback in the direction of an established move,” they should initially be treated as one hypothesis.

Diversification belongs across mechanisms, not terminology.

---

## A5. The edge has a clock

The holding period should match the mechanism producing the opportunity.

Examples:

- **Trend:** days to months
- **Macro value:** months to years
- **Carry:** weeks to months
- **Fix/rebalance flows:** minutes to hours
- **Stop cascades:** seconds to minutes
- **Event-volatility trades:** hours to days

For intraday strategies, the time window is part of the signal itself.

Session definitions, benchmark times, exchange opens, contract rolls, and daily-close conventions are therefore not cosmetic implementation details.

---

## A6. Volatility is a state variable

Volatility affects both signal quality and portfolio construction.

Key principles:

- volatility clusters;
- expected returns do not scale mechanically with volatility;
- high-volatility regimes alter stop distance, liquidity, and execution;
- inverse-volatility scaling can materially change the properties of a strategy;
- in options, volatility itself becomes the traded object.

Every strategy should therefore distinguish between:

**raw signal performance**

and

**performance after volatility scaling.**

If the second works but the first does not, the apparent improvement may come primarily from risk transformation rather than predictive alpha.

---

## A7. Microstructure comes before backtest excitement

Before evaluating returns, test:

### Cost
\[
\text{Expected edge} > \text{spread + slippage + fees + financing}
\]

### Capacity
Can the trade absorb meaningful size without erasing the opportunity?

### Execution
Does the result require fills that would be unrealistic during the exact periods when the signal occurs?

### Market structure
Does the signal depend on:
- clustered stops,
- auction imbalances,
- dealer inventory,
- benchmark execution,
- forced liquidation,
- thin liquidity?

Many slow strategies survive because transaction costs are small relative to expected movement.

Many intraday ideas fail because the spread-to-edge ratio is too high.

---

## A8. Risk engineering is survival, not alpha

Core tools:

- volatility targeting
- gross exposure caps
- correlation limits
- fractional Kelly
- stop-loss design
- portfolio diversification

These should be evaluated primarily on:

- maximum drawdown
- expected shortfall
- tail loss
- recovery time
- leverage stability

not merely average return.

---

## A9. Falsification comes before optimization

Every strategy must beat a simpler control.

Examples:

- sweep + entry vs. the same entry without the sweep
- ICT stack vs. plain breakout/pullback
- TheStrat confirmation vs. FTFC alone
- momentum + volatility scaling vs. volatility scaling alone

Additional requirements:

- asset-by-asset results
- out-of-sample testing
- parameter plateaus rather than isolated peaks
- realistic costs
- publication-date splits
- post-publication performance
- multiple-testing awareness

The question is not:

> “Can I backtest this profitably?”

It is:

> “What is the simplest explanation for the observed return, and does the added rule contribute anything?”

---

# Part B — Asset-Specific Structure

# FX

## B-FX1. Everything is relative

An FX pair is one currency priced in another.

There is no equity-style structural upward drift.

Therefore:
- valuation must be relative;
- momentum is cross-currency;
- mean-reversion rules cannot simply be imported from equities;
- every long position is simultaneously a short position in another currency.

PPP and related valuation signals therefore belong naturally in FX.

---

## B-FX2. Session geometry replaces the equity open

FX trades continuously, but liquidity and institutional flow do not.

Relevant anchors include:

- Asia session
- London open
- London–New York overlap
- WM/Reuters 16:00 London fix
- 17:00 New York rollover
- month-end rebalancing windows

An intraday FX strategy without an explicit session clock is usually underspecified.

---

## B-FX3. Structural flow is unusually important

Recurring actors include:

- central banks
- corporates
- asset managers
- benchmark trackers
- dealers managing inventory

This produces opportunities around:

- intervention
- benchmark fixes
- month-end hedging
- large institutional rebalancing

These are especially attractive because the payer and timing can often be identified directly.

---

## B-FX4. Carry is a core FX premium

Interest-rate differentials create persistent return differences through forward points and swaps.

Carry should be treated as its own risk-transfer premium.

Its return must be evaluated against:

- financing costs
- volatility
- crash risk
- funding-currency reversals
- risk-off unwinds

Carry is persistent precisely because the return compensates investors for bearing unpleasant states.

---

# Futures

## B-F1. Term structure matters

Futures returns depend not only on spot movement but also on the shape and evolution of the curve.

Relevant concepts:

- contango
- backwardation
- basis
- roll yield
- convenience yield
- storage economics
- hedging pressure

Term structure is therefore both an economic signal and an implementation variable.

---

## B-F2. Contract mechanics create recurring flows

Futures contain built-in institutional events:

- expiry
- contract rolls
- delivery windows
- daily settlement
- margin changes
- index rebalancing

These can create predictable temporary flows.

Contract selection and roll methodology must therefore be part of the strategy specification.

---

## B-F3. Futures are the cleanest trend laboratory

Futures offer:

- deep liquidity
- low trading friction in major contracts
- easy shorting
- standardized contracts
- broad cross-asset coverage

This is why much of the systematic trend-following literature is expressed through futures.

However, pooled evidence must still be checked asset by asset.

A portfolio-level trend result does not prove that every underlying market contains independent momentum predictability.

---

## B-F4. Basis converges

As expiry approaches, futures and deliverable cash prices are economically linked.

Convergence creates:

- arbitrage flows
- roll pressure
- basis compression
- occasional squeezes

This makes basis dynamics a futures-specific source of both signal and execution risk.

---

# Equity Options

## B-E1. Volatility is the primary state space

Options transform volatility from a conditioning variable into a directly tradable exposure.

The core relationship is:

\[
\text{Implied volatility} \quad \text{vs.} \quad \text{realized volatility}
\]

Relevant structures include:

- variance risk premium
- skew
- volatility term structure
- event volatility
- dispersion

Equity-index options are particularly rich because they combine:

- positive long-run equity drift
- asymmetric crash risk
- persistent demand for downside protection

---

## B-E2. Greeks are the exposure language

Every options strategy is a portfolio of:

- delta
- gamma
- vega
- theta

The option label alone is insufficient.

Two spreads with similar payoff diagrams can have materially different sensitivity to:

- spot movement
- volatility
- time decay
- jumps
- liquidity

Short-vol strategies must therefore define risk limits as part of the strategy itself because losses are nonlinear and regime-dependent.

---

## B-E3. Event timing matters

Scheduled events create known uncertainty-resolution windows.

Examples:

- CPI
- FOMC
- earnings
- option expiry
- index rebalancing

The correct research question is not:

> “Does volatility fall after the event?”

It is:

> “Was the event premium priced above subsequently realized event risk after transaction costs and tail losses?”

Similarly, historical return anomalies around announcements must be checked for publication decay before being treated as live edges.

---

## B-E4. Instrument mechanics constrain the strategy

Relevant details include:

- American vs. European exercise
- early assignment
- cash vs. physical settlement
- pin risk
- expiry mechanics
- 0DTE gamma
- strike liquidity
- bid-ask width

For intraday options research, underlying OHLC is not sufficient.

Serious testing requires historical option chains with realistic bid/ask and execution assumptions.

---

# Part C — Portfolio Architecture

## Core strategies

These are the candidates with the strongest combination of economic rationale, long evidence, and scalable implementation.

### FX
- trend
- carry
- relative value

### Futures
- trend
- term structure / carry

### Equity options
- volatility risk premium
- skew / downside-insurance premium

---

## Tactical overlays

These are shorter-lived and more capacity-constrained.

### FX
- Asia → London transitions
- benchmark fixes
- month-end flows
- stop-cluster continuation

### Futures
- roll windows
- opening/closing flows
- short-term basis dislocations

### Options
- event-volatility mispricing
- expiry effects
- end-of-day flows
- volatility compression/expansion setups

These require substantially stricter execution and cost testing than the core strategies.

---

# Part D — The Screening Rule

Every new strategy must answer six questions:

> **1. What is the economic transfer?**  
> Who gains when I lose, and who loses when I gain?

> **2. Why does it persist?**  
> Mandate, hedging demand, risk aversion, behavioral bias, liquidity need, or institutional constraint?

> **3. What is its clock?**  
> Seconds, session, day, month, or multi-year horizon?

> **4. What is the stripped benchmark?**  
> What simpler rule expresses the same underlying exposure?

> **5. Does the added complexity contribute anything?**  
> Incremental return, better tails, better timing, or lower costs?

> **6. Does it survive reality?**  
> Out-of-sample data, post-publication performance, spreads, slippage, financing, and capacity.

If these cannot be answered, the strategy remains a **research hypothesis**, not an allocation.

The full research process is therefore:

\[
\boxed{
\text{Economic mechanism}
\rightarrow
\text{Signal}
\rightarrow
\text{Stripped benchmark}
\rightarrow
\text{Implementation}
\rightarrow
\text{Risk engineering}
\rightarrow
\text{Allocation}
}
\]

That is the common framework across FX, futures, and equity options.
