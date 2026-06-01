# -*- coding: utf-8 -*-
"""
0050 AI Signal Quality Validation

This is NOT an AI trading model.
It is an AI-assisted validation layer for the 0050 vs TW50 event dataset.

Recommended input:
    0050_v1_1_ai_event_dataset_full_features.csv

Output:
    0050_ai_signal_quality_validation_outputs.xlsx
"""

import warnings
warnings.filterwarnings("ignore")

import re
import numpy as np
import pandas as pd
from IPython.display import display
from google.colab import files

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix
)
from sklearn.inspection import permutation_importance

OUTPUT_FILE = "0050_ai_signal_quality_validation_outputs.xlsx"
ROUND_TRIP_COST = 0.02
STRONG_EDGE_THRESHOLD = 0.05

print("Please upload the event dataset.")
print("Recommended: 0050_v1_1_ai_event_dataset_full_features.csv")
print("Acceptable: xlsx with Combined_Data sheet.")
uploaded = files.upload()
file_name = list(uploaded.keys())[0]
print("Loaded:", file_name)


def clean_number(x):
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.number)):
        return float(x)
    s = str(x).strip().replace(",", "").replace("TWD", "").replace("%", "").replace("−", "-")
    s = re.sub(r"[^\d\.\-\+eE]", "", s)
    if s in ["", "-", "+", "."]:
        return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def find_col(df, candidates):
    cols = list(df.columns)
    lower_map = {str(c).lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    for cand in candidates:
        cand_low = cand.lower()
        for c in cols:
            if cand_low in str(c).lower():
                return c
    return None


def normalize_time_hhmm(x):
    if pd.isna(x):
        return np.nan
    if hasattr(x, "strftime"):
        return x.strftime("%H:%M")
    s = str(x).strip()
    if re.fullmatch(r"\d{3,4}", s):
        s = s.zfill(4)
        return s[:2] + ":" + s[2:]
    m = re.search(r"(\d{1,2}):(\d{2})", s)
    if m:
        return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
    return np.nan


def time_to_minutes(hhmm):
    if pd.isna(hhmm):
        return np.nan
    try:
        hh, mm = str(hhmm).split(":")[:2]
        return int(hh) * 60 + int(mm)
    except Exception:
        return np.nan


def assign_session(mins):
    if pd.isna(mins):
        return "Unknown"
    if mins < 9 * 60 + 5:
        return "pre_0905"
    if mins < 9 * 60 + 45:
        return "early_main_0905_0945"
    if mins < 10 * 60:
        return "early_mid_0945_1000"
    if mins < 12 * 60 + 45:
        return "midday_main_1000_1245"
    if mins <= 13 * 60:
        return "lunch_tail_1245_1300"
    return "after_1300"


def calc_profit_factor(pnl):
    pnl = pd.to_numeric(pnl, errors="coerce").dropna()
    gp = pnl[pnl > 0].sum()
    gl = pnl[pnl < 0].sum()
    if gl < 0:
        return gp / abs(gl)
    if gp > 0 and gl == 0:
        return np.inf
    return np.nan


def perf_summary(data, pnl_col="pnl_twd", group_cols=None):
    def _calc(x):
        pnl = pd.to_numeric(x[pnl_col], errors="coerce").dropna()
        n = len(pnl)
        if n == 0:
            return pd.Series({
                "trades": 0, "wins": 0, "losses": 0, "flats": 0,
                "win_rate": np.nan, "net_pnl": 0, "avg_pnl": np.nan,
                "gross_profit": 0, "gross_loss": 0, "profit_factor": np.nan
            })
        gp = pnl[pnl > 0].sum()
        gl = pnl[pnl < 0].sum()
        return pd.Series({
            "trades": n,
            "wins": int((pnl > 0).sum()),
            "losses": int((pnl < 0).sum()),
            "flats": int((pnl == 0).sum()),
            "win_rate": float((pnl > 0).mean()),
            "net_pnl": float(pnl.sum()),
            "avg_pnl": float(pnl.mean()),
            "gross_profit": float(gp),
            "gross_loss": float(gl),
            "profit_factor": calc_profit_factor(pnl)
        })
    if group_cols is None:
        return _calc(data).to_frame().T
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    return data.groupby(group_cols, dropna=False).apply(_calc).reset_index()


def safe_auc(y_true, y_prob):
    try:
        if len(np.unique(y_true)) < 2:
            return np.nan
        return roc_auc_score(y_true, y_prob)
    except Exception:
        return np.nan


def evaluate_model(name, model, X, y, dataset_name):
    pred = model.predict(X)
    prob = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else pred
    cm = confusion_matrix(y, pred, labels=[0, 1])
    return {
        "model": name,
        "dataset": dataset_name,
        "n": len(y),
        "positive_rate": float(np.mean(y)) if len(y) else np.nan,
        "auc": safe_auc(y, prob),
        "accuracy": accuracy_score(y, pred) if len(y) else np.nan,
        "precision": precision_score(y, pred, zero_division=0) if len(y) else np.nan,
        "recall": recall_score(y, pred, zero_division=0) if len(y) else np.nan,
        "f1": f1_score(y, pred, zero_division=0) if len(y) else np.nan,
        "tn": cm[0, 0], "fp": cm[0, 1], "fn": cm[1, 0], "tp": cm[1, 1],
    }


def feature_names_from_preprocessor(preprocessor):
    names = []
    try:
        num_features = preprocessor.transformers_[0][2]
        cat_features = preprocessor.transformers_[1][2]
        names += list(num_features)
        ohe = preprocessor.named_transformers_["cat"].named_steps["onehot"]
        names += list(ohe.get_feature_names_out(cat_features))
    except Exception:
        pass
    return names


def show(df, title=None, n=None):
    out = df.copy()
    for c in out.select_dtypes(include=[float]).columns:
        out[c] = out[c].round(6)
    if title:
        print("\n" + "=" * 90)
        print(title)
        print("=" * 90)
    display(out.head(n) if n else out)
    return out


# ============================================================
# 1. Load data
# ============================================================

if file_name.lower().endswith(".csv"):
    raw = pd.read_csv(file_name)
elif file_name.lower().endswith(".xlsx"):
    xls = pd.ExcelFile(file_name)
    print("Sheets:", xls.sheet_names)
    if "Combined_Data" in xls.sheet_names:
        raw = pd.read_excel(file_name, sheet_name="Combined_Data")
    elif "Parsed_B3_Events" in xls.sheet_names:
        raw = pd.read_excel(file_name, sheet_name="Parsed_B3_Events")
    else:
        raw = pd.read_excel(file_name, sheet_name=xls.sheet_names[0])
else:
    raise ValueError("Please upload CSV or XLSX.")

print("Raw shape:", raw.shape)
print("Columns:", raw.columns.tolist())
display(raw.head(3))

df = raw.copy()

# If file contains multiple versions, use v1-like version as original candidate pool.
version_col = find_col(df, ["version"])
if version_col is not None:
    print("Versions found:", df[version_col].dropna().astype(str).unique().tolist())
    v1_mask = df[version_col].astype(str).str.contains("v1", case=False, na=False)
    if v1_mask.sum() > 0:
        df = df[v1_mask].copy()
        print("Filtered to v1-like rows:", df.shape)

# ============================================================
# 2. Standardize fields
# ============================================================

pnl_col = find_col(df, ["pnl_twd", "pnl_no_cost", "net_pnl", "淨損益 TWD", "pnl"])
if pnl_col is None:
    raise ValueError("Cannot find pnl column. Need pnl_twd or pnl_no_cost.")

df["pnl_twd"] = df[pnl_col].apply(clean_number)
df["pnl_cost_002"] = df["pnl_twd"] - ROUND_TRIP_COST

entry_dt_col = find_col(df, ["entry_dt", "entry_datetime", "entry_time", "entry_timestamp", "entry_date_time"])
date_col = find_col(df, ["entry_date", "date"])
hhmm_col = find_col(df, ["entry_time_hhmm", "entry_hhmm", "time_hhmm"])

if entry_dt_col is not None:
    df["entry_dt"] = pd.to_datetime(df[entry_dt_col], errors="coerce")
elif date_col is not None and hhmm_col is not None:
    df["entry_dt"] = pd.to_datetime(df[date_col].astype(str) + " " + df[hhmm_col].astype(str), errors="coerce")
else:
    df["entry_dt"] = pd.NaT

if "entry_year" not in df.columns:
    df["entry_year"] = df["entry_dt"].dt.year

df["entry_year"] = pd.to_numeric(df["entry_year"], errors="coerce")

if "entry_month" not in df.columns:
    df["entry_month"] = df["entry_dt"].dt.to_period("M").astype(str)

if "entry_weekday" not in df.columns:
    df["entry_weekday"] = df["entry_dt"].dt.day_name()

if hhmm_col is not None:
    df["entry_time_hhmm"] = df[hhmm_col].apply(normalize_time_hhmm)
else:
    df["entry_time_hhmm"] = df["entry_dt"].apply(normalize_time_hhmm)

df["entry_minutes"] = df["entry_time_hhmm"].apply(time_to_minutes)

session_col = find_col(df, ["session_block", "session"])
if session_col is not None:
    df["session_block"] = df[session_col].astype(str)
else:
    df["session_block"] = df["entry_minutes"].apply(assign_session)

sig_col = find_col(df, ["signal_count_today", "trade_count_today", "daily_signal_count"])
if sig_col is not None:
    df["signal_count_today"] = pd.to_numeric(df[sig_col], errors="coerce")
else:
    df = df.sort_values(["entry_dt"])
    df["signal_count_today"] = df.groupby(df["entry_dt"].dt.date).cumcount() + 1


def assign_split(y):
    if pd.isna(y):
        return "Unknown"
    y = int(y)
    if y <= 2024:
        return "Train_2022_2024"
    if y == 2025:
        return "Validation_2025"
    if y >= 2026:
        return "Recent_Check_2026"
    return "Unknown"

if "data_split" not in df.columns:
    df["data_split"] = df["entry_year"].apply(assign_split)

# Labels
# Binary label: cost-adjusted positive signal
# Three-class label: strong / weak / failed

df["good_signal_cost002"] = (df["pnl_cost_002"] > 0).astype(int)


def quality_label(p):
    if pd.isna(p):
        return "unknown"
    if p >= STRONG_EDGE_THRESHOLD:
        return "strong"
    if p > 0:
        return "weak"
    return "failed"

df["signal_quality_3class"] = df["pnl_cost_002"].apply(quality_label)

# ============================================================
# 3. Features and leakage control
# ============================================================

candidate_numeric_features = [
    "entry_relative_deviation",
    "deviation_slope_1bar",
    "deviation_slope_3bar",
    "tw50_return_5m",
    "tw50_return_15m",
    "etf_return_5m",
    "etf_return_15m",
    "volume_ratio_at_entry",
    "realized_vol_10bar",
    "signal_count_today",
    "entry_minutes",
    "minutes_since_open",
    "minutes_to_close",
]

candidate_categorical_features = [
    "session_block",
    "entry_weekday",
]

# Never use post-trade / outcome columns as entry-time features.
leakage_keywords = [
    "exit", "mfe", "mae", "holding", "bars_held", "pnl",
    "profit", "quality_label", "signal_quality", "good_signal",
    "result", "label"
]

numeric_features = []
for c in candidate_numeric_features:
    if c in df.columns and not any(k.lower() in c.lower() for k in leakage_keywords):
        df[c] = pd.to_numeric(df[c], errors="coerce")
        numeric_features.append(c)

categorical_features = []
for c in candidate_categorical_features:
    if c in df.columns and not any(k.lower() in c.lower() for k in leakage_keywords):
        df[c] = df[c].astype(str)
        categorical_features.append(c)

feature_cols = numeric_features + categorical_features
if not feature_cols:
    raise ValueError("No usable features found. Check event dataset columns.")

print("Numeric features:", numeric_features)
print("Categorical features:", categorical_features)

model_df = df.dropna(subset=["pnl_twd", "pnl_cost_002", "good_signal_cost002"]).copy()
model_df = model_df[model_df["data_split"].isin(["Train_2022_2024", "Validation_2025", "Recent_Check_2026"])].copy()

train_df = model_df[model_df["data_split"] == "Train_2022_2024"].copy()
valid_df = model_df[model_df["data_split"] == "Validation_2025"].copy()
recent_df = model_df[model_df["data_split"] == "Recent_Check_2026"].copy()

X_train = train_df[feature_cols]
y_train = train_df["good_signal_cost002"]
X_valid = valid_df[feature_cols]
y_valid = valid_df["good_signal_cost002"]
X_recent = recent_df[feature_cols]
y_recent = recent_df["good_signal_cost002"]

print("Split sizes:", {"train": len(train_df), "validation": len(valid_df), "recent": len(recent_df)})

# ============================================================
# 4. Data check and label distribution
# ============================================================

data_check = pd.DataFrame({
    "item": [
        "input_file", "rows_after_filter", "train_rows", "validation_rows", "recent_rows",
        "pnl_col", "round_trip_cost_for_label", "positive_label_definition",
        "numeric_features", "categorical_features", "leakage_excluded"
    ],
    "value": [
        file_name, len(model_df), len(train_df), len(valid_df), len(recent_df),
        pnl_col, ROUND_TRIP_COST, "good_signal_cost002 = 1 if pnl_twd - 0.02 > 0",
        ", ".join(numeric_features), ", ".join(categorical_features),
        "exit_reason, exit price, exit deviation, MFE, MAE, holding time, pnl-derived labels"
    ]
})

label_distribution = model_df.groupby(["data_split", "signal_quality_3class"]).size().reset_index(name="count")
binary_label_distribution = model_df.groupby(["data_split", "good_signal_cost002"]).size().reset_index(name="count")
overall_perf = perf_summary(model_df, "pnl_twd")
perf_by_split = perf_summary(model_df, "pnl_twd", "data_split")
perf_by_quality = perf_summary(model_df, "pnl_twd", "signal_quality_3class")
quality_by_session = perf_summary(model_df, "pnl_twd", ["session_block", "signal_quality_3class"])

show(data_check, "Data Check")
show(label_distribution, "Three-Class Label Distribution")
show(binary_label_distribution, "Binary Label Distribution")
show(perf_by_split, "Performance by Split")

# ============================================================
# 5. Model pipelines
# ============================================================

numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer(transformers=[
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features),
])

