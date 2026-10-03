# TTFM Research Specification v1.1

## 1. Purpose

Find the market conditions that create useful continuation or reversal opportunities. Then test whether TTFM helps identify and trade them.

Answer four questions separately:

1. What participant behavior could explain the opportunity?
2. Under which observable conditions does the opportunity appear?
3. Does TTFM add information beyond simpler rules?
4. Does TTFM improve results after costs?

TTFM is a candidate framework for detecting and trading opportunities. Its patterns are not assumed to be an edge.

This document defines the research process and the first experiment. Later TTFM experiments need their own frozen rule sheets before testing. No result is implied by the definitions below.

## 2. Terms

| Term | Meaning |
|---|---|
| Economic explanation | Participant behavior that could create the opportunity: urgent orders, temporary pressure, or persistent trading demand. |
| Market state | Conditions observable at the decision time: trend, volatility, session, recent price movement, and level characteristics. |
| Price response | What price does after an encounter or confirmation. |
| Detection rule | Evidence that an opportunity may be actionable, such as reclaim or CISD. |
| Trading rule | Entry, position size, stop, target, and management. |
| Trading edge | Repeatable positive net expectancy under an executable rule. |

Predictive information, a plausible explanation, and a profitable trading rule are separate findings. A useful prediction can still be too small to trade.

## 3. Economic hypotheses

| ID | Candidate explanation | Predicted behavior | Evidence that would help distinguish it |
|---|---|---|---|
| MEC-01 | Conditional orders create urgent trading when a salient level breaks. | Faster movement in the direction of the break. | Greater aggressive trading and price impact near salient levels than comparable crossings; direct order evidence where available. |
| MEC-02 | Temporary trading pressure moves price beyond levels that opposing liquidity can sustain. | An initial move followed by reversal as pressure fades. | Aggressive trading weakens, liquidity returns, and impact decays without continuing information-driven repricing. |
| MEC-03 | Information, hedging, or execution demand persists. | Directional movement resumes after a pullback. | Persistent signed trading pressure, repeated continuation, and relevant external information where available. |

These explanations may coexist. A stop-driven move can be followed by reversal or develop into a longer trend. The categories are not mutually exclusive labels for individual charts.

Price patterns alone cannot establish order motive. Futures trades and order-book data provide additional evidence but do not automatically identify stops, dealer inventory, or institutional intent. Spot broker quotes describe that feed's price behavior; they do not measure global FX order flow.

For each hypothesis record both its predicted behavior and a rival explanation. Ask which additional observation could separate them. When the data cannot do so, leave the explanation unresolved.

## 4. Research sequence

1. Build and validate the encounter dataset.
2. Test pre-declared economic hypotheses together with their market states.
3. Compare TTFM detection with simple rules at the same decision time.
4. Compare complete trading policies on the same opportunities and risk budget.
5. Validate frozen rules on later data and then forward test them.

A failed pooled test rejects the pooled hypothesis. It does not automatically reject separately registered conditional hypotheses. For example, a level break may predict continuation in a directional state and reversal elsewhere.

A failed prediction must not be rescued by searching unregistered filters until it works. New ideas receive new experiment IDs and count as additional tests. Lack of direct mechanism evidence is recorded as uncertainty, not as proof that no trading opportunity exists.

## 5. Levels and encounters

Candidate level families are previous-day highs/lows, previous-week highs/lows, completed-session highs/lows, confirmed swings, and round numbers. Test families separately at first.

Every level needs:

- A fixed calculation and price convention.
- A timestamp when it becomes available.
- An expiry rule.
- A definition of approach, touch, and breach.
- A rule for overlapping levels and repeated encounters.

The initial rule is one first eligible breach per level. Later touches need separate experiments. A level is not available before it can be calculated. A developing session high is a different feature from a completed session high.

For a swing using `k` bars on either side, the candidate high must exceed all those highs. It becomes available only when the final confirming bar closes. Define ties, timeframe, `k`, and expiry in its rule sheet.

Record level age, prominence, departure distance, earlier encounters, and creation session. Calculate each feature using only information available at the relevant decision time.

