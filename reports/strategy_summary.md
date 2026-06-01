# Strategy Summary

## 0050 vs TW50 Intraday Deviation Reversion Research

This project studies an intraday deviation reversion signal between Taiwan 0050 ETF and a TW50 simulated NAV reference.

The project is a **research portfolio**, not a production-ready trading system. The main goal is to demonstrate a disciplined quantitative research workflow from market hypothesis to event-level validation, cost stress testing, high-risk sample review, and AI-assisted signal quality validation.

---

## 1. Research Question

The core research question is:

> When 0050 ETF trades at a negative deviation relative to TW50 simulated NAV, under what conditions does the deviation behave like a short-term reversion opportunity rather than a weak or false signal?

The strategy does not assume that every negative deviation is tradable.

Instead, it studies whether signal quality improves when the deviation is supported by:

* TW50 short-term direction
* deviation slope
* trading session
* realized volatility
* volume ratio
* repeated signal count
* cost-adjusted performance

---

## 2. Market Hypothesis

A negative deviation can represent two different market states.

### Tracking Lag

```text
TW50 moves upward
→ 0050 ETF price temporarily lags
→ negative deviation appears
→ potential short-term reversion
```

### Risk Repricing

```text
TW50 does not confirm strength
→ negative deviation may reflect market weakness
→ reversion probability decreases
```

Therefore, deviation alone is not sufficient. The signal requires market-state confirmation.

---

## 3. Research Workflow

```text
v1.1 baseline
→ event dataset construction
→ v1.1 vs v2-A comparison
→ v2-A failure analysis
→ v2-B2 / v2-B3 refinement
→ cost and slippage stress test
→ high-risk sample review
→ AI-assisted signal quality validation
```

The workflow focuses on hypothesis-driven refinement rather than brute-force parameter optimization.

---

## 4. Version Evolution

| Version           | Purpose                | Key Change                                              | Result                                          |
| ----------------- | ---------------------- | ------------------------------------------------------- | ----------------------------------------------- |
| v1.1 No Overnight | Baseline signal pool   | Original intraday deviation reversion                   | 361 trades, PF about 1.98                       |
| v2-A              | Direction confirmation | Add `TW50_return_5m > 0`                                | 258 trades, PF about 2.66                       |
| v2-B2             | Late-entry reduction   | Exclude `deviation_slope_1bar > 0`                      | Avoids entering after reversion already started |
| v2-B3             | Final signal candidate | Exclude positive slope and main 09:45–10:00 weak window | 223 trades, PF about 3.60                       |

---

## 5. Current Main Result: v2-B3

v2-B3 is the strongest current signal layer in this research cycle.

| Metric        |       v2-B3 |
| ------------- | ----------: |
| Trades        |         223 |
| Net PnL       |  about 7.80 |
| Avg PnL       | about 0.035 |
| Profit Factor |  about 3.60 |
| Gross Loss    | about -3.00 |
| Max Loss      | about -0.25 |

Important positioning:

> v2-B3 is a final signal candidate, not a final tradable strategy.

---

## 6. Key Findings

### 6.1 TW50 Direction Improves Signal Quality

Adding `TW50_return_5m > 0` reduced the trade count but improved the quality of the remaining signal pool.

The market interpretation is:

```text
TW50 upward confirmation
→ deviation is more likely tracking lag
→ reversion quality improves
```

---

### 6.2 Deviation Slope Helps Avoid Late Entry

Positive deviation slope can indicate that the deviation has already started reverting before entry.

This may reduce the remaining expected edge.

The slope filter helps avoid entering after the cleanest part of the move has already occurred.

---

### 6.3 Session Timing Matters

The 09:45–10:00 window was identified as a weaker post-opening interval.

Lunch-tail trades between 12:45 and 13:00 also become more fragile after cost because there is less time remaining before market close.

---

### 6.4 High RV Should Not Be Blindly Excluded

High realized volatility is not automatically bad.

Under the v2-B3 condition set, high RV samples contributed positively.

This suggests that high RV may sometimes represent:

```text
larger intraday dislocation
larger reversion opportunity
stronger temporary deviation
```

rather than pure noise.

---

### 6.5 Execution Is the Main Bottleneck

The signal layer looks meaningful, but the strategy is thin-edge and execution-sensitive.

Cost stress testing showed:

* Cost 0.01 remains relatively acceptable
* Cost 0.02 weakens the edge significantly
* 0.5 tick each side slippage can make the strategy fail

Therefore, execution quality is critical.

---

## 7. AI-Assisted Validation

The v1.1 event dataset was converted into a supervised learning sample.

Target label:

```text
good_signal_cost002 = 1 if pnl_twd - 0.02 > 0
```

This labels a signal as good only if it remains positive after a 0.02 round-trip cost assumption.

Models tested:

* Logistic Regression
* Random Forest
* XGBoost

The AI module excludes post-trade leakage fields such as:

```text
exit_reason
exit_price
exit_relative_deviation
MFE
MAE
holding time
pnl-derived labels
```

Main AI interpretation:

* XGBoost overfits
* Random Forest has weak validation AUC but useful feature importance
* Important features overlap with the rule-based logic
* AI is useful for feature validation, not direct trading

Correct positioning:

```text
AI-assisted signal quality validation
```

not:

```text
AI trading model
```

---

## 8. Main Limitations

This project does not claim live tradability.

Known limitations:

1. No tick-level order book data
2. No real bid-ask spread data
3. No live fill-rate study
4. No limit order queue simulation
5. High sensitivity to cost and slippage
6. Limited ML sample size
7. AI validation is not strong enough for direct trade prediction
8. v2-B3 is not production-ready

---

## 9. Recommended Future Work

The next research stage should focus on execution and risk control rather than adding more entry filters.

Recommended directions:

### 1. Lunch-Tail Execution-Aware Filter

Study whether 12:45–13:00 signals should require stronger TW50 momentum, deeper deviation, or better execution conditions.

### 2. Repeated Signal Expected-Edge Threshold

Study whether the third signal onward in the same day should require stronger expected edge.

### 3. EXIT_TIME Exit-Efficiency Research

Study whether earlier time stop, partial reversion exit, or dynamic exit threshold can improve after-cost performance.

### 4. Execution Feasibility Review

Study spread, fill probability, volume condition, and realistic limit order execution.

---

## 10. Portfolio Value

This project demonstrates the following research capabilities:

```text
market microstructure reasoning
ETF deviation logic
event dataset construction
conditional signal validation
failure analysis
cost and slippage awareness
high-risk sample taxonomy
AI-assisted feature validation
conservative strategy communication
```

The strongest value of the project is not only the backtest result.

The main value is the complete research process:

```text
market hypothesis
→ structured data
→ conditional testing
→ failure analysis
→ signal refinement
→ execution stress
→ AI-assisted validation
→ conservative conclusion
```

---

## 11. Final Summary

This project presents a refined intraday ETF deviation signal candidate supported by event-level analysis and AI-assisted feature validation.

It should be understood as:

```text
A disciplined quantitative research workflow.
```

not as:

```text
A finished live trading system.
```

The next major step is to test whether the signal candidate can survive realistic execution constraints.
