# Methodology

This document explains the research methodology behind the 0050 vs TW50 intraday deviation reversion project.

The project is designed as a quantitative research workflow, not as a production trading system. The goal is to demonstrate how a market hypothesis can be converted into event-level data, tested through conditional filters, stress-tested for execution risk, and finally reviewed with AI-assisted validation.

---

## 1. Research Objective

The core research question is:

> When 0050 ETF trades at a negative deviation relative to a TW50 simulated NAV reference, under what conditions does that deviation behave like a short-term reversion opportunity rather than a weak or false signal?

The strategy does not assume that every negative deviation is tradable. Instead, it studies which entry-time conditions improve signal quality.

Key dimensions include:

* TW50 short-term return
* entry relative deviation
* deviation slope
* trading session
* volume ratio
* realized volatility
* repeated signal count
* exit behavior
* cost and slippage sensitivity

---

## 2. Market Logic

A negative deviation can have different meanings depending on market context.

### 2.1 Tracking Lag

A potentially valid setup occurs when TW50 moves upward first, while 0050 ETF price temporarily lags behind.

```text
TW50 short-term upward move
→ underlying basket reacts first
→ 0050 ETF price lags
→ negative deviation appears
→ deviation may revert
```

In this case, the deviation may represent a temporary tracking lag.

### 2.2 Risk Repricing

A lower-quality setup occurs when TW50 does not confirm strength or the broader market weakens.

```text
TW50 weak or non-confirming
→ 0050 negative deviation may reflect risk repricing
→ apparent discount is less reliable
→ reversion probability weakens
```

This is why the research does not use deviation alone. It requires additional market-state filters.

---

## 3. Baseline: v1.1 No Overnight

The first research version is v1.1 No Overnight.

Purpose:

* Build a baseline intraday deviation reversion strategy
* Avoid overnight risk
* Generate a candidate event dataset
* Create a baseline for later comparison

Key result:

| Metric        |       v1.1 |
| ------------- | ---------: |
| Trades        |        361 |
| Profit Factor | about 1.98 |

The v1.1 version is not treated as the final strategy. Its main role is to provide the original candidate signal pool for further analysis.

---

## 4. Event Dataset Construction

Instead of only reading the TradingView backtest summary, each trade was converted into an event-level dataset.

Each event includes entry-time and exit-time information such as:

* entry time
* exit time
* entry relative deviation
* exit relative deviation
* TW50 return over 5 minutes and 15 minutes
* ETF return over 5 minutes and 15 minutes
* deviation slope over 1 bar and 3 bars
* volume ratio at entry
* realized volatility
* session block
* signal count within the same day
* holding time
* exit reason
* PnL

The event dataset allows the strategy to be analyzed beyond total backtest performance.

It supports questions such as:

* Which session has better signal quality?
* Does TW50 direction improve the signal?
* Are repeated signals weaker?
* Are losses concentrated in specific time windows?
* Is high realized volatility a risk or an opportunity?
* Does the strategy survive after cost assumptions?

This is the main transition from simple backtesting to structured research.

---

## 5. v2-A: TW50 5-Minute Upward Filter

The first major improvement was v2-A.

Rule added:

```text
TW50_return_5m > 0
```

Purpose:

* Use TW50 short-term direction as confirmation
* Separate tracking lag from weak deviation
* Remove lower-quality signals when the underlying reference does not confirm upward strength

Result:

| Version | Trades | Profit Factor |
| ------- | -----: | ------------: |
| v1.1    |    361 |    about 1.98 |
| v2-A    |    258 |    about 2.66 |

Interpretation:

The improvement is not simply caused by reducing trade count. The TW50 filter adds market logic by requiring the reference index to support the reversion hypothesis.

In strategy-language terms:

```text
Deviation alone = candidate signal
Deviation + TW50 upward confirmation = higher-quality candidate
```

---

## 6. v2-A Failure Analysis

After v2-A, the next step was not to keep adding random filters. Instead, failure samples were reviewed to identify recurring weaknesses.

Several patterns were observed:

1. Some trades entered too late after the deviation had already started reverting.
2. The 09:45–10:00 window appeared weaker than expected.
3. Repeated signals in the same day showed signs of signal decay.
4. Some EXIT_TIME samples were positive but thin after cost.
5. Some periods were more fragile under transaction cost assumptions.

This failure analysis led to the next refinement stage.

---

## 7. v2-B2: Deviation Slope Filter

v2-B2 excluded cases where the one-bar deviation slope was positive:

```text
deviation_slope_1bar > 0
```

Market interpretation:

If the deviation has already started moving upward before entry, the strategy may be entering after part of the reversion has already occurred.