## 6. Two decision times

**Encounter time, t0:** the level first meets the registered encounter rule.

**Confirmation time, t1:** a later condition becomes observable, such as reclaim or CISD. An event may never receive confirmation.

Keep separate outcomes for each time:

- Encounter outcomes describe movement after t0.
- Confirmation outcomes describe movement after t1.

Movement before t1 is a possible input to a confirmation rule. It is not a payoff that the rule could have captured after confirmation.

For example, “breach followed by failure” cannot be treated as information known at the breach. Define the failure window, record when failure is confirmed, and measure subsequent prediction from that time.

Use the first executable quote after the required confirmation and entry latency for trading results. A completed-bar signal cannot receive the price from earlier in that bar.

## 7. Price-response outcomes

Use one common barrier race for the primary continuation/reversal classification.

For an upward encounter, freeze a reference price `p0`, a volatility measure `a0`, and an observation horizon at t0:

- **Continuation:** price reaches `p0 + b × a0` first.
- **Reversal:** price reaches `p0 − b × a0` first.
- **Neither:** neither barrier is reached before the horizon ends.

Reverse the signs for downward encounters. Freeze volatility at the starting time; do not update barriers using future volatility. At t1, a confirmation experiment starts a new race with its own contemporaneous reference price and volatility.

Use tick sequence to determine which barrier was reached first. If sequence or data coverage is insufficient, record **unknown**, rather than treating missing information as neither. State how gaps and simultaneous or unresolved crossings are handled.

Reclaim, maximum overshoot, and failure to continue are separate path features. They are not extra requirements silently added to one side of the barrier race.

Also record signed returns, MFE, and MAE at 5, 15, 30, 60, and 120 minutes where measurable. Orient directional outcomes to the encounter direction. Keep missing-horizon flags and reasons.

## 8. Market states and controls

Start with a small set of states defined before outcome inspection:

- Prior direction and trend strength.
- Volatility.
- Session and scheduled announcements.
- Recent approach speed, distance, and pullback depth.
- Level family, age, and prominence.

Test the mechanism and its proposed state together. Describe the specific expected difference before measuring it.

Controls must isolate the comparison of interest. A test of trend should not match away trend. A test of session should not require identical sessions.

For a salient-level test, compare encounters with non-salient crossings under similar pre-event conditions. Generate candidate control levels before their encounters. Match using pre-event features, never subsequent returns, reclaim, or target hits.

Record matching quality, unmatched events, control reuse, and sample exclusions. Matching supports a conditional comparison; it does not by itself prove causation.

## 9. First experiment: GEN1-01

This is the starting contract. The parameter choices are research defaults, not empirically established optimal values. Any change after outcome inspection creates a new experiment version and belongs in the testing record.

| Item | Frozen definition |
|---|---|
| Market | 6E futures. Use actual contracts, not synthetic prices, for event and execution measurements. |
| Daily session | Exchange trading-date calendar, including holiday sessions. Save the exact calendar used. |
| Active contract | Highest-volume eligible contract in the previous completed exchange session; retain it for the whole next session. |
| Roll handling | On a contract change, build the prior-session references from that same contract's history. Exclude events without adequate same-contract history. Never bridge a return across contracts. |
| Level family | Previous completed exchange-session high and low, calculated from eligible trades in the active contract. |
| Level availability | Start of the next exchange session. |
| Expiry | End of that next session. |
| Encounter | First upward trade crossing of the high or downward trade crossing of the low, by at least one tick, following an observed trade on the inside. If the opening trade is already beyond a level, exclude that level for the session and record an opening-gap event separately. |
| Start price | Encounter trade price. Record distance beyond the level separately. |
| Volatility | Mean true range of the previous 20 completed one-hour bars, using same-contract trade OHLC. Exclude incomplete bars under the coverage rules. |
| Primary outcome | Continuation/reversal/neither over 60 minutes, with barriers at ±0.5 times starting volatility around the start price. |
| Secondary outcomes | Directional returns, MFE, and MAE at the horizons in §7. These are descriptive unless separately registered. |
| Cost measurement | Contemporaneous bid/ask, commissions, exchange fees, and explicit slippage assumptions. The barrier outcome itself is a price-response measure, not a net trading result. |

