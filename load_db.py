"""
Mutual Fund Analytics - Star Schema Database Creation & Loading

This module runs the SQLite schema definition script (schema.sql),
generates a calendar date dimension table, and populates the star schema database.
"""

import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

def load_data_to_sqlite():
    """
    Constructs the SQLite tables from schema.sql, generates a complete
    dim_date table, and loads cleaned data into star schema tables.
    """
    processed_dir = os.path.join("data", "processed")
    db_path = "bluestock_mf.db"
    
    print("=" * 80)
    print("STARTING DATABASE CREATION AND DATA LOADING")
    print("=" * 80)
    
    # 1. Initialize SQLite database and run schema.sql
    print("[INIT] Creating SQLite tables using schema.sql...")
    if not os.path.exists("schema.sql"):
        print("[ERROR] Schema file 'schema.sql' not found.")
        return False
        
    conn = sqlite3.connect(db_path)
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.close()
    
    # Create SQLAlchemy engine
    engine = create_engine(f"sqlite:///{db_path}")
    
    # 2. Generate calendar date dimension table
    print("[DATE DIMENSION] Generating dim_date table...")
    df_nav = pd.read_csv(os.path.join(processed_dir, "02_nav_history.csv"))
    df_tx = pd.read_csv(os.path.join(processed_dir, "08_investor_transactions.csv"))
    df_bench = pd.read_csv(os.path.join(processed_dir, "10_benchmark_indices.csv"))
    
    all_dates = pd.concat([
        pd.to_datetime(df_nav['date']),
        pd.to_datetime(df_tx['transaction_date']),
        pd.to_datetime(df_bench['date'])
    ])
    
    min_date = all_dates.min()
    max_date = all_dates.max()
    print(f"  -> Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    
    # Generate daily indices
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    df_date = pd.DataFrame({'date': date_range})
    df_date['year'] = df_date['date'].dt.year
    df_date['month'] = df_date['date'].dt.month
    df_date['day'] = df_date['date'].dt.day
    df_date['quarter'] = df_date['date'].dt.quarter
    df_date['day_of_week'] = df_date['date'].dt.dayofweek
    df_date['day_name'] = df_date['date'].dt.day_name()
    df_date['month_name'] = df_date['date'].dt.month_name()
    df_date['is_weekend'] = df_date['day_of_week'].isin([5, 6]).astype(int)
    
    # String dates
    df_date['date'] = df_date['date'].dt.strftime('%Y-%m-%d')
    
    # Clear any existing rows to avoid double insertions
    with engine.begin() as sql_conn:
        sql_conn.exec_driver_sql("DELETE FROM dim_date")
        
    df_date.to_sql("dim_date", con=engine, if_exists="append", index=False)
    print(f"  -> Loaded {len(df_date)} calendar records into 'dim_date'.")
    
    # Helper load function
    def load_table(csv_name, table_name, select_cols=None):
        csv_path = os.path.join(processed_dir, csv_name)
        df = pd.read_csv(csv_path)
        
        # Clear existing rows
        with engine.begin() as sql_conn:
            sql_conn.exec_driver_sql(f"DELETE FROM {table_name}")
            
        df_to_load = df[select_cols] if select_cols else df
        df_to_load.to_sql(table_name, con=engine, if_exists="append", index=False)
        
        db_count = pd.read_sql_query(f"SELECT COUNT(*) FROM {table_name}", con=engine).iloc[0, 0]
        print(f"[LOAD] Table '{table_name}': Loaded {db_count} rows.")
        return len(df) == db_count
        
    # Load all tables
    load_table("01_fund_master.csv", "dim_fund")
    load_table("02_nav_history.csv", "fact_nav")
    load_table("08_investor_transactions.csv", "fact_transactions")
    
    perf_cols = [
        'amfi_code', 'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct',
        'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 'std_dev_ann_pct', 'max_drawdown_pct',
        'aum_crore', 'morningstar_rating', 'risk_grade', 'expense_ratio_pct', 'anomaly_flag'
    ]
    load_table("07_scheme_performance.csv", "fact_performance", select_cols=perf_cols)
    load_table("03_aum_by_fund_house.csv", "fact_aum")
    load_table("04_monthly_sip_inflows.csv", "sip_inflows")
    load_table("05_category_inflows.csv", "category_inflows")
    load_table("06_industry_folio_count.csv", "industry_folio_count")
    load_table("09_portfolio_holdings.csv", "portfolio_holdings")
    load_table("10_benchmark_indices.csv", "benchmark_indices")
    
    print("-" * 80)
    print("[SUCCESS] Star schema tables populated successfully.")
    print("=" * 80)
    return True

if __name__ == "__main__":
    load_data_to_sqlite()
