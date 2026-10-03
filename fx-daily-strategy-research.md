# FX Daily Strategy Research — Candidates, Grading, Test-Ready Rules

Date: 2026-10-02

**Assumed market:** spot FX or FX CFDs on G10 majors, using daily bars (New York 17:00 close), with retail spreads and overnight swap.

Constraints: only old, simple, published ideas; no machine learning; no indicator mashups.

---

## Part 1 — The 10 candidates

### TREND

**1. Time-series momentum (12-month)**
- **Rule:** Go long a pair if its 12-month total return is positive, short if negative, and size each position by the inverse of its volatility.
- **Why it pays:** Central banks smoothing rates, corporate hedgers and tourists trade for policy or business reasons, not profit, and investors under-react to macro news. They keep doing it because profit isn't their goal.
- **Fits:** G10 majors, liquid crosses, futures. **Doesn't fit:** pegged currencies (HKD, DKK, SAR), the managed CNY, or EURCHF during its 2011–15 floor.
- **Published:** Moskowitz, Ooi & Pedersen, *Time Series Momentum*, Journal of Financial Economics (2012). Its FX roots are much older (Sweeney, Journal of Finance, 1986).

**2. Moving-average crossover**
- **Rule:** Long when the fast moving average is above the slow one, short when it is below, always in the market.
- **Why it pays:** Central bank intervention slows adjustment, so trends persist. Trend profits cluster around intervention days, and central banks keep intervening because their mandate is stability, not profit.
- **Fits:** majors that trend, such as USDJPY and AUDUSD. **Doesn't fit as well:** tightly linked crosses that tend to range (EURGBP, AUDNZD, EURCHF).
- **Published:** Levich & Thomas, Journal of International Money and Finance (1993); LeBaron, Journal of International Economics (1999).
- **Caveat:** Neely, Weller & Ulrich (JFQA, 2009) show these profits have decayed over time.

### BREAKOUT

**3. Donchian channel breakout (Turtle System 2)**
- **Rule:** Buy a break of the 55-day high, sell a break of the 55-day low, and exit on the opposite 20-day extreme.
- **Why it pays:** Stop-loss orders cluster beyond recent highs and lows. When they trigger, they push price further in the breakout direction. Traders keep placing stops there because it's standard risk practice.
- **Fits:** majors and futures. **Doesn't fit:** pegged currencies.
- **Published:** Donchian, Financial Analysts Journal (1960); *The Original Turtle Trading Rules* (written 1983, published 2003); Osler, Journal of Finance (2003), for the stop-order mechanism.

**4. Opening range breakout**
- **Rule:** Trade in the direction of the first break of the day's opening range.
- **Why it pays:** Orders that build up overnight are released at the cash-market open, and traders who react to overnight news at the open pay for that imbalance.
- **Fits:** exchange-traded futures and stocks that have a defined open. **Doesn't fit:** spot FX, which trades 24 hours with no open.
- **Published:** Crabel, *Day Trading with Short Term Price Patterns and Opening Range Breakout* (1990).

### MEAN REVERSION

**5. Purchasing-power-parity (PPP) value**
- **Rule:** Each month, buy the currencies that have become cheapest in real terms over the past 5 years and short the dearest.
- **Why it pays:** Trend followers and carry traders push currencies away from fair value, and trade flows slowly pull them back. Those investors can't wait 3–5 years because of short-horizon mandates and career risk.
- **Fits:** floating G10 currencies with reliable inflation (CPI) data. **Doesn't fit:** pegs, high-inflation emerging markets, or timing a single pair.
- **Published:** Cassel, Economic Journal (1918); Rogoff, Journal of Economic Literature (1996); Asness, Moskowitz & Pedersen, Journal of Finance (2013).

**6. RSI(2) pullback**
- **Rule:** Buy when the 2-day RSI is below 10 and price is above its 200-day average; exit when price closes above its 5-day average.
- **Why it pays:** You get paid for buying from panicked or forced sellers in equity indices, which have an upward drift.
- **Fits:** US equity indices. **Doesn't fit:** FX, which has no built-in upward drift and no reliable daily reversal in the majors.
- **Published:** Connors & Alvarez, *Short Term Trading Strategies That Work* (2008).

