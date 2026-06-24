# Mutual Fund Analytics

Project scaffolding for mutual fund data ingestion and initial validation.

## Structure

- `data/raw/` - incoming CSV datasets and raw NAV exports
- `data/processed/` - cleansed and derived datasets
- `notebooks/` - Jupyter notebooks for exploration
- `sql/` - SQL scripts and queries
- `dashboard/` - dashboard assets and exports
- `reports/` - summary reports and deliverables

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Place your 10 CSV datasets into `data/raw/`.
4. Run the ingestion script:
   ```bash
   python mutual_fund_ingestion.py
   ```

## Notes

- The script loads all CSV files in `data/raw/` and prints dataset shape, dtypes, head, and anomalies.
- It fetches live NAV data for HDFC Top 100 Direct and five key schemes, then saves them to `data/raw/`.
- It inspects `fund_master` metadata and validates AMFI codes against `nav_history` data if those files are present.
