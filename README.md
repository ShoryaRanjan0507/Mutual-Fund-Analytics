# Bluestock Insight 360: Data Warehouse & Quantitative Risk Platform

Welcome to the **Bluestock Mutual Fund Analytics** repository. This project modernization establishes a unified data warehouse and quant platform for Bluestock's retail mutual fund offerings, centering on an end-to-end star schema ETL, quantitative risk modeling, investor cohort tracking, and portfolio concentration analysis.

---

## 1. Project Architecture & Workflow

The pipeline parses and links ten primary raw CSV datasets, standardizing and cleaning data daily before storing it in a SQLite star-schema database. It then executes Jupyer analytical scripts, plots charts, and provides decision-making CLI tools.

```
       [ 10 Raw CSVs ]
              │
              ▼
    [ data_ingestion.py ]  ──> Generates Initial Data Quality Report
              │
              ▼
      [ clean_data.py ]    ──> Standardizes, Deduplicates, & Holiday Forward-fills
              │
              ▼
       [ load_db.py ]      ──> Populates bluestock_mf.db Star Schema
              │
              ▼
    [ verify_ingestion.py] ──> Tests Constraints & Runs 10 SQL Analytics
              │
    ┌─────────┴─────────┐
    ▼                   ▼
[ notebooks ]      [ deliverables ]
  - EDA_Analysis     - var_cvar_report.csv
  - Performance      - rolling_sharpe_chart.png
  - Advanced         - recommender.py (CLI Tool)
```

---

## 2. Setup & Installation

Ensure you have Python 3.8+ installed. 

1. **Clone or navigate to the workspace**:
   ```bash
   cd "c:/Mutual Fund Analytics"
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. How to Run the Pipeline

Execute the master orchestrator to run all ETL, schema creation, query tests, notebook compilations, and PDF generation steps:
```bash
python run_pipeline.py
```

### Expected Output Summary
```text
================================================================================
                       ETL PIPELINE EXECUTION SUMMARY
================================================================================
  Pipeline Step                                 | Status     | Duration    
--------------------------------------------------------------------------------
  Data Ingestion & Quality Report               | SUCCESS    | 0.95s       
  Data Cleaning & Standardization               | SUCCESS    | 1.12s       
  Star Schema Database Loading                  | SUCCESS    | 0.45s       
  Referential Integrity & Query Verification     | SUCCESS    | 0.58s       
  Exploratory Data Analysis Notebook (16 Charts)| SUCCESS    | 12.30s      
  Performance Scorecard Notebook & CSVs         | SUCCESS    | 4.12s       
  Advanced Analytics Notebook, VaR & Sharpe Plot| SUCCESS    | 5.80s       
  Dashboard PDF Build Consolidation             | SUCCESS    | 0.10s       
================================================================================
  Total Pipeline Duration: 25.42 seconds
  Pipeline Result: SUCCESS
================================================================================
```

---

## 4. Analytical Tools & Utilities

### 4.1 Interactive Recommender Utility
Recommends the top 3 schemes matching a user's risk profile based on historical risk-adjusted efficiency (Sharpe Ratio).

- **Execution**:
  ```bash
  python recommender.py --risk Moderate
  ```
- **Arguments**:
  - `-r` or `--risk`: `Low`, `Moderate`, or `High` (case-insensitive).
  - *Fallback*: If executed without arguments, it prompts for interactive keyboard input.

---

## 5. Dataset Dictionary

| Table Name | Source CSV | Shape | Key Join Columns | Description |
| :--- | :--- | :--- | :--- | :--- |
| `dim_fund` | `01_fund_master.csv` | 40 x 15 | `amfi_code` (PK) | Schemes launch dates, expenses, and managers. |
| `dim_date` | Generated | 1,609 x 9 | `date` (PK) | Continuous calendar time slice dimension. |
| `fact_nav` | `02_nav_history.csv` | 64,320 x 3 | `amfi_code`, `date` (PKs)| Daily Net Asset Values (forward-filled). |
| `fact_transactions`| `08_investor_transactions.csv` | 32,778 x 14 | `transaction_id` (PK) | Retail transactions (SIP, lumpsum, redemption). |
| `fact_performance` | `07_scheme_performance.csv`| 40 x 16 | `amfi_code` (PK) | Volatilities, drawdowns, alphas, and betas. |
| `fact_aum` | `03_aum_by_fund_house.csv` | 240 x 6 | `aum_id` (PK) | Quarterly historical assets per AMC. |

---

## 6. Project Deliverables

- **SQLite Database**: `bluestock_mf.db` (Normalized star schema)
- **Analytical Notebooks**:
  - `EDA_Analysis.ipynb`: 16 charts representing trends, demographics, and segments.
  - `Performance_Analytics.ipynb`: Alpha/Beta, cage ratios, and Composite Scorecard ranking.
  - `Advanced_Analytics.ipynb`: Historical VaR (95%), CVaR (95%), investor cohorts, and sector HHI rankings.
- **Tail-Risk CSV Report**: `var_cvar_report.csv` (Historical VaR/CVaR metrics)
- **Sharpe Curve Plot**: `rolling_sharpe_chart.png` (90-day rolling Sharpe timelines for 5 key schemes)
- **Consolidated PDF**: `Dashboard.pdf` (Multi-page dashboard compilation)
- **Recommender CLI**: `recommender.py`
