# Mutual Fund Analytics - Data Quality & Ingestion Report

**Execution Date:** 2026-06-19
**Environment:** Python 3.14, Pandas 3.0.2

## 1. Dataset Loading and Schema Summary

| Dataset File | Shape | Columns | Primary Key Candidate / Joins |
| :--- | :--- | :--- | :--- |
| [01_fund_master.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/01_fund_master.csv) | (40, 15) | `amfi_code, fund_house, scheme_name, category, sub_category...` | amfi_code |
| [02_nav_history.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/02_nav_history.csv) | (46000, 3) | `amfi_code, date, nav` | amfi_code |
| [03_aum_by_fund_house.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/03_aum_by_fund_house.csv) | (90, 5) | `date, fund_house, aum_lakh_crore, aum_crore, num_schemes` | date/month |
| [04_monthly_sip_inflows.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/04_monthly_sip_inflows.csv) | (48, 6) | `month, sip_inflow_crore, active_sip_accounts_crore, new_sip_accounts_lakh, sip_aum_lakh_crore...` | date/month |
| [05_category_inflows.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/05_category_inflows.csv) | (144, 3) | `month, category, net_inflow_crore` | date/month |
| [06_industry_folio_count.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/06_industry_folio_count.csv) | (21, 6) | `month, total_folios_crore, equity_folios_crore, debt_folios_crore, hybrid_folios_crore...` | date/month |
| [07_scheme_performance.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/07_scheme_performance.csv) | (40, 19) | `amfi_code, scheme_name, fund_house, category, plan...` | amfi_code |
| [08_investor_transactions.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/08_investor_transactions.csv) | (32778, 13) | `investor_id, transaction_date, amfi_code, transaction_type, amount_inr...` | amfi_code |
| [09_portfolio_holdings.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/09_portfolio_holdings.csv) | (322, 8) | `amfi_code, stock_symbol, stock_name, sector, weight_pct...` | amfi_code |
| [10_benchmark_indices.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/10_benchmark_indices.csv) | (8050, 3) | `date, index_name, close_value` | date/month |

## 2. Dataset Anomalies and Data Quality Observations

- **Anomaly 1:** **04_monthly_sip_inflows.csv**: Column `yoy_growth_pct` contains 12 missing values (25.0%). This is expected because YoY growth cannot be calculated for the first 12 months (Jan 2022 - Dec 2022) without 2021 historical data.
- **Anomaly 2:** **08_investor_transactions.csv**: Found 880 SIP transactions where the `amount_inr` is less than the scheme's `min_sip_amount` (500 INR). Minimum amount found is 400 INR.

## 3. Referential Integrity Validation (AMFI Codes)

- Unique AMFI codes in `01_fund_master.csv`: **40**
- Unique AMFI codes in `02_nav_history.csv`: **40**

> [!NOTE]
> **Validation Result:** SUCCESS: Every AMFI scheme code in the fund master exists in the NAV history dataset! Referential integrity is 100% intact.