### Primary state hypotheses

Define prior trend as the close-to-close change over 20 completed exchange sessions, divided by daily ATR over those sessions. Use same-contract history. Orient trend to the encounter direction. The resulting score has no units.

- **Aligned:** oriented trend is greater than +0.5.
- **Opposed:** oriented trend is less than −0.5.
- **Neutral:** between those thresholds, including the boundaries.

GEN1-01 has three primary comparisons: salient encounters versus matched control crossings within each state. The directional hypothesis is greater continuation at salient levels. Also report reversals and neither outcomes. A pooled comparison is descriptive and cannot replace a failed primary comparison.

### Control generation and matching

Before each session, generate 20 pseudo-levels using seed 42, market ID, and exchange trading date. Draw uniformly from the previous session's range extended by one prior daily ATR on either side, round to the tick, and remove duplicate levels. Exclude candidates within two ticks of the known previous-day/week extrema or a price that is an exact multiple of 50 ticks. Do not replace excluded candidates.

Apply the same crossing and expiry rules to control levels. Upward and downward control crossings are separate event types.

Match each structural event to at most one control encounter, without control reuse, using:

- The same trading date, encounter direction, and trend state.
- The same four-hour clock block in America/Chicago (00:00–04:00, 04:00–08:00, and so on), with encounter times within 120 minutes.
- Starting volatility within 20%.
- Five-minute pre-encounter directional return within 0.25 starting-volatility units.

Choose the eligible control with the smallest absolute time difference; break ties by earlier time, then lower level price. Process structural encounters in timestamp order. Exclude controls whose outcome interval overlaps the structural event's interval, or whose crossing falls inside another structural event's outcome interval. Retain dates and time differences for dependence and matching checks. Report unmatched events; do not relax matching after seeing outcomes.

Some sessions or states may have too few usable controls. This design also leaves possible time-of-day differences within its matching blocks. Report those differences; do not describe the comparison as causal. Inadequate support is an insufficient-evidence outcome, not permission to invent a more favorable comparison. Other control designs require new IDs.

### Evidence gate

The primary effect is the difference in continuation probability between structural and matched control events in each state.

- Research materiality floor: +5 percentage points. This is a screening threshold, not a claim of profitability.
- Minimum support per state: 500 matched encounters, 200 distinct trading dates, and three calendar years.
- Resample complete trading dates in 20-date blocks, carrying all matched events together. Use 2,000 bootstrap draws and seed 42. Every replicate must contain the requested number of dates.
- Control the three primary comparisons at a familywise 5% error rate. A simple implementation uses a 98.33% two-sided interval for each effect.
- A state passes the prediction gate only if its interval's lower bound exceeds +5 percentage points on validation data.
- Report yearly effects and repeat the interval calculation using 10- and 40-date blocks. The effect must remain positive under both checks and in at least two-thirds of years with 50 or more matched events.
- If support is inadequate, or the interval spans the materiality floor, label the result insufficient evidence. If its upper bound is below the floor, it fails the registered materiality test.

Development data establishes feasibility and checks data handling. It does not count as independent confirmation. Freeze any resulting amendments before validation. Reserve the final holdout for the complete frozen trading policy, not repeated intermediate decisions.

GEN1-01 can establish conditional price behavior. Its data alone may leave the stop-flow explanation unresolved. Do not label a passing result “stops proven.”

If 6E data is unavailable, the experiment is blocked. An EURUSD quote-feed study can be registered separately with its own session, price, control, and execution definitions; it is not a silent substitution.

## 10. Bias and location research

After the initial baseline, compare simple bias rules: no bias, prior-day direction, 5- or 20-day momentum, and precisely defined daily or four-hour structure.

Report directional probabilities and expected returns. Probability calibration matters: a predicted 60% should correspond to roughly 60% observed success on later data. A higher directional hit rate alone does not establish positive expectancy.