models = {
    "Logistic_Regression": Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
    ]),
    "Random_Forest": Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", RandomForestClassifier(
            n_estimators=400,
            max_depth=4,
            min_samples_leaf=8,
            random_state=42,
            class_weight="balanced_subsample",
        )),
    ]),
}

try:
    from xgboost import XGBClassifier
    models["XGBoost_Optional"] = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", XGBClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
        )),
    ])
except Exception:
    print("XGBoost is not available. Skipping XGBoost.")

# ============================================================
# 6. Train and evaluate models
# ============================================================

metrics_rows = []
feature_importance_tables = {}
trained_models = {}

for name, model in models.items():
    print("\nTraining:", name)

    if len(train_df) == 0 or len(np.unique(y_train)) < 2:
        print("Skipping because training set has no data or only one class.")
        continue

    model.fit(X_train, y_train)
    trained_models[name] = model

    metrics_rows.append(evaluate_model(name, model, X_train, y_train, "Train_2022_2024"))
    if len(valid_df) > 0:
        metrics_rows.append(evaluate_model(name, model, X_valid, y_valid, "Validation_2025"))
    if len(recent_df) > 0:
        metrics_rows.append(evaluate_model(name, model, X_recent, y_recent, "Recent_Check_2026"))

    try:
        preprocess_fitted = model.named_steps["preprocess"]
        feat_names = feature_names_from_preprocessor(preprocess_fitted)
        final_model = model.named_steps["model"]

        if hasattr(final_model, "feature_importances_"):
            values = final_model.feature_importances_
            fi = pd.DataFrame({"feature": feat_names[:len(values)], "importance": values}).sort_values("importance", ascending=False)
            feature_importance_tables[name] = fi
        elif hasattr(final_model, "coef_"):
            values = final_model.coef_[0]
            fi = pd.DataFrame({"feature": feat_names[:len(values)], "coef": values, "abs_coef": np.abs(values)}).sort_values("abs_coef", ascending=False)
            feature_importance_tables[name] = fi
    except Exception as e:
        print("Feature importance failed for", name, ":", e)

