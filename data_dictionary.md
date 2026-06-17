# Data Dictionary - Mutual Fund Analytics Star Schema

This document details the SQLite database schemas, columns, data types, constraints, business meanings, and source references for the tables loaded in `bluestock_mf.db`.

---

## 1. Dimension Tables

### `dim_fund`
- **Source Reference**: `data/raw/01_fund_master.csv`
- **Business Description**: Holds static/master data about all mutual fund schemes, managers, limits, and identifiers.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | Unique Association of Mutual Funds in India (AMFI) scheme identifier code. |
| `fund_house` | TEXT | NOT NULL | The Asset Management Company (AMC) name. |
| `scheme_name` | TEXT | NOT NULL | The official name of the mutual fund scheme version. |
| `category` | TEXT | NOT NULL | Broad asset class category (Equity, Debt, Hybrid, Index, etc.). |
| `sub_category` | TEXT | NOT NULL | Granular investment sub-category (Large Cap, Mid Cap, Gilt, Liquid, ELSS). |
| `plan` | TEXT | NOT NULL | Regular or Direct transaction plan type. |
| `launch_date` | TEXT | - | Scheme launch date formatted as `YYYY-MM-DD`. |
| `benchmark` | TEXT | - | Benchmark index that the scheme compares against (e.g. NIFTY 100 TRI). |
| `expense_ratio_pct` | REAL | - | Stated annual fee charged by the fund, as a percentage of assets. |
| `exit_load_pct` | REAL | - | Redemption charge fee percentage if withdrawn early. |
| `min_sip_amount` | REAL | - | Minimum transaction requirement for systematic investment plans (SIP). |
| `min_lumpsum_amount` | REAL | - | Minimum transaction requirement for one-time lumpsum investments. |
| `fund_manager` | TEXT | - | Main portfolio manager directing the scheme investments. |
| `risk_category` | TEXT | - | Stated risk classification level (Low, Moderate, High, Very High). |
| `sebi_category_code` | TEXT | - | SEBI standard code for reporting categories (e.g. EC01, DC02). |

---

### `dim_date`
- **Source Reference**: Dynamically derived calendar range covering dates in the dataset.
- **Business Description**: A complete daily calendar dimension table enabling time-slice queries, weekend grouping, and seasonal trends.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | PRIMARY KEY | ISO string date key formatted as `YYYY-MM-DD`. |
| `year` | INTEGER | NOT NULL | Calendar year (e.g., 2024). |
| `month` | INTEGER | NOT NULL | Calendar month index (1 to 12). |
| `day` | INTEGER | NOT NULL | Day of the month index (1 to 31). |
| `quarter` | INTEGER | NOT NULL | Calendar quarter index (1 to 4). |
| `day_of_week` | INTEGER | NOT NULL | Day index where 0 represents Monday and 6 represents Sunday. |
| `day_name` | TEXT | NOT NULL | Full name of the calendar day (e.g. Monday). |
| `month_name` | TEXT | NOT NULL | Full name of the calendar month (e.g. January). |
| `is_weekend` | INTEGER | NOT NULL | Binary flag where 1 represents Saturday/Sunday and 0 represents weekdays. |

---

## 2. Fact Tables

### `fact_nav`
- **Source Reference**: `data/raw/02_nav_history.csv` (Cleaned & Forward-filled)
- **Business Description**: Daily Net Asset Value (NAV) price data point for each scheme. Missing weekend/holiday entries are forward-filled with the last business day's NAV.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY, FK | Foreign key pointing to `dim_fund(amfi_code)`. |
| `date` | TEXT | PRIMARY KEY, FK | Foreign key pointing to `dim_date(date)`. |
| `nav` | REAL | NOT NULL | Cleaned NAV unit price value (strictly > 0). |

---

### `fact_transactions`
- **Source Reference**: `data/raw/08_investor_transactions.csv` (Cleaned & Standardized)
- **Business Description**: Granular transaction-level history record of individual investor interactions.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | INTEGER | PRIMARY KEY, AUTOINC | Unique auto-incrementing transaction index identifier. |
| `investor_id` | TEXT | NOT NULL | Masked identifier representing the investor. |
| `transaction_date` | TEXT | NOT NULL, FK | Foreign key pointing to `dim_date(date)`. |
| `amfi_code` | INTEGER | NOT NULL, FK | Foreign key pointing to `dim_fund(amfi_code)`. |
| `transaction_type` | TEXT | CHECK enum | Canonical transaction category: `SIP`, `Lumpsum`, or `Redemption`. |
| `amount_inr` | REAL | CHECK > 0 | Amount value in Indian Rupees (strictly > 0). |
| `state` | TEXT | - | State code/name where the transaction was registered. |
| `city` | TEXT | - | City name where the transaction occurred. |
| `city_tier` | TEXT | - | Tier classification (T30: Top 30 cities, B30: Beyond Top 30). |
| `age_group` | TEXT | - | Age bracket classification of the investor. |
| `gender` | TEXT | - | Stated gender category of the investor. |
| `annual_income_lakh` | REAL | - | Declared yearly household income in Lakhs of INR. |
| `payment_mode` | TEXT | - | Mode of funding transfer (UPI, Mandate, Net Banking, Cheque). |
| `kyc_status` | TEXT | CHECK enum | Status of KYC validation check: `Verified` or `Pending`. |

---

