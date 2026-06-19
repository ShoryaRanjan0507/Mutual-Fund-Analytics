"""
Mutual Fund Analytics - Performance & Risk Analytics Jupyter Notebook Generator

This module programmatically constructs and executes the Performance_Analytics.ipynb Jupyter notebook,
generating CAGR metrics, Sharpe/Sortino ratios, Alpha/Beta regressions, and max drawdowns.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from scipy.stats import linregress
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

def create_and_run_analytics():
    """
    Computes performance scorecard and Alpha/Beta values, saves them as CSV deliverables,
    builds the Performance_Analytics.ipynb notebook, and runs it programmatically.
    """
    db_path = "bluestock_mf.db"
    notebook_path = "Performance_Analytics.ipynb"
    
    print("=" * 80)
    print("GENERATING JUPYTER NOTEBOOK FOR PERFORMANCE ANALYTICS")
    print("=" * 80)
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file '{db_path}' not found!")
        return False
        
    # 1. Connect to SQLite and load data for pre-calculations
    conn = sqlite3.connect(db_path)
    df_nav = pd.read_sql_query("SELECT amfi_code, date, nav FROM fact_nav ORDER BY amfi_code, date", conn)
    df_fund = pd.read_sql_query("SELECT amfi_code, scheme_name, fund_house, category, plan, expense_ratio_pct FROM dim_fund", conn)
    df_bench = pd.read_sql_query("SELECT date, index_name, close_value FROM benchmark_indices WHERE index_name IN ('NIFTY100', 'NIFTY50') ORDER BY index_name, date", conn)
    conn.close()
    
    # Format dates
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    df_bench['date'] = pd.to_datetime(df_bench['date'])
    
    # --- Compute daily returns ---
    df_nav = df_nav.sort_values(by=['amfi_code', 'date'])
    df_nav['daily_return'] = df_nav.groupby('amfi_code')['nav'].pct_change()
    
    # --- Compute CAGR (1yr, 3yr, 5yr) ---
    end_date = df_nav['date'].max()
    start_1yr = end_date - pd.DateOffset(years=1)
    start_3yr = end_date - pd.DateOffset(years=3)
    
    cagr_data = []
    for amfi, grp in df_nav.groupby('amfi_code'):
        grp = grp.set_index('date')
        nav_end = grp.loc[end_date, 'nav']
        
        # 1-Year CAGR
        try:
            nav_1yr = grp.loc[grp.index.asof(start_1yr), 'nav']
            cagr_1 = (nav_end / nav_1yr) ** 1.0 - 1.0
        except Exception:
            cagr_1 = np.nan
            
        # 3-Year CAGR
        try:
            nav_3yr = grp.loc[grp.index.asof(start_3yr), 'nav']
            cagr_3 = (nav_end / nav_3yr) ** (1.0 / 3.0) - 1.0
        except Exception:
            cagr_3 = np.nan
            
        # 5-Year CAGR (Use maximum history)
        try:
            min_date = grp.index.min()
            actual_span_years = (end_date - min_date).days / 365.25
            nav_start_max = grp.loc[min_date, 'nav']
            cagr_5 = (nav_end / nav_start_max) ** (1.0 / actual_span_years) - 1.0
        except Exception:
            cagr_5 = np.nan
            
        cagr_data.append({
            'amfi_code': amfi,
            'cagr_1yr': cagr_1,
            'cagr_3yr': cagr_3,
            'cagr_5yr_max': cagr_5
        })
    df_cagr = pd.DataFrame(cagr_data)
    
    # --- Sharpe and Sortino Ratios ---
    risk_free_annual = 0.065
    ratios_data = []
    for amfi, grp in df_nav.groupby('amfi_code'):
        returns = grp['daily_return'].dropna()
        if returns.empty:
            ratios_data.append({'amfi_code': amfi, 'sharpe_ratio': np.nan, 'sortino_ratio': np.nan})
            continue
            
        mean_ret = returns.mean()
        std_ret = returns.std()
        ann_return = mean_ret * 252
        ann_vol = std_ret * np.sqrt(252)
        sharpe = (ann_return - risk_free_annual) / ann_vol if ann_vol > 0 else np.nan
        
        downside_returns = returns[returns < 0]
        if not downside_returns.empty:
            downside_vol = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(252)
            sortino = (ann_return - risk_free_annual) / downside_vol if downside_vol > 0 else np.nan
        else:
            sortino = np.nan
            
        ratios_data.append({
            'amfi_code': amfi,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino
        })
    df_ratios = pd.DataFrame(ratios_data)
    
    # --- Alpha and Beta against NIFTY100 ---
    df_nifty = df_bench[df_bench['index_name'] == 'NIFTY100'].copy()
    df_nifty['nifty_return'] = df_nifty['close_value'].pct_change()
    df_nifty_clean = df_nifty[['date', 'nifty_return']].dropna()
    
    ab_data = []
    for amfi, grp in df_nav.groupby('amfi_code'):
        merged = pd.merge(grp[['date', 'daily_return']], df_nifty_clean, on='date', how='inner').dropna()
        if len(merged) < 30:
            ab_data.append({'amfi_code': amfi, 'alpha': np.nan, 'beta': np.nan})
            continue
            
        slope, intercept, r_val, p_val, std_err = linregress(merged['nifty_return'], merged['daily_return'])
        alpha = intercept * 252
        ab_data.append({
            'amfi_code': amfi,
            'alpha': alpha,
            'beta': slope
        })
    df_ab = pd.DataFrame(ab_data)
    
    # Save alpha_beta.csv
    df_ab_export = pd.merge(df_fund[['amfi_code', 'scheme_name']], df_ab, on='amfi_code')
    df_ab_export.to_csv("alpha_beta.csv", index=False)
    print("  -> Saved alpha_beta.csv")
    
    # --- Maximum Drawdown & Worst Period ---
    mdd_data = []
    for amfi, grp in df_nav.groupby('amfi_code'):
        grp = grp.sort_values(by='date').copy().reset_index(drop=True)
        grp['running_max'] = grp['nav'].cummax()
        grp['drawdown'] = grp['nav'] / grp['running_max'] - 1.0
        
        mdd = grp['drawdown'].min()
        trough_idx = grp['drawdown'].idxmin()
        trough_row = grp.loc[trough_idx]
        trough_date = trough_row['date']
        
        sub_grp = grp.loc[:trough_idx]
        peak_row = sub_grp[sub_grp['nav'] == sub_grp['running_max']].iloc[-1]
        peak_date = peak_row['date']
        
        post_trough = grp.loc[trough_idx:]
        recovery_rows = post_trough[post_trough['nav'] >= peak_row['nav']]
        recovery_date = recovery_rows.iloc[0]['date'].strftime('%Y-%m-%d') if not recovery_rows.empty else "Unrecovered"
            
        mdd_data.append({
            'amfi_code': amfi,
            'max_drawdown': mdd,
            'worst_drawdown_peak': peak_date.strftime('%Y-%m-%d'),
            'worst_drawdown_trough': trough_date.strftime('%Y-%m-%d'),
            'worst_drawdown_recovery': recovery_date
        })
    df_mdd = pd.DataFrame(mdd_data)
    
    # --- Fund Scorecard (0 - 100) ---
    df_metrics = df_fund.copy()
    df_metrics = pd.merge(df_metrics, df_cagr, on='amfi_code')
    df_metrics = pd.merge(df_metrics, df_ratios, on='amfi_code')
    df_metrics = pd.merge(df_metrics, df_ab, on='amfi_code')
    df_metrics = pd.merge(df_metrics, df_mdd, on='amfi_code')
    
    df_metrics['rank_3yr'] = df_metrics['cagr_3yr'].rank(pct=True) * 100
    df_metrics['rank_sharpe'] = df_metrics['sharpe_ratio'].rank(pct=True) * 100
    df_metrics['rank_alpha'] = df_metrics['alpha'].rank(pct=True) * 100
    df_metrics['rank_expense'] = df_metrics['expense_ratio_pct'].rank(ascending=False, pct=True) * 100
    df_metrics['rank_mdd'] = df_metrics['max_drawdown'].rank(pct=True) * 100
    
    df_metrics['composite_score'] = (
        0.30 * df_metrics['rank_3yr'] +
        0.25 * df_metrics['rank_sharpe'] +
        0.20 * df_metrics['rank_alpha'] +
        0.15 * df_metrics['rank_expense'] +
        0.10 * df_metrics['rank_mdd']
    )
    
    df_metrics = df_metrics.sort_values(by='composite_score', ascending=False).reset_index(drop=True)
    df_metrics['rank_overall'] = df_metrics.index + 1
    
    df_scorecard_cols = [
        'rank_overall', 'amfi_code', 'scheme_name', 'fund_house', 'category', 'plan',
        'cagr_1yr', 'cagr_3yr', 'cagr_5yr_max', 'sharpe_ratio', 'sortino_ratio', 'alpha', 'beta', 'max_drawdown',
        'expense_ratio_pct', 'composite_score', 'worst_drawdown_peak', 'worst_drawdown_trough', 'worst_drawdown_recovery'
    ]
    df_scorecard = df_metrics[df_scorecard_cols].copy()
    df_scorecard.to_csv("fund_scorecard.csv", index=False)
    print("  -> Saved fund_scorecard.csv")
    
    # 2. Programmatically generate the Jupyter Notebook
    nb = nbf.v4.new_notebook()
    cells = []
    
    cells.append(nbf.v4.new_markdown_cell("""# Mutual Fund Analytics - Performance & Risk Analytics

