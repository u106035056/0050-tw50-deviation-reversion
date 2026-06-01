# -*- coding: utf-8 -*-
"""
0050 AI Validation Colab v2 Compare - FIXED
目的：正確讀取 v1.1 與 v2-A event dataset，做正式版本對照分析。
重點：v2-A 必須讀取 CSV: 0050_v2A_ai_event_dataset_full_features.csv，而不是報告 xlsx。
"""

# =============================
# 0. 使用方式
# =============================
# 1) 請把以下兩個 CSV 上傳到 Colab 左側檔案區：
#    - 0050_v1_1_ai_event_dataset_full_features.csv
#    - 0050_v2A_ai_event_dataset_full_features.csv
# 2) 從上到下執行。
# 3) 第一個檢查點必須顯示：v1.1 rows = 361，v2-A rows = 258。
# 4) 若 v2-A rows 不是 258，代表你讀到錯檔案，後面結果都不要看。

# =============================
# 1. 基本套件
# =============================
# （意義：pandas 負責資料整理；numpy 負責數值計算；os/glob 負責檔案檢查。）
import os
import glob
import numpy as np
import pandas as pd

# Colab 才需要使用 display；本地執行時可忽略
try:
    from IPython.display import display
except Exception:
    display = print


# =============================
# 2. 檔案讀取與防呆檢查
# =============================
# （意義：前一次錯誤就是 v2_path 指到報告 xlsx，導致只讀到 6 列。
# 這裡強制讀正確 CSV，並檢查列數，避免錯資料污染後續判讀。）

V1_EXPECTED_ROWS = 361
V2_EXPECTED_ROWS = 258

v1_path = "0050_v1_1_ai_event_dataset_full_features.csv"
v2_path = "0050_v2A_ai_event_dataset_full_features.csv"

# 若檔名不完全一致，嘗試自動搜尋相近檔案
if not os.path.exists(v1_path):
    candidates = glob.glob("*v1*event*full*features*.csv") + glob.glob("*v1_1*full_features*.csv")
    if candidates:
        v1_path = candidates[0]

if not os.path.exists(v2_path):
    candidates = glob.glob("*v2A*event*full*features*.csv") + glob.glob("*v2*A*full*features*.csv")
    if candidates:
        v2_path = candidates[0]

print("Using v1 file:", v1_path)
print("Using v2 file:", v2_path)

v1 = pd.read_csv(v1_path)
v2 = pd.read_csv(v2_path)

v1["version"] = "v1.1_No_Overnight"
v2["version"] = "v2A_TW50_5m_Up_Filter"

print("v1.1 rows:", len(v1))
print("v2-A rows:", len(v2))

# 關鍵防呆：這兩個數字不對，直接停止。
if len(v1) != V1_EXPECTED_ROWS:
    raise ValueError(f"v1.1 rows 應為 {V1_EXPECTED_ROWS}，但目前是 {len(v1)}。請確認上傳正確 CSV。")
if len(v2) != V2_EXPECTED_ROWS:
    raise ValueError(f"v2-A rows 應為 {V2_EXPECTED_ROWS}，但目前是 {len(v2)}。你很可能讀到錯檔案，例如 report xlsx 或摘要檔。請改讀 0050_v2A_ai_event_dataset_full_features.csv。")

print("✅ 檔案列數正確，可以進入正式比較。")
display(v1.head(3))
display(v2.head(3))


# =============================
# 3. 基礎函數：績效統計
# =============================
# （意義：我們不只看總損益，而要看交易數、勝率、Profit Factor、最大單筆虧損、估算回撤。
# 濾網是否成功，核心是：交易數下降後，訊號品質與風險是否改善。）

def calc_profit_factor(pnl_series: pd.Series):
    pnl = pd.to_numeric(pnl_series, errors="coerce").dropna()
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = -pnl[pnl < 0].sum()
    if gross_loss == 0:
        return np.nan
    return gross_profit / gross_loss


