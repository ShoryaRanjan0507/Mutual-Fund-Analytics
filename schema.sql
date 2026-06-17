-- schema.sql
-- Star Schema design for Mutual Fund Analytics (SQLite)

-- Enable foreign keys check in SQLite (must be run per connection)
PRAGMA foreign_keys = ON;

-- -------------------------------------------------------------
-- 1. DIMENSION TABLES
-- -------------------------------------------------------------

-- dim_fund: Master list of mutual fund schemes
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    plan TEXT NOT NULL,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount REAL,
    min_lumpsum_amount REAL,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

-- dim_date: Date dimension for clean temporal queries and slicing
CREATE TABLE IF NOT EXISTS dim_date (
    date TEXT PRIMARY KEY, -- format YYYY-MM-DD
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL, -- 0=Monday, 6=Sunday or similar
    day_name TEXT NOT NULL,
    month_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL -- 0=False, 1=True
);

-- -------------------------------------------------------------
-- 2. FACT TABLES (Star Schema Core)
-- -------------------------------------------------------------

-- fact_nav: Historical daily Net Asset Value (NAV) records
CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code INTEGER NOT NULL,
    date TEXT NOT NULL,
    nav REAL NOT NULL,
    PRIMARY KEY (amfi_code, date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE,
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- fact_transactions: Investor transactions (SIP, Lumpsum, Redemption)
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr REAL NOT NULL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT CHECK (kyc_status IN ('Verified', 'Pending')),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE
);

-- fact_performance: Scheme-level return percentages, risk metrics and rating
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    expense_ratio_pct REAL,
    anomaly_flag INTEGER CHECK (anomaly_flag IN (0, 1)),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE
);

-- fact_aum: Historical Assets Under Management (AUM) by fund house
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL NOT NULL,
    aum_crore REAL NOT NULL,
    num_schemes INTEGER NOT NULL,
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- -------------------------------------------------------------
-- 3. ANCILLARY / ADDITIONAL DATA TABLES
-- -------------------------------------------------------------

-- sip_inflows: Monthly industry-wide SIP inflow indicators
CREATE TABLE IF NOT EXISTS sip_inflows (
    month TEXT PRIMARY KEY, -- format YYYY-MM
    sip_inflow_crore REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL
);

-- category_inflows: Net inflows into different category classes monthly
CREATE TABLE IF NOT EXISTS category_inflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL, -- format YYYY-MM
    category TEXT NOT NULL,
    net_inflow_crore REAL
);

-- industry_folio_count: Monthly folio count by segment
CREATE TABLE IF NOT EXISTS industry_folio_count (
    month TEXT PRIMARY KEY, -- format YYYY-MM
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

-- portfolio_holdings: Company equity holdings for each scheme
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    sector TEXT,
    weight_pct REAL NOT NULL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE
);

-- benchmark_indices: Index close pricing (NIFTY50, etc.)
CREATE TABLE IF NOT EXISTS benchmark_indices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    index_name TEXT NOT NULL,
    close_value REAL NOT NULL,
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_nav_amfi_date ON fact_nav(amfi_code, date);
CREATE INDEX IF NOT EXISTS idx_transactions_amfi ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_holdings_amfi ON portfolio_holdings(amfi_code);
CREATE INDEX IF NOT EXISTS idx_indices_date_name ON benchmark_indices(date, index_name);
