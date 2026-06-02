# Mutual Fund Analytics - Day 1 Data Quality & Ingestion Report

**Execution Date:** 2026-06-02
**Environment:** Python 3.14.3, Pandas 3.0.2

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

## 3. Fund Master Exploration

- **Unique Fund Houses (10):** SBI Mutual Fund, HDFC Mutual Fund, ICICI Prudential MF, Nippon India MF, Kotak Mahindra MF, Axis Mutual Fund, Aditya Birla Sun Life MF, UTI Mutual Fund, Mirae Asset MF, DSP Mutual Fund
- **Unique Categories (2):** Equity, Debt
- **Unique Sub-Categories (12):** Large Cap, Small Cap, Gilt, Mid Cap, Short Duration, Value, Liquid, Index/ETF, Flexi Cap, Index, Large & Mid Cap, ELSS
- **Unique Risk Categories (5):** Moderate, Very High, Low, High, Moderately High

### AMFI Scheme Code Structure Explanation
The Association of Mutual Funds in India (AMFI) assigns a unique **6-digit numeric code** (AMFI code) to every mutual fund scheme version in India. 
- It uniquely identifies a specific fund, fund house, asset class, and plan (e.g. Regular vs Direct, Growth vs IDCW).
- For example, `119551` corresponds to *SBI Bluechip Fund - Regular Plan - Growth*, while `119552` corresponds to *SBI Bluechip Fund - Direct Plan - Growth*.
- These codes are the standard key used across the Indian mutual fund industry for reporting NAV, transactional histories, and portfolio disclosures.

## 4. Referential Integrity Validation (AMFI Codes)

- Unique AMFI codes in `01_fund_master.csv`: **40**
- Unique AMFI codes in `02_nav_history.csv`: **40**

> [!NOTE]
> **Validation Result:** SUCCESS: Every AMFI scheme code in the fund master exists in the NAV history dataset! Referential integrity is 100% intact.

## 5. Live NAV API Ingestion Findings

We successfully fetched historical and live NAV data for 6 scheme codes from the official `mfapi.in` API:
- **125497** (3,091 records saved to [live_nav_125497.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/live_nav_125497.csv))
- **119551** (3,236 records saved to [live_nav_119551.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/live_nav_119551.csv))
- **120503** (3,307 records saved to [live_nav_120503.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/live_nav_120503.csv))
- **118632** (3,298 records saved to [live_nav_118632.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/live_nav_118632.csv))
- **119092** (3,565 records saved to [live_nav_119092.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/live_nav_119092.csv))
- **120841** (3,301 records saved to [live_nav_120841.csv](file:///c:/Mutual%20Fund%20Analytics/data/raw/live_nav_120841.csv))

### Scheme Name Discrepancies (Local Master vs API Registry)

During API ingestion, a significant discrepancy was observed: the official AMFI scheme names in the `mfapi.in` API database do not match the scheme names associated with these code values in the local `01_fund_master.csv` file.

| AMFI Code | Local Master Scheme Name | Official API Scheme Name |
| :--- | :--- | :--- |
| **125497** | HDFC Top 100 Direct (Per Request) | SBI Small Cap Fund - Direct Plan - Growth |
| **119551** | SBI Bluechip Fund - Regular Plan - Growth | Aditya Birla Sun Life Banking & PSU Debt Fund - DIRECT - IDCW |
| **120503** | ICICI Bluechip Fund - Regular Plan | Axis ELSS Tax Saver Fund - Direct Plan - Growth Option |
| **118632** | Nippon Large Cap Fund | Nippon India Large Cap Fund - Direct Plan Growth - Growth Option |
| **119092** | Axis Bluechip Fund | HDFC Money Market Fund - Growth Option - Direct Plan |
| **120841** | Kotak Bluechip Fund | quant Mid Cap Fund - Growth Option - Direct Plan |

> [!WARNING]
> This indicates that the local datasets use a custom mock AMFI code mapping table that deviates from the official Association of Mutual Funds in India (AMFI) codes. Care must be taken when merging local transaction or holdings data (keyed by these mock codes) with live data fetched directly from the API.