import sqlite3
import pandas as pd
import json
import math

def export_data():
    """
    Reads the SQLite database, compiles all necessary data points, KPIs,
    and trends, and exports them as dashboard_data.json for the web front-end.
    """
    conn = sqlite3.connect("c:/Mutual Fund Analytics/bluestock_mf.db")
    
    def clean_val(v):
        """Replace NaN/inf with None for JSON compatibility."""
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return v

    def clean_records(records):
        """Clean a list of dicts, replacing NaN with None."""
        return [{k: clean_val(v) for k, v in r.items()} for r in records]

    def safe_to_records(df):
        """Convert DataFrame to records with NaN replaced by None."""
        return clean_records(df.where(df.notna(), None).to_dict('records'))

    data = {}

    # 1. KPI Cards
    df_txn = pd.read_sql_query("SELECT transaction_type, COUNT(*) as cnt, SUM(amount_inr) as total FROM fact_transactions GROUP BY transaction_type", conn)
    txn_dict = df_txn.set_index('transaction_type').to_dict('index')
    data['kpis'] = {
        'total_schemes': int(pd.read_sql_query("SELECT COUNT(*) as c FROM dim_fund", conn)['c'][0]),
        'total_investors': int(pd.read_sql_query("SELECT COUNT(DISTINCT investor_id) as c FROM fact_transactions", conn)['c'][0]),
        'total_transactions': int(pd.read_sql_query("SELECT COUNT(*) as c FROM fact_transactions", conn)['c'][0]),
        'sip_count': int(txn_dict.get('SIP', {}).get('cnt', 0)),
        'sip_total': float(txn_dict.get('SIP', {}).get('total', 0)),
        'lumpsum_count': int(txn_dict.get('Lumpsum', {}).get('cnt', 0)),
        'lumpsum_total': float(txn_dict.get('Lumpsum', {}).get('total', 0)),
        'redemption_count': int(txn_dict.get('Redemption', {}).get('cnt', 0)),
        'redemption_total': float(txn_dict.get('Redemption', {}).get('total', 0)),
        'total_aum_crore': float(pd.read_sql_query("SELECT SUM(aum_crore) as c FROM fact_aum WHERE date=(SELECT MAX(date) FROM fact_aum)", conn)['c'][0]),
        'total_folios_crore': float(pd.read_sql_query("SELECT total_folios_crore FROM industry_folio_count ORDER BY month DESC LIMIT 1", conn)['total_folios_crore'][0]),
        'latest_sip_inflow': float(pd.read_sql_query("SELECT sip_inflow_crore FROM sip_inflows ORDER BY month DESC LIMIT 1", conn)['sip_inflow_crore'][0]),
        'fund_houses': int(pd.read_sql_query("SELECT COUNT(DISTINCT fund_house) as c FROM dim_fund", conn)['c'][0]),
    }

    # 2. Fund Performance Table
    df_perf = pd.read_sql_query("""
        SELECT f.amfi_code, f.scheme_name, f.fund_house, f.category, f.plan, f.risk_category,
               p.return_1yr_pct, p.return_3yr_pct, p.return_5yr_pct,
               p.sharpe_ratio, p.sortino_ratio, p.alpha, p.beta,
               p.std_dev_ann_pct, p.max_drawdown_pct, p.aum_crore,
               p.morningstar_rating, p.risk_grade, p.expense_ratio_pct
        FROM dim_fund f
        JOIN fact_performance p ON f.amfi_code = p.amfi_code
        ORDER BY p.sharpe_ratio DESC
    """, conn)
    data['fund_performance'] = safe_to_records(df_perf)

    # 3. Fund Scorecard
    import csv
    scorecard = []
    with open("c:/Mutual Fund Analytics/fund_scorecard.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scorecard.append({
                'rank': int(row['rank_overall']),
                'scheme_name': row['scheme_name'],
                'fund_house': row['fund_house'],
                'category': row['category'],
                'plan': row['plan'],
                'cagr_1yr': round(float(row['cagr_1yr'])*100, 2),
                'cagr_3yr': round(float(row['cagr_3yr'])*100, 2),
                'sharpe_ratio': round(float(row['sharpe_ratio']), 2),
                'sortino_ratio': round(float(row['sortino_ratio']), 2),
                'alpha': round(float(row['alpha'])*100, 2),
                'max_drawdown': round(float(row['max_drawdown'])*100, 2),
                'expense_ratio': float(row['expense_ratio_pct']),
                'composite_score': round(float(row['composite_score']), 2),
            })
    data['scorecard'] = scorecard

    # 4. AUM by Fund House (latest)
    df_aum = pd.read_sql_query("""
        SELECT fund_house, aum_crore, num_schemes
        FROM fact_aum
        WHERE date = (SELECT MAX(date) FROM fact_aum)
        ORDER BY aum_crore DESC
    """, conn)
    data['aum_by_house'] = safe_to_records(df_aum)

    # 5. AUM Trend
    df_aum_trend = pd.read_sql_query("""
        SELECT date, SUM(aum_crore) as total_aum
        FROM fact_aum
        GROUP BY date
        ORDER BY date
    """, conn)
    data['aum_trend'] = safe_to_records(df_aum_trend)

    # 6. SIP Inflows Trend
    df_sip = pd.read_sql_query("SELECT * FROM sip_inflows ORDER BY month", conn)
    data['sip_trend'] = safe_to_records(df_sip)

    # 7. Transaction by State
    df_state = pd.read_sql_query("""
        SELECT state, COUNT(*) as count, SUM(amount_inr) as total_amount
        FROM fact_transactions
        GROUP BY state
        ORDER BY total_amount DESC
    """, conn)
    data['state_transactions'] = safe_to_records(df_state)

    # 8. Transaction Type Split
    data['txn_type_split'] = [
        {'type': 'SIP', 'count': data['kpis']['sip_count'], 'total': data['kpis']['sip_total']},
        {'type': 'Lumpsum', 'count': data['kpis']['lumpsum_count'], 'total': data['kpis']['lumpsum_total']},
        {'type': 'Redemption', 'count': data['kpis']['redemption_count'], 'total': data['kpis']['redemption_total']}
    ]

    # 9. Age Group
    df_age = pd.read_sql_query("""
        SELECT age_group, 
               COUNT(*) as count,
               AVG(amount_inr) as avg_amount,
               SUM(amount_inr) as total_amount,
               SUM(CASE WHEN transaction_type='SIP' THEN amount_inr ELSE 0 END) as sip_total,
               COUNT(CASE WHEN transaction_type='SIP' THEN 1 END) as sip_count
        FROM fact_transactions
        GROUP BY age_group
        ORDER BY age_group
    """, conn)
    data['age_group'] = safe_to_records(df_age)

    # 10. Monthly Transaction Volume
    df_monthly = pd.read_sql_query("""
        SELECT substr(transaction_date, 1, 7) as month, 
               COUNT(*) as count,
               SUM(amount_inr) as total,
               SUM(CASE WHEN transaction_type='SIP' THEN amount_inr ELSE 0 END) as sip_total,
               SUM(CASE WHEN transaction_type='Lumpsum' THEN amount_inr ELSE 0 END) as lumpsum_total,
               SUM(CASE WHEN transaction_type='Redemption' THEN amount_inr ELSE 0 END) as redemption_total
        FROM fact_transactions
        GROUP BY substr(transaction_date, 1, 7)
        ORDER BY month
    """, conn)
    data['monthly_transactions'] = safe_to_records(df_monthly)

    # 11. Category inflows
    df_cat = pd.read_sql_query("""
        SELECT month, category, net_inflow_crore
        FROM category_inflows
        ORDER BY month, category
    """, conn)
    data['category_inflows'] = safe_to_records(df_cat)

    # 12. Category inflow totals
    df_cat_total = pd.read_sql_query("""
        SELECT category, SUM(net_inflow_crore) as total
        FROM category_inflows
        GROUP BY category
        ORDER BY total DESC
    """, conn)
    data['category_inflow_totals'] = safe_to_records(df_cat_total)

    # 13. Folio count trend
    df_folio = pd.read_sql_query("SELECT * FROM industry_folio_count ORDER BY month", conn)
    data['folio_trend'] = safe_to_records(df_folio)

    # 14. Gender distribution
    df_gender = pd.read_sql_query("""
        SELECT gender, COUNT(*) as count, SUM(amount_inr) as total_amount,
               AVG(amount_inr) as avg_amount
        FROM fact_transactions
        GROUP BY gender
    """, conn)
    data['gender_distribution'] = safe_to_records(df_gender)

    # 15. City tier
    df_tier = pd.read_sql_query("""
        SELECT city_tier, COUNT(*) as count, SUM(amount_inr) as total_amount
        FROM fact_transactions
        GROUP BY city_tier
        ORDER BY city_tier
    """, conn)
    data['city_tier'] = safe_to_records(df_tier)

    # 16. VaR/CVaR report
    var_data = []
    with open("c:/Mutual Fund Analytics/var_cvar_report.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            var_data.append({
                'amfi_code': int(row['amfi_code']),
                'scheme_name': row['scheme_name'],
                'var_95': round(float(row['historical_var_95'])*100, 4),
                'cvar_95': round(float(row['historical_cvar_95'])*100, 4),
            })
    data['var_cvar'] = var_data

    # 17. NAV trend for top 5 funds (sampled for performance)
    df_nav = pd.read_sql_query("""
        SELECT n.amfi_code, f.scheme_name, n.date, n.nav
        FROM fact_nav n
        JOIN dim_fund f ON n.amfi_code = f.amfi_code
        WHERE n.amfi_code IN (148567, 120505, 120843, 100033, 119551)
        AND n.date >= '2022-01-01'
        ORDER BY n.date
    """, conn)
    # Sample every 5th day for performance
    nav_sampled = []
    for code in df_nav['amfi_code'].unique():
        subset = df_nav[df_nav['amfi_code'] == code].iloc[::5]
        for _, row in subset.iterrows():
            nav_sampled.append({
                'amfi_code': int(row['amfi_code']),
                'scheme_name': row['scheme_name'],
                'date': row['date'],
                'nav': round(float(row['nav']), 2)
            })
    data['nav_trend'] = nav_sampled

    # 18. Benchmark NIFTY50 trend (sampled)
    df_nifty = pd.read_sql_query("""
        SELECT date, close_value FROM benchmark_indices
        WHERE index_name = 'NIFTY50'
        ORDER BY date
    """, conn)
    nifty_sampled = df_nifty.iloc[::5].to_dict('records')
    data['nifty_trend'] = [{'date': r['date'], 'value': round(r['close_value'], 2)} for r in nifty_sampled]

    # 19. Risk scatter data
    risk_scatter = []
    for _, row in df_perf.iterrows():
        if row['std_dev_ann_pct'] and row['return_3yr_pct']:
            risk_scatter.append({
                'name': row['scheme_name'][:30],
                'return_3yr': round(float(row['return_3yr_pct']), 2) if row['return_3yr_pct'] else 0,
                'std_dev': round(float(row['std_dev_ann_pct']), 2) if row['std_dev_ann_pct'] else 0,
                'aum': float(row['aum_crore']) if row['aum_crore'] else 0,
                'category': row['category'],
                'risk_grade': row['risk_grade'],
            })
    data['risk_scatter'] = risk_scatter

    # 20. Payment mode
    df_pay = pd.read_sql_query("""
        SELECT payment_mode, COUNT(*) as count, SUM(amount_inr) as total
        FROM fact_transactions
        GROUP BY payment_mode
    """, conn)
    data['payment_mode'] = safe_to_records(df_pay)

    conn.close()

    # Write to JSON
    with open("c:/Mutual Fund Analytics/dashboard/dashboard_data.json", "w") as f:
        json.dump(data, f, indent=2, default=str)

    print("Dashboard data exported successfully!")
    return True

if __name__ == "__main__":
    export_data()