### SEASONAL

**7. Day-of-week effect in FX**
- **Rule:** Trade the dollar on the weekdays that were historically strong or weak for it.
- **Why it pays:** It doesn't; no one is systematically on the losing side.
- **Fits:** in theory, any pair.
- **Published:** McFarland, Pettit & Sung, Journal of Finance (1982).

**8. Month-end equity-hedge rebalancing**
- **Rule:** If US stocks beat foreign stocks during the month, sell USD into month-end; if they lagged, buy USD.
- **Why it pays:** Foreign investors holding US stocks must re-hedge their currency exposure at month-end whatever the price, because their mandate requires it.
- **Fits:** USD against EUR, GBP and JPY. **Doesn't fit:** minor pairs.
- **Published:** Melvin & Prins, Journal of Financial Markets (2015).

### POSITION SIZING

**9. Volatility targeting**
- **Rule:** Size each position as target volatility divided by the pair's forecast volatility.
- **Why it pays:** Nobody loses. It works because volatility clusters (calm and turbulent periods persist) while returns don't rise with volatility, so cutting size when volatility is high improves return per unit of risk.
- **Fits:** all pairs. **Weaker when** volatility jumps suddenly, as when the CHF floor broke in 2015.
- **Published:** J.P. Morgan, *RiskMetrics Technical Document* (1996); Turtle "N" unit sizing (1983); Moreira & Muir, Journal of Finance (2017).

**10. Kelly criterion**
- **Rule:** Bet the fraction of equity that maximises long-run growth, given your edge and its variance.
- **Why it pays:** It doesn't create any edge; it only scales an edge you already have.
- **Fits:** situations where the edge is reliably known. **Doesn't fit:** noisy trading strategies, where the edge is uncertain.
- **Published:** Kelly, Bell System Technical Journal (1956).

---

## Part 2 — Grading

"Old" was counted as at least about 15 years since publication.

| # | Candidate | Old & published | Real reason it pays | Fits daily FX | Verdict |
|---|---|---|---|---|---|
| 1 | 12-month momentum | ✅ | ✅ | ✅ | **PASS** |
| 2 | Moving-average crossover | ✅ | ✅ | ✅ (profits have decayed) | **PASS** |
| 3 | Donchian 55/20 | ✅ | ✅ | ✅ | **PASS** |
| 4 | Opening range breakout | ✅ | ⚠️ | ❌ no open, and it's intraday | FAIL |
| 5 | PPP value | ✅ | ✅ | ✅ (slow strategy) | **PASS** |
| 6 | RSI(2) | ✅ | ❌ no equity-style drift in FX | ❌ | FAIL |
| 7 | Day of week | ✅ | ❌ no counterparty, likely data-mined | ✅ | FAIL |
| 8 | Month-end rebalancing | ❌ published 2015 | ✅ | ⚠️ effect is concentrated around the 4pm London fix, which daily bars can't isolate | FAIL |
| 9 | Volatility targeting | ✅ | ✅ (risk reduction, not alpha) | ✅ | **PASS (as overlay)** |
| 10 | Kelly | ✅ | ❌ creates no edge | ✅ | FAIL |

Strategies 1–3 are largely the same bet on trends. Test 1 as the main version and use 2 and 3 as robustness checks, not as diversification.

---

## Part 3 — Exact rules ready to test

### Shared setup for all strategies
- **Universe:** EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, NZDUSD, USDCAD, USDSEK, USDNOK.
- **Exclusions:** no pegged pairs; treat EURCHF 2011-09 to 2015-01 as untradeable.
- **Bars:** daily, closing at 17:00 New York.
- **Execution:** compute the signal at the day-t close and fill at the day t+1 close.
- **Returns:** total return including swap/rollover.
- **Costs:** 1–2 pips spread for majors, 3–5 for USDSEK and USDNOK.

### A. 12-month momentum (Moskowitz, Ooi & Pedersen conventions)
- **Rebalance:** last trading day of each month.
- **Signal:** sign of the pair's 252-day total return.
- **Size:** 40% ÷ σ.
  - σ is an exponentially weighted average of squared daily returns, with a 60-day centre of mass, annualised by √261.
  - For a practical portfolio of 9 pairs, use 10% ÷ σ per pair.
