from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parent
RAW_DIR = WORKSPACE_ROOT / "Day 1" / "data" / "raw"
PROCESSED_DIR = WORKSPACE_ROOT / "Day 1" / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "bluestock_mf.db"
SCHEMA_PATH = ROOT / "schema.sql"
QUERIES_PATH = ROOT / "queries.sql"
DICT_PATH = ROOT / "data_dictionary.md"


def parse_date(series, fmt=None):
    if fmt:
        return pd.to_datetime(series, format=fmt, errors="coerce").dt.normalize()
    return pd.to_datetime(series, errors="coerce").dt.normalize()


def standardize_text(series):
    return series.astype(str).str.strip().replace({"nan": None})


def clean_fund_master():
    df = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    df["launch_date"] = parse_date(df["launch_date"])
    for col in ["expense_ratio_pct", "exit_load_pct", "min_sip_amount", "min_lumpsum_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["category"] = standardize_text(df["category"]).str.title()
    df["plan"] = standardize_text(df["plan"]).str.title()
    df["benchmark"] = standardize_text(df["benchmark"])
    return df


def clean_nav_history():
    df = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    df["date"] = parse_date(df["date"])
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna(subset=["amfi_code", "date", "nav"]).copy()
    df = df[df["nav"] > 0].copy()
    df = df.sort_values(["amfi_code", "date"]) 
    df = df.drop_duplicates(["amfi_code", "date"], keep="last")

    filled = []
    for code, group in df.groupby("amfi_code", sort=False):
        group = group.set_index("date").sort_index()
        expanded = group.asfreq("D")
        expanded["amfi_code"] = code
        expanded["nav"] = expanded["nav"].ffill()
        expanded = expanded.dropna(subset=["nav"]).reset_index()
        filled.append(expanded)

    df_clean = pd.concat(filled, ignore_index=True)
    df_clean = df_clean["amfi_code date nav".split()]
    return df_clean


def clean_aum_by_fund_house():
    df = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")
    df["date"] = parse_date(df["date"])
    df["fund_house"] = standardize_text(df["fund_house"])
    df["aum_lakh_crore"] = pd.to_numeric(df["aum_lakh_crore"], errors="coerce")
    df["aum_crore"] = pd.to_numeric(df["aum_crore"], errors="coerce")
    df["num_schemes"] = pd.to_numeric(df["num_schemes"], errors="coerce").astype("Int64")
    return df.dropna(subset=["date", "fund_house"])


def clean_monthly_sip_inflows():
    df = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")
    df["month"] = parse_date(df["month"])
    for col in ["sip_inflow_crore", "active_sip_accounts_crore", "new_sip_accounts_lakh", "sip_aum_lakh_crore", "yoy_growth_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def clean_category_inflows():
    df = pd.read_csv(RAW_DIR / "05_category_inflows.csv")
    df["month"] = parse_date(df["month"])
    df["category"] = standardize_text(df["category"]).str.title()
    df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce")
    return df


def clean_industry_folio_count():
    df = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv")
    df["month"] = parse_date(df["month"])
    for col in ["total_folios_crore", "equity_folios_crore", "debt_folios_crore", "hybrid_folios_crore", "others_folios_crore"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def clean_scheme_performance():
    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    numeric_cols = [
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "aum_crore",
        "expense_ratio_pct",
        "morningstar_rating",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["scheme_name"] = standardize_text(df["scheme_name"])
    df["fund_house"] = standardize_text(df["fund_house"])
    df["category"] = standardize_text(df["category"]).str.title()
    df["plan"] = standardize_text(df["plan"]).str.title()
    df["risk_grade"] = standardize_text(df["risk_grade"]).str.title()

    anomalies = []
    for _, row in df.iterrows():
        notes = []
        for col in numeric_cols:
            if pd.isna(row[col]):
                notes.append(f"{col} invalid")
        if not pd.isna(row["expense_ratio_pct"]):
            if not (0.1 <= row["expense_ratio_pct"] <= 2.5):
                notes.append("expense_ratio_pct out of range")
        if notes:
            anomalies.append("; ".join(notes))
        else:
            anomalies.append("")
    df["anomaly_notes"] = anomalies
    df["anomaly_flag"] = df["anomaly_notes"].astype(bool)
    return df


def clean_investor_transactions():
    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
    df["transaction_date"] = parse_date(df["transaction_date"])
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")

    mapping = {
        "sip": "SIP",
        "sips": "SIP",
        "lumpsum": "Lumpsum",
        "lump sum": "Lumpsum",
        "lump-sum": "Lumpsum",
        "redemption": "Redemption",
        "redeem": "Redemption",
    }
    df["transaction_type"] = (
        df["transaction_type"].astype(str)
        .str.strip()
        .str.lower()
        .replace(mapping)
        .replace({"sip": "SIP", "lumpsum": "Lumpsum", "redemption": "Redemption"})
    )
    valid_transaction_types = {"SIP", "Lumpsum", "Redemption"}
    df.loc[~df["transaction_type"].isin(valid_transaction_types), "transaction_type"] = None

    df["state"] = standardize_text(df["state"]).str.title()
    df["city"] = standardize_text(df["city"]).str.title()
    df["city_tier"] = standardize_text(df["city_tier"]).str.upper()
    df["age_group"] = standardize_text(df["age_group"])
    df["gender"] = standardize_text(df["gender"]).str.title()
    df["payment_mode"] = standardize_text(df["payment_mode"]).str.title()
    df["kyc_status"] = standardize_text(df["kyc_status"]).replace(
        {
            "Verified": "Verified",
            "Pending": "Pending",
            "Not Verified": "Not Verified",
            "Not verified": "Not Verified",
            "Rejected": "Rejected",
        }
    )
    valid_kyc = {"Verified", "Pending", "Not Verified", "Rejected"}
    df.loc[~df["kyc_status"].isin(valid_kyc), "kyc_status"] = "Unknown"

    df = df.dropna(subset=["investor_id", "transaction_date", "amfi_code", "amount_inr"])
    df = df[df["amount_inr"] > 0]
    return df


def clean_portfolio_holdings():
    df = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")
    df["portfolio_date"] = parse_date(df["portfolio_date"])
    df["weight_pct"] = pd.to_numeric(df["weight_pct"], errors="coerce")
    df["market_value_cr"] = pd.to_numeric(df["market_value_cr"], errors="coerce")
    df["current_price_inr"] = pd.to_numeric(df["current_price_inr"], errors="coerce")
    df["stock_symbol"] = standardize_text(df["stock_symbol"]).str.upper()
    df["stock_name"] = standardize_text(df["stock_name"])
    df["sector"] = standardize_text(df["sector"]).str.title()
    return df


def clean_benchmark_indices():
    df = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv")
    df["date"] = parse_date(df["date"])
    df["index_name"] = standardize_text(df["index_name"]).str.title()
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")
    return df


def write_clean_csvs(cleaned):
    for name, df in cleaned.items():
        dest = PROCESSED_DIR / name
        df.to_csv(dest, index=False)


def build_date_dimension(date_frames):
    all_dates = pd.concat(date_frames, ignore_index=True).dropna().unique()
    all_dates = pd.to_datetime(all_dates).normalize()
    df = pd.DataFrame({"date": np.sort(all_dates)})
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.weekday >= 5
    df["is_business_day"] = ~df["is_weekend"]
    df["month_name"] = df["date"].dt.month_name()
    df["quarter_name"] = "Q" + df["quarter"].astype(str)
    return df


def build_schema_sql():
    return """
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_business_day BOOLEAN NOT NULL,
    month_name TEXT NOT NULL,
    quarter_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT,
    fund_house TEXT,
    category TEXT,
    plan TEXT,
    benchmark TEXT,
    launch_date DATE,
    expense_ratio_pct REAL,
    risk_category TEXT
);

CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    nav REAL NOT NULL,
    PRIMARY KEY (amfi_code, date_key),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    transaction_type TEXT,
    amount_inr REAL NOT NULL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code INTEGER NOT NULL,
    snapshot_date_key INTEGER NOT NULL,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating REAL,
    risk_grade TEXT,
    anomaly_flag BOOLEAN,
    anomaly_notes TEXT,
    PRIMARY KEY (amfi_code, snapshot_date_key),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (snapshot_date_key) REFERENCES dim_date (date_key)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    date_key INTEGER NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER,
    PRIMARY KEY (date_key, fund_house),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);
"""


def write_supporting_files():
    SCHEMA_PATH.write_text(build_schema_sql(), encoding="utf-8")
    QUERIES_PATH.write_text(
        """
-- 1. Top 5 funds by latest AUM in fact_aum
SELECT fund_house, aum_crore
FROM fact_aum
WHERE date_key = (SELECT MAX(date_key) FROM fact_aum)
ORDER BY aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month for each fund
SELECT d.year,
       d.month,
       n.amfi_code,
       f.scheme_name,
       AVG(n.nav) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date_key = d.date_key
LEFT JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY d.year, d.month, n.amfi_code, f.scheme_name
ORDER BY d.year, d.month, avg_nav DESC;

-- 3. Year-over-year SIP growth by year
WITH sip_totals AS (
    SELECT d.year AS year,
           SUM(t.amount_inr) AS total_sip
    FROM fact_transactions t
    JOIN dim_date d ON t.date_key = d.date_key
    WHERE t.transaction_type = 'SIP'
    GROUP BY d.year
)
SELECT year,
       total_sip,
       LAG(total_sip) OVER (ORDER BY year) AS prior_year_sip,
       ROUND(100.0 * (total_sip - LAG(total_sip) OVER (ORDER BY year)) / NULLIF(LAG(total_sip) OVER (ORDER BY year), 0), 2) AS yoy_growth_pct
FROM sip_totals
ORDER BY year;

-- 4. Transactions count and volume by investor state
SELECT state,
       COUNT(*) AS transaction_count,
       SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- 5. Funds with expense ratio below 1%
SELECT amfi_code,
       scheme_name,
       fund_house,
       expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- 6. Top 5 funds by 5-year return
SELECT amfi_code,
       scheme_name,
       return_5yr_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY return_5yr_pct DESC
LIMIT 5;

-- 7. Total transactions and amount by fund house
SELECT f.fund_house,
       COUNT(*) AS transactions,
       SUM(t.amount_inr) AS total_amount_inr
FROM fact_transactions t
JOIN dim_fund f ON t.amfi_code = f.amfi_code
GROUP BY f.fund_house
ORDER BY total_amount_inr DESC
LIMIT 10;

-- 8. Redemption share by year
SELECT d.year,
       SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount_inr ELSE 0 END) AS redemption_amount,
       SUM(t.amount_inr) AS total_amount
FROM fact_transactions t
JOIN dim_date d ON t.date_key = d.date_key
GROUP BY d.year
ORDER BY d.year;

-- 9. NAV volatility by fund (standard deviation of NAV)
SELECT n.amfi_code,
       f.scheme_name,
       ROUND(STDDEV(n.nav), 4) AS nav_stddev
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY n.amfi_code, f.scheme_name
ORDER BY nav_stddev DESC
LIMIT 10;

-- 10. AUM growth trend by date for top fund houses
SELECT d.date,
       a.fund_house,
       a.aum_crore
FROM fact_aum a
JOIN dim_date d ON a.date_key = d.date_key
WHERE a.fund_house IN (
    SELECT fund_house
    FROM fact_aum
    WHERE date_key = (SELECT MAX(date_key) FROM fact_aum)
    ORDER BY aum_crore DESC
    LIMIT 5
)
ORDER BY a.fund_house, d.date;
""",
        encoding="utf-8",
    )
    DICT_PATH.write_text(
        """
# Data Dictionary

## dim_date
- `date_key` (INTEGER): Surrogate key in YYYYMMDD format. Derived from all date columns across loaded datasets.
- `date` (DATE): Calendar date.
- `year` (INTEGER): Calendar year.
- `quarter` (INTEGER): Quarter of the year.
- `month` (INTEGER): Month number.
- `day` (INTEGER): Day of month.
- `day_of_week` (TEXT): Day name.
- `is_weekend` (BOOLEAN): True if Saturday or Sunday.
- `is_business_day` (BOOLEAN): True when not weekend.
- `month_name` (TEXT): Full month name.
- `quarter_name` (TEXT): Quarter label.

## dim_fund
- `amfi_code` (INTEGER): Unique identifier for each mutual fund scheme.
- `scheme_name` (TEXT): Full scheme name.
- `fund_house` (TEXT): Asset management company.
- `category` (TEXT): Fund category.
- `plan` (TEXT): Plan type such as Regular or Direct.
- `benchmark` (TEXT): Benchmark index.
- `launch_date` (DATE): Date the scheme was launched.
- `expense_ratio_pct` (REAL): Expense ratio percentage.
- `risk_category` (TEXT): Risk category from the fund master source.

## fact_nav
- `amfi_code` (INTEGER): Foreign key to `dim_fund`.
- `date_key` (INTEGER): Foreign key to `dim_date`.
- `nav` (REAL): Net asset value per unit.

Source: `Day 1/data/raw/02_nav_history.csv`

## fact_transactions
- `transaction_id` (INTEGER): Auto-generated transaction record key.
- `investor_id` (TEXT): Unique investor identifier.
- `amfi_code` (INTEGER): Foreign key to `dim_fund`.
- `date_key` (INTEGER): Foreign key to `dim_date`.
- `transaction_type` (TEXT): Normalized into SIP, Lumpsum, or Redemption.
- `amount_inr` (REAL): Transaction amount in INR.
- `state` (TEXT): Investor state.
- `city` (TEXT): Investor city.
- `city_tier` (TEXT): City tier code.
- `age_group` (TEXT): Age bracket.
- `gender` (TEXT): Investor gender.
- `annual_income_lakh` (REAL): Annual income in lakhs.
- `payment_mode` (TEXT): Payment method.
- `kyc_status` (TEXT): KYC status normalized to Verified, Pending, Not Verified, Rejected, or Unknown.

Source: `Day 1/data/raw/08_investor_transactions.csv`

## fact_performance
- `amfi_code` (INTEGER): Foreign key to `dim_fund`.
- `snapshot_date_key` (INTEGER): Foreign key to `dim_date` representing the performance snapshot date.
- `return_1yr_pct` (REAL): One-year return percentage.
- `return_3yr_pct` (REAL): Three-year return percentage.
- `return_5yr_pct` (REAL): Five-year return percentage.
- `benchmark_3yr_pct` (REAL): Benchmark three-year return.
- `alpha` (REAL): Alpha.
- `beta` (REAL): Beta.
- `sharpe_ratio` (REAL): Sharpe ratio.
- `sortino_ratio` (REAL): Sortino ratio.
- `std_dev_ann_pct` (REAL): Annualized standard deviation percentage.
- `max_drawdown_pct` (REAL): Maximum drawdown percentage.
- `aum_crore` (REAL): AUM in crores.
- `expense_ratio_pct` (REAL): Expense ratio percentage.
- `morningstar_rating` (REAL): Morningstar rating.
- `risk_grade` (TEXT): Risk grade.
- `anomaly_flag` (BOOLEAN): True when numeric validation or range checks found issues.
- `anomaly_notes` (TEXT): Notes describing any data anomalies.

Source: `Day 1/data/raw/07_scheme_performance.csv`

## fact_aum
- `date_key` (INTEGER): Foreign key to `dim_date`.
- `fund_house` (TEXT): Asset management company name.
- `aum_lakh_crore` (REAL): AUM in lakh crore.
- `aum_crore` (REAL): AUM in crore.
- `num_schemes` (INTEGER): Number of schemes held by the fund house.

Source: `Day 1/data/raw/03_aum_by_fund_house.csv`
""",
        encoding="utf-8",
    )


def load_database(cleaned):
    if DB_PATH.exists():
        DB_PATH.unlink()

    engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}", echo=False, future=True)
    schema_sql = build_schema_sql()
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON;")
    with engine.raw_connection() as raw_conn:
        raw_conn.executescript(schema_sql)

    # Build and load date dimension from all relevant date columns.
    date_frames = [
        cleaned["01_fund_master.csv"]["launch_date"].dropna(),
        cleaned["02_nav_history.csv"]["date"].dropna(),
        cleaned["03_aum_by_fund_house.csv"]["date"].dropna(),
        cleaned["04_monthly_sip_inflows.csv"]["month"].dropna(),
        cleaned["05_category_inflows.csv"]["month"].dropna(),
        cleaned["06_industry_folio_count.csv"]["month"].dropna(),
        cleaned["08_investor_transactions.csv"]["transaction_date"].dropna(),
        cleaned["09_portfolio_holdings.csv"]["portfolio_date"].dropna(),
        cleaned["10_benchmark_indices.csv"]["date"].dropna(),
    ]
    date_dim = build_date_dimension(date_frames)
    date_dim.to_sql("dim_date", engine, if_exists="append", index=False)

    # Load dim_fund with the union of fund master and performance schemes.
    fund_master = cleaned["01_fund_master.csv"].copy()
    performance = cleaned["07_scheme_performance.csv"].copy()
    performance = performance[["amfi_code", "scheme_name", "fund_house", "category", "plan", "expense_ratio_pct", "risk_grade"]]
    fund_ref = fund_master.merge(performance, on="amfi_code", how="outer", suffixes=("", "_perf"))
    fund_ref["scheme_name"] = fund_ref["scheme_name"].fillna(fund_ref["scheme_name_perf"])
    fund_ref["fund_house"] = fund_ref["fund_house"].fillna(fund_ref["fund_house_perf"])
    fund_ref["category"] = fund_ref["category"].fillna(fund_ref["category_perf"])
    fund_ref["plan"] = fund_ref["plan"].fillna(fund_ref["plan_perf"])
    fund_ref["expense_ratio_pct"] = fund_ref["expense_ratio_pct"].fillna(fund_ref["expense_ratio_pct_perf"])
    fund_ref["risk_category"] = fund_ref["risk_category"].fillna(fund_ref["risk_grade"])
    fund_ref = fund_ref[[
        "amfi_code",
        "scheme_name",
        "fund_house",
        "category",
        "plan",
        "benchmark",
        "launch_date",
        "expense_ratio_pct",
        "risk_category",
    ]].drop_duplicates(subset=["amfi_code"])
    with engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM dim_fund;")
    fund_ref.to_sql("dim_fund", engine, if_exists="append", index=False)

    nav = cleaned["02_nav_history.csv"].copy()
    nav = nav.merge(date_dim[["date_key", "date"]], on="date", how="left")
    nav["amfi_code"] = pd.to_numeric(nav["amfi_code"], errors="coerce").astype("Int64")
    nav.dropna(subset=["date_key"], inplace=True)
    nav["date_key"] = nav["date_key"].astype(int)
    nav = nav[["amfi_code", "date_key", "nav"]]
    nav.to_sql("fact_nav", engine, if_exists="append", index=False)

    tx = cleaned["08_investor_transactions.csv"].copy()
    tx = tx.merge(date_dim[["date_key", "date"]], left_on="transaction_date", right_on="date", how="left")
    tx.drop(columns=["date"], inplace=True)
    tx["amfi_code"] = pd.to_numeric(tx["amfi_code"], errors="coerce").astype("Int64")
    tx["amount_inr"] = pd.to_numeric(tx["amount_inr"], errors="coerce")
    tx = tx.dropna(subset=["amfi_code", "date_key", "amount_inr"])
    tx["date_key"] = tx["date_key"].astype(int)
    tx = tx[[
        "investor_id",
        "amfi_code",
        "date_key",
        "transaction_type",
        "amount_inr",
        "state",
        "city",
        "city_tier",
        "age_group",
        "gender",
        "annual_income_lakh",
        "payment_mode",
        "kyc_status",
    ]]
    tx.to_sql("fact_transactions", engine, if_exists="append", index=False)

    perf = cleaned["07_scheme_performance.csv"].copy()
    # Use a valid snapshot date for performance rows. If the source lacks an explicit date,
    # assign the most recent date in the date dimension.
    if "snapshot_date" in perf.columns:
        perf["snapshot_date"] = parse_date(perf["snapshot_date"])
        perf = perf.merge(date_dim[["date_key", "date"]], left_on="snapshot_date", right_on="date", how="left")
    else:
        if not date_dim.empty:
            perf["date_key"] = date_dim["date_key"].max()
        else:
            perf["date_key"] = pd.NA
    perf["snapshot_date_key"] = perf["date_key"].astype("Int64")
    perf = perf[[
        "amfi_code",
        "snapshot_date_key",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "aum_crore",
        "expense_ratio_pct",
        "morningstar_rating",
        "risk_grade",
        "anomaly_flag",
        "anomaly_notes",
    ]]
    perf.to_sql("fact_performance", engine, if_exists="append", index=False)

    aum = cleaned["03_aum_by_fund_house.csv"].copy()
    aum = aum.merge(date_dim[["date_key", "date"]], on="date", how="left")
    aum["date_key"] = aum["date_key"].astype(int)
    aum = aum[["date_key", "fund_house", "aum_lakh_crore", "aum_crore", "num_schemes"]]
    aum.to_sql("fact_aum", engine, if_exists="append", index=False)

    return {
        "dim_date": len(date_dim),
        "dim_fund": len(fund_ref),
        "fact_nav": len(nav),
        "fact_transactions": len(tx),
        "fact_performance": len(perf),
        "fact_aum": len(aum),
    }


def verify_counts(cleaned):
    raw_counts = {}
    for name in cleaned:
        raw_file = RAW_DIR / name
        raw_counts[name] = len(pd.read_csv(raw_file))
    cleaned_counts = {name: len(df) for name, df in cleaned.items()}
    return raw_counts, cleaned_counts


def main():
    cleaned = {
        "01_fund_master.csv": clean_fund_master(),
        "02_nav_history.csv": clean_nav_history(),
        "03_aum_by_fund_house.csv": clean_aum_by_fund_house(),
        "04_monthly_sip_inflows.csv": clean_monthly_sip_inflows(),
        "05_category_inflows.csv": clean_category_inflows(),
        "06_industry_folio_count.csv": clean_industry_folio_count(),
        "07_scheme_performance.csv": clean_scheme_performance(),
        "08_investor_transactions.csv": clean_investor_transactions(),
        "09_portfolio_holdings.csv": clean_portfolio_holdings(),
        "10_benchmark_indices.csv": clean_benchmark_indices(),
    }

    write_clean_csvs(cleaned)
    write_supporting_files()
    counts = verify_counts(cleaned)
    load_stats = load_database(cleaned)

    print("Raw row counts:")
    for name, count in counts[0].items():
        print(f"  {name}: {count}")
    print("\nCleaned row counts:")
    for name, count in counts[1].items():
        print(f"  {name}: {count}")
    print("\nLoaded SQLite row counts:")
    for table, count in load_stats.items():
        print(f"  {table}: {count}")
    print("\nCreated/updated files:\n  bluestock_mf.db\n  schema.sql\n  queries.sql\n  data_dictionary.md")


if __name__ == "__main__":
    main()
