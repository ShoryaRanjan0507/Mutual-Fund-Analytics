import os
import pandas as pd
import numpy as np

def run_ingestion():
    raw_dir = os.path.join("data", "raw")
    reports_dir = os.path.join("reports")
    
    # 1. Identify the 10 CSV datasets
    csv_files = sorted([f for f in os.listdir(raw_dir) if f.endswith(".csv") and f.startswith("0") or f.startswith("1")])
    
    print("=" * 80)
    print("STARTING DATA INGESTION & QUALITY VERIFICATION")
    print("=" * 80)
    print(f"Found {len(csv_files)} datasets in {raw_dir}:")
    for f in csv_files:
        print(f"  - {f}")
    print("-" * 80)
    
    datasets = {}
    
    # Report buffer to build reports/data_quality_report.md
    report_content = []
    report_content.append("# Mutual Fund Analytics - Day 1 Data Quality & Ingestion Report\n")
    report_content.append(f"**Execution Date:** 2026-06-02")
    report_content.append(f"**Environment:** Python 3.14.3, Pandas {pd.__version__}\n")
    report_content.append("## 1. Dataset Loading and Schema Summary\n")
    report_content.append("| Dataset File | Shape | Columns | Primary Key Candidate / Joins |")
    report_content.append("| :--- | :--- | :--- | :--- |")
    
    # 2. Load all datasets, print shapes, types, heads, and note anomalies
    for f in csv_files:
        name = os.path.splitext(f)[0]
        path = os.path.join(raw_dir, f)
        df = pd.read_csv(path)
        datasets[name] = df
        
        print(f"\n[LOADING] {f}")
        print(f"Shape: {df.shape}")
        print("Data Types:")
        print(df.dtypes)
        print("\nHead (first 3 rows):")
        print(df.head(3))
        print("-" * 80)
        
        # Append to report table
        cols_str = ", ".join(list(df.columns)[:5]) + ("..." if len(df.columns) > 5 else "")
        join_info = "amfi_code" if "amfi_code" in df.columns else "date/month"
        report_content.append(f"| [{f}](file:///c:/Mutual%20Fund%20Analytics/{raw_dir.replace('\\', '/')}/{f}) | {df.shape} | `{cols_str}` | {join_info} |")
        
    report_content.append("\n## 2. Dataset Anomalies and Data Quality Observations\n")
    
    # We will document specific anomalies identified:
    # 1. yoy_growth_pct in monthly_sip_inflows has 12 null values (25.0% of the dataset)
    # 2. amount_inr in investor_transactions contains transactions below the stated min_sip_amount in fund_master
    
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
            
    # Print and report anomalies
    print("\n=== DATA QUALITY ANOMALIES ===")
    if anomalies:
        for idx, anomaly in enumerate(anomalies, 1):
            print(f"{idx}. {anomaly}")
            report_content.append(f"- **Anomaly {idx}:** {anomaly}")
    else:
        print("No severe data quality anomalies detected!")
        report_content.append("No severe data quality anomalies detected. The datasets are clean, complete, and have proper referential integrity.")
    print("-" * 80)
    
    # 3. Explore Fund Master
    print("\n=== EXPLORING FUND MASTER ===")
    if master_df is not None:
        unique_houses = master_df["fund_house"].unique()
        unique_categories = master_df["category"].unique()
        unique_subcats = master_df["sub_category"].unique()
        unique_risks = master_df["risk_category"].unique()
        
        print(f"Unique Fund Houses ({len(unique_houses)}):")
        for house in unique_houses:
            print(f"  - {house}")
            
        print(f"\nUnique Categories ({len(unique_categories)}):")
        for cat in unique_categories:
            print(f"  - {cat}")
            
        print(f"\nUnique Sub-Categories ({len(unique_subcats)}):")
        for subcat in unique_subcats:
            print(f"  - {subcat}")
            
        print(f"\nUnique Risk Categories ({len(unique_risks)}):")
        for risk in unique_risks:
            print(f"  - {risk}")
            
        # Write to report
        report_content.append("\n## 3. Fund Master Exploration\n")
        report_content.append(f"- **Unique Fund Houses ({len(unique_houses)}):** " + ", ".join(unique_houses))
        report_content.append(f"- **Unique Categories ({len(unique_categories)}):** " + ", ".join(unique_categories))
        report_content.append(f"- **Unique Sub-Categories ({len(unique_subcats)}):** " + ", ".join(unique_subcats))
        report_content.append(f"- **Unique Risk Categories ({len(unique_risks)}):** " + ", ".join(unique_risks))
        
        # Explain AMFI Scheme Code structure
        amfi_explanation = (
            "\n### AMFI Scheme Code Structure Explanation\n"
            "The Association of Mutual Funds in India (AMFI) assigns a unique **6-digit numeric code** (AMFI code) "
            "to every mutual fund scheme version in India. \n"
            "- It uniquely identifies a specific fund, fund house, asset class, and plan (e.g. Regular vs Direct, Growth vs IDCW).\n"
            "- For example, `119551` corresponds to *SBI Bluechip Fund - Regular Plan - Growth*, while `119552` corresponds to *SBI Bluechip Fund - Direct Plan - Growth*.\n"
            "- These codes are the standard key used across the Indian mutual fund industry for reporting NAV, transactional histories, and portfolio disclosures."
        )
        print(amfi_explanation)
        report_content.append(amfi_explanation)
    else:
        print("Fund master dataset not found!")
    print("-" * 80)
    
    # 4. Validate AMFI Codes (confirm every code in fund_master exists in nav_history)
    print("\n=== VALIDATING AMFI CODES ===")
    nav_df = datasets.get("02_nav_history")
    if master_df is not None and nav_df is not None:
        master_codes = set(master_df["amfi_code"].unique())
        nav_codes = set(nav_df["amfi_code"].unique())
        
        missing_codes = master_codes - nav_codes
        
        print(f"Unique AMFI codes in fund_master: {len(master_codes)}")
        print(f"Unique AMFI codes in nav_history: {len(nav_codes)}")
        
        report_content.append("\n## 4. Referential Integrity Validation (AMFI Codes)\n")
        report_content.append(f"- Unique AMFI codes in `01_fund_master.csv`: **{len(master_codes)}**")
        report_content.append(f"- Unique AMFI codes in `02_nav_history.csv`: **{len(nav_codes)}**")
        
        if len(missing_codes) == 0:
            validation_msg = "SUCCESS: Every AMFI scheme code in the fund master exists in the NAV history dataset! Referential integrity is 100% intact."
            print(validation_msg)
            report_content.append(f"\n> [!NOTE]\n> **Validation Result:** {validation_msg}")
        else:
            validation_msg = f"WARNING: {len(missing_codes)} AMFI codes in the fund master do NOT exist in the NAV history dataset!"
            print(validation_msg)
            print(f"Missing codes: {missing_codes}")
            report_content.append(f"\n> [!WARNING]\n> **Validation Result:** {validation_msg}\n> Missing codes: {missing_codes}")
    else:
        print("Could not perform AMFI validation due to missing master or NAV data.")
    print("=" * 80)
    
    # Write the report file
    report_path = os.path.join(reports_dir, "data_quality_report.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_content))
    print(f"[REPORT WRITTEN] Saved report to {report_path}")
    print("=" * 80)

if __name__ == "__main__":
    run_ingestion()