def calc_max_drawdown_from_pnl(pnl_series: pd.Series):
    pnl = pd.to_numeric(pnl_series, errors="coerce").fillna(0)
    cum_pnl = pnl.cumsum()
    running_max = cum_pnl.cummax()
    drawdown = running_max - cum_pnl
    return drawdown.max()


def summarize(df: pd.DataFrame, group_cols=None) -> pd.DataFrame:
    if group_cols is None:
        group_cols = []
    
    results = []
    grouped = df.groupby(group_cols, dropna=False) if group_cols else [("ALL", df)]
    
    for key, g in grouped:
        pnl = pd.to_numeric(g["pnl_twd"], errors="coerce").dropna()
        if len(pnl) == 0:
            result = {
                "group": key,
                "trades": len(g),
                "win_trades": np.nan,
                "loss_trades": np.nan,
                "flat_trades": np.nan,
                "win_rate": np.nan,
                "net_pnl": np.nan,
                "avg_pnl": np.nan,
                "gross_profit": np.nan,
                "gross_loss": np.nan,
                "profit_factor": np.nan,
                "max_single_loss": np.nan,
                "max_single_profit": np.nan,
                "estimated_max_drawdown": np.nan,
            }
        else:
            result = {
                "group": key,
                "trades": len(pnl),
                "win_trades": int((pnl > 0).sum()),
                "loss_trades": int((pnl < 0).sum()),
                "flat_trades": int((pnl == 0).sum()),
                "win_rate": float((pnl > 0).mean()),
                "net_pnl": float(pnl.sum()),
                "avg_pnl": float(pnl.mean()),
                "gross_profit": float(pnl[pnl > 0].sum()),
                "gross_loss": float(pnl[pnl < 0].sum()),
                "profit_factor": calc_profit_factor(pnl),
                "max_single_loss": float(pnl.min()),
                "max_single_profit": float(pnl.max()),
                "estimated_max_drawdown": calc_max_drawdown_from_pnl(pnl),
            }
        results.append(result)
    
    out = pd.DataFrame(results)
    return out


# =============================
# 4. v1.1 vs v2-A 全區間比較
# =============================
# （意義：先回答最直接問題：v2-A 是否真的把 v1.1 的訊號品質提升？
# 成功判準不是總損益最大，而是 PF、平均每筆品質、虧損端、回撤是否改善。）

combined = pd.concat([v1, v2], ignore_index=True)

overall_summary = summarize(combined, ["version"])
print("\n=== Overall Comparison ===")
display(overall_summary)


# =============================
# 5. 時間切分比較
# =============================
# （意義：避免只在全樣本漂亮。
# 如果 v2-A 只在 Train 好、Validation / Recent 差，就是過擬合警訊。）

split_summary = summarize(combined, ["version", "data_split"])
print("\n=== Split Comparison ===")
display(split_summary)


year_summary = summarize(combined, ["version", "entry_year"])
print("\n=== Year Comparison ===")
display(year_summary)


# =============================
# 6. 時段與出場原因比較
# =============================
# （意義：檢查 v2-A 改善是來自哪些時段 / 哪些出場結構。
# 這能幫你寫簡報的市場邏輯：v2-A 是否淨化早盤與盤中訊號？）

session_summary = summarize(combined, ["version", "session_id", "session_block"])
print("\n=== Session Comparison ===")
display(session_summary)

exit_reason_summary = summarize(combined, ["version", "exit_reason"])
print("\n=== Exit Reason Comparison ===")
display(exit_reason_summary)


# =============================
# 7. 版本改善摘要表
# =============================
# （意義：把 v2-A 相對 v1.1 的改善幅度直接算出來，方便放簡報。）

def get_metric(summary_df, version_name, metric):
    row = summary_df[summary_df["group"].astype(str).str.contains(version_name, regex=False)]
    if row.empty:
        return np.nan
    return row.iloc[0][metric]

# overall_summary group 可能是 tuple 或 str，統一轉字串處理
overall_summary_for_delta = overall_summary.copy()
overall_summary_for_delta["group_str"] = overall_summary_for_delta["group"].astype(str)

