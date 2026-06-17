import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

def load_data_to_sqlite():
    processed_dir = os.path.join("data", "processed")
    db_path = "bluestock_mf.db"
    
    print("=" * 80)
    print("STARTING DATABASE CREATION AND DATA LOADING")
    print("=" * 80)
    
    # 1. Initialize SQLite database and run schema.sql
    print("[INIT] Creating SQLite tables using schema.sql...")
    conn = sqlite3.connect(db_path)
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.close()
    print("[INIT] Schema created successfully.")
    
    # Create SQLAlchemy engine
    engine = create_engine(f"sqlite:///{db_path}")
    
    # 2. Load cleaned dataframes to identify all date keys
    print("[DATE DIMENSION] Generating dim_date table...")
    df_nav = pd.read_csv(os.path.join(processed_dir, "02_nav_history.csv"))
    df_tx = pd.read_csv(os.path.join(processed_dir, "08_investor_transactions.csv"))
    df_bench = pd.read_csv(os.path.join(processed_dir, "10_benchmark_indices.csv"))
    
    # Concat all dates to find min and max date range
    all_dates = pd.concat([
        pd.to_datetime(df_nav['date']),
        pd.to_datetime(df_tx['transaction_date']),
        pd.to_datetime(df_bench['date'])
    ])
    
    min_date = all_dates.min()
    max_date = all_dates.max()
    print(f"Date range detected: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    
    # Generate continuous daily date range
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    
    df_date = pd.DataFrame({'date': date_range})
    df_date['year'] = df_date['date'].dt.year
    df_date['month'] = df_date['date'].dt.month
    df_date['day'] = df_date['date'].dt.day
    df_date['quarter'] = df_date['date'].dt.quarter
    df_date['day_of_week'] = df_date['date'].dt.dayofweek  # 0 = Monday, 6 = Sunday
    df_date['day_name'] = df_date['date'].dt.day_name()
    df_date['month_name'] = df_date['date'].dt.month_name()
    df_date['is_weekend'] = df_date['day_of_week'].isin([5, 6]).astype(int)
    
    # Format date as string to match TEXT columns in SQLite
    df_date['date'] = df_date['date'].dt.strftime('%Y-%m-%d')
    
    # Load dim_date
    df_date.to_sql("dim_date", con=engine, if_exists="append", index=False)
    print(f"[DATE DIMENSION] Loaded {len(df_date)} calendar date records.")
    
    # Helper to check row counts and load
    def load_table(csv_name, table_name, select_cols=None):
        csv_path = os.path.join(processed_dir, csv_name)
        df = pd.read_csv(csv_path)
        source_count = len(df)
        
        if select_cols:
            df_to_load = df[select_cols]
        else:
            df_to_load = df
            
        # Write to SQL
        df_to_load.to_sql(table_name, con=engine, if_exists="append", index=False)
        
        # Verify row count
        db_count = pd.read_sql_query(f"SELECT COUNT(*) FROM {table_name}", con=engine).iloc[0, 0]
        print(f"[LOAD] Table '{table_name}': loaded {db_count} rows (Source CSV: {source_count} rows)")
        
        # Verify match
        if source_count == db_count:
            print(f"  -> SUCCESS: Row counts match perfectly ({db_count})")
        else:
            print(f"  -> WARNING: Row counts differ! DB has {db_count}, CSV has {source_count}")
            
    # Load all remaining tables in order of dependencies (Dimensions first, then facts)
    
    # 1. dim_fund (01_fund_master.csv)
    load_table("01_fund_master.csv", "dim_fund")
    
    # 2. fact_nav (02_nav_history.csv)
    load_table("02_nav_history.csv", "fact_nav")
    
    # 3. fact_transactions (08_investor_transactions.csv)
    load_table("08_investor_transactions.csv", "fact_transactions")
    
    # 4. fact_performance (07_scheme_performance.csv)
    # We select only the columns matching SQL schema, filtering out fund attributes like scheme_name, etc.
    perf_cols = [
        'amfi_code', 'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct',
        'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 'std_dev_ann_pct', 'max_drawdown_pct',
        'aum_crore', 'morningstar_rating', 'risk_grade', 'expense_ratio_pct', 'anomaly_flag'
    ]
    load_table("07_scheme_performance.csv", "fact_performance", select_cols=perf_cols)
    
    # 5. fact_aum (03_aum_by_fund_house.csv)
    load_table("03_aum_by_fund_house.csv", "fact_aum")
    
    # Ancillary Tables
    # 6. sip_inflows (04_monthly_sip_inflows.csv)
    load_table("04_monthly_sip_inflows.csv", "sip_inflows")
    
    # 7. category_inflows (05_category_inflows.csv)
    load_table("05_category_inflows.csv", "category_inflows")
    
    # 8. industry_folio_count (06_industry_folio_count.csv)
    load_table("06_industry_folio_count.csv", "industry_folio_count")
    
    # 9. portfolio_holdings (09_portfolio_holdings.csv)
    load_table("09_portfolio_holdings.csv", "portfolio_holdings")
    
    # 10. benchmark_indices (10_benchmark_indices.csv)
    load_table("10_benchmark_indices.csv", "benchmark_indices")
    
    print("=" * 80)
    print("DATABASE LOADING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    load_data_to_sqlite()
