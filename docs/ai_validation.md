# AI-Assisted Signal Quality Validation

This document explains the AI-assisted validation layer used in the 0050 vs TW50 intraday deviation reversion research.

The key point is:

> This module is not an AI trading model.
> It is an AI-assisted signal quality validation layer.

The purpose is to test whether entry-time features in the event dataset can help explain signal quality after transaction cost assumptions.

---

## 1. Purpose of the AI Module

After building the rule-based strategy versions, the v1.1 event dataset was converted into a supervised learning sample.

The main research question was:

> Can machine learning identify which entry-time features are associated with higher-quality deviation reversion signals?

This is different from asking:

> Can machine learning directly trade the strategy?

The AI layer is used for:

* feature validation
* signal quality ranking
* failure-pattern discovery
* future research direction
* checking whether rule-based logic is reflected in the data

It is not used for:

* direct trading
* live signal generation
* autonomous decision-making
* production deployment

---

## 2. Input Dataset

The AI validation uses the v1.1 event dataset as the original candidate signal pool.

Reason:

* v1.1 contains the broader raw candidate pool
* it includes both good and weak signals
* it is less affected by later manual filtering
* it is more suitable for studying what separates high-quality and low-quality signals

Using a later filtered version such as v2-B3 would introduce selection bias because many weak cases have already been removed by rule-based filters.

---

## 3. Target Label Design

The binary label is:

```text
good_signal_cost002 = 1 if pnl_twd - 0.02 > 0
```

This means a signal is labeled as good only if it remains positive after a 0.02 round-trip cost assumption.

Why use cost-adjusted labeling?

Because this is a thin-edge intraday strategy. A signal that is profitable before cost may not be practically useful after transaction cost and slippage.

Therefore, the label is designed to be closer to practical trading reality than a simple raw PnL label.

---

## 4. Feature Set

The AI validation focuses on entry-time features only.

Examples of candidate features:

```text
entry_relative_deviation
deviation_slope_1bar
deviation_slope_3bar
tw50_return_5m
tw50_return_15m
etf_return_5m
etf_return_15m
volume_ratio_at_entry
realized_vol_10bar
signal_count_today
entry_minutes
minutes_since_open
minutes_to_close
session_block
entry_weekday
```

These features are selected because they are observable at or before entry.

---

## 5. Leakage Control

Post-trade information is intentionally excluded.

Excluded leakage-prone fields include:

```text
exit_reason
exit_price
exit_relative_deviation
MFE
MAE
holding_minutes
pnl-derived labels
future return after entry
```

This is important because including post-trade information would create data leakage and make the model look artificially strong.

The model should only use information that would have been available when making the entry decision.

---

## 6. Time-Based Split

The dataset is split by time, not randomly.

| Split        | Period    | Purpose                               |
| ------------ | --------- | ------------------------------------- |
| Train        | 2022–2024 | Learn initial signal-quality patterns |
| Validation   | 2025      | Check whether patterns generalize     |
| Recent Check | 2026      | Check more recent regime behavior     |

Random train-test split is avoided because financial event data is time-dependent. Random splitting can mix regimes and overstate model performance.

A time-based split is more conservative and closer to real research practice.

---

## 7. Models Tested

Three model families were used:

```text
Logistic Regression
Random Forest
XGBoost
```

### 7.1 Logistic Regression

Purpose:

* interpretable baseline
* tests whether linear relationships explain signal quality

Interpretation:

Logistic Regression is useful as a simple baseline, but the signal-quality structure appears too nonlinear and regime-dependent for a linear model alone.

### 7.2 Random Forest

Purpose:

* capture nonlinear feature interactions
* examine feature importance
* test whether ranking ability exists

Interpretation:

Random Forest shows stronger in-sample structure, but out-of-sample predictive strength is limited. Its main value is feature validation rather than direct prediction.

### 7.3 XGBoost

Purpose:

* test a stronger nonlinear model
* check whether gradient-boosted trees can capture more complex interaction patterns

Interpretation:

XGBoost overfits significantly. The in-sample performance is too strong relative to validation performance, so it should not be used as a direct trading model in this research stage.

---

## 8. Model Performance Interpretation

The AI models do not provide strong enough out-of-sample predictive power to justify direct trading use.

Main observations:

* Logistic Regression has limited validation strength
* Random Forest has weak validation AUC but useful feature importance
* XGBoost overfits
* Model performance is not stable enough across time splits
* Sample size is limited

Correct interpretation:

```text
The AI module provides feature validation and research guidance.
```

Incorrect interpretation:

```text
The AI module creates a profitable trading model.
```

---