metrics_df = pd.DataFrame(metrics_rows)
show(metrics_df, "Model Metrics")

for name, fi in feature_importance_tables.items():
    show(fi, f"Feature Importance - {name}", n=20)

# ============================================================
# 7. Permutation importance on validation
# ============================================================

permutation_tables = {}

if len(valid_df) > 10 and len(np.unique(y_valid)) >= 2:
    for name, model in trained_models.items():
        try:
            result = permutation_importance(model, X_valid, y_valid, n_repeats=20, random_state=42, scoring="roc_auc")
            perm = pd.DataFrame({
                "feature": feature_cols,
                "importance_mean": result.importances_mean,
                "importance_std": result.importances_std,
            }).sort_values("importance_mean", ascending=False)
            permutation_tables[name] = perm
            show(perm, f"Permutation Importance - {name}", n=20)
        except Exception as e:
            print("Permutation importance failed for", name, ":", e)
else:
    print("Validation set too small or one-class only. Skipping permutation importance.")

# ============================================================
# 8. Optional SHAP
# ============================================================

shap_summary = pd.DataFrame({"status": ["not_run"], "reason": ["SHAP optional. Feature importance is baseline output."]})

try:
    import shap
    if "Random_Forest" in trained_models and len(valid_df) > 0:
        rf_pipe = trained_models["Random_Forest"]
        preprocess_fitted = rf_pipe.named_steps["preprocess"]
        rf_model = rf_pipe.named_steps["model"]
        X_valid_trans = preprocess_fitted.transform(X_valid)
        feat_names = feature_names_from_preprocessor(preprocess_fitted)
        try:
            X_valid_dense = X_valid_trans.toarray()
        except Exception:
            X_valid_dense = X_valid_trans
        explainer = shap.TreeExplainer(rf_model)
        shap_values = explainer.shap_values(X_valid_dense)
        shap_vals = shap_values[1] if isinstance(shap_values, list) else shap_values
        mean_abs = np.abs(shap_vals).mean(axis=0)
        shap_summary = pd.DataFrame({
            "feature": feat_names[:len(mean_abs)],
            "mean_abs_shap": mean_abs,
        }).sort_values("mean_abs_shap", ascending=False)
        show(shap_summary, "SHAP Summary - Random Forest", n=20)