### `fact_performance`
- **Source Reference**: `data/raw/07_scheme_performance.csv` (Cleaned & Checked)
- **Business Description**: Long-term risk, return and rating parameters computed at the scheme level.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY, FK | Unique scheme code pointing to `dim_fund(amfi_code)`. |
| `return_1yr_pct` | REAL | - | Stated return rate over a 1-year window. |
| `return_3yr_pct` | REAL | - | Stated return rate over a 3-year window. |
| `return_5yr_pct` | REAL | - | Stated return rate over a 5-year window. |
| `benchmark_3yr_pct` | REAL | - | Return of the scheme benchmark index over a 3-year window. |
| `alpha` | REAL | - | Risk-adjusted metric showing outperformance margin. |
| `beta` | REAL | - | Volatility indicator relative to the benchmark index. |
| `sharpe_ratio` | REAL | - | Stated risk-reward performance efficiency index. |
| `sortino_ratio` | REAL | - | Downside risk-reward return adjustment ratio. |
| `std_dev_ann_pct` | REAL | - | Annualized deviation volatility indicator as a percentage. |
| `max_drawdown_pct` | REAL | - | Worst peak-to-trough value loss percentage. |
| `aum_crore` | REAL | - | Assets under management value in crores of INR. |
| `morningstar_rating` | INTEGER | - | Morningstar scale rating value (1 to 5 stars). |
| `risk_grade` | TEXT | - | Qualitative risk description. |
| `expense_ratio_pct` | REAL | - | Scheme expense ratio percentage (verified against Master file). |
| `anomaly_flag` | INTEGER | CHECK (0, 1) | Flag indicating return anomaly check (1 = Outlier/Null, 0 = Normal). |

---

### `fact_aum`
- **Source Reference**: `data/raw/03_aum_by_fund_house.csv`
- **Business Description**: Quarterly historical AUM trends tracked at the fund house (AMC) level.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `aum_id` | INTEGER | PRIMARY KEY, AUTOINC | Unique index key record identifier. |
| `date` | TEXT | NOT NULL, FK | Foreign key pointing to `dim_date(date)` representing reporting day. |
| `fund_house` | TEXT | NOT NULL | Stated Asset Management Company name. |
| `aum_lakh_crore` | REAL | NOT NULL | Fund house AUM expressed in Lakh Crores of INR. |
| `aum_crore` | REAL | NOT NULL | Fund house AUM expressed in Crores of INR. |
| `num_schemes` | INTEGER | NOT NULL | Total active scheme products listed under this AMC. |

---

## 3. Ancillary Tables

### `sip_inflows`
- **Source Reference**: `data/raw/04_monthly_sip_inflows.csv`
- **Business Description**: Monthly aggregate mutual fund industry SIP inflows.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | PRIMARY KEY | Stated month identifier formatted as `YYYY-MM`. |
| `sip_inflow_crore` | REAL | - | Total SIP investment inflow amount in crores of INR. |
| `active_sip_accounts_crore` | REAL | - | Volume count of active SIP accounts in crores. |
| `new_sip_accounts_lakh` | REAL | - | Stated new SIP openings count in Lakhs. |
| `sip_aum_lakh_crore` | REAL | - | Total AUM backed by SIP systems in Lakh Crores. |
| `yoy_growth_pct` | REAL | - | Stated year-over-year inflow percentage growth index. |

---

### `category_inflows`
- **Source Reference**: `data/raw/05_category_inflows.csv`
- **Business Description**: Monthly industry net inflows grouped by broad product categories.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINC | Stated serial record index identifier. |
| `month` | TEXT | NOT NULL | Stated month identifier formatted as `YYYY-MM`. |
| `category` | TEXT | NOT NULL | broad fund category class (e.g. Large Cap, Sectoral). |
| `net_inflow_crore` | REAL | - | Stated net fund inflow in Crores of INR. |

---

### `industry_folio_count`
- **Source Reference**: `data/raw/06_industry_folio_count.csv`
- **Business Description**: Stated folio volumes tracked across different asset segments monthly.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | PRIMARY KEY | Stated month identifier formatted as `YYYY-MM`. |
| `total_folios_crore` | REAL | - | Total folio registration counts in crores. |
| `equity_folios_crore` | REAL | - | Folios registered under equity category. |
| `debt_folios_crore` | REAL | - | Folios registered under debt category. |
| `hybrid_folios_crore` | REAL | - | Folios registered under hybrid category. |
| `others_folios_crore` | REAL | - | Folios registered under index/other categories. |

---

### `portfolio_holdings`
- **Source Reference**: `data/raw/09_portfolio_holdings.csv`
- **Business Description**: Equity/asset holdings list for each mutual fund scheme.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINC | Unique holding index identifier. |
| `amfi_code` | INTEGER | NOT NULL, FK | Stated mutual fund scheme code pointing to `dim_fund(amfi_code)`. |
| `stock_symbol` | TEXT | NOT NULL | NSE ticket listing code (e.g. RELIANCE, HDFCBANK). |
| `stock_name` | TEXT | NOT NULL | Stated company name. |
| `sector` | TEXT | - | Broad corporate industry sector (Banking, IT, Telecom, etc.). |
| `weight_pct` | REAL | NOT NULL | Stated holding allocation weight percentage (0 - 100%). |
| `market_value_cr` | REAL | - | Stated allocation market value in Crores of INR. |
| `current_price_inr` | REAL | - | Close pricing per stock unit in INR. |
| `portfolio_date` | TEXT | NOT NULL | Date when holdings list was reported, formatted as `YYYY-MM-DD`. |

---

### `benchmark_indices`
- **Source Reference**: `data/raw/10_benchmark_indices.csv`
- **Business Description**: Stated historical index closing prices.

| Column Name | Data Type | Key / Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINC | Stated index price serial record indicator. |
| `date` | TEXT | NOT NULL, FK | Date of closing index price pointing to `dim_date(date)`. |
| `index_name` | TEXT | NOT NULL | Identifier code representation (e.g., NIFTY50). |
| `close_value` | REAL | NOT NULL | Index closing value price. |