## 9. Feature Importance Findings

Although model performance is not strong enough for direct trading, feature importance still provides useful research signals.

Important features identified or supported by the AI validation include:

```text
deviation_slope_1bar
deviation_slope_3bar
tw50_return_5m
tw50_return_15m
realized_vol_10bar
entry_minutes
minutes_to_close
volume_ratio_at_entry
entry_relative_deviation
signal_count_today
```

These features overlap with the rule-based research logic.

This overlap is important because it suggests that the manual strategy design was not purely arbitrary. The machine learning layer independently highlights similar dimensions of signal quality.

---

## 10. Relationship to Rule-Based Strategy Logic

The rule-based research found that signal quality depends on:

* TW50 direction
* deviation slope
* time window
* repeated signal count
* cost sensitivity
* realized volatility regime

The AI validation supports the idea that these features are relevant to signal quality.

For example:

| Feature             | Research Interpretation                                                 |
| ------------------- | ----------------------------------------------------------------------- |
| TW50 return         | Confirms whether the deviation is likely tracking lag or weak repricing |
| Deviation slope     | Helps avoid late-entry signals                                          |
| Entry timing        | Reflects session-dependent signal behavior                              |
| Realized volatility | May represent larger reversion opportunity under the right condition    |
| Volume ratio        | May reflect market participation and execution quality                  |
| Signal count        | Helps detect repeated-signal decay                                      |

---

## 11. Score Bucket Interpretation

The AI model should be interpreted more as a signal-quality ranking tool than a binary trading classifier.

A useful research direction is:

```text
Use model score to rank signal quality
instead of using model prediction to directly trade
```

This means the model can help identify:

* potentially stronger signals
* weaker signals
* samples requiring additional review
* future conditional filters to test

This is more realistic than expecting the model to perfectly predict each trade outcome.

---

## 12. Why the AI Model Is Not Used Directly

The AI model is not used directly for trading for several reasons:

1. Sample size is limited.
2. Validation AUC is weak.
3. XGBoost overfits.
4. Market regimes change over time.
5. Execution costs dominate thin-edge strategies.
6. The model has not been tested with live or tick-level execution data.
7. Prediction quality is not yet stable enough.

Therefore, the model is used only as a research validation layer.

---

## 13. Practical Value of the AI Layer

Even though the AI model is not tradable by itself, it adds value to the research process.

It helps answer:

```text
Which features repeatedly appear related to signal quality?
Do model findings align with rule-based market logic?
Which samples should be reviewed further?
Which future filters are worth testing?
Where might overfitting occur?
```

This supports a more disciplined research workflow.

---

## 14. Future AI Research Roadmap

Potential future AI work includes:

### 14.1 Strong / Weak / Failed Signal Classification

Convert the binary label into a multi-class signal quality label:

```text
strong signal
weak signal
failed signal
```

This may help separate good trades, thin trades, and clearly bad trades.

### 14.2 SHAP Interpretation

Use SHAP to explain model predictions and inspect whether feature effects match market logic.

Focus features:

```text
TW50_return_5m
TW50_return_15m
deviation_slope_1bar
realized_vol_10bar
session_block
volume_ratio_at_entry
signal_count_today
```

### 14.3 Signal Ranking System

Use model probability as a ranking score rather than a direct trading signal.

This can support future research on:

* filtering weak signals
* raising thresholds for repeated signals
* identifying high-risk sessions
* improving sample review efficiency

### 14.4 Walk-Forward Validation

Use walk-forward testing to evaluate whether feature importance and signal ranking remain stable across time.

### 14.5 Execution-Aware Features

Add features related to execution feasibility, such as:

* spread proxy
* volume concentration
* time-to-close
* recent volatility compression
* intraday liquidity condition

---

## 15. Final Interpretation

The AI-assisted validation layer should be summarized as:

```text
A feature-validation and signal-quality research tool that supports the rule-based strategy logic, while remaining too weak for direct trading deployment.
```

The contribution of the AI layer is not that it replaces market reasoning. Its contribution is that it helps validate whether market-reasoned features appear relevant in the event dataset.

The correct conclusion is:

> AI helps validate and prioritize research directions, but does not yet produce a standalone tradable model.

---

## 16. Summary

The AI validation module strengthens the project by showing that the strategy research is not limited to static rule testing.

It demonstrates the ability to:

* convert trade events into supervised learning samples
* define practical cost-adjusted labels
* avoid data leakage
* use time-based validation
* compare interpretable and nonlinear models
* identify feature-importance patterns
* avoid overclaiming AI results
* position machine learning as a research accelerator rather than a black-box trading system
