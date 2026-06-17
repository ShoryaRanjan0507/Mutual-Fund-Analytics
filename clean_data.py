import os
import pandas as pd
import numpy as np

def clean_datasets():
    raw_dir = os.path.join("data", "raw")
    processed_dir = os.path.join("data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    print("=" * 80)
    print("STARTING DATA CLEANING PROCESS")
    print("=" * 80)
    
    # 1. Clean nav_history.csv (02_nav_history.csv)
    print("[CLEANING] 02_nav_history.csv...")
    nav_path = os.path.join(raw_dir, "02_nav_history.csv")
    df_nav = pd.read_csv(nav_path)
    print(f"Original shape: {df_nav.shape}")
    
    # Parse dates to datetime
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    
    # Remove duplicates
    df_nav = df_nav.drop_duplicates(subset=['amfi_code', 'date'])
    print(f"Shape after duplicate removal: {df_nav.shape}")
    
    # Validate NAV > 0
    df_nav = df_nav[df_nav['nav'] > 0]
    print(f"Shape after validating NAV > 0: {df_nav.shape}")
    
    # Forward-fill missing NAV for holidays/weekends
    # Group by amfi_code, reindex to daily range, and ffill
    filled_dfs = []
    for amfi, group in df_nav.groupby('amfi_code'):
        # Set date as index
        group = group.set_index('date')
        # Generate complete daily date range
        full_idx = pd.date_range(start=group.index.min(), end=group.index.max(), freq='D')
        # Reindex group
        group_filled = group.reindex(full_idx)
        group_filled['amfi_code'] = amfi
        # Forward-fill nav
        group_filled['nav'] = group_filled['nav'].ffill()
        # Reset index to get date column back
        group_filled = group_filled.reset_index().rename(columns={'index': 'date'})
        filled_dfs.append(group_filled)
        
    df_nav_clean = pd.concat(filled_dfs, ignore_index=True)
    
    # Drop any remaining rows where nav is still NaN (e.g. if start date nav was somehow NaN)
    df_nav_clean = df_nav_clean.dropna(subset=['nav'])
    
    # Sort by amfi_code + date
    df_nav_clean = df_nav_clean.sort_values(by=['amfi_code', 'date']).reset_index(drop=True)
    print(f"Shape after forward-filling holidays/weekends: {df_nav_clean.shape}")
    
    # Convert date back to string
    df_nav_clean['date'] = df_nav_clean['date'].dt.strftime('%Y-%m-%d')
    
    # Save processed file
    df_nav_clean.to_csv(os.path.join(processed_dir, "02_nav_history.csv"), index=False)
    print("Processed 02_nav_history.csv successfully saved.")
    
    # 2. Clean investor_transactions.csv (08_investor_transactions.csv)
    print("\n[CLEANING] 08_investor_transactions.csv...")
    tx_path = os.path.join(raw_dir, "08_investor_transactions.csv")
    df_tx = pd.read_csv(tx_path)
    print(f"Original shape: {df_tx.shape}")
    
    # Standardise transaction_type values
    tx_map = {
        'sip': 'SIP',
        'lumpsum': 'Lumpsum',
        'redemption': 'Redemption'
    }
    df_tx['transaction_type'] = df_tx['transaction_type'].str.strip().str.lower().map(tx_map).fillna(df_tx['transaction_type'])
    print(f"Unique transaction types: {df_tx['transaction_type'].unique()}")
    
    # Validate amount > 0
    df_tx = df_tx[df_tx['amount_inr'] > 0]
    print(f"Shape after validating amount_inr > 0: {df_tx.shape}")
    
    # Fix date formats
    df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date']).dt.strftime('%Y-%m-%d')
    
    # Check KYC status enum values
    df_tx['kyc_status'] = df_tx['kyc_status'].str.strip().str.capitalize()
    print(f"Unique KYC statuses: {df_tx['kyc_status'].unique()}")
    
    # Save processed file
    df_tx.to_csv(os.path.join(processed_dir, "08_investor_transactions.csv"), index=False)
    print("Processed 08_investor_transactions.csv successfully saved.")
    
    # 3. Clean scheme_performance.csv (07_scheme_performance.csv)
    print("\n[CLEANING] 07_scheme_performance.csv...")
    perf_path = os.path.join(raw_dir, "07_scheme_performance.csv")
    df_perf = pd.read_csv(perf_path)
    print(f"Original shape: {df_perf.shape}")
    
    # Validate return values are numeric
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct']
    for col in return_cols:
        df_perf[col] = pd.to_numeric(df_perf[col], errors='coerce')
        
    # Flag anomalies
    # Extreme return outliers (e.g. > 100% or < -50%) or null values in return columns
    anom_mask = (
        df_perf['return_1yr_pct'].isna() |
        df_perf['return_3yr_pct'].isna() |
        df_perf['return_5yr_pct'].isna() |
        (df_perf['return_1yr_pct'] > 100) | (df_perf['return_1yr_pct'] < -50) |
        (df_perf['return_3yr_pct'] > 100) | (df_perf['return_3yr_pct'] < -50) |
        (df_perf['return_5yr_pct'] > 100) | (df_perf['return_5yr_pct'] < -50)
    )
    df_perf['anomaly_flag'] = anom_mask.astype(int)
    print(f"Number of flagged anomalies in scheme returns: {df_perf['anomaly_flag'].sum()}")
    
    # Check expense_ratio range (0.1% - 2.5%)
    # Let's flag schemes with invalid expense ratios
    df_perf['expense_ratio_valid'] = df_perf['expense_ratio_pct'].between(0.1, 2.5).astype(int)
    invalid_exp = df_perf[df_perf['expense_ratio_valid'] == 0]
    if not invalid_exp.empty:
        print(f"Warning: Found {len(invalid_exp)} schemes with expense ratio outside [0.1%, 2.5%]:")
        for idx, row in invalid_exp.iterrows():
            print(f"  - AMFI {row['amfi_code']}: {row['scheme_name']} ({row['expense_ratio_pct']}%)")
    
    # Save processed file
    df_perf.to_csv(os.path.join(processed_dir, "07_scheme_performance.csv"), index=False)
    print("Processed 07_scheme_performance.csv successfully saved.")
    
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
        print(f"\n[STANDARDIZING] {f}...")
        path = os.path.join(raw_dir, f)
        df = pd.read_csv(path)
        print(f"Original shape: {df.shape}")
        
        # Strip string values
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].astype(str).str.strip()
            
        # Deduplicate
        df = df.drop_duplicates()
        print(f"Shape after deduplication: {df.shape}")
        
        # Fix date/month formats if columns exist
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        elif 'portfolio_date' in df.columns:
            df['portfolio_date'] = pd.to_datetime(df['portfolio_date']).dt.strftime('%Y-%m-%d')
        elif 'month' in df.columns:
            # We want month to be YYYY-MM
            df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m')
        elif 'launch_date' in df.columns:
            df['launch_date'] = pd.to_datetime(df['launch_date']).dt.strftime('%Y-%m-%d')
            
        # Save processed file
        df.to_csv(os.path.join(processed_dir, f), index=False)
        print(f"Processed {f} successfully saved.")
        
    print("=" * 80)
    print("DATA CLEANING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    clean_datasets()