except Exception as e:
    shap_summary = pd.DataFrame({"status": ["not_run"], "reason": [str(e)]})
    print("SHAP skipped:", e)

# ============================================================
# 9. Model score bucket analysis
# ============================================================

score_tables = {}

for name, model in trained_models.items():
    frames = []
    for dataset_name, part_df, X_part in [
        ("Train_2022_2024", train_df, X_train),
        ("Validation_2025", valid_df, X_valid),
        ("Recent_Check_2026", recent_df, X_recent),
    ]:
        if len(part_df) == 0:
            continue
        prob = model.predict_proba(X_part)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_part)
        temp = part_df.copy()
        temp["model"] = name
        temp["dataset"] = dataset_name
        temp["pred_good_prob"] = prob
        try:
            temp["score_bucket"] = pd.qcut(temp["pred_good_prob"], q=5, duplicates="drop")
        except Exception:
            temp["score_bucket"] = pd.cut(temp["pred_good_prob"], bins=5)
        frames.append(temp)
    if frames:
        scored = pd.concat(frames, ignore_index=True)
        bucket_perf = perf_summary(scored, "pnl_cost_002", ["model", "dataset", "score_bucket"])
        score_tables[name] = bucket_perf
        show(bucket_perf, f"Score Bucket Performance - {name}", n=30)