For locations, compare level families and characteristics under similar states. Do not start with an arbitrary POI score. Build a score or model only after showing useful out-of-sample information.

Keep a pre-declared interaction even if its individual inputs have weak effects. Remove features only after testing their registered role, including relevant interactions.

## 11. TTFM detection tests

Write exact rules for HTF bias, C2, C3/C4, sweep/reclaim, CISD, multi-timeframe alignment, and any other tested feature. Each rule must specify inputs, timeframe, confirmation time, ties, invalidation, and missing-data handling. Do not infer definitions from terminology or from a favorable chart.

At each decision time compare three models or policies:

1. Market state and information available at that time.
2. The same information plus a simple price rule, such as reclaim or momentum.
3. The same information plus the registered TTFM feature.

Measure future outcomes from that common time using the same horizon. Report incremental predictive accuracy, calibration, effect size, coverage, and uncertainty on later data.

A confirmation-time comparison is conditional on surviving to that time. Also compare full policies from the original encounter set. Count events without confirmation and opportunities missed while waiting.

Pre-register a small set of plausible interactions. Examples are trend × CISD, location × CISD, or reclaim × CISD. A fixed feature ladder is useful for comparison, but it must not prevent testing a registered combination whose individual effects are weak.

## 12. Trading-policy tests

Start with a simple policy: entry after the decision, fixed-volatility stop, and fixed-time exit. Give it the same available information and risk budget as the TTFM policy.

Compare changes to entry, stop, target, and management separately before combining them. Candidate alternatives include breakout or retracement entry, FVG entry, protected-swing invalidation, structural targets, partial profits, and break-even movement.

Freeze order type, latency, order expiry, fill rules, gap treatment, and stop execution. A touched limit is not automatically a filled order. Where queue data is unavailable, use a stated conservative fill rule and report the uncertainty.

For manual execution, supply the same rule sheet and record classification disagreements, decision latency, skipped setups, and rule deviations. Manual and automated tests use the same underlying event definitions and costs.

## 13. Common opportunities and risk

Different stops change position size and the meaning of R. Different entry rules change which trades fill. Compare policies using the same starting capital, risk per opportunity, portfolio exposure limits, and eligible encounter set.

Report:

- Net P&L per eligible encounter, counting no-trade opportunities as zero.
- Net expectancy per filled trade and trade frequency.
- Unfilled orders, missed winners, and adverse selection.
- Capital exposure, drawdown, and portfolio results.
- MFE, MAE, and time in trade.

Use common risk-normalized or cash units for policy comparison. Also report each policy's own R results, with its denominator stated. Do not compare different R units as if they were identical.

For an expectancy claim, require the validation confidence interval for the net improvement over the baseline to lie above zero. Register a practical improvement floor before the test. A rule can separately pass a risk-improvement test without improving expectancy; label that benefit accurately.

## 14. Target tests

Compare frozen target-selection policies on the same opportunities, entries, stops, and sizing. Policies may use fixed R, volatility distance, a qualifying structural level, or time exit.

Two targets at the same price are the same target on that path, regardless of their names.

Separate two questions:

1. Does a structural level predict different behavior after matching for distance and state?
2. Does a structural target-selection policy improve net trading results?

A useful policy does not have to increase target-hit probability. It may improve payoff size or avoid poor exits. Conversely, a high hit rate may have poor expectancy.

Report hit-before-stop probability, net expectancy, target distance, time to outcome, and results by distance. Handle levels that expire or change after entry using a frozen rule.

## 15. Costs

Use executable bid/ask prices and commissions, exchange fees, slippage, and financing or roll costs where relevant. Do not subtract the spread twice if it is already included in entry and exit prices.

Stress costs at 1.0, 1.25, 1.5, and 2.0 times the baseline assumptions. Apply separate realistic models to standard and micro contracts; do not assume identical fills or costs.

Report price-response results separately from tradable net returns.

## 16. Data and reproducibility gate

No inference runs before the required data checks pass. Empty, missing, stale, or incomplete inputs cannot pass by default.