- **Holding:** one month.

### B. Moving-average crossover
- **Signal:** long if the 50-day average close is above the 200-day average close, short otherwise; always in the market.
- **Check:** evaluated daily.
- **Size:** use overlay E.
- **Robustness pairs (Levich & Thomas):** 1/200, 5/20, 1/5.

### C. Donchian / Turtle System 2
- **Long entry:** close above the highest high of the prior 55 days.
- **Short entry:** close below the lowest low of the prior 55 days.
- **Exits:** exit longs on a close below the prior 20-day low, and shorts on a close above the prior 20-day high.
- **Stop:** 2N from entry, where N is the 20-day Wilder Average True Range.
- **Size (Turtle native):** one unit = (1% of equity) ÷ (N × value of one price point). No pyramiding in the base test.

### D. PPP value (Asness, Moskowitz & Pedersen conventions)
- **Rebalance:** monthly.
- **Signal for each currency i against USD:**
  - V_i = ln(average spot from 54–66 months ago ÷ spot today) − (Δln CPI_i − Δln CPI_US) over the same period.
  - Spot is quoted as USD per unit of foreign currency.
- **CPI timing:** lag CPI by 2 months to avoid look-ahead bias. AUD and NZD CPI are quarterly, so carry the last value forward.
- **Weights:** rank the 9 currencies by V; weight each in proportion to (its rank − the average rank), scaled so longs total +1 and shorts total −1. This keeps the portfolio USD-neutral.

### E. Volatility-targeting overlay (apply to A, B and D)
- **Forecast volatility:** σ is an exponentially weighted average with λ = 0.94 (the RiskMetrics setting), annualised by √261.
- **Notional per pair:** equity × (10% ÷ √9) ÷ σ.
- **Limits:**
  - Cap leverage at 3× per pair.
  - Rebalance only when a position drifts more than 20% from target, to limit costs.

---

**Not included:** carry (long high-interest-rate currencies against low-rate ones) is the best-documented premium in FX, but it isn't in the five requested families (trend, mean reversion, breakout, seasonal, position sizing). It is a candidate for a follow-up write-up.

---

## Part 4 — More recent strategies that build on these

These are mostly less than 15 years old, so by definition they fail the "old" check. Use them as **variants and controls for the strategies that passed**, not as replacements. Several are critiques that change how the originals should be tested, and those are the most useful.

### Comparison table