# ============================================================
# 10. Conclusion
# ============================================================

top_features_text = []
for name, fi in feature_importance_tables.items():
    top_feats = fi.head(8).iloc[:, 0].astype(str).tolist()
    top_features_text.append(f"{name}: " + ", ".join(top_feats))
if not top_features_text:
    top_features_text.append("No feature importance available.")

conclusion_text = f"""
0050 AI Signal Quality Validation Conclusion

1. This module is an AI-assisted validation layer, not an AI trading model.
2. The target label is good_signal_cost002 = 1 if pnl_twd - {ROUND_TRIP_COST:.2f} > 0.
3. The purpose is to test whether entry-time features can explain signal quality after cost.
4. We used time-based split: Train = 2022-2024, Validation = 2025, Recent Check = 2026.
5. Leakage columns are intentionally excluded: exit_reason, exit_price, exit_relative_deviation, MFE, MAE, holding time, and pnl-derived labels.
6. Logistic Regression is used as an interpretable baseline. Random Forest is used to check non-linear interactions. XGBoost is optional.
7. If TW50_return_5m, deviation slope, session, signal_count_today, realized_vol_10bar, or volume_ratio_at_entry appear important, this supports the market-logic research.
8. This should be presented as AI-driven signal quality validation / feature stability check, not as an autonomous trading model.

Top feature snapshots:
{chr(10).join(top_features_text)}
"""

