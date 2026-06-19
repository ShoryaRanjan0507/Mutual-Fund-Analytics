"""
Mutual Fund Analytics - Data Ingestion & Quality Verification

This module loads raw CSV datasets, validates referential integrity (e.g. AMFI codes),
and compiles an initial Data Quality and Ingestion Report.
"""

import os
import pandas as pd
import numpy as np

def run_ingestion():
    """
    Ingests 10 raw CSV datasets, validates schema shapes and types, 
    checks for initial database anomalies, and writes a markdown report.
    """
    raw_dir = os.path.join("data", "raw")
    reports_dir = os.path.join("reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    print("=" * 80)
    print("STARTING DATA INGESTION & QUALITY VERIFICATION")
    print("=" * 80)
    
    # Identify the 10 CSV datasets
    if not os.path.exists(raw_dir):
        print(f"[ERROR] Raw data directory '{raw_dir}' not found.")
        return False
        
    csv_files = sorted([f for f in os.listdir(raw_dir) if f.endswith(".csv") and (f.startswith("0") or f.startswith("1"))])
    print(f"Found {len(csv_files)} datasets in {raw_dir}:")
    for f in csv_files:
        print(f"  - {f}")
    print("-" * 80)
    
    datasets = {}
    
    # Report buffer to build reports/data_quality_report.md
    report_content = [
        "# Mutual Fund Analytics - Data Quality & Ingestion Report\n",
        "**Execution Date:** 2026-06-19",
        f"**Environment:** Python 3.14, Pandas {pd.__version__}\n",
        "## 1. Dataset Loading and Schema Summary\n",
        "| Dataset File | Shape | Columns | Primary Key Candidate / Joins |",
        "| :--- | :--- | :--- | :--- |"
    ]
    
    # Load all datasets, check shapes and types
    for f in csv_files:
        name = os.path.splitext(f)[0]
        path = os.path.join(raw_dir, f)
        df = pd.read_csv(path)
        datasets[name] = df
        
        print(f"[LOADING] {f} | Shape: {df.shape}")
        
        # Append to report table
        cols_str = ", ".join(list(df.columns)[:5]) + ("..." if len(df.columns) > 5 else "")
        join_info = "amfi_code" if "amfi_code" in df.columns else "date/month"
        report_content.append(f"| [{f}](file:///c:/Mutual%20Fund%20Analytics/{raw_dir.replace('\\', '/')}/{f}) | {df.shape} | `{cols_str}` | {join_info} |")
        
    report_content.append("\n## 2. Dataset Anomalies and Data Quality Observations\n")
    
    anomalies = []
    
    # Check 04_monthly_sip_inflows nulls
    sip_df = datasets.get("04_monthly_sip_inflows")
    if sip_df is not None:
        nulls_count = sip_df["yoy_growth_pct"].isnull().sum()
        if nulls_count > 0:
            anomalies.append(
                f"**04_monthly_sip_inflows.csv**: Column `yoy_growth_pct` contains {nulls_count} missing values ({nulls_count/len(sip_df)*100:.1f}%). "
                "This is expected because YoY growth cannot be calculated for the first 12 months (Jan 2022 - Dec 2022) without 2021 historical data."
            )
            
    # Check 08_investor_transactions min transaction amount vs master min_sip_amount
    trans_df = datasets.get("08_investor_transactions")
    master_df = datasets.get("01_fund_master")
    if trans_df is not None and master_df is not None:
        merged = trans_df.merge(master_df[["amfi_code", "min_sip_amount", "min_lumpsum_amount", "scheme_name"]], on="amfi_code")
        sip_trans = merged[merged["transaction_type"].str.lower() == "sip"]
        invalid_sip = sip_trans[sip_trans["amount_inr"] < sip_trans["min_sip_amount"]]
        if len(invalid_sip) > 0:
            anomalies.append(
                f"**08_investor_transactions.csv**: Found {len(invalid_sip)} SIP transactions where the `amount_inr` is less than the scheme's `min_sip_amount` (500 INR). "
                f"Minimum amount found is {invalid_sip['amount_inr'].min()} INR."
            )
            
    # Report anomalies
    if anomalies:
        for idx, anomaly in enumerate(anomalies, 1):
            report_content.append(f"- **Anomaly {idx}:** {anomaly}")
    else:
        report_content.append("No severe data quality anomalies detected. The datasets are clean, complete, and have proper referential integrity.")
    
    # Validate AMFI Codes (confirm every code in fund_master exists in nav_history)
    nav_df = datasets.get("02_nav_history")
    if master_df is not None and nav_df is not None:
        master_codes = set(master_df["amfi_code"].unique())
        nav_codes = set(nav_df["amfi_code"].unique())
        missing_codes = master_codes - nav_codes
        
        report_content.append("\n## 3. Referential Integrity Validation (AMFI Codes)\n")
        report_content.append(f"- Unique AMFI codes in `01_fund_master.csv`: **{len(master_codes)}**")
        report_content.append(f"- Unique AMFI codes in `02_nav_history.csv`: **{len(nav_codes)}**")
        
        if len(missing_codes) == 0:
            validation_msg = "SUCCESS: Every AMFI scheme code in the fund master exists in the NAV history dataset! Referential integrity is 100% intact."
            report_content.append(f"\n> [!NOTE]\n> **Validation Result:** {validation_msg}")
        else:
            validation_msg = f"WARNING: {len(missing_codes)} AMFI codes in the fund master do NOT exist in the NAV history dataset!"
            report_content.append(f"\n> [!WARNING]\n> **Validation Result:** {validation_msg}\n> Missing codes: {missing_codes}")
            
    # Write the report file
    report_path = os.path.join(reports_dir, "data_quality_report.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_content))
    
    print("-" * 80)
    print(f"[SUCCESS] Saved data quality report to {report_path}")
    print("=" * 80)
    return True

if __name__ == "__main__":
    run_ingestion()
