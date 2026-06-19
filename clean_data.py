"""
Mutual Fund Analytics - Data Cleaning & Standardisation

This module handles deduplication, filters out invalid negative/zero values,
standardizes string identifiers, and forward-fills NAV records for weekends/holidays.
"""

import os
import pandas as pd
import numpy as np

def clean_datasets():
    """
    Cleans all 10 raw CSV datasets, standardizing schemas, handling missing keys,
    forward-filling NAV records, and saving the outputs to data/processed.
    """
    raw_dir = os.path.join("data", "raw")
    processed_dir = os.path.join("data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    print("=" * 80)
    print("STARTING DATA CLEANING PROCESS")
    print("=" * 80)
    
    # 1. Clean nav_history.csv (02_nav_history.csv)
    print("[CLEANING] 02_nav_history.csv...")
    nav_path = os.path.join(raw_dir, "02_nav_history.csv")
    if not os.path.exists(nav_path):
        print(f"[ERROR] NAV history file '{nav_path}' not found.")
        return False
        
    df_nav = pd.read_csv(nav_path)
    
    # Parse dates to datetime
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    
    # Remove duplicates
    df_nav = df_nav.drop_duplicates(subset=['amfi_code', 'date'])
    
    # Validate NAV > 0
    df_nav = df_nav[df_nav['nav'] > 0]
    
    # Forward-fill missing NAV for holidays/weekends
    filled_dfs = []
    for amfi, group in df_nav.groupby('amfi_code'):
        group = group.set_index('date')
        full_idx = pd.date_range(start=group.index.min(), end=group.index.max(), freq='D')
        group_filled = group.reindex(full_idx)
        group_filled['amfi_code'] = amfi
        group_filled['nav'] = group_filled['nav'].ffill()
        group_filled = group_filled.reset_index().rename(columns={'index': 'date'})
        filled_dfs.append(group_filled)
        
    df_nav_clean = pd.concat(filled_dfs, ignore_index=True)
    df_nav_clean = df_nav_clean.dropna(subset=['nav'])
    df_nav_clean = df_nav_clean.sort_values(by=['amfi_code', 'date']).reset_index(drop=True)
    
    # Convert date back to string
    df_nav_clean['date'] = df_nav_clean['date'].dt.strftime('%Y-%m-%d')
    
    # Save processed file
    df_nav_clean.to_csv(os.path.join(processed_dir, "02_nav_history.csv"), index=False)
    print(f"  -> Saved clean fact_nav dataset with {len(df_nav_clean)} rows.")
    
    # 2. Clean investor_transactions.csv (08_investor_transactions.csv)
    print("[CLEANING] 08_investor_transactions.csv...")
    tx_path = os.path.join(raw_dir, "08_investor_transactions.csv")
    if not os.path.exists(tx_path):
        print(f"[ERROR] Transactions file '{tx_path}' not found.")
        return False
        
    df_tx = pd.read_csv(tx_path)
    
    # Standardise transaction_type values
    tx_map = {
        'sip': 'SIP',
        'lumpsum': 'Lumpsum',
        'redemption': 'Redemption'
    }
    df_tx['transaction_type'] = df_tx['transaction_type'].str.strip().str.lower().map(tx_map).fillna(df_tx['transaction_type'])
    
    # Validate amount > 0
    df_tx = df_tx[df_tx['amount_inr'] > 0]
    
    # Fix date formats
    df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date']).dt.strftime('%Y-%m-%d')
    df_tx['kyc_status'] = df_tx['kyc_status'].str.strip().str.capitalize()
    
    # Save processed file
    df_tx.to_csv(os.path.join(processed_dir, "08_investor_transactions.csv"), index=False)
    print(f"  -> Saved clean fact_transactions dataset with {len(df_tx)} rows.")
    
    # 3. Clean scheme_performance.csv (07_scheme_performance.csv)
    print("[CLEANING] 07_scheme_performance.csv...")
    perf_path = os.path.join(raw_dir, "07_scheme_performance.csv")
    if not os.path.exists(perf_path):
        print(f"[ERROR] Scheme performance file '{perf_path}' not found.")
        return False
        
    df_perf = pd.read_csv(perf_path)
    
    # Validate return values are numeric
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct']
    for col in return_cols:
        df_perf[col] = pd.to_numeric(df_perf[col], errors='coerce')
        
    # Flag anomalies (outlier returns > 100% or < -50% or null values)
    anom_mask = (
        df_perf['return_1yr_pct'].isna() |
        df_perf['return_3yr_pct'].isna() |
        df_perf['return_5yr_pct'].isna() |
        (df_perf['return_1yr_pct'] > 100) | (df_perf['return_1yr_pct'] < -50) |
        (df_perf['return_3yr_pct'] > 100) | (df_perf['return_3yr_pct'] < -50) |
        (df_perf['return_5yr_pct'] > 100) | (df_perf['return_5yr_pct'] < -50)
    )
    df_perf['anomaly_flag'] = anom_mask.astype(int)
    df_perf['expense_ratio_valid'] = df_perf['expense_ratio_pct'].between(0.1, 2.5).astype(int)
    
    # Save processed file
    df_perf.to_csv(os.path.join(processed_dir, "07_scheme_performance.csv"), index=False)
    print(f"  -> Saved clean fact_performance dataset with {len(df_perf)} rows. Flagged {df_perf['anomaly_flag'].sum()} anomalies.")
    
    # 4. Process and standardise remaining 7 CSV files
    other_files = [
        "01_fund_master.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv"
    ]
    
    for f in other_files:
        path = os.path.join(raw_dir, f)
        if not os.path.exists(path):
            print(f"[ERROR] Source file '{path}' not found.")
            continue
            
        df = pd.read_csv(path)
        
        # Strip string values
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].astype(str).str.strip()
            
        # Deduplicate
        df = df.drop_duplicates()
        
        # Fix date/month formats
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        elif 'portfolio_date' in df.columns:
            df['portfolio_date'] = pd.to_datetime(df['portfolio_date']).dt.strftime('%Y-%m-%d')
        elif 'month' in df.columns:
            df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m')
        elif 'launch_date' in df.columns:
            df['launch_date'] = pd.to_datetime(df['launch_date']).dt.strftime('%Y-%m-%d')
            
        # Save processed file
        df.to_csv(os.path.join(processed_dir, f), index=False)
        print(f"  -> Saved clean {f} with {len(df)} rows.")
        
    print("-" * 80)
    print("[SUCCESS] Data cleaning complete. Clean CSVs populated in data/processed/.")
    print("=" * 80)
    return True

if __name__ == "__main__":
    clean_datasets()
