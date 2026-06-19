"""
Mutual Fund Analytics - Star Schema Referential Integrity & Analytical Query Verification

This module performs validations across row counts and database foreign key checks,
then executes the 10 analytical SQL queries from queries.sql.
"""

import os
import sqlite3
import pandas as pd

def verify_all():
    """
    Validates database schema constraints, matches table sizes,
    and runs the analytical queries to ensure execution accuracy.
    """
    db_path = "bluestock_mf.db"
    processed_dir = os.path.join("data", "processed")
    queries_file = "queries.sql"
    
    print("=" * 80)
    print("STARTING DATA AND QUERY VERIFICATION PROCESS")
    print("=" * 80)
    
    # 1. Check database exists
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file '{db_path}' not found!")
        return False
    print(f"[VERIFY] Database file '{db_path}' exists.")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # 2. Check foreign key constraints
    print("\n[VERIFY] Checking Foreign Key Constraints...")
    fk_check = pd.read_sql_query("PRAGMA foreign_key_check", conn)
    if fk_check.empty:
        print("  -> SUCCESS: All foreign key constraints are 100% intact (0 violations).")
    else:
        print("  -> WARNING: Found foreign key violations!")
        print(fk_check)
        
    # 3. Verify row counts matching source CSVs
    print("\n[VERIFY] Verifying Table Row Counts against CSVs...")
    tables_to_verify = [
        ("01_fund_master.csv", "dim_fund"),
        ("02_nav_history.csv", "fact_nav"),
        ("03_aum_by_fund_house.csv", "fact_aum"),
        ("07_scheme_performance.csv", "fact_performance"),
        ("08_investor_transactions.csv", "fact_transactions"),
        ("04_monthly_sip_inflows.csv", "sip_inflows"),
        ("05_category_inflows.csv", "category_inflows"),
        ("06_industry_folio_count.csv", "industry_folio_count"),
        ("09_portfolio_holdings.csv", "portfolio_holdings"),
        ("10_benchmark_indices.csv", "benchmark_indices")
    ]
    
    mismatches = 0
    for csv_file, table_name in tables_to_verify:
        csv_path = os.path.join(processed_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"  - [ERROR] Processed CSV '{csv_file}' not found!")
            mismatches += 1
            continue
            
        csv_count = len(pd.read_csv(csv_path))
        db_count = pd.read_sql_query(f"SELECT COUNT(*) FROM {table_name}", conn).iloc[0, 0]
        
        if csv_count == db_count:
            print(f"  - Table '{table_name}': Match ({db_count} rows)")
        else:
            print(f"  - Table '{table_name}': MISMATCH! DB has {db_count}, CSV has {csv_count}")
            mismatches += 1
            
    if mismatches == 0:
        print("  -> SUCCESS: All row counts match processed source files perfectly.")
    else:
        print(f"  -> WARNING: Found {mismatches} row count mismatches.")
        
    # 4. Read and execute the 10 analytical queries
    print("\n[VERIFY] Executing 10 Analytical Queries...")
    if not os.path.exists(queries_file):
        print(f"[ERROR] Queries file '{queries_file}' not found!")
        conn.close()
        return False
        
    with open(queries_file, "r") as f:
        queries_content = f.read()
        
    # Split queries by semicolon
    queries = [q.strip() for q in queries_content.split(";") if q.strip()]
    
    query_idx = 1
    for query in queries:
        lines = query.split("\n")
        label = f"Query {query_idx}"
        for line in lines:
            if line.strip().startswith("--"):
                label = line.strip().replace("--", "").strip()
                break
                
        print(f"\nRunning: {label}")
        print("-" * 50)
        try:
            df_res = pd.read_sql_query(query, conn)
            # print snippet of first 2 rows for checking
            print(df_res.head(2))
            print(f"Total rows returned: {len(df_res)}")
        except Exception as e:
            print(f"[ERROR] Failed to run query: {e}")
            
        query_idx += 1
        
    conn.close()
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    return True

if __name__ == "__main__":
    verify_all()
