
# %% [markdown]
# # 0050 vs TW50｜AI Signal Quality Validation v1
# 
# 這份 Notebook 的目的不是證明策略已可實盤，而是把 `v1.1 No Overnight` 產生的 361 筆 candidate signals 做成可重現的分析流程。
# 
# 核心問題：
# 
# > 進場當下的特徵，能不能分辨這筆 candidate signal 比較像 Strong、Weak，還是 Failed？
# 
# 流程：讀取資料 → 檢查欄位 → 分箱分析 → 時間切分 → 簡單模型 → Signal Quality Score → 匯出結果。
# 
# （背後意義：這是把「策略回測結果」升級成「可標記、可驗證、可用 AI 輔助篩選訊號品質」的研究流程。）
# %% [markdown]
# ## 0. 使用方式
# 
# 1. 先把 `0050_v1_1_ai_event_dataset_full_features.csv` 上傳到 Colab。
# 2. 從上到下執行。
# 3. 先看分箱分析，再看模型結果。
# 4. 不要只看模型準確率，要看 Top score / Bottom score 的 Profit Factor 差異。
# 
# （背後意義：模型不是用來炫技，而是檢查它能否把高品質訊號排在前面、低品質訊號排在後面。）
# %%
# === 1. 基本套件 ===
# （這些套件分別負責：資料整理 pandas、數值計算 numpy、畫圖 matplotlib、機器學習 sklearn）
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report

pd.set_option('display.max_columns', 120)
pd.set_option('display.width', 200)
# %%
# === 2. 上傳 CSV ===
# （如果你在 Colab 執行，這段會跳出上傳按鈕；請上傳完整特徵版 CSV）
try:
    from google.colab import files
    uploaded = files.upload()
    DATA_PATH = list(uploaded.keys())[0]
except Exception:
    # （如果不是在 Colab，而是在本機 / ChatGPT 環境，請把檔名放在同資料夾）
    DATA_PATH = '0050_v1_1_ai_event_dataset_full_features.csv'

print('DATA_PATH =', DATA_PATH)
# %%
# === 3. 讀取資料 ===
# （一列 = 一筆 candidate trade / event sample）
df = pd.read_csv(DATA_PATH)

# 時間欄位轉成 datetime，後續方便切年、切月份、排序。
for col in ['entry_time', 'exit_time', 'entry_date']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