| Recent work | Builds on | What it changes | Evidence relative to the original | Simple, no mashup? | Fits daily FX? | Use in the test plan |
|---|---|---|---|---|---|---|
| Hurst, Ooi & Pedersen, *A Century of Evidence on Trend-Following Investing*, Journal of Portfolio Management (2017) | #1 | Equal-weight blend of 1-, 3- and 12-month momentum signals | Positive in every decade since 1880, across 67 markets; the blend is smoother than 12-month alone | ✅ (same rule, three lookbacks) | ✅ | **Add** as variant A2 |
| Levine & Pedersen, *Which Trend Is Your Friend?*, Financial Analysts Journal (2016) | #1, #2, #3 | Shows momentum, moving-average crossovers and breakouts are all filters on past returns, and nearly equivalent | Confirms they are one bet | n/a (a unifying result) | ✅ | **Treat A, B and C as one factor**; don't count them as diversification |
| Kim, Tse & Wald, *Time Series Momentum and Volatility Scaling*, Journal of Financial Markets (2016) | #1 + #9 | Removes volatility scaling from momentum | Much of the momentum edge comes from the volatility scaling; unscaled, it looks close to buy-and-hold | ✅ | ✅ | **Mandatory control:** run A with and without overlay E |
| Huang, Li, Wang & Zhou, *Time-Series Momentum: Is It There?*, Journal of Financial Economics (2020) | #1 | Tests whether each asset's own past return predicts its future return | Weak per-asset predictability; the reported effect is largely a pooled or cross-sectional artefact | n/a (a critique) | ✅ | **Check per pair**, not just at portfolio level |
| Menkhoff, Sarno, Schmeling & Schrimpf, *Currency Momentum Strategies*, Journal of Financial Economics (2012) | #1 | Cross-sectional ranking: buy past winners and short past losers among currencies | Large spreads, but concentrated in minor, high-risk, high-cost currencies; weak in G10 | ✅ | ⚠️ weak on G10 after costs | Optional; expect little in G10 |
| Garg, Goulding, Harvey & Mazzoleni, *Breaking Bad Trends*, Financial Analysts Journal (2021) | #1, #2 | Adjusts the blend of fast and slow trend signals at turning points, when the two disagree | Better behaviour after trend reversals in their sample | ⚠️ the switching logic edges toward a mashup | ✅ | Skip in the first round |
| Clenow, *Following the Trend*, Wiley (2013) | #2, #3 + #9 | Moving-average trend filter plus Donchian-style entries, with ATR-based risk sizing, run across diversified futures | Practitioner backtests, not peer-reviewed | ⚠️ combines several filters | ✅ | Skip; C already covers it |
| Menkhoff, Sarno, Schmeling & Schrimpf, *Currency Value*, Review of Financial Studies (2017) | #5 | Adjusts the real exchange rate for fundamentals such as productivity, export quality and net foreign assets | Adjusted value predicts better than raw PPP | ⚠️ needs extra macro data | ✅ | Optional variant D2 if the data is available |
| Asness, Moskowitz & Pedersen, *Value and Momentum Everywhere*, Journal of Finance (2013) | #1 + #5 | 50/50 portfolio of currency value and momentum | Value and momentum are negatively correlated, so the combination has a better Sharpe ratio than either alone | ✅ (two passing rules, equal weight) | ✅ | **Add** as portfolio F = ½A + ½D |
| Barroso & Santa-Clara, *Beyond the Carry Trade: Optimal Currency Portfolios*, Journal of Financial and Quantitative Analysis (2015) | #1, #5, carry | Uses an optimiser to weight many currency signals together | Strong in-sample; high risk of overfitting | ❌ optimised mashup | ✅ | Exclude |
| Harvey et al., *The Impact of Volatility Targeting*, Journal of Portfolio Management (2018) | #9 | Tests volatility targeting across asset classes | Raises Sharpe for equities and credit; **negligible Sharpe gain for FX and bonds**, but cuts tail events everywhere | ✅ | ✅ | Expect E to reduce drawdowns, **not** to raise Sharpe |
| Moreira & Muir, *Volatility-Managed Portfolios*, Journal of Finance (2017) | #9 | Scales exposure by the inverse of recent variance | Gains (alpha) mainly in equity factors | ✅ | ⚠️ weak for FX | Context only |
| Cederburg, O'Doherty, Wang & Yan, *On the Performance of Volatility-Managed Portfolios*, Journal of Financial Economics (2020) | #9 | Tests the Moreira–Muir approach out of sample | No reliable improvement out of sample | n/a (a critique) | ✅ | Keep E simple; don't tune λ |
| Carver, *Systematic Trading*, Harriman House (2015) | #2 + #9 + #10 | Blended fast-to-slow moving-average crossovers, volatility targeting, and capped fractional-Kelly risk | Practitioner work; robust design rules | ⚠️ the blending adds layers | ✅ | Borrow the fractional-Kelly cap only (see below) |
| MacLean, Thorp & Ziemba (eds.), *The Kelly Capital Growth Investment Criterion*, World Scientific (2011) | #10 | Fractional Kelly (betting ¼ to ½ of full Kelly) | Fractional Kelly gives up some growth for much smaller drawdowns | ✅ | ✅ | Optional cap: ≤ ½ Kelly based on the out-of-sample Sharpe ratio |
| Krohn, Mueller & Whelan, *Foreign Exchange Fixings and Returns Around the Clock*, Journal of Finance (2024) | #8 | USD tends to rise before the main daily currency fixes and fall after them | Strong, but the effect is intraday | ✅ | ❌ intraday | Exclude |

### What changes in the test plan

