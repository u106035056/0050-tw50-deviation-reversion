# Results Summary

This document summarizes the main research results of the 0050 vs TW50 intraday deviation reversion project.

The purpose is to show how the strategy evolved from a baseline deviation signal into a more refined signal candidate through event-level validation, failure analysis, cost stress testing, and AI-assisted feature validation.

---

## 1. Version Overview

| Version           | Main Purpose                          |     Trade Count | Main Result                       |
| ----------------- | ------------------------------------- | --------------: | --------------------------------- |
| v1.1 No Overnight | Baseline candidate signal pool        |             361 | PF about 1.98                     |
| v2-A              | Add TW50 5-minute upward confirmation |             258 | PF improves to about 2.66         |
| v2-B2             | Exclude positive deviation slope      | Reduced further | Avoids late-entry signals         |
| v2-B3             | Final signal candidate                |             223 | PF about 3.60, Net PnL about 7.80 |

The main research path is:

```text
v1.1 baseline
→ v2-A direction confirmation
→ v2-B2 late-entry filter
→ v2-B3 refined signal candidate
→ cost/slippage stress test
→ high-risk sample review
→ AI-assisted signal quality validation
```

---

## 2. v1.1 Baseline

### Purpose

v1.1 was designed as the original intraday deviation reversion baseline.

The baseline rule aimed to capture cases where 0050 ETF traded at a negative deviation relative to a TW50 simulated NAV reference.

### Key Results

| Metric        |        v1.1 |
| ------------- | ----------: |
| Trades        |         361 |
| Profit Factor |  about 1.98 |
| Gross Profit  | about 14.85 |
| Gross Loss    | about -7.50 |
| Net PnL       |  about 7.35 |
| Avg PnL       | about 0.020 |
| Max Loss      | about -0.55 |

### Interpretation

v1.1 showed that the deviation signal had a positive baseline edge, but the signal pool was still mixed.

The baseline included both:

```text
higher-quality tracking lag signals
lower-quality or false deviation signals
```

Therefore, v1.1 was treated as the original candidate pool rather than the final strategy.

---

## 3. v2-A: TW50 5-Minute Upward Filter

### Main Change

v2-A added a short-term TW50 direction filter:

```text
TW50_return_5m > 0
```

### Purpose

The goal was to test whether TW50 short-term upward confirmation improves signal quality.

Market logic:

```text
TW50 moves upward
→ 0050 temporarily lags
→ negative deviation is more likely to reflect tracking lag
→ reversion signal quality improves
```

### Key Results

| Metric        |        v1.1 |        v2-A |
| ------------- | ----------: | ----------: |
| Trades        |         361 |         258 |
| Profit Factor |  about 1.98 |  about 2.66 |
| Gross Loss    | about -7.50 | about -4.60 |
| Max Loss      | about -0.55 | about -0.35 |
| Avg PnL       | about 0.020 | about 0.030 |

### Interpretation

The v2-A result supports the idea that TW50 direction is not just a technical filter. It helps distinguish between:

```text
tracking lag
vs.
risk repricing / weak deviation
```

The trade count decreased, but the quality of the remaining signal pool improved.

---

## 4. v2-B2: Deviation Slope Filter

### Main Change

v2-B2 excluded cases where the deviation slope was already positive:

```text
deviation_slope_1bar > 0
```

### Purpose

The goal was to reduce late-entry signals.

If the deviation has already started reverting before entry, the remaining expected edge may be smaller. Entering after the signal has already begun to repair can make the trade more vulnerable to cost and slippage.

### Interpretation

The slope filter is not simply a statistical adjustment. It reflects a market timing idea:

```text
Avoid entering after the deviation repair has already started.
```

This helps reduce low-quality entries where the strategy is chasing the remaining tail of the move.

---

## 5. v2-B3: Final Signal Candidate

### Main Change

v2-B3 combines:

```text
1. Exclude deviation_slope_1bar > 0
2. Exclude the main 09:45–10:00 weak window
```

### Key Results

| Metric                 |       v2-B3 |
| ---------------------- | ----------: |
| Trades                 |         223 |
| Net PnL                |  about 7.80 |
| Avg PnL                | about 0.035 |
| Profit Factor          |  about 3.60 |
| Gross Loss             | about -3.00 |
| Max Loss               | about -0.25 |
| Estimated Max Drawdown |  about 0.25 |

### Interpretation

v2-B3 is the strongest current signal layer in this research cycle.

However, it is intentionally described as:

```text
final signal candidate
```

not as:

```text
final tradable strategy
```

The result shows that the signal can be refined through market-logic filters, but execution feasibility is still unresolved.

---

## 6. Cost and Slippage Stress Test

### Purpose

Because this is an intraday thin-edge strategy, transaction cost and slippage are critical.

