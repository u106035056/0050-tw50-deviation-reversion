# 0050 vs TW50 Intraday Deviation Reversion Research

This repository documents a quantitative research workflow for an intraday deviation reversion strategy between Taiwan 0050 ETF and a TW50 simulated NAV reference.

This project is a **research portfolio**, not a production-ready trading system. The main goal is to demonstrate a disciplined strategy research process, including market hypothesis design, event dataset construction, conditional validation, cost and slippage stress testing, high-risk sample review, and AI-assisted signal quality validation.

---

## Project Positioning

* **Project type:** ETF intraday deviation reversion research
* **Primary object:** 0050 ETF vs TW50 simulated NAV
* **Research focus:** Signal quality, market logic, event-level validation, execution sensitivity
* **Main version:** v2-B3 final signal candidate
* **Important limitation:** v2-B3 is **not** a final tradable strategy
* **AI module:** AI-assisted signal quality validation, **not** an AI trading model

---

## Core Hypothesis

A negative deviation between 0050 ETF market price and TW50 simulated NAV is not automatically a valid arbitrage signal.

The same negative deviation can represent two different market states.

### 1. Tracking Lag

TW50 moves upward first, while 0050 ETF market price temporarily lags behind.

```text
TW50 short-term upward move
→ underlying basket reacts first
→ 0050 price temporarily lags
→ negative deviation appears
→ potential short-term reversion
```

### 2. Risk Repricing

TW50 does not confirm strength, or the broader market is weakening. In this case, the apparent discount may reflect risk repricing rather than a clean reversion opportunity.

```text
TW50 weak or non-confirming
→ negative deviation may not be cheap
→ signal quality decreases
→ reversion probability weakens
```

Therefore, this research does not treat deviation alone as sufficient. It tests whether entry-time features such as TW50 return, deviation slope, session timing, realized volatility, volume ratio, and repeated signal count can help separate higher-quality reversion candidates from lower-quality signals.

---

## Research Workflow

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

The workflow emphasizes **hypothesis-driven iteration**, not brute-force parameter optimization.

---

## Strategy Version Summary

| Version           | Purpose                | Main Change                                                 | Key Result                                                    |
| ----------------- | ---------------------- | ----------------------------------------------------------- | ------------------------------------------------------------- |
| v1.1 No Overnight | Baseline               | Original intraday deviation reversion, no overnight holding | 361 trades, PF about 1.98                                     |
| v2-A              | Direction confirmation | Add `TW50_return_5m > 0`                                    | 258 trades, PF about 2.66                                     |
| v2-B2             | Late-entry reduction   | Exclude `deviation_slope_1bar > 0`                          | Reduces entries after deviation has already started reverting |
| v2-B3             | Final signal candidate | Exclude slope > 0 and the main 09:45–10:00 weak window      | 223 trades, Net PnL about 7.80, PF about 3.60                 |

---

## Key Results

### v1.1 Baseline

The v1.1 baseline produced 361 event trades and showed an initial positive edge. However, the raw deviation signal still mixed higher-quality tracking lag opportunities with weaker or false deviation signals.

### v2-A: TW50 5m Upward Filter

The v2-A version added a TW50 5-minute upward confirmation filter:

```text
TW50_return_5m > 0
```

This reduced trades from 361 to 258 and improved PF from about 1.98 to about 2.66.

The main interpretation is not simply that fewer trades improved performance. Rather, the TW50 filter helped distinguish:

```text
clean tracking lag
vs.
weak deviation during non-confirming market states
```

### v2-B3: Final Signal Candidate

After additional failure analysis, v2-B3 excluded:

```text
deviation_slope_1bar > 0
main 09:45–10:00 weak window
```

v2-B3 result summary:

| Metric        |       v2-B3 |
| ------------- | ----------: |
| Trades        |         223 |
| Net PnL       |  about 7.80 |
| Avg PnL       | about 0.035 |
| Profit Factor |  about 3.60 |
| Gross Loss    | about -3.00 |
| Max Loss      | about -0.25 |

This version is treated as the current **final signal candidate**, not as a final tradable strategy.

---

## Cost and Slippage Sensitivity

The strategy is a thin-edge intraday strategy. Cost and slippage materially affect the result.

Main interpretation:

```text
Signal layer: meaningful
Execution layer: still unproven
Live tradability: not yet established
```

Cost stress testing showed:

* Cost 0.01 remains relatively acceptable
* Cost 0.02 weakens the edge significantly
* 0.5 tick each side slippage can make the strategy fail

Therefore, the next stage should not be endless signal filtering. The more important direction is execution feasibility:

```text
limit order feasibility
fill probability
bid-ask spread
slippage control
exit efficiency
```

---

## High-Risk Sample Review

The high-risk sample review identified several remaining risk sources:

| Risk Area                     | Interpretation                                                                               |
| ----------------------------- | -------------------------------------------------------------------------------------------- |
| Lunch tail 12:45–13:00        | Becomes weak after transaction cost because remaining reversion time is short                |
| Repeated signals              | Signal decay appears, especially from the third signal onward                                |
| EXIT_TIME samples             | Not toxic, but indicate weaker exit efficiency                                               |
| High RV samples               | Should not be blindly excluded; under v2-B3, high realized volatility contributes positively |
| Early training-period samples | More fragile after cost adjustment                                                           |

A key finding is that high realized volatility is not necessarily pure noise. Under the v2-B3 condition set, high RV may represent larger reversion opportunity rather than a simple risk filter to exclude.

---

## AI-Assisted Signal Quality Validation

After the rule-based research process, the v1.1 event dataset was converted into a supervised learning sample.

The AI validation target was:

```text
good_signal_cost002 = 1 if pnl_twd - 0.02 > 0
```

This means a trade is labeled as a good signal only if it remains positive after a 0.02 round-trip cost assumption.

Models tested:

```text
Logistic Regression
Random Forest
XGBoost
```

Time-based split:

```text
Train: 2022–2024
Validation: 2025
Recent Check: 2026
```

To avoid data leakage, post-trade columns were excluded:

```text
exit_reason
exit_price
exit_relative_deviation
MFE
MAE
holding time
pnl-derived labels
```

### AI Validation Interpretation

The machine learning models are **not** strong enough to be used as direct trading models.

Main observations:

* XGBoost overfits significantly
* Random Forest shows weak validation AUC but useful feature importance
* Feature importance supports the relevance of:

  * deviation slope
  * TW50 returns
  * realized volatility
  * entry timing
  * volume ratio
  * entry relative deviation
  * signal count

Therefore, the AI module is positioned as:

```text
AI-assisted signal quality validation
```

not as:

```text
AI trading model
```

The purpose is to validate whether the rule-based market logic is reflected in event-level features, not to automate direct trade prediction.

---

## Repository Structure

```text
README.md
requirements.txt
.gitignore

raw_uploads/
  Raw and intermediate uploaded research artifacts

raw_uploads_archive/
  Archive area for duplicate or intermediate files in later cleanup

data/
  README.md
  raw_tradingview/
  processed_event_dataset/
  outputs/

docs/
  methodology.md
  results_summary.md
  ai_validation.md
  limitations_and_future_work.md
  interview_notes.md

reports/
  strategy_summary.md

notebooks/
  Research notebooks after cleanup

src/
  Utility scripts after cleanup
```

At the current stage, `raw_uploads/` contains raw and intermediate research artifacts. A later cleanup pass can move canonical files into `data/`, `notebooks/`, and `src/` after file-by-file review.

---

## Current Canonical Research Artifacts

Key research files include:

```text
0050_v1_1_ai_event_dataset_full_features.csv
0050_v2A_ai_event_dataset_full_features_FIXED.csv
UPLOAD_THIS_TO_COLAB__v2B3_Parsed_B3_Events_223.csv
0050_v1_1_vs_v2A_comparison_FIXED.xlsx
v2A_failure_analysis_outputs.xlsx
0050_v2B3_high_risk_sample_review_outputs_FIXED.xlsx
0050_ai_signal_quality_validation_outputs_FIXED.xlsx
```

These files represent the core research path from baseline construction to AI-assisted validation.

---

## Known Limitations

This repository does not claim that the strategy is ready for live deployment.

Major limitations:

1. No tick-level order book data
2. No real bid-ask spread or live fill-rate study
3. No direct limit order execution simulation
4. High sensitivity to cost and slippage
5. Limited ML sample size
6. AI validation has weak out-of-sample predictive power
7. v2-B3 is a final signal candidate, not a production-ready strategy

---

## Future Work

The future research direction should focus on execution and risk management rather than simply adding more entry filters.

Recommended next steps:

### 1. Lunch-Tail Execution-Aware Filter

Study whether 12:45–13:00 signals should require stronger TW50 momentum, deeper deviation, or better execution conditions.

### 2. Repeated Signal Expected-Edge Threshold

Study whether the third signal onward in the same day should require a higher expected edge, such as stronger TW50 movement or deeper deviation.

### 3. EXIT_TIME Exit-Efficiency Research

Study whether earlier time stop, partial reversion exit, or dynamic exit thresholds can improve exit efficiency.

---

## Portfolio Interpretation

This project is best understood as a demonstration of the following research abilities:

```text
market microstructure reasoning
event dataset construction
hypothesis-driven strategy iteration
failure analysis
cost and slippage awareness
high-risk sample taxonomy
AI-assisted feature validation
conservative strategy communication
```

The goal is not to claim a finished trading system, but to show a complete and disciplined research workflow that can be extended into more robust quantitative strategy development.

---

## Disclaimer

This repository is for research and portfolio demonstration only.

It is not investment advice, not a recommendation to trade, and not a production-ready trading strategy.