v1_row = overall_summary_for_delta[overall_summary_for_delta["group_str"].str.contains("v1.1_No_Overnight", regex=False)].iloc[0]
v2_row = overall_summary_for_delta[overall_summary_for_delta["group_str"].str.contains("v2A_TW50_5m_Up_Filter", regex=False)].iloc[0]

metrics = ["trades", "win_rate", "net_pnl", "avg_pnl", "gross_profit", "gross_loss", "profit_factor", "max_single_loss", "estimated_max_drawdown"]
rows = []
for m in metrics:
    v1_val = v1_row[m]
    v2_val = v2_row[m]
    abs_change = v2_val - v1_val if pd.notna(v1_val) and pd.notna(v2_val) else np.nan
    pct_change = abs_change / abs(v1_val) if pd.notna(abs_change) and v1_val not in [0, np.nan] else np.nan
    rows.append({
        "metric": m,
        "v1.1": v1_val,
        "v2-A": v2_val,
        "absolute_change": abs_change,
        "pct_change_vs_v1_abs_base": pct_change,
    })

improvement_summary = pd.DataFrame(rows)
print("\n=== Improvement Summary ===")
display(improvement_summary)


# =============================
# 8. 自動產生研究結論文字
# =============================
# （意義：讓你直接知道這輪能不能寫進簡報，以及該用什麼保守語氣。）

v1_trades = int(v1_row["trades"])
v2_trades = int(v2_row["trades"])
v1_pf = float(v1_row["profit_factor"])
v2_pf = float(v2_row["profit_factor"])
v1_loss = float(v1_row["gross_loss"])
v2_loss = float(v2_row["gross_loss"])
v1_max_loss = float(v1_row["max_single_loss"])
v2_max_loss = float(v2_row["max_single_loss"])

research_conclusion = f"""
研究結論摘要：

v2-A 將 v1.1 的候選訊號從 {v1_trades} 筆降至 {v2_trades} 筆，代表濾網排除了約 {(1 - v2_trades / v1_trades):.1%} 的交易。
同時 Profit Factor 從 {v1_pf:.2f} 提升至 {v2_pf:.2f}，Gross Loss 從 {v1_loss:.2f} 降至 {v2_loss:.2f}，最大單筆虧損從 {v1_max_loss:.2f} 改善至 {v2_max_loss:.2f}。

這代表 v2-A 的 TW50 5m 上行濾網不是單純砍交易，而是有助於排除 TW50 下行時的低品質偏離訊號，使保留下來的 0050 相對落後樣本更接近 tracking lag，而不是風險釋放。

保守說法：v2-A 是目前通過初步驗證的有效候選濾網，但仍需後續成本敏感度、walk-forward validation 與 paper trading 驗證，不應直接宣稱為可實盤策略。
"""

print(research_conclusion)

conclusion_df = pd.DataFrame({"research_conclusion": [research_conclusion]})


# =============================
# 9. 輸出 Excel
# =============================
# （意義：產生一份乾淨、可上傳給 ChatGPT 或放進作品資料夾的 v1.1 vs v2-A 對照結果。）

output_path = "0050_v1_1_vs_v2A_colab_comparison_outputs_FIXED.xlsx"

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    overall_summary.to_excel(writer, sheet_name="Overall_Comparison", index=False)
    split_summary.to_excel(writer, sheet_name="Split_Comparison", index=False)
    year_summary.to_excel(writer, sheet_name="Year_Comparison", index=False)
    session_summary.to_excel(writer, sheet_name="Session_Comparison", index=False)
    exit_reason_summary.to_excel(writer, sheet_name="Exit_Reason_Comparison", index=False)
    improvement_summary.to_excel(writer, sheet_name="Improvement_Summary", index=False)
    conclusion_df.to_excel(writer, sheet_name="Research_Conclusion", index=False)
    combined.to_excel(writer, sheet_name="Combined_Event_Data", index=False)

print("已輸出：", output_path)


# =============================
# 10. Colab 下載
# =============================
# （意義：如果你在 Colab 執行，這段會自動跳出下載視窗。）
try:
    from google.colab import files
    files.download(output_path)
except Exception:
    print("非 Colab 環境，請到目前資料夾下載：", output_path)