1. **Add A2 (Hurst, Ooi & Pedersen):** same as A, but the signal is the equal-weighted average of sign(21-day return), sign(63-day return) and sign(252-day return), sized with the same 10% ÷ σ.
2. **Add the control A0 (Kim, Tse & Wald):** A with fixed equal notional per pair, no volatility scaling. If A beats A0 only through scaling, the edge is risk management, not trend.
3. **Add F (Asness, Moskowitz & Pedersen):** ½·A + ½·D, each scaled to the same volatility before combining.
4. **Per-pair check (Huang, Li, Wang & Zhou):** report t-statistics for each pair, not only for the pooled portfolio.
5. **Set expectations for E (Harvey et al.):** in FX, judge E on maximum drawdown and worst month, not on Sharpe.
6. **Treat A, B and C as one bet (Levine & Pedersen):** pick one trend rule for allocation; use the other two only as robustness checks.
7. **Excluded:** Barroso & Santa-Clara (optimised mashup), Krohn, Mueller & Whelan (intraday), and Breaking Bad Trends (first round only, too complex).

---

## Part 5 — TTFM and TheStrat compared

Both are recent practitioner methods, popularised on YouTube, X/Twitter and commercial indicators. They have no peer-reviewed track record. Each one repackages older, published ideas, so the useful question is: **does the new packaging add anything beyond the old component it is built on?**

### What they are