The cost stress test asks:

```text
Does the signal survive after realistic trading friction?
```

### Main Findings

| Stress Condition   | Interpretation                     |
| ------------------ | ---------------------------------- |
| No cost            | v2-B3 looks strong                 |
| Cost 0.01          | Still relatively acceptable        |
| Cost 0.02          | Edge weakens significantly         |
| 0.5 tick each side | Strategy can fail                  |
| Combined stress    | Edge becomes fragile or disappears |

### Interpretation

The signal layer appears meaningful, but live tradability depends heavily on execution quality.

Main execution questions:

```text
Can entries be filled with limit orders?
How often does the spread consume the edge?
Can exits be improved?
Which time windows are most execution-sensitive?
```

This is why the next research stage should focus on execution feasibility instead of endlessly adding entry filters.

---

## 7. High-Risk Sample Review

The high-risk sample review identified several remaining weaknesses in v2-B3.

| Risk Area              | Finding                                           | Interpretation                                       |
| ---------------------- | ------------------------------------------------- | ---------------------------------------------------- |
| Lunch tail 12:45–13:00 | Weakens after cost                                | Remaining reversion time is short                    |
| Repeated signals       | Signal decay appears from the third signal onward | Later same-day signals may need higher expected edge |
| EXIT_TIME samples      | Not toxic, but thinner                            | Exit rule may be inefficient                         |
| High RV samples        | Positive contribution under v2-B3                 | High volatility should not be blindly excluded       |
| Early training samples | More fragile after cost                           | Regime sensitivity remains                           |

### Key Interpretation

The most important finding is that high realized volatility is not automatically bad.

Under the v2-B3 condition set, high RV can represent:

```text
larger deviation movement
larger reversion opportunity
more exploitable intraday dislocation
```

Therefore, high RV should be studied carefully rather than removed as a simple risk filter.

---

## 8. AI-Assisted Signal Quality Validation

### Purpose

The AI validation module was designed to test whether entry-time features can explain signal quality.

It is not intended to be a direct trading model.

### Label Design

The binary target label was:

```text
good_signal_cost002 = 1 if pnl_twd - 0.02 > 0
```

This means a trade is considered a good signal only if it remains profitable after a 0.02 round-trip cost assumption.

### Models Tested

```text
Logistic Regression
Random Forest
XGBoost
```

### Time-Based Split

| Split        | Period    |
| ------------ | --------- |
| Train        | 2022–2024 |
| Validation   | 2025      |
| Recent Check | 2026      |

### Leakage Control

The model excludes post-trade information such as:

```text
exit_reason
exit_price
exit_relative_deviation
MFE
MAE
holding time
pnl-derived labels
```

### Main Findings

* Logistic Regression has limited out-of-sample strength.
* Random Forest shows weak validation AUC but useful feature importance.
* XGBoost overfits and should not be used as a trading model.
* Important features overlap with the rule-based research logic.

Relevant features include:

```text
deviation slope
TW50 returns
realized volatility
entry timing
volume ratio
entry relative deviation
signal count
```

### Interpretation

The AI module supports feature validation, not direct trade prediction.

Correct positioning:

```text
AI-assisted signal quality validation
```

Incorrect positioning:

```text
AI trading model
```

---

## 9. Main Research Conclusions

### 9.1 The Deviation Signal Has Conditional Value

The baseline signal has a positive edge, but its quality depends heavily on market conditions.

Deviation alone is not enough.

### 9.2 TW50 Direction Improves Signal Quality

Adding TW50 short-term upward confirmation improves the signal pool by filtering out weaker non-confirming cases.

### 9.3 Late Entry Matters

Positive deviation slope can indicate that the reversion has already started, reducing remaining expected edge.

### 9.4 Session Timing Matters

The 09:45–10:00 window and lunch-tail area require special attention because signal quality and execution feasibility vary by session.

### 9.5 Execution Is the Main Bottleneck

v2-B3 looks strong before heavy cost assumptions, but performance is sensitive to cost and slippage.

### 9.6 AI Helps Validate Features, Not Replace Market Logic

Machine learning is useful for checking whether important features align with rule-based market reasoning, but the current sample is not enough for a robust AI trading model.

---

## 10. Final Positioning

The current research result should be described as:

```text
A refined intraday deviation signal candidate supported by event-level validation, cost stress testing, high-risk sample review, and AI-assisted feature validation.
```

It should not be described as:

```text
A production-ready arbitrage strategy.
```

The strongest value of this project is not only the backtest result, but the complete research workflow:

```text
market hypothesis
→ event dataset
→ conditional testing
→ failure analysis
→ signal refinement
→ execution stress test
→ AI-assisted validation
→ conservative conclusion
```
