"""
Mutual Fund Analytics - Sharpe Ratio-Based Recommender Utility

This command-line utility recommends the top 3 mutual fund schemes
matching the user's stated risk appetite (Low, Moderate, or High)
based on their historical annualized Sharpe ratio.
"""

import os
import sqlite3
import argparse
import sys

def get_recommendations(risk_appetite):
    """
    Connects to the database and selects the top 3 mutual fund schemes
    matching the given risk appetite by Sharpe ratio, formatting the output
    as an ASCII table.
    """
    appetite = risk_appetite.strip().lower()
    
    # Map input to database categories
    if appetite == 'low':
        target_grades = ['Low']
        appetite_label = 'Low'
    elif appetite == 'moderate':
        target_grades = ['Moderate', 'Moderately High']
        appetite_label = 'Moderate'
    elif appetite == 'high':
        target_grades = ['High', 'Very High']
        appetite_label = 'High'
    else:
        print(f"Error: Invalid risk appetite '{risk_appetite}'. Choose from Low, Moderate, or High.")
        sys.exit(1)
        
    db_path = "bluestock_mf.db"
    if not os.path.exists(db_path):
        if os.path.exists("c:/Mutual Fund Analytics/bluestock_mf.db"):
            db_path = "c:/Mutual Fund Analytics/bluestock_mf.db"
        else:
            print(f"Error: Database file '{db_path}' not found. Run from the workspace root.")
            sys.exit(1)
            
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query top 3 funds
    placeholders = ','.join('?' for _ in target_grades)
    query = f"""
        SELECT f.amfi_code, f.scheme_name, f.risk_category, p.sharpe_ratio
        FROM dim_fund f
        JOIN fact_performance p ON f.amfi_code = p.amfi_code
        WHERE f.risk_category IN ({placeholders})
        ORDER BY p.sharpe_ratio DESC
        LIMIT 3
    """
    
    cursor.execute(query, target_grades)
    rows = cursor.fetchall()
    conn.close()
    
    print("=" * 100)
    print(f"                       MUTUAL FUND RECOMMENDER SYSTEM (Risk Appetite: {appetite_label})")
    print("=" * 100)
    
    if not rows:
        print("No schemes matched the specified risk appetite.")
        return
        
    header_fmt = "  {:<10} | {:<50} | {:<15} | {:<12}"
    row_fmt = "  {:<10} | {:<50} | {:<15} | {:<12.2f}"
    
    print(header_fmt.format("AMFI Code", "Scheme Name", "Risk Category", "Sharpe Ratio"))
    print("-" * 100)
    for row in rows:
        amfi_code, scheme_name, risk_category, sharpe_ratio = row
        display_name = scheme_name[:47] + "..." if len(scheme_name) > 50 else scheme_name
        print(row_fmt.format(amfi_code, display_name, risk_category, sharpe_ratio))
        
    print("=" * 100)
    print("  * Recommendations are based on historical risk-adjusted efficiency (Sharpe Ratio).")
    print("=" * 100)

def main():
    """
    Entry point supporting command-line arguments and interactive prompts.
    """
    parser = argparse.ArgumentParser(description="Simple Mutual Fund Recommender Utility.")
    parser.add_argument(
        '-r', '--risk', 
        type=str, 
        help="Risk appetite: Low, Moderate, or High (case-insensitive)."
    )
    args = parser.parse_args()
    
    if args.risk:
        get_recommendations(args.risk)
    else:
        print("Welcome to the Mutual Fund Recommender!")
        try:
            user_input = input("Enter your risk appetite (Low / Moderate / High): ")
            get_recommendations(user_input)
        except KeyboardInterrupt:
            print("\nExiting recommender.")
            sys.exit(0)

if __name__ == "__main__":
    main()