conclusion_df = pd.DataFrame({"conclusion": [conclusion_text]})

readme_df = pd.DataFrame({
    "section": ["Purpose", "Input", "Label", "Leakage Control", "Modeling Principle", "How to use in portfolio"],
    "content": [
        "Use machine learning to validate signal quality features in the 0050 vs TW50 event dataset.",
        "Recommended input: v1.1 event dataset, because it is closer to the original candidate signal pool.",
        "good_signal_cost002 = 1 if pnl_twd - 0.02 > 0. Three-class label is strong / weak / failed.",
        "Exclude post-trade columns such as exit_reason, MFE, MAE, exit price, holding time, and pnl-derived features.",
        "Use time-based split. Do not use random split for financial event validation.",
        "Present this as AI-assisted validation, not as an AI trading model."
    ]
})

# ============================================================
# 11. Export Excel
# ============================================================

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    readme_df.to_excel(writer, sheet_name="README", index=False)
    data_check.to_excel(writer, sheet_name="Data_Check", index=False)
    model_df.to_excel(writer, sheet_name="Model_Dataset", index=False)

    label_distribution.to_excel(writer, sheet_name="Label_3Class_Distribution", index=False)
    binary_label_distribution.to_excel(writer, sheet_name="Label_Binary_Distribution", index=False)

    overall_perf.to_excel(writer, sheet_name="Overall_Performance", index=False)
    perf_by_split.to_excel(writer, sheet_name="Performance_By_Split", index=False)
    perf_by_quality.to_excel(writer, sheet_name="Performance_By_Label", index=False)
    quality_by_session.to_excel(writer, sheet_name="Label_By_Session", index=False)

    pd.DataFrame({"feature": numeric_features, "type": "numeric"}).to_excel(writer, sheet_name="Numeric_Features", index=False)
    pd.DataFrame({"feature": categorical_features, "type": "categorical"}).to_excel(writer, sheet_name="Categorical_Features", index=False)

    metrics_df.to_excel(writer, sheet_name="Model_Metrics", index=False)

    for name, fi in feature_importance_tables.items():
        fi.to_excel(writer, sheet_name=("FI_" + name)[:31], index=False)

    for name, perm in permutation_tables.items():
        perm.to_excel(writer, sheet_name=("Permutation_" + name)[:31], index=False)

    shap_summary.to_excel(writer, sheet_name="SHAP_Optional", index=False)

    for name, bucket_perf in score_tables.items():
        bucket_perf.to_excel(writer, sheet_name=("Score_Buckets_" + name)[:31], index=False)

    conclusion_df.to_excel(writer, sheet_name="AI_Validation_Conclusion", index=False)

print("\nDone. Exported:", OUTPUT_FILE)
files.download(OUTPUT_FILE)
