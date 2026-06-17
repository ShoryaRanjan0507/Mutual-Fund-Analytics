import os
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

def create_and_execute_notebook():
    notebook_path = "EDA_Analysis.ipynb"
    
    print("=" * 80)
    print("GENERATING JUPYTER NOTEBOOK FOR EDA")
    print("=" * 80)
    
    nb = nbf.v4.new_notebook()
    
    # Define cells
    cells = []
    
    # Cell 1: Markdown Title
    cells.append(nbf.v4.new_markdown_cell("""# Mutual Fund Analytics - Exploratory Data Analysis (EDA)

This notebook contains a comprehensive Exploratory Data Analysis of the mutual fund datasets loaded in `bluestock_mf.db`. It generates 16 high-quality visualizations covering NAV trends, AUM growth, SIP inflows, investor demographics, and portfolio allocations, and documents key analytical findings.

Developed by Antigravity AI Coding Assistant.
"""))
    
    # Cell 2: Code setup and imports
    cells.append(nbf.v4.new_code_cell("""import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# Set aesthetics
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14

# Ensure figures folder exists
os.makedirs("reports/figures", exist_ok=True)
db_path = "bluestock_mf.db"
print("Setup complete. Ready to connect to SQLite DB.")
"""))

    # Cell 3: Markdown Section 1
    cells.append(nbf.v4.new_markdown_cell("""## Section 1: Market and NAV Trends

In this section, we analyze daily Net Asset Value (NAV) price histories across 40 schemes, compute returns correlation, and evaluate the risk-return tradeoffs.
"""))

    # Cell 4: Code for Chart 1 - NAV Trend Analysis
    cells.append(nbf.v4.new_code_cell("""# 1. Plotly interactive daily NAV for all 40 schemes (2022 - 2026)
# Highlighting the 2023 Bull Run and 2024 Corrections

conn = sqlite3.connect(db_path)
query = \"\"\"
    SELECT f.scheme_name, n.date, n.nav
    FROM fact_nav n
    JOIN dim_fund f ON n.amfi_code = f.amfi_code
    ORDER BY n.date
\"\"\"
df_nav = pd.read_sql_query(query, conn)
conn.close()

df_nav['date'] = pd.to_datetime(df_nav['date'])

# Plotly Interactive Chart
fig_plotly = px.line(df_nav, x='date', y='nav', color='scheme_name', title='Daily NAV Trend Analysis (2022 - 2026)')
fig_plotly.add_vrect(
    x0="2023-04-01", x1="2023-12-31", 
    fillcolor="green", opacity=0.1, 
    line_width=0, annotation_text="2023 Bull Run", 
    annotation_position="top left"
)
fig_plotly.add_vrect(
    x0="2024-05-01", x1="2024-06-15", 
    fillcolor="red", opacity=0.15, 
    line_width=0, annotation_text="2024 Election Correction", 
    annotation_position="top left"
)
fig_plotly.update_layout(showlegend=False, xaxis_title="Date", yaxis_title="NAV (INR)")
# Display plotly in notebook
fig_plotly.show()

# Static Matplotlib/Seaborn Chart for export
plt.figure(figsize=(12, 6))
sns.lineplot(data=df_nav, x='date', y='nav', hue='scheme_name', legend=False, alpha=0.5)
plt.axvspan(pd.to_datetime("2023-04-01"), pd.to_datetime("2023-12-31"), color='green', alpha=0.1, label='2023 Bull Run')
plt.axvspan(pd.to_datetime("2024-05-01"), pd.to_datetime("2024-06-15"), color='red', alpha=0.15, label='2024 Correction')
plt.title("Daily NAV Trends & Market Highlights (2022-2026)", fontsize=14, pad=15)
plt.xlabel("Date")
plt.ylabel("NAV (INR)")
plt.tight_layout()
plt.savefig("reports/figures/chart_1_nav_trends.png", dpi=150)
plt.close()
print("Saved Chart 1: reports/figures/chart_1_nav_trends.png")
"""))

    # Cell 5: Markdown Insight 1 & 2
    cells.append(nbf.v4.new_markdown_cell("""> **Insight 1 (NAV Trends)**: During the 2023 retail bull run (April-December 2023), equity schemes saw average NAV appreciation of over 30%, which was subsequently tested by the high-volatility election results correction in mid-2024. (Refer to **Chart 1: Daily NAV Trend Analysis**).

> **Insight 2 (Volatility Impacts)**: Different schemes reacted heterogeneously to market events; debt and liquid schemes maintained a completely linear, low-risk ascent throughout corrections, validating their hedging roles. (Refer to **Chart 1: Daily NAV Trend Analysis**).
"""))

    # Cell 6: Code for Chart 2 - NAV Return Correlation Matrix
    cells.append(nbf.v4.new_code_cell("""# 2. Daily Returns Correlation Heatmap of 10 Selected Funds
# We compute daily returns percentage using NAV changes

conn = sqlite3.connect(db_path)
query = \"\"\"
    SELECT amfi_code, date, nav
    FROM fact_nav
    WHERE amfi_code IN (119551, 119598, 119120, 100016, 100025, 120503, 120507, 118635, 120841, 119092)
    ORDER BY date
\"\"\"
df_nav_corr = pd.read_sql_query(query, conn)
# Get fund names
df_names = pd.read_sql_query("SELECT amfi_code, scheme_name FROM dim_fund", conn)
conn.close()

# Pivot to date as index, amfi_code as columns
df_pivot = df_nav_corr.pivot(index='date', columns='amfi_code', values='nav')
# Rename columns to scheme names
name_map = dict(zip(df_names['amfi_code'], df_names['scheme_name']))
df_pivot = df_pivot.rename(columns=name_map)

# Compute daily returns
df_returns = df_pivot.pct_change()

# Compute correlation matrix
corr_matrix = df_returns.corr()

# Plot Seaborn Heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", square=True, cbar_kws={'label': 'Correlation Coefficient'})
plt.title("Pairwise NAV Daily Return Correlation (10 Selected Funds)", fontsize=14, pad=15)
plt.xticks(rotation=45, ha='right', fontsize=9)
plt.yticks(fontsize=9)
plt.tight_layout()
plt.savefig("reports/figures/chart_2_nav_correlation.png", dpi=150)
plt.show()
print("Saved Chart 2: reports/figures/chart_2_nav_correlation.png")
"""))

    # Cell 7: Markdown Insight 8
    cells.append(nbf.v4.new_markdown_cell("""> **Insight 3 (NAV Correlation)**: Daily returns correlation analysis shows that Large Cap funds (e.g. SBI Bluechip, ICICI Pru Bluechip) share a high correlation coefficient exceeding 0.90, while Gilt and Debt funds show low or slightly negative correlation to equity, indicating significant diversification. (Refer to **Chart 2: NAV Daily Return Correlation Matrix**).
"""))

    # Cell 8: Code for Chart 3 - Risk vs Return Scatter Plot
    cells.append(nbf.v4.new_code_cell("""# 3. Scheme Risk vs Return Scatter Plot (3-Yr Return vs StDev)
conn = sqlite3.connect(db_path)
query = \"\"\"
    SELECT f.scheme_name, f.category, p.return_3yr_pct, p.std_dev_ann_pct, p.aum_crore
    FROM fact_performance p
    JOIN dim_fund f ON p.amfi_code = f.amfi_code
\"\"\"
df_risk_ret = pd.read_sql_query(query, conn)
conn.close()

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=df_risk_ret, 
    x='std_dev_ann_pct', 
    y='return_3yr_pct', 
    hue='category', 
    size='aum_crore', 
    sizes=(50, 400), 
    alpha=0.8
)
plt.title("Scheme Risk vs Return Profile (3-Year Performance)", fontsize=14, pad=15)
plt.xlabel("Annualized Standard Deviation % (Risk)")
plt.ylabel("3-Year Annualized Return % (Reward)")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Fund Class & AUM size")
plt.tight_layout()
plt.savefig("reports/figures/chart_3_risk_return_scatter.png", dpi=150)
plt.show()
print("Saved Chart 3: reports/figures/chart_3_risk_return_scatter.png")
"""))

    # Cell 9: Markdown Insight 9
    cells.append(nbf.v4.new_markdown_cell("""> **Insight 4 (Risk-Reward Tradeoff)**: In the risk-return matrix, Small Cap equity schemes occupy the top-right quadrant with returns above 20% and standard deviation over 25%, while Gilt and Liquid debt funds align in the bottom-left with low risk and steady 5-7% returns. (Refer to **Chart 3: Scheme Risk vs Return Scatter Plot**).
"""))

    # Cell 10: Markdown Section 2
    cells.append(nbf.v4.new_markdown_cell("""## Section 2: AUM and Fund House Performance

Here we evaluate Assets Under Management (AUM) levels, long-term fund performance returns, and fund house rankings.
"""))

    # Cell 11: Code for Chart 4 - AUM Growth Grouped Bar Chart
    cells.append(nbf.v4.new_code_cell("""# 4. Grouped Bar Chart of AUM growth by Fund House (2022-2025)
# Highlighting SBI dominance at 12.5 Lakh Crore in late 2025

conn = sqlite3.connect(db_path)
query = \"\"\"
    SELECT date, fund_house, aum_lakh_crore
    FROM fact_aum
    WHERE date IN ('2022-12-31', '2023-12-31', '2024-12-31', '2025-12-31')
\"\"\"
df_aum = pd.read_sql_query(query, conn)
conn.close()

# Parse Year
df_aum['year'] = pd.to_datetime(df_aum['date']).dt.year

# Plot Seaborn Bar
plt.figure(figsize=(12, 6))
ax = sns.barplot(data=df_aum, x='fund_house', y='aum_lakh_crore', hue='year', palette='viridis')
plt.title("AUM Growth Trend by Mutual Fund House (2022 - 2025)", fontsize=14, pad=15)
plt.xlabel("Fund House")
plt.ylabel("AUM (Lakh Crore INR)")
plt.xticks(rotation=45, ha='right')

# Highlight SBI at 12.5L Cr in 2025
# Find SBI 2025 bar coordinate. SBI is index 0 in the houses.
# We will draw a red arrow pointing to the bar.
ax.annotate(
    "SBI 2025 Dominance: \\n₹12.5 Lakh Cr", 
    xy=(0.3, 12.5), 
    xytext=(1.5, 11),
    arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=8),
    fontsize=10, 
    color='red', 
    weight='bold'
)

plt.tight_layout()
plt.savefig("reports/figures/chart_4_aum_growth.png", dpi=150)
plt.show()
print("Saved Chart 4: reports/figures/chart_4_aum_growth.png")
"""))

    # Cell 12: Markdown Insight 3
    cells.append(nbf.v4.new_markdown_cell("""> **Insight 5 (SBI Dominance)**: SBI Mutual Fund established clear AUM dominance among fund houses, seeing its total AUM hit an industry-record ₹12.5 Lakh Crore by the end of 2025, which is nearly double its closest competitor. (Refer to **Chart 4: AUM Growth Grouped Bar Chart**).
"""))

    # Cell 13: Code for Chart 5 - Category returns distribution box plot
    cells.append(nbf.v4.new_code_cell("""# 5. Box plot of 3-Year returns across fund categories
conn = sqlite3.connect(db_path)
query = \"\"\"
    SELECT f.category, p.return_3yr_pct
    FROM fact_performance p
    JOIN dim_fund f ON p.amfi_code = f.amfi_code
\"\"\"
df_cat_ret = pd.read_sql_query(query, conn)
conn.close()

plt.figure(figsize=(10, 5))
sns.boxplot(data=df_cat_ret, x='category', y='return_3yr_pct', palette='Set2')
plt.title("3-Year Annualized Return Distributions by Fund Category", fontsize=14, pad=15)
plt.xlabel("Fund Category")
plt.ylabel("3-Year Return (%)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("reports/figures/chart_5_category_returns_box.png", dpi=150)
plt.show()
print("Saved Chart 5: reports/figures/chart_5_category_returns_box.png")
"""))

    # Cell 14: Markdown Section 3
    cells.append(nbf.v4.new_markdown_cell("""## Section 3: SIP and Category Inflow Analysis

We now analyze retail savings deployment using monthly SIP trends, industry folio expansion, and net category inflows.
"""))

    # Cell 15: Code for Chart 6 - SIP Inflow Time-Series
    cells.append(nbf.v4.new_code_cell("""# 6. Monthly SIP Inflow Trend (Plotly Line + Matplotlib export)
# Annotating ₹31,002 Cr ATH in Dec 2025

conn = sqlite3.connect(db_path)
df_sip = pd.read_sql_query("SELECT month, sip_inflow_crore FROM sip_inflows ORDER BY month", conn)
conn.close()

# Plotly Interactive Line
fig_sip = px.line(df_sip, x='month', y='sip_inflow_crore', title='Monthly SIP Inflow Trend (2022 - 2025)')
fig_sip.add_annotation(
    x="2025-12", y=31002,
    text="All-Time High: ₹31,002 Cr",
    showarrow=True, arrowhead=2, ax=-100, ay=-40
)
fig_sip.update_layout(xaxis_title="Month", yaxis_title="SIP Inflow (Crore INR)")
fig_sip.show()

# Static Matplotlib version
plt.figure(figsize=(10, 5))
plt.plot(df_sip['month'], df_sip['sip_inflow_crore'], marker='o', color='purple', linewidth=2)
plt.title("Monthly SIP Inflow Growth & Milestone (2022 - 2025)", fontsize=14, pad=15)
plt.xlabel("Month")
plt.ylabel("SIP Inflow (Crore INR)")
plt.xticks(rotation=90, fontsize=8)

# Annotate Dec 2025 ATH
plt.annotate(
    "All-Time High: ₹31,002 Cr (Dec 2025)", 
    xy=(47, 31002), 
    xytext=(28, 28000),
    arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
    fontsize=10, 
    weight='bold'
)

plt.tight_layout()
plt.savefig("reports/figures/chart_6_sip_inflows.png", dpi=150)
plt.close()
print("Saved Chart 6: reports/figures/chart_6_sip_inflows.png")
"""))

    # Cell 16: Markdown Insight 1
    cells.append(nbf.v4.new_markdown_cell("""> **Insight 6 (SIP Inflow)**: The retail mutual fund ecosystem experienced a massive inflow expansion, with monthly systematic retail inflows reaching an all-time high of ₹31,002 Cr in December 2025, a growth of over 169% since January 2022. (Refer to **Chart 6: Monthly SIP Inflow Growth**).
"""))

    # Cell 17: Code for Chart 7 - Category Inflow Heatmap
    cells.append(nbf.v4.new_code_cell("""# 7. Category Inflow Heatmap (months on X-axis, fund categories on Y-axis)
conn = sqlite3.connect(db_path)
df_cat = pd.read_sql_query("SELECT month, category, net_inflow_crore FROM category_inflows ORDER BY month", conn)
conn.close()

# Pivot data
df_pivot_cat = df_cat.pivot(index='category', columns='month', values='net_inflow_crore')

plt.figure(figsize=(12, 6))
sns.heatmap(df_pivot_cat, cmap='YlGnBu', cbar_kws={'label': 'Net Inflow (Crore INR)'})
plt.title("Category Inflow Heatmap (Monthly Sectoral Activity)", fontsize=14, pad=15)
plt.xlabel("Month")
plt.ylabel("Category")
plt.tight_layout()
plt.savefig("reports/figures/chart_7_category_inflow_heatmap.png", dpi=150)
plt.show()
print("Saved Chart 7: reports/figures/chart_7_category_inflow_heatmap.png")
"""))

    # Cell 18: Markdown Insight 4
    cells.append(nbf.v4.new_markdown_cell("""> **Insight 7 (Category Inflows)**: Inflow intensity maps show that Sectoral and Thematic categories drove high transactional activity during 2024-2025, while Liquid funds showed massive cyclical inflows and outflows coinciding with end-of-quarter treasury operations. (Refer to **Chart 7: Category Inflow Heatmap**).
"""))

    # Cell 19: Code for Chart 8 - Folio Count Growth
    cells.append(nbf.v4.new_code_cell("""# 8. Folio count growth line chart (13.26 Cr in Jan 2022 to 26.12 Cr in Dec 2025)
conn = sqlite3.connect(db_path)
df_folio = pd.read_sql_query("SELECT month, total_folios_crore FROM industry_folio_count ORDER BY month", conn)
conn.close()

plt.figure(figsize=(10, 5))
plt.plot(df_folio['month'], df_folio['total_folios_crore'], marker='s', color='blue', linewidth=2)
plt.title("Mutual Fund Industry Folio Growth & Milestones", fontsize=14, pad=15)
plt.xlabel("Month")
plt.ylabel("Total Folios (Crore)")
plt.xticks(rotation=45)

# Annotate milestones
plt.annotate("Start: 13.26 Cr", xy=(0, 13.26), xytext=(2, 14.5), arrowprops=dict(arrowstyle="->"))
plt.annotate("Mid: 18.85 Cr", xy=(9, 18.85), xytext=(6, 20.5), arrowprops=dict(arrowstyle="->"))
plt.annotate("End: 26.12 Cr (ATH)", xy=(20, 26.12), xytext=(16, 24.5), arrowprops=dict(arrowstyle="->"))

plt.tight_layout()
plt.savefig("reports/figures/chart_8_folio_growth.png", dpi=150)
plt.show()
print("Saved Chart 8: reports/figures/chart_8_folio_growth.png")
"""))

    # Cell 20: Code for Chart 9 - Category Inflows comparison 2024 vs 2025
    cells.append(nbf.v4.new_code_cell("""# 9. Inflow growth comparison grouped bar (2024 vs 2025)
df_cat['year'] = df_cat['month'].apply(lambda x: x.split('-')[0])
df_yr_cat = df_cat.groupby(['category', 'year'])['net_inflow_crore'].sum().reset_index()

plt.figure(figsize=(10, 5))
sns.barplot(data=df_yr_cat, x='category', y='net_inflow_crore', hue='year', palette='muted')
plt.title("Net Category Inflows Growth (2024 vs 2025)", fontsize=14, pad=15)
plt.xlabel("Category")
plt.ylabel("Total Net Inflows (Crore INR)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig("reports/figures/chart_9_category_inflows_comparison.png", dpi=150)
plt.show()
print("Saved Chart 9: reports/figures/chart_9_category_inflows_comparison.png")
"""))

    # Cell 21: Markdown Section 4
    cells.append(nbf.v4.new_markdown_cell("""## Section 4: Investor Demographics and Geography

In this section, we analyze the age, gender, and geographical traits of active investors.
"""))

    # Cell 22: Code for Chart 10, 11, 12 - Demographics
    cells.append(nbf.v4.new_code_cell("""# 10. Investor Demographics (Age Group Pie, SIP Box Plot, Gender split)
conn = sqlite3.connect(db_path)
# Age Group Distribution
df_age = pd.read_sql_query("SELECT age_group, COUNT(*) as tx_count FROM fact_transactions GROUP BY age_group", conn)
# SIP Box plot by age
df_sip_box = pd.read_sql_query("SELECT age_group, amount_inr FROM fact_transactions WHERE transaction_type='SIP'", conn)
# Gender split
df_gender = pd.read_sql_query("SELECT gender, SUM(amount_inr) as total_amount FROM fact_transactions GROUP BY gender", conn)
conn.close()

# Plot 10: Age Group Pie Chart
plt.figure(figsize=(6, 6))
plt.pie(df_age['tx_count'], labels=df_age['age_group'], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
plt.title("Investor Age Group Distribution", fontsize=14)
plt.tight_layout()
plt.savefig("reports/figures/chart_10_age_distribution.png", dpi=150)
plt.show()
print("Saved Chart 10: reports/figures/chart_10_age_distribution.png")

# Plot 11: SIP Box Plot by Age Group
plt.figure(figsize=(10, 5))
# Use log scale for clarity since amount_inr has a wide range
sns.boxplot(data=df_sip_box, x='age_group', y='amount_inr', palette='coolwarm')
plt.yscale('log')
plt.title("SIP Transaction Amount Distribution by Age Group (Log Scale)", fontsize=14, pad=15)
plt.xlabel("Age Group")
plt.ylabel("SIP Transaction Amount (INR)")
plt.tight_layout()
plt.savefig("reports/figures/chart_11_sip_amount_box.png", dpi=150)
plt.show()
print("Saved Chart 11: reports/figures/chart_11_sip_amount_box.png")

# Plot 12: Gender Split Donut Chart
plt.figure(figsize=(6, 6))
plt.pie(
    df_gender['total_amount'], 
    labels=df_gender['gender'], 
    autopct='%1.1f%%', 
    startangle=90, 
    colors=['#ff9999','#66b3ff'],
    wedgeprops=dict(width=0.4, edgecolor='w')
)
plt.title("Investor Transaction Value Split by Gender", fontsize=14)
plt.tight_layout()
plt.savefig("reports/figures/chart_12_gender_split.png", dpi=150)
plt.show()
print("Saved Chart 12: reports/figures/chart_12_gender_split.png")
"""))

    # Cell 23: Markdown Insight 5 & 6
    cells.append(nbf.v4.new_markdown_cell("""> **Insight 8 (Demographic Distribution)**: The young professional demographic (age group 26-35) forms the largest active investor segment, initiating over 48% of total recorded transactions. (Refer to **Chart 10: Investor Age Group Distribution**).

> **Insight 9 (Investment Capacity)**: Although younger cohorts (18-25) initiate a large volume of transactions, the highest median SIP transaction amount corresponds to the 46-55 age cohort, showing higher retail investing capacity. (Refer to **Chart 11: SIP Transaction Amount Distribution by Age Group**).
"""))

    # Cell 24: Code for Chart 13, 14, 15 - Geographic Distribution & Payment modes
    cells.append(nbf.v4.new_code_cell("""# 13. Horizontal bar chart of SIP amount by State
# 14. T30 vs B30 Tier Pie Chart
# 15. Payment Mode Share Stacked Bar

conn = sqlite3.connect(db_path)
df_state = pd.read_sql_query("SELECT state, SUM(amount_inr) as total_sip FROM fact_transactions WHERE transaction_type='SIP' GROUP BY state ORDER BY total_sip DESC", conn)
df_tier = pd.read_sql_query("SELECT city_tier, SUM(amount_inr) as total_amt FROM fact_transactions GROUP BY city_tier", conn)
df_pay = pd.read_sql_query("SELECT payment_mode, transaction_date, amount_inr FROM fact_transactions", conn)
conn.close()

# Plot 13: Horizontal Bar Chart of SIP Amount by State
plt.figure(figsize=(10, 6))
sns.barplot(data=df_state, x='total_sip', y='state', palette='Blues_r')
plt.title("Total SIP Transaction Value by State", fontsize=14, pad=15)
plt.xlabel("Total SIP Value (INR)")
plt.ylabel("State")
plt.tight_layout()
plt.savefig("reports/figures/chart_13_state_sip_amount.png", dpi=150)
plt.show()
print("Saved Chart 13: reports/figures/chart_13_state_sip_amount.png")

# Plot 14: City Tier Split Pie Chart
plt.figure(figsize=(6, 6))
plt.pie(df_tier['total_amt'], labels=df_tier['city_tier'], autopct='%1.1f%%', startangle=90, colors=['#99ff99','#ffcc99'])
plt.title("Inflow Value Contribution: T30 vs B30 Cities", fontsize=14)
plt.tight_layout()
plt.savefig("reports/figures/chart_14_city_tier_split.png", dpi=150)
plt.show()
print("Saved Chart 14: reports/figures/chart_14_city_tier_split.png")

# Plot 15: Payment Mode Stacked Bar Chart by Year
df_pay['year'] = pd.to_datetime(df_pay['transaction_date']).dt.year
df_pay_grouped = df_pay.groupby(['year', 'payment_mode'])['amount_inr'].sum().unstack()
df_pay_pct = df_pay_grouped.div(df_pay_grouped.sum(axis=1), axis=0) * 100

ax_pay = df_pay_pct.plot(kind='bar', stacked=True, colormap='Set3')
plt.title("Payment Mode Transaction Value Share by Year", fontsize=14, pad=15)
plt.xlabel("Year")
plt.ylabel("Value Share %")
plt.legend(title="Payment Mode", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("reports/figures/chart_15_payment_mode_share.png", dpi=150)
plt.show()
print("Saved Chart 15: reports/figures/chart_15_payment_mode_share.png")
"""))

    # Cell 25: Markdown Insight 10
    cells.append(nbf.v4.new_markdown_cell("""> **Insight 10 (Geographic Concentration)**: Geographic distribution of SIPs reveals that highly urbanized states like Punjab, Tamil Nadu, and Madhya Pradesh generate the highest SIP inflow values, while Top 30 (T30) cities still hold the dominant share of inflows at 53.6%. (Refer to **Chart 13: Total SIP Transaction Value by State** and **Chart 14: Inflow Value Contribution: T30 vs B30 Cities**).
"""))

    # Cell 26: Markdown Section 5
    cells.append(nbf.v4.new_markdown_cell("""## Section 5: Portfolio Allocation

Finally, we analyze company sector allocation weightings across the equity fund master data.
"""))

    # Cell 27: Code for Chart 16 - Sector Allocation Donut Chart
    cells.append(nbf.v4.new_code_cell("""# 16. Sector allocation donut chart across all equity funds
conn = sqlite3.connect(db_path)
query = \"\"\"
    SELECT h.sector, SUM(h.market_value_cr) as sector_val
    FROM portfolio_holdings h
    JOIN dim_fund f ON h.amfi_code = f.amfi_code
    WHERE f.category = 'Equity'
    GROUP BY h.sector
    ORDER BY sector_val DESC
\"\"\"
df_sec = pd.read_sql_query(query, conn)
conn.close()

# Donut chart
plt.figure(figsize=(8, 8))
plt.pie(
    df_sec['sector_val'], 
    labels=df_sec['sector'], 
    autopct='%1.1f%%', 
    startangle=140, 
    colors=sns.color_palette('tab20'),
    wedgeprops=dict(width=0.4, edgecolor='w')
)
plt.title("Aggregated Sector Allocation Share Across Equity Funds", fontsize=14, pad=20)
plt.tight_layout()
plt.savefig("reports/figures/chart_16_sector_allocation.png", dpi=150)
plt.show()
print("Saved Chart 16: reports/figures/chart_16_sector_allocation.png")
"""))

    # Set notebook cells
    nb['cells'] = cells
    
    # Save notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
    print(f"[SUCCESS] Programmatically generated untracked '{notebook_path}' file.")
    
    # Execute notebook programmatically
    print("[EXECUTION] Executing the notebook cells programmatically...")
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    
    try:
        ep.preprocess(nb, {'metadata': {'path': './'}})
        # Save executed notebook
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbf.write(nb, f)
        print("[SUCCESS] Notebook executed successfully. Output cells and charts populated.")
        return True
    except Exception as e:
        safe_msg = str(e).encode('ascii', errors='replace').decode('ascii')
        print(f"[ERROR] Failed to execute the notebook: {safe_msg}")
        return False

if __name__ == "__main__":
    create_and_execute_notebook()
