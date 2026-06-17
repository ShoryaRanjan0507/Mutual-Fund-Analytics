-- queries.sql
-- 10 Analytical SQL queries for Mutual Fund Analytics

-- 1. Top 5 funds by AUM
SELECT 
    f.amfi_code, 
    f.scheme_name, 
    f.fund_house, 
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month for each scheme (first 20 rows shown in output)
SELECT 
    f.scheme_name, 
    d.year, 
    d.month, 
    ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN dim_date d ON n.date = d.date
GROUP BY f.scheme_name, d.year, d.month
ORDER BY f.scheme_name, d.year, d.month
LIMIT 20;

-- 3. SIP Year-over-Year (YoY) Growth calculation by month
-- Compares monthly SIP inflows to the same calendar month of the previous year
SELECT 
    curr.month AS current_month,
    curr.sip_inflow_crore AS current_inflow_cr,
    prev.month AS previous_year_month,
    prev.sip_inflow_crore AS previous_inflow_cr,
    ROUND(((curr.sip_inflow_crore - prev.sip_inflow_crore) / prev.sip_inflow_crore) * 100, 2) AS calculated_yoy_growth_pct,
    curr.yoy_growth_pct AS reported_yoy_growth_pct
FROM sip_inflows curr
JOIN sip_inflows prev ON substr(curr.month, 6, 2) = substr(prev.month, 6, 2)
                     AND CAST(substr(curr.month, 1, 4) AS INTEGER) = CAST(substr(prev.month, 1, 4) AS INTEGER) + 1
ORDER BY curr.month;

-- 4. Transaction volume and amount by State
SELECT 
    state,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- 5. Funds with expense ratio < 1%
SELECT 
    amfi_code, 
    scheme_name, 
    plan, 
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- 6. Average return of funds by risk category
SELECT 
    f.risk_category,
    COUNT(*) AS fund_count,
    ROUND(AVG(p.return_1yr_pct), 2) AS avg_return_1yr_pct,
    ROUND(AVG(p.return_3yr_pct), 2) AS avg_return_3yr_pct,
    ROUND(AVG(p.return_5yr_pct), 2) AS avg_return_5yr_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
GROUP BY f.risk_category
ORDER BY avg_return_3yr_pct DESC;

-- 7. Top 3 stock holdings for each mutual fund scheme (by weight_pct)
WITH ranked_holdings AS (
    SELECT 
        h.amfi_code,
        f.scheme_name,
        h.stock_symbol,
        h.stock_name,
        h.sector,
        h.weight_pct,
        ROW_NUMBER() OVER (PARTITION BY h.amfi_code ORDER BY h.weight_pct DESC) as rank
    FROM portfolio_holdings h
    JOIN dim_fund f ON h.amfi_code = f.amfi_code
)
SELECT 
    amfi_code,
    scheme_name,
    stock_symbol,
    stock_name,
    sector,
    weight_pct,
    rank
FROM ranked_holdings
WHERE rank <= 3
ORDER BY amfi_code, rank;

-- 8. Total transaction amount and volume by gender and age group
SELECT 
    gender,
    age_group,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY gender, age_group
ORDER BY gender, total_amount_inr DESC;

-- 9. Funds beating their 3-year benchmark returns
SELECT 
    p.amfi_code,
    f.scheme_name,
    p.return_3yr_pct,
    p.benchmark_3yr_pct,
    ROUND(p.return_3yr_pct - p.benchmark_3yr_pct, 2) AS outperformance_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_3yr_pct > p.benchmark_3yr_pct
ORDER BY outperformance_pct DESC;

-- 10. Most preferred payment mode in each state (by transaction volume)
WITH payment_counts AS (
    SELECT 
        state,
        payment_mode,
        COUNT(*) AS transaction_count,
        ROW_NUMBER() OVER (PARTITION BY state ORDER BY COUNT(*) DESC) as rank
    FROM fact_transactions
    GROUP BY state, payment_mode
)
SELECT 
    state,
    payment_mode,
    transaction_count
FROM payment_counts
WHERE rank = 1
ORDER BY transaction_count DESC;
