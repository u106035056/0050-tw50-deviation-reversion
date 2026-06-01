# 0050 vs TW50 Intraday Deviation Reversion Research

This repository organizes quantitative research on intraday deviation reversion between 0050 and TW50.

Positioning and Scope
This repository is a research portfolio, not a production trading system.
v2-B3 is the final signal candidate within this research cycle, not a final tradable strategy.
AI work is positioned as AI-assisted signal quality validation and feature validation, not an autonomous AI trading model.
Backtest and validation statistics in this repository should not be interpreted as a claim of live trading profitability.
Core Research Storyline
v1.1 baseline
361 trades
Original intraday deviation reversion baseline
v2-A
Adds TW50_return_5m > 0 filter
Trades reduce to 258
PF improves from about 1.98 to about 2.66
Gross loss improves from about -7.50 to about -4.60
Max single loss improves from about -0.55 to about -0.35
v2-B2
Excludes deviation_slope_1bar > 0
Avoids late entry after deviation has already started reverting
v2-B3
Excludes positive slope and the main 09:45-10:00 weak window
223 trades
Net PnL about 7.80
Avg PnL about 0.035
PF about 3.60
Gross loss about -3.00
Max loss about -0.25
Positioning: final signal candidate, not final tradable strategy
Cost and slippage stress
v2-B3 is a thin-edge strategy
Cost 0.01 remains acceptable
Cost 0.02 weakens the edge significantly
0.5 tick each side slippage can make the strategy fail
Execution quality and slippage control are critical
High-risk sample review
Lunch tail (12:45-13:00) becomes weak after cost
Repeated signals show decay, especially from the third signal onward
EXIT_TIME is not toxic, but indicates exit-efficiency weakness
High RV should not be blindly excluded; under v2-B3 it can still contribute strong positive results
Remaining risks are concentrated in execution, exit efficiency, time-window effects, and signal decay
AI-assisted signal quality validation
Uses v1.1 event dataset as the candidate signal pool
Label: good_signal_cost002 = 1 if pnl_twd - 0.02 > 0
Models: Logistic Regression, Random Forest, XGBoost (optional)
Time split: Train 2022-2024, Validation 2025, Recent Check 2026
Leakage columns excluded: exit_reason, exit price, exit deviation, MFE, MAE, holding time, pnl-derived labels
Model performance is not strong enough for direct trading use
XGBoost shows overfitting behavior
Random Forest has weak validation AUC but still provides useful feature-importance signals
Use as AI-assisted validation only
Repository Structure
notebooks/: exploratory and presentation notebooks
src/: reusable research utilities
data/: standardized research data layout
docs/: methodology and detailed analysis notes
reports/: concise strategy-level summary
raw_uploads/: incoming raw research files
raw_uploads_archive/: duplicate, intermediate, unclear, obsolete, and package files (non-destructive archive)
Data Management Principle
Do not permanently delete uploaded research files.
Archive non-canonical or uncertain files into raw_uploads_archive/.
Keep canonical files in official folders under data/, docs/, reports/, notebooks/, and src/.
Current Initialization Note
At the time of this cleanup pass, no existing uploaded research files were found in raw_uploads/. The structure is prepared for immediate ingestion and file-by-file curation once uploads are available.