The goal is to avoid late-entry signals where the expected remaining edge is weaker.

---

## 8. v2-B3: Final Signal Candidate

v2-B3 combines the slope filter with exclusion of the main 09:45–10:00 weak window.

Main refinements:

```text
Exclude deviation_slope_1bar > 0
Exclude main 09:45–10:00 weak window
```

Result summary:

| Metric        |       v2-B3 |
| ------------- | ----------: |
| Trades        |         223 |
| Net PnL       |  about 7.80 |
| Avg PnL       | about 0.035 |
| Profit Factor |  about 3.60 |
| Gross Loss    | about -3.00 |
| Max Loss      | about -0.25 |

v2-B3 is treated as the current final signal candidate.

Important:

> v2-B3 is not a final tradable strategy. It is a refined signal candidate that still requires execution feasibility research.

---

## 9. Cost and Slippage Stress Testing

Because this is an intraday thin-edge strategy, execution cost is critical.

The strategy was stress-tested under different transaction cost and slippage assumptions.

Main conclusions:

* No-cost performance is strong.
* Small cost assumptions still leave some edge.
* A 0.02 round-trip cost weakens the edge significantly.
* 0.5 tick each side slippage can make the strategy fail.

This suggests that the main bottleneck is not only signal discovery but execution feasibility.

Key execution questions:

* Can the strategy enter with limit orders?
* What is the fill probability?
* How often does the spread consume the edge?
* Can exits be improved?
* Are specific time windows more execution-sensitive?

---

## 10. High-Risk Sample Review

After cost stress testing, high-risk samples were reviewed to identify remaining weaknesses.

Key findings:

### 10.1 Lunch Tail

Signals between 12:45 and 13:00 can become fragile after cost because there is limited time left for reversion.

Future work should study whether these signals require stronger TW50 momentum or deeper deviation.

### 10.2 Repeated Signals

Repeated signals in the same day appear to show signal decay, especially from the third signal onward.

Possible future direction:

```text
Require higher expected edge for later same-day signals
```

### 10.3 EXIT_TIME Samples

EXIT_TIME samples are not necessarily toxic, but they indicate that the exit rule may be inefficient.

Future work should test:

* earlier time stop
* partial reversion exit
* dynamic exit thresholds

### 10.4 High Realized Volatility

High realized volatility should not be blindly excluded.

Under the v2-B3 condition set, high RV samples contributed positively. This suggests that volatility may sometimes represent larger reversion opportunity rather than pure noise.

---

## 11. AI-Assisted Signal Quality Validation

After the rule-based research process, the v1.1 event dataset was converted into a supervised learning sample.

Target label:

```text
good_signal_cost002 = 1 if pnl_twd - 0.02 > 0
```

This means a trade is considered a good signal only if it remains profitable after a 0.02 round-trip cost assumption.

Models tested:

* Logistic Regression
* Random Forest
* XGBoost

Data split:

| Split        | Period    |
| ------------ | --------- |
| Train        | 2022–2024 |
| Validation   | 2025      |
| Recent Check | 2026      |

Leakage control:

The model excludes post-trade information such as:

* exit reason
* exit price
* exit relative deviation
* MFE
* MAE
* holding time
* PnL-derived labels

The purpose is to ensure the model only uses entry-time information.

---

## 12. AI Validation Interpretation

The AI validation module is not used as a trading model.

Main observations:

* XGBoost overfits.
* Random Forest has weak validation AUC.
* Feature importance still provides useful research information.
* Important features overlap with the rule-based strategy logic.

Relevant features include:

* deviation slope
* TW50 return
* realized volatility
* entry timing
* volume ratio
* entry relative deviation
* repeated signal count

The correct interpretation is:

```text
AI as signal quality validation
not AI as autonomous trading model
```

The AI layer supports feature validation and future research direction, but it does not prove that the model can directly predict profitable trades in live trading.

---

## 13. Research Philosophy

This project follows a conservative research philosophy:

1. Start from market logic, not blind parameter search.
2. Build an event dataset, not only a backtest summary.
3. Use filters only when supported by market reasoning.
4. Analyze failures before adding new rules.
5. Stress-test cost and slippage.
6. Avoid overclaiming live tradability.
7. Use AI to validate features, not to replace market understanding.

The goal is to demonstrate a repeatable research workflow that can be extended to other ETF deviation or intraday microstructure strategies.

---

## 14. Summary

The methodology can be summarized as:

```text
market hypothesis
→ event dataset
→ baseline validation
→ conditional filtering
→ failure analysis
→ refined signal candidate
→ cost and execution stress
→ high-risk taxonomy
→ AI-assisted validation
```

This workflow is designed to show disciplined strategy research capability rather than present a finished production system.