This notebook contains mathematical formulations, CAGR computations, Sharpe & Sortino ratios, OLS regressions for Alpha/Beta, Maximum Drawdown calculations, and a composite Fund Scorecard ranking.

Developed by Antigravity AI Coding Assistant.
"""))

    cells.append(nbf.v4.new_code_cell("""import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress

sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11

db_path = "bluestock_mf.db"
"""))

    cells.append(nbf.v4.new_markdown_cell("""## 1. Daily Returns Distribution Validation"""))
    cells.append(nbf.v4.new_code_cell("""conn = sqlite3.connect(db_path)
df_nav = pd.read_sql_query("SELECT amfi_code, date, nav FROM fact_nav ORDER BY amfi_code, date", conn)
df_names = pd.read_sql_query("SELECT amfi_code, scheme_name FROM dim_fund", conn)
conn.close()

df_nav['date'] = pd.to_datetime(df_nav['date'])
df_nav = df_nav.sort_values(by=['amfi_code', 'date'])
df_nav['daily_return'] = df_nav.groupby('amfi_code')['nav'].pct_change()

name_map = dict(zip(df_names['amfi_code'], df_names['scheme_name']))
selected_amfi = [119551, 119598, 119120]

plt.figure(figsize=(10, 5))
for amfi in selected_amfi:
    subset = df_nav[df_nav['amfi_code'] == amfi].dropna()
    sns.kdeplot(subset['daily_return'], fill=True, label=name_map[amfi], alpha=0.3)
plt.xlim(-0.04, 0.04)
plt.title("Daily Return Distributions (Density Plot)", fontsize=14)
plt.xlabel("Daily Return")
plt.ylabel("Density")
plt.legend()
plt.tight_layout()
plt.savefig("reports/figures/returns_distribution.png", dpi=150)
plt.close()
print("Saved returns distribution chart.")
"""))

    cells.append(nbf.v4.new_markdown_cell("""## 2. CAGR Comparison Table"""))
    cells.append(nbf.v4.new_code_cell("""df_scorecard = pd.read_csv("fund_scorecard.csv")
print(df_scorecard[['rank_overall', 'scheme_name', 'cagr_1yr', 'cagr_3yr', 'cagr_5yr_max']].head(10).to_string(index=False))
"""))

    cells.append(nbf.v4.new_markdown_cell("""## 3. Sharpe & Sortino Ratios Ranking"""))
    cells.append(nbf.v4.new_code_cell("""print(df_scorecard[['rank_overall', 'scheme_name', 'sharpe_ratio', 'sortino_ratio']].head(10).to_string(index=False))
"""))

    cells.append(nbf.v4.new_markdown_cell("""## 4. Alpha & Beta (OLS Regressions against Nifty 100)"""))
    cells.append(nbf.v4.new_code_cell("""print(df_scorecard[['rank_overall', 'scheme_name', 'alpha', 'beta']].head(10).to_string(index=False))
"""))

    cells.append(nbf.v4.new_markdown_cell("""## 5. Maximum Drawdown & Worst Drawdown Date Ranges"""))
    cells.append(nbf.v4.new_code_cell("""print(df_scorecard[['rank_overall', 'scheme_name', 'max_drawdown', 'worst_drawdown_peak', 'worst_drawdown_trough', 'worst_drawdown_recovery']].head(10).to_string(index=False))
"""))

    cells.append(nbf.v4.new_markdown_cell("""## 6. Composite Fund Scorecard"""))
    cells.append(nbf.v4.new_code_cell("""print(df_scorecard[['rank_overall', 'scheme_name', 'category', 'composite_score']].head(10).to_string(index=False))
"""))

    cells.append(nbf.v4.new_markdown_cell("""## 7. Tracking Error & Benchmark Comparison Chart"""))
    cells.append(nbf.v4.new_code_cell("""conn = sqlite3.connect(db_path)
df_nav_full = pd.read_sql_query("SELECT amfi_code, date, nav FROM fact_nav", conn)
df_bench_full = pd.read_sql_query("SELECT date, index_name, close_value FROM benchmark_indices", conn)
conn.close()

df_nav_full['date'] = pd.to_datetime(df_nav_full['date'])
df_bench_full['date'] = pd.to_datetime(df_bench_full['date'])

top_5_amfi = df_scorecard.head(5)['amfi_code'].tolist()
top_5_names = df_scorecard.head(5)['scheme_name'].tolist()

end_dt = df_nav_full['date'].max()
start_dt = end_dt - pd.DateOffset(years=3)

df_nav_3yr = df_nav_full[(df_nav_full['date'] >= start_dt) & (df_nav_full['date'] <= end_dt)]
df_bench_3yr = df_bench_full[(df_bench_full['date'] >= start_dt) & (df_bench_full['date'] <= end_dt)]

plt.figure(figsize=(12, 7))
nifty100_daily = df_bench_full[df_bench_full['index_name'] == 'NIFTY100'].sort_values('date').copy()
nifty100_daily['ret'] = nifty100_daily['close_value'].pct_change()
nifty100_daily_clean = nifty100_daily[['date', 'ret']].dropna()

tracking_errors = {}
for amfi, name in zip(top_5_amfi, top_5_names):
    fund_data = df_nav_3yr[df_nav_3yr['amfi_code'] == amfi].sort_values('date').copy()
    if fund_data.empty:
        continue
    start_val = fund_data.iloc[0]['nav']
    fund_data['indexed_nav'] = (fund_data['nav'] / start_val) * 100.0
    plt.plot(fund_data['date'], fund_data['indexed_nav'], label=name, alpha=0.8)
    
    fund_data['ret'] = fund_data['nav'].pct_change()
    merged = pd.merge(fund_data[['date', 'ret']], nifty100_daily_clean, on='date', how='inner')
    tracking_err = (merged['ret_x'] - merged['ret_y']).std() * np.sqrt(252)
    tracking_errors[name] = tracking_err

for idx_name in ['NIFTY50', 'NIFTY100']:
    idx_data = df_bench_3yr[df_bench_3yr['index_name'] == idx_name].sort_values('date').copy()
    if idx_data.empty:
        continue
    start_val = idx_data.iloc[0]['close_value']
    idx_data['indexed_close'] = (idx_data['close_value'] / start_val) * 100.0
    plt.plot(idx_data['date'], idx_data['indexed_close'], label=f"Benchmark: {idx_name}", linewidth=2.5, linestyle='--')

plt.title("Top 5 Funds vs Benchmarks (3-Year Indexed Return - Base 100)", fontsize=14, pad=15)
plt.xlabel("Date")
plt.ylabel("Indexed Value")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("benchmark_comparison.png", dpi=150)
plt.close()
print("Saved benchmark comparison chart.")
"""))

    nb['cells'] = cells
    
    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
        
    print(f"Jupyter Notebook '{notebook_path}' written successfully.")
    
    # Run the notebook programmatically
    print("Executing Performance_Analytics.ipynb cells programmatically...")
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    try:
        ep.preprocess(nb, {'metadata': {'path': './'}})
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbf.write(nb, f)
        print("[SUCCESS] Performance_Analytics.ipynb executed successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to run Performance_Analytics.ipynb: {e}")
        return False

if __name__ == "__main__":
    create_and_run_analytics()