**TheStrat** (Rob Smith, 2010s)
- **Candle labels:** every candle is a **1** (inside bar: within the prior bar's range), a **2** (directional: breaks one side of the prior bar, labelled 2u or 2d) or a **3** (outside bar: breaks both sides).
- **Setups:** these labels combine into named setups, such as 2‑1‑2 continuation, 2‑2 reversal and 3‑1‑2.
- **Full Timeframe Continuity (FTFC):** only trade when price is above (or below) the open of the current day, week, month and quarter candles.
- **Targets:** taken from prior bar extremes and "broadening formations".

**TTFM — TTrades Fractal Model** (TTrades, about 2023–24, derived from ICT)
- **Origin:** builds on ICT (Inner Circle Trader, Michael Huddleston) concepts such as "Power of Three", liquidity sweeps, premium/discount and SMT divergence.
- **Core idea:** pair a higher‑timeframe candle with a lower one, for example 15m–4H or Daily–Weekly.
  1. **Sweep:** a higher‑timeframe candle C2 trades beyond C1's high or low, then closes back inside C1's range.
  2. **Confirmation (CISD, "change in state of delivery"):** on the lower timeframe, price closes beyond the open of the run of candles that made the extreme.
  3. **Entry and target:** enter in the reversal direction and target the opposite side of the higher‑timeframe range.
- **Failure condition:** price returns to the sweep extreme.
- **Extras:** T‑Spot, SMT divergence, time windows, and projection levels at −1, −2, −2.5, −4 and −4.5.
- **Premise:** the stated premise is "algorithmic price delivery" (ICT's "Interbank Price Delivery Algorithm"), for which there is no published evidence.

### The old idea underneath each

| Component | Older published equivalent | Relation to this research |
|---|---|---|
| TheStrat FTFC (price above the period open on several timeframes) | Multi‑horizon time‑series momentum (Moskowitz, Ooi & Pedersen 2012; Hurst, Ooi & Pedersen 2017), but with calendar‑anchored, variable lookbacks | A variant of **A / A2** |
| TheStrat 1 → 2 (inside‑bar breakout) | Crabel (1990): inside‑day and narrow‑range breakouts | A short‑term version of **#3/#4** |
| TheStrat 3 (outside bar) and 2‑2 reversal | Outside / key reversal days (classic chart‑pattern literature, e.g. Schwager, *Technical Analysis*, 1996) | No proven edge in FX |
| TTFM sweep‑and‑reclaim (C2) | **Turtle Soup**, a failed 20‑day breakout fade (Connors & Raschke, *Street Smarts*, 1995) | The **opposite** of **C** (Donchian) |
| TTFM "liquidity" at prior highs and lows | Stop‑loss and take‑profit clustering (Osler, *Journal of Finance* 2003; Osler, *Journal of International Money and Finance* 2005) | Osler finds stop clusters cause **continuation** and take‑profit clusters cause reversals at round numbers. That only partly supports TTFM. |
| TTFM 50% "equilibrium", T‑Spot, projections | None | Untestable or ad hoc |

### Grading against the three checks

| | Old & published | Real reason it pays | Fits daily FX | Simple, no mashup | Verdict |
|---|---|---|---|---|---|
| **TheStrat** | ❌ 2010s, practitioner only (components are old) | ⚠️ only through its momentum component; no counterparty story for the candle numbers | ⚠️ daily FX candles depend on the broker's close time and Sunday bars, so the 1/2/3 labels change between data feeds. Weekly and monthly opens are fine. | ❌ candle pattern + multi‑timeframe filter + targets | **FAIL** |
| **TTFM** | ❌ 2020s, commercial, derived from ICT | ⚠️ partial: run stops can reverse, but published FX evidence (Osler) leans toward continuation | ⚠️ Weekly–Daily pairing fits; the intraday pairings (5m–1H, 15m–4H) and time windows do not | ❌ sweep + CISD + T‑Spot + SMT + time filters | **FAIL** |
| *Turtle Soup (TTFM's old core)* | ✅ 1995 | ⚠️ the losers are late breakout traders, but that contradicts the continuation evidence behind C | ✅ | ✅ | **Borderline**: test as a control only |

### Comparison with the strategies that passed

| | A: 12‑month momentum | C: Donchian 55/20 | TheStrat | TTFM |
|---|---|---|---|---|
| Direction | Trend | Trend / breakout | Trend (continuation) + some reversals | Reversal (fades breakouts) |
| Holding period | About 1 month or more | Weeks to months | 1–5 bars | Days to weeks (Weekly–Daily) |
| Free parameters | 1–2 | 3 | Many (setup choice, which timeframes, targets) | Many (pairing, CISD variant, filters, projections) |
| Evidence | Decades, many markets, peer‑reviewed | Decades, practitioner + academic | Marketing and anecdote | Marketing and anecdote |
| Mechanical? | Fully | Fully | Mostly (the 1/2/3 labels are objective) | Partly (T‑Spot and SMT are discretionary) |
| Main risk | Decay, crowding | Whipsaw | Overfitting; data‑feed sensitivity | Overfitting; contradicts the continuation evidence |

### If you still want to test them: minimal mechanical versions as falsification tests

Run these on the same universe, data, costs and execution as Part 3. Each has exactly one benchmark. A method earns a place only if it beats its benchmark after costs, out of sample.

**S1 — TheStrat 2‑1‑2 continuation with FTFC (daily bars)**
- **Setup:** bar t‑2 is a 2u (or 2d) and bar t‑1 is a 1 (inside bar).
- **FTFC filter:** for longs, the close at t‑1 is above the current week's open, month's open and quarter's open; mirror this for shorts.
- **Entry:** buy stop at H(t‑1) + 1 pip, or sell stop at L(t‑1) − 1 pip, valid for day t only.
- **Stop:** the opposite side of the inside bar.
- **Exit:** 1R target, the stop, or 5 days, whichever comes first.
- **Benchmarks:**
  1. The same entries **without** FTFC. This tests whether the candle pattern adds anything.
  2. FTFC alone as a daily position: long when all three are bullish, short when all three are bearish, flat otherwise. This tests whether the edge is just momentum (A).

**T1 — TTFM core on Weekly–Daily**
- **Bullish setup:** weekly bar C2 has a low below C1's low and closes above C1's low. The bearish setup is the mirror image.
- **Confirmation (CISD):** during the following week, a daily close above the open of the first candle in the most recent run of consecutive down‑close daily candles.
- **Entry:** at that daily close.
- **Stop:** C2's low.
- **Target:** C1's high.
- **Time exit:** the end of the second week after C2.
- **Benchmarks:**
  1. The same rule **without** the CISD step (enter at C2's close). This tests whether CISD adds anything.
  2. **Turtle Soup** on daily bars:
     - **Trigger:** today makes a new 20‑day low, and the previous 20‑day low was at least 4 days earlier.
     - **Entry:** buy stop just above the earlier 20‑day low.
     - **Stop:** below today's low.
     - **Exit:** 5 days, or 1R.
     - Mirror all of this for shorts.
  3. Check that the T1 results are not simply the negative of C's results over the same dates.

**Expectation, given the published evidence:** S1's benchmark 2 (FTFC alone, i.e. momentum) will probably explain most of S1's result. T1 and Turtle Soup will probably fail after costs on G10 daily data, because published FX evidence favours continuation through prior extremes, not reversal.