print('資料筆數與欄位數:', df.shape)
display(df.head())
print('
欄位清單：')
print(df.columns.tolist())
# %%
# === 4. 資料完整性檢查 ===
# （先確認樣本數、時間範圍、label 分布是否正常，避免後面模型建立在髒資料上）
print('entry_time range:', df['entry_time'].min(), '→', df['entry_time'].max())
print('data_split distribution:')
display(df['data_split'].value_counts(dropna=False))

print('quality_label distribution:')
display(df['quality_label'].value_counts(dropna=False))

print('exit_reason distribution:')
display(df['exit_reason'].value_counts(dropna=False))

# 檢查核心特徵缺值
core_features = [
    'entry_relative_deviation', 'volume_ratio_at_entry',
    'deviation_slope_1bar', 'deviation_slope_3bar',
    'etf_return_5m', 'etf_return_15m',
    'tw50_return_5m', 'tw50_return_15m',
    'realized_vol_10bar', 'minutes_since_open', 'minutes_to_close',
    'session_id', 'signal_count_today', 'is_2025_high_prob_session'
]
missing = df[core_features].isna().sum().sort_values(ascending=False)
print('核心特徵缺值：')
display(missing)
# %% [markdown]
# ## 1. Label 設計
# 
# 這裡先做兩種 label：
# 
# 1. `target_profit`：獲利 = 1，非獲利 = 0。  
#    （用來檢查模型能否分辨「結果上是否賺錢」。）
# 
# 2. `target_strong_failed`：只保留 Strong 與 Failed，排除 Weak。  
#    （用來檢查模型能否分辨「高品質訊號」與「低品質訊號」。）
# 
# （背後意義：金融策略不要一開始就把所有樣本混成一團。Weak 樣本常常是模糊區，先排除它，有助於檢查特徵是否真的能分辨強弱。）
# %%
# === 5. 建立 label ===
# （target_profit：最直覺、最粗的 label。獲利 = 1，其他 = 0）
df['target_profit'] = (df['pnl_twd'] > 0).astype(int)

# （target_strong_failed：只用 Strong / Failed，不用 Weak。這更接近 signal quality 分類。）
strong_mask = df['quality_label'].astype(str).str.contains('Strong', na=False)
failed_mask = df['quality_label'].astype(str).str.contains('Failed', na=False)
df['target_strong_failed'] = np.nan
df.loc[strong_mask, 'target_strong_failed'] = 1
df.loc[failed_mask, 'target_strong_failed'] = 0

print('target_profit distribution:')
display(df['target_profit'].value_counts())
print('
target_strong_failed distribution（排除 Weak 後）：')
display(df['target_strong_failed'].value_counts(dropna=False))
# %% [markdown]
# ## 2. 分箱分析
# 
# 分箱分析會把連續特徵切成幾段，例如偏離幅度、成交量倍率、斜率、大盤方向，然後看每一段的勝率、Profit Factor、平均損益。
# 
# （背後意義：先用人看得懂的方式檢查規律，避免一開始就把資料丟進黑箱模型。）
# %%
# === 6. 工具函數：計算 Profit Factor 與分箱統計 ===
def profit_factor(x):
    gross_profit = x[x > 0].sum()
    gross_loss = -x[x < 0].sum()
    if gross_loss == 0:
        return np.inf if gross_profit > 0 else np.nan
    return gross_profit / gross_loss


def summarize_group(data, group_col, pnl_col='pnl_twd'):
    g = data.groupby(group_col, dropna=False)
    out = g.agg(
        n=('trade_id', 'count'),
        win_rate=('target_profit', 'mean'),
        avg_pnl=(pnl_col, 'mean'),
        median_pnl=(pnl_col, 'median'),
        total_pnl=(pnl_col, 'sum'),
        strong_ratio=('quality_label', lambda s: s.astype(str).str.contains('Strong', na=False).mean()),
        failed_ratio=('quality_label', lambda s: s.astype(str).str.contains('Failed', na=False).mean()),
        weak_ratio=('quality_label', lambda s: s.astype(str).str.contains('Weak', na=False).mean()),
        max_loss=(pnl_col, 'min'),
        max_win=(pnl_col, 'max'),
        pf=(pnl_col, profit_factor),
    ).reset_index()
    return out.sort_values('n', ascending=False)
# %%
# === 7. 建立分箱欄位 ===
# （這些 bucket 是用來看每個區間的訊號品質，而不是直接拿來當最終交易規則。）
work = df.copy()

work['rd_bucket_custom'] = pd.cut(
    work['entry_relative_deviation'],
    bins=[-np.inf, -0.6, -0.4, -0.3, -0.2],
    labels=['RD < -0.6', '-0.6 ~ -0.4', '-0.4 ~ -0.3', '-0.3 ~ -0.2']
)

work['vr_bucket_custom'] = pd.cut(
    work['volume_ratio_at_entry'],
    bins=[1.5, 2, 3, 5, np.inf],
    labels=['1.5 ~ 2', '2 ~ 3', '3 ~ 5', '> 5'],
    include_lowest=True
)

work['slope1_bucket_custom'] = pd.cut(
    work['deviation_slope_1bar'],
    bins=[-np.inf, -0.1, -0.02, 0.02, 0.1, np.inf],
    labels=['強惡化 < -0.1', '輕惡化 -0.1~-0.02', '近乎持平', '輕修復 0.02~0.1', '強修復 > 0.1']
)

work['tw50_5m_dir_custom'] = np.where(work['tw50_return_5m'] > 0, 'TW50_5m_上行', 'TW50_5m_下行或持平')

# 檢視幾個核心分箱
for col in ['data_split', 'session_block', 'rd_bucket_custom', 'vr_bucket_custom', 'slope1_bucket_custom', 'tw50_5m_dir_custom']:
    print('
====', col, '====')
    display(summarize_group(work, col))
# %%
# === 8. 分箱視覺化：各時段 Profit Factor ===
# （用來檢查不同時段的訊號品質，而不是只看整體績效。）
session_summary = summarize_group(work, 'session_block')
plot_df = session_summary.replace([np.inf, -np.inf], np.nan).dropna(subset=['pf']).sort_values('pf', ascending=False)

plt.figure(figsize=(10, 5))
plt.bar(plot_df['session_block'].astype(str), plot_df['pf'])
plt.xticks(rotation=45, ha='right')
plt.ylabel('Profit Factor')
plt.title('Profit Factor by Session Block')
plt.tight_layout()
plt.show()
# %% [markdown]
# ## 3. 簡單模型：Signal Quality Score
# 
# 這裡先用三種模型：
# 
# 1. Logistic Regression（線性基準模型）  
# 2. Decision Tree（直覺規則模型）  
# 3. Random Forest（簡單非線性組合模型）
# 
# （背後意義：不是要一開始追求最強模型，而是先檢查「這些特徵是否有可泛化的分辨力」。）
# %%
# === 9. 準備模型資料 ===
# （只使用進場當下可取得的特徵。不能把 pnl、exit_reason、MFE、MAE 當輸入，否則會資料洩漏。）
feature_cols = [
    'entry_relative_deviation',
    'volume_ratio_at_entry',
    'deviation_slope_1bar',
    'deviation_slope_3bar',
    'etf_return_5m',
    'etf_return_15m',
    'tw50_return_5m',
    'tw50_return_15m',
    'realized_vol_10bar',
    'minutes_since_open',
    'minutes_to_close',
    'session_id',
    'signal_count_today',
    'is_2025_high_prob_session',
]

# 模型目標：第一版先用 target_profit；你也可以改成 target_strong_failed。
TARGET = 'target_profit'
model_df = work.dropna(subset=feature_cols + [TARGET]).copy()

train_df = model_df[model_df['data_split'].astype(str).str.contains('Train')].copy()
val_df = model_df[model_df['data_split'].astype(str).str.contains('Validation')].copy()
recent_df = model_df[model_df['data_split'].astype(str).str.contains('Recent')].copy()

print('train/val/recent sizes:', len(train_df), len(val_df), len(recent_df))

X_train, y_train = train_df[feature_cols], train_df[TARGET].astype(int)
X_val, y_val = val_df[feature_cols], val_df[TARGET].astype(int)
X_recent, y_recent = recent_df[feature_cols], recent_df[TARGET].astype(int)
# %%
# === 10. 建立模型 pipeline ===
# （numeric 特徵先補缺值、標準化；session_id 先當數值處理，第一版保持簡單。）
numeric_features = feature_cols
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

preprocess = ColumnTransformer(
    transformers=[('num', numeric_transformer, numeric_features)],
    remainder='drop'
)

models = {
    'LogisticRegression': LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42),
    'DecisionTree_depth3': DecisionTreeClassifier(max_depth=3, min_samples_leaf=15, random_state=42, class_weight='balanced'),
    'RandomForest_depth4': RandomForestClassifier(n_estimators=300, max_depth=4, min_samples_leaf=10, random_state=42, class_weight='balanced'),
}

pipelines = {name: Pipeline(steps=[('preprocess', preprocess), ('model', model)]) for name, model in models.items()}
# %%
# === 11. 模型評估函數 ===
# （AUC 看排序能力；F1/Precision/Recall 看分類能力。但金融策略更重要的是 score 分組後的 Profit Factor。）
def evaluate_model(pipe, X, y, split_name):
    pred = pipe.predict(X)
    if hasattr(pipe, 'predict_proba'):
        proba = pipe.predict_proba(X)[:, 1]
    else:
        proba = pred
    out = {
        'split': split_name,
        'n': len(y),
        'accuracy': accuracy_score(y, pred),
        'precision': precision_score(y, pred, zero_division=0),
        'recall': recall_score(y, pred, zero_division=0),
        'f1': f1_score(y, pred, zero_division=0),
    }
    try:
        out['auc'] = roc_auc_score(y, proba)
    except Exception:
        out['auc'] = np.nan
    return out, proba

metrics = []
score_tables = []

for name, pipe in pipelines.items():
    pipe.fit(X_train, y_train)
    for split_name, X, y, part in [
        ('Train_2022_2024', X_train, y_train, train_df),
        ('Validation_2025', X_val, y_val, val_df),
        ('Recent_2026', X_recent, y_recent, recent_df),
    ]:
        m, proba = evaluate_model(pipe, X, y, split_name)
        m['model'] = name
        metrics.append(m)
        tmp = part[['trade_id', 'entry_time', 'data_split', 'pnl_twd', 'quality_label', 'target_profit']].copy()
        tmp['model'] = name
        tmp['score'] = proba
        score_tables.append(tmp)

metrics_df = pd.DataFrame(metrics)[['model','split','n','accuracy','precision','recall','f1','auc']]
display(metrics_df)
# %%
# === 12. Signal Quality Score 分組 ===
# （真正要看的是：模型分數高的交易組，是否比低分組有更好的 Profit Factor。）
all_scores = pd.concat(score_tables, ignore_index=True)

def assign_score_bucket(s):
    # 依每個 model + split 內部做分位數分組：低 30%、中 40%、高 30%。
    try:
        return pd.qcut(s, q=[0, 0.3, 0.7, 1.0], labels=['Bottom_30%', 'Middle_40%', 'Top_30%'], duplicates='drop')
    except Exception:
        return pd.Series(['Unknown'] * len(s), index=s.index)

all_scores['score_bucket'] = all_scores.groupby(['model','data_split'])['score'].transform(assign_score_bucket)

score_summary = all_scores.groupby(['model','data_split','score_bucket'], dropna=False).agg(
    n=('trade_id','count'),
    win_rate=('target_profit','mean'),
    avg_pnl=('pnl_twd','mean'),
    total_pnl=('pnl_twd','sum'),
    pf=('pnl_twd', profit_factor),
).reset_index()

# 方便閱讀：先看 RandomForest
rf_summary = score_summary[score_summary['model'] == 'RandomForest_depth4']
display(rf_summary)
# %%
# === 13. Random Forest 特徵重要性 ===
# （用來初步看模型認為哪些特徵比較有分辨力；注意這只是提示，不是絕對因果。）
rf_pipe = pipelines['RandomForest_depth4']
rf_model = rf_pipe.named_steps['model']
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

display(importance_df)

plt.figure(figsize=(9, 5))
plt.bar(importance_df['feature'], importance_df['importance'])
plt.xticks(rotation=60, ha='right')
plt.ylabel('Feature Importance')
plt.title('Random Forest Feature Importance')
plt.tight_layout()
plt.show()
# %%
# === 14. 匯出分析結果 ===
# （把分箱、模型指標、score 分組、特徵重要性輸出成 Excel，方便貼到簡報或後續整理。）
output_path = '0050_colab_ai_validation_outputs.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    summarize_group(work, 'data_split').to_excel(writer, sheet_name='By_Data_Split', index=False)
    summarize_group(work, 'session_block').to_excel(writer, sheet_name='By_Session', index=False)
    summarize_group(work, 'rd_bucket_custom').to_excel(writer, sheet_name='By_RD_Bucket', index=False)
    summarize_group(work, 'vr_bucket_custom').to_excel(writer, sheet_name='By_Volume_Bucket', index=False)
    summarize_group(work, 'slope1_bucket_custom').to_excel(writer, sheet_name='By_Slope_Bucket', index=False)
    summarize_group(work, 'tw50_5m_dir_custom').to_excel(writer, sheet_name='By_TW50_Direction', index=False)
    metrics_df.to_excel(writer, sheet_name='Model_Metrics', index=False)
    score_summary.to_excel(writer, sheet_name='Score_Buckets', index=False)
    importance_df.to_excel(writer, sheet_name='Feature_Importance', index=False)

print('已輸出：', output_path)

# Colab 下載
try:
    from google.colab import files
    files.download(output_path)
except Exception:
    pass
# %% [markdown]
# ## 4. 你應該怎麼解讀結果？
# 
# 重點不是看模型準確率有多高，而是看：
# 
# 1. Validation / Recent 的 AUC 是否高於 0.5。  
#    （代表模型排序能力是否比亂猜好。）
# 
# 2. Random Forest / Logistic 的 Top 30% score 組，Profit Factor 是否高於 Bottom 30%。  
#    （代表模型分數是否真的能排序訊號品質。）
# 
# 3. 分箱結果是否有市場邏輯。  
#    例如 TW50 上行時訊號更好，就合理；如果只出現奇怪時段或樣本太少，要保守。
# 
# 4. 如果模型在 Train 很好、Validation / Recent 很差，代表可能過度擬合。  
#    （不要拿訓練集好結果去說策略有效。）
# 
# （背後意義：AI 驗證不是追求漂亮數字，而是檢查訊號品質是否能被穩定、可解釋、樣本外不崩潰地分辨。）
# %% [markdown]
# ## 5. 下一步升級方向
# 
# 第一版跑完後，不要急著加複雜模型。下一步建議：
# 
# 1. 改善 label：從單純 pnl > 0，升級成 `回補幅度 + MAE + exit_reason` 的 Strong / Weak / Failed。  
#    （背後意義：讓模型學「訊號品質」，而不是只學最後有沒有賺一點。）
# 
# 2. 做 walk-forward validation。  
#    （背後意義：用滾動時間切分檢查規律是否穩定，降低過擬合。）
# 
# 3. 檢查 Top score 策略是否能改善 Profit Factor。  
#    （背後意義：AI 要有用，必須讓高分組比原始 v1.1 更好。）
# 
# 4. 最後才設計 v2 濾網。  
#    （背後意義：濾網要從資料證據與市場邏輯推導，不要手動亂調參。）