Check timestamp order and timezones, quote/trade validity, coverage, session boundaries, contract transitions, and reconstruction of bars. Preserve genuine same-timestamp price changes and revisits. Remove overlapping exports using reliable record identity or source reconciliation; identical timestamp and price alone do not prove a duplicate.

Retain raw sources when possible. Adding sequence numbers to a previously price-sorted file cannot restore original chronology. Mark uncertain ordering and exclude affected sequence-dependent outcomes.

Every run must bind together:

- Exact market universe, date range, calendar, and parameter sheet.
- Raw-input fingerprints, source lineage, and cleaning log.
- Code hashes, environment, and random seeds.
- Encounter table, controls, matching ledger, and exclusions.
- Horizon eligibility and unknown outcomes.
- Statistics, decision gates, and generated result text.

Check actual table pairs and counts against the declared universe and manifest. Check that quality reports refer to the same inputs. Reject stale or inconsistent artifacts. Generate reported numbers from those bound results and verify reconciliation before writing the decision.

## 17. Validation and testing discipline

Split eligible trading dates chronologically: 60% development, 20% validation, and 20% final holdout. Assign the whole date and all its related markets/events to one partition.

Remove training events whose outcome windows extend into the next partition. Treat overlapping events, repeated levels, related markets, and serial dependence explicitly in inference. Resampling rows independently is not acceptable.

Use validation once for the registered promotion decision. If results trigger new feature or threshold choices, those choices require another untouched evaluation sample. Do not repeatedly tune against the same validation set and call it out of sample.

Keep the final holdout untouched until the entire trading policy is frozen. Previously examined history is exploratory; relabeling its final 20% does not make it untouched again. Use genuinely unused dates or a forward sample when necessary.

Maintain permanent experiment IDs, including failures and inconclusive tests. Declare which comparisons are primary, how multiple tests are controlled, and which checks are descriptive. Neighboring-parameter checks assess stability; they must not become an undeclared search for a winner.

## 18. Required rule sheet for each later experiment

Before testing, record the hypothesis and rivals, available evidence, market/data source, event and control definitions, decision times, outcomes, states, primary metric, practical effect floor, uncertainty method, minimum support, costs, validation dates, and pass/fail/insufficient-evidence rules.

Any missing operational definition blocks that experiment. Keep TTFM definitions separate from the economic hypothesis so the same underlying opportunity can be tested with simpler detection and execution.

## 19. Results and component labels

Report four independent statuses for every branch:

| Question | Possible result |
|---|---|
| Price prediction | Supported, unsupported, or insufficient evidence. |
| Economic explanation | Evidence supports it, evidence contradicts it, or unresolved. State competing explanations. |
| TTFM detection | Adds information, redundant, harmful, or insufficient evidence. |
| Trading policy | Positive net expectancy, non-positive, or insufficient evidence; separately report risk benefits. |

Label components by demonstrated function: market-state feature, detection feature, execution feature, risk feature, redundant, or rejected. Reserve an established economic edge-source claim for evidence that supports the proposed return-generating mechanism. A mechanism-consistent prediction is a weaker and still useful finding.

## 20. Delivery order

First deliver GEN1-01's validated encounter dataset, matching ledger, conditional price-response results, and qualified economic interpretation.

Then extend to reversal and persistent-flow hypotheses with their own contracts. Compare simple bias and location rules, add precisely defined TTFM detection, and finally test entries, stops, targets, and management under common risk and realistic costs.

The final output is a clear account of what behavior exists, when it occurs, what evidence explains it, and whether TTFM improves detection or net execution. An unresolved economic explanation must remain visible even if a trading policy works.

## Research references

- [Osler: Currency Orders and Exchange-Rate Dynamics](https://www.newyorkfed.org/research/staff_reports/sr125.html). Evidence on order clustering and exchange-rate behavior; motivation for hypotheses, not proof of TTFM.
- [Osler: Support for Resistance](https://www.newyorkfed.org/research/epr/00v06n2/0007osle.html). Evidence on published FX levels; not a blanket validation of every local swing.
- [CME: Market by Order](https://www.cmegroup.com/articles/faqs/market-by-order-mbo.html). Scope of anonymous order-level market data.
