"""
Mutual Fund Analytics - Master ETL and Execution Pipeline

This script serves as the centralized orchestrator for the entire Capstone project.
It runs data ingestion, cleaning, database loading, schema verification, 
Jupyter Notebook generation, analytical charts plotting, and PDF consolidation.
"""

import time
import sys

# Import pipeline steps
try:
    from data_ingestion import run_ingestion
    from clean_data import clean_datasets
    from load_db import load_data_to_sqlite
    from verify_ingestion import verify_all
    from generate_eda import create_and_execute_notebook as run_eda
    from generate_analytics import create_and_run_analytics as run_performance
    from build_advanced_analytics import create_advanced_analytics_notebook as run_advanced
    from build_pdf import build_pdf
except ImportError as e:
    print(f"Error importing pipeline steps: {e}")
    sys.exit(1)

def run_pipeline():
    """
    Executes all steps of the analytical pipeline sequentially, measuring times
    and compiling a summary of execution statuses.
    """
    pipeline_steps = [
        ("Data Ingestion & Quality Report", run_ingestion),
        ("Data Cleaning & Standardization", clean_datasets),
        ("Star Schema Database Loading", load_data_to_sqlite),
        ("Referential Integrity & Query Verification", verify_all),
        ("Exploratory Data Analysis Notebook (16 Charts)", run_eda),
        ("Performance Scorecard Notebook & CSVs", run_performance),
        ("Advanced Analytics Notebook, VaR & Sharpe Plot", run_advanced),
        ("Dashboard PDF Build Consolidation", build_pdf)
    ]
    
    print("=" * 80)
    print("                 BLUESTOCK MUTUAL FUND ANALYTICS PIPELINE")
    print("=" * 80)
    
    execution_reports = []
    overall_success = True
    
    start_pipeline_time = time.time()
    
    for label, func in pipeline_steps:
        step_start = time.time()
        print(f"\n[PIPELINE STEP START] {label}")
        print("-" * 80)
        
        try:
            success = func()
        except Exception as e:
            print(f"[PIPELINE STEP ERROR] {label} failed with exception: {e}")
            success = False
            
        step_end = time.time()
        duration = step_end - step_start
        
        execution_reports.append({
            "step": label,
            "status": "SUCCESS" if success else "FAILED",
            "duration_sec": duration
        })
        
        if not success:
            overall_success = False
            # We continue running other steps to get a full report of what passes/fails
            
    end_pipeline_time = time.time()
    total_duration = end_pipeline_time - start_pipeline_time
    
    print("\n" + "=" * 80)
    print("                       ETL PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    header_fmt = "  {:<45} | {:<10} | {:<12}"
    row_fmt = "  {:<45} | {:<10} | {:<12.2f}s"
    print(header_fmt.format("Pipeline Step", "Status", "Duration"))
    print("-" * 80)
    for report in execution_reports:
        # Use simple color code markers (ASCII standard)
        status_str = report["status"]
        print(row_fmt.format(report["step"], status_str, report["duration_sec"]))
    print("=" * 80)
    print(f"Total Pipeline Duration: {total_duration:.2f} seconds")
    print(f"Pipeline Result: {'SUCCESS' if overall_success else 'FAILED'}")
    print("=" * 80)
    
    return overall_success

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
