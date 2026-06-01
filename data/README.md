# Data README

This document explains the data organization for the 0050 vs TW50 intraday deviation reversion research project.

The repository currently contains both canonical research artifacts and intermediate files. The main goal of this file is to clarify which files are used as primary research inputs and which files are retained as raw or archived materials.

---

## 1. Data Organization Principle

The project data is separated into three conceptual layers:

```text
raw_uploads/
→ original uploaded files, raw exports, intermediate outputs, duplicate versions

data/processed_event_dataset/
→ cleaned or canonical event datasets used for analysis

data/outputs/
→ final or semi-final analysis outputs, Excel reports, comparison tables

data/raw_tradingview/
→ raw TradingView exports before event-dataset transformation
```

At the current stage, most files remain in `raw_uploads/` for safety. This avoids accidentally deleting or misclassifying research artifacts before a complete file-by-file review.

---

## 2. Current Canonical Research Artifacts

The following files are considered the core research artifacts.

### 2.1 Event Datasets

| File                                                  | Role                                                                              |
| ----------------------------------------------------- | --------------------------------------------------------------------------------- |
| `0050_v1_1_ai_event_dataset_full_features.csv`        | v1.1 baseline event dataset; main input for AI-assisted signal quality validation |
| `0050_v2A_ai_event_dataset_full_features_FIXED.csv`   | v2-A event dataset after TW50 5-minute upward filter                              |
| `UPLOAD_THIS_TO_COLAB__v2B3_Parsed_B3_Events_223.csv` | parsed v2-B3 event dataset with 223 trades                                        |

These datasets represent the main event-level research path from baseline to refined signal candidate.

---

### 2.2 Analysis Outputs

| File                                                   | Role                                         |
| ------------------------------------------------------ | -------------------------------------------- |
| `0050_v1_1_vs_v2A_comparison_FIXED.xlsx`               | formal comparison between v1.1 and v2-A      |
| `v2A_failure_analysis_outputs.xlsx`                    | failure analysis output after v2-A           |
| `0050_v2B3_high_risk_sample_review_outputs_FIXED.xlsx` | v2-B3 high-risk sample review output         |
| `0050_ai_signal_quality_validation_outputs_FIXED.xlsx` | AI-assisted signal quality validation output |

These output files support the main conclusions in the README and docs.

---

### 2.3 Raw TradingView Exports

| File                                                                                         | Role                                            |
| -------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `0050_vs_TW50_Baseline_Backtest_v1.1_No_Overnight_+_Entry_Features_TWSE_0050_2026-06-01.csv` | TradingView export with entry features          |
| `0050_vs_TW50_Baseline_Backtest_v1.1_No_Overnight_TWSE_0050_2026-06-01.csv`                  | baseline TradingView export                     |
| `0050_vs_TW50_Baseline_Backtest_v1.1_No_Overnight_TWSE_0050_2026-06-01.xlsx`                 | baseline TradingView export in Excel format     |
| `TWSE_DLY_0050, 5.csv`                                                                       | raw 5-minute 0050 data export                   |
| `TWSE_DLY_0050, 5 (1).csv`                                                                   | duplicate or alternate raw 5-minute data export |
| `TWSE_DLY_0050, 5 (2).csv`                                                                   | duplicate or alternate raw 5-minute data export |

These files are kept for traceability and reproducibility.

---

## 3. Suggested Future Folder Layout

After file-by-file review, the repository can be cleaned into the following structure:

```text
data/
  raw_tradingview/
    0050_vs_TW50_Baseline_Backtest_v1.1_No_Overnight_+_Entry_Features_TWSE_0050_2026-06-01.csv
    0050_vs_TW50_Baseline_Backtest_v1.1_No_Overnight_TWSE_0050_2026-06-01.csv
    0050_vs_TW50_Baseline_Backtest_v1.1_No_Overnight_TWSE_0050_2026-06-01.xlsx
    TWSE_DLY_0050, 5.csv
    TWSE_DLY_0050, 5 (1).csv
    TWSE_DLY_0050, 5 (2).csv

  processed_event_dataset/
    0050_v1_1_ai_event_dataset_full_features.csv
    0050_v2A_ai_event_dataset_full_features_FIXED.csv
    0050_v2B3_parsed_events_223.csv

  outputs/
    0050_v1_1_vs_v2A_comparison_FIXED.xlsx
    v2A_failure_analysis_outputs.xlsx
    0050_v2B3_high_risk_sample_review_outputs_FIXED.xlsx
    0050_ai_signal_quality_validation_outputs_FIXED.xlsx
```

---

## 4. Intermediate and Duplicate Files

Several files in `raw_uploads/` are intermediate, duplicate, or package files.

Examples:

```text
files with "(1)" in the filename
older non-FIXED outputs
zip packages
temporary HTML exports
early Colab output files
```

These files are not necessarily wrong, but they should not be treated as the primary research outputs.

Recommended future handling:

```text
raw_uploads_archive/
→ duplicate files
→ old intermediate outputs
→ zip packages
→ unclear temporary files
```

This preserves traceability while keeping the main repository clean.

---

## 5. Why Raw Uploads Are Preserved

The raw upload folder is intentionally preserved because the project evolved through multiple research iterations.

The raw files provide:

* historical traceability
* debugging evidence
* intermediate analysis outputs
* backup versions
* reproducibility references

No raw research file should be permanently deleted without review.

---

## 6. Data Usage Notes

The core files for understanding the project are:

```text
0050_v1_1_ai_event_dataset_full_features.csv
0050_v2A_ai_event_dataset_full_features_FIXED.csv
UPLOAD_THIS_TO_COLAB__v2B3_Parsed_B3_Events_223.csv
0050_v1_1_vs_v2A_comparison_FIXED.xlsx
v2A_failure_analysis_outputs.xlsx
0050_v2B3_high_risk_sample_review_outputs_FIXED.xlsx
0050_ai_signal_quality_validation_outputs_FIXED.xlsx
```

These files are sufficient to understand:

* baseline signal construction
* v1.1 vs v2-A comparison
* failure analysis
* v2-B3 event sample
* high-risk sample review
* AI-assisted validation

---

## 7. Data Limitation

The data currently does not include:

* tick-level order book
* real bid-ask spread
* actual limit order fill information
* live execution records
* paper trading execution logs

Therefore, the current dataset supports signal research and event-level validation, but not full live-trading execution validation.

---

## 8. Summary

This data layer supports a research workflow rather than a production trading system.

The current data is sufficient for:

```text
event-level signal analysis
strategy version comparison
failure review
cost stress testing
AI-assisted feature validation
```

The next data improvement should focus on:

```text
bid-ask spread
fill probability
tick-level liquidity
execution feasibility
paper-trading logs
```
