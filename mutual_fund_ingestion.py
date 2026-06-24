import json
import os
import re
from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

SCHEMES = {
    "125497": "HDFC_Top_100_Direct",
    "119551": "SBI_Bluechip",
    "120503": "ICICI_Bluechip",
    "118632": "Nippon_Large_Cap",
    "119092": "Axis_Bluechip",
    "120841": "Kotak_Bluechip",
}


def ensure_directories():
    for path in [RAW_DIR, PROCESSED_DIR, Path("notebooks"), Path("sql"), Path("dashboard"), Path("reports")]:
        path.mkdir(parents=True, exist_ok=True)


def normalize_dataset_name(name: str) -> str:
    normalized = name.lower().strip()
    normalized = re.sub(r"^\d+_", "", normalized)
    return normalized


def load_csv_datasets(raw_dir: Path):
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in data/raw/. Place your datasets there and rerun.")
        return {}

    datasets = {}
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
        except Exception as exc:
            print(f"Failed to read {csv_file.name}: {exc}")
            continue

        normalized_name = normalize_dataset_name(csv_file.stem)
        print("\n============================================")
        print(f"Dataset: {csv_file.name} (normalized: {normalized_name})")
        print(f"Shape: {df.shape}")
        print("Dtypes:")
        print(df.dtypes)
        print("Head:")
        print(df.head(5).to_string(index=False))

        missing = df.isna().sum()
        duplicates = df.duplicated().sum()
        print("Missing values per column:")
        print(missing[missing > 0].to_string() if missing.any() else "None")
        print(f"Duplicate rows: {duplicates}")

        datasets[normalized_name] = df

    return datasets


def nav_api_to_csv(scheme_code: str, scheme_name: str, raw_dir: Path):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"Fetching NAV for {scheme_name} ({scheme_code}) from {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        print(f"Failed to fetch NAV for {scheme_name}: {exc}")
        return None

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON response for {scheme_name}: {exc}")
        return None

    records = []
    for item in data.get("data", []):
        records.append({
            "scheme_code": scheme_code,
            "scheme_name": scheme_name,
            "date": item.get("date"),
            "nav": item.get("nav"),
        })

    if not records:
        print(f"No NAV records returned for {scheme_name}.")
        return None

    out_path = raw_dir / f"nav_{scheme_code}_{scheme_name}.csv"
    pd.DataFrame(records).to_csv(out_path, index=False)
    print(f"Saved NAV history to {out_path}")
    return out_path


def fetch_all_nav(raw_dir: Path):
    for scheme_code, scheme_name in SCHEMES.items():
        nav_api_to_csv(scheme_code, scheme_name, raw_dir)


def explore_fund_master(df: pd.DataFrame):
    print("\n=== Fund master exploration ===")
    for column in ["fund_house", "category", "sub_category", "risk_grade"]:
        if column in df.columns:
            unique_values = df[column].dropna().unique()
            print(f"{column}: {len(unique_values)} unique values")
            print(sorted(unique_values)[:20])
        else:
            print(f"Column '{column}' not found in fund_master.")

    if "scheme_code" in df.columns:
        sample_codes = df["scheme_code"].dropna().astype(str).head(10).tolist()
        print("Sample AMFI scheme codes:", sample_codes)
        print("AMFI scheme code lengths:", sorted(df["scheme_code"].dropna().astype(str).map(len).unique()))


def validate_amfi_codes(master_df: pd.DataFrame, nav_history_df: pd.DataFrame):
    if "scheme_code" not in master_df.columns:
        print("fund_master is missing scheme_code column.")
        return
    if "scheme_code" not in nav_history_df.columns:
        print("nav_history is missing scheme_code column.")
        return

    master_codes = set(master_df["scheme_code"].dropna().astype(str).unique())
    nav_codes = set(nav_history_df["scheme_code"].dropna().astype(str).unique())
    missing_in_nav = sorted(master_codes - nav_codes)
    missing_in_master = sorted(nav_codes - master_codes)

    print("\n=== AMFI code validation ===")
    print(f"Unique codes in fund_master: {len(master_codes)}")
    print(f"Unique codes in nav_history: {len(nav_codes)}")
    print(f"Codes in fund_master missing from nav_history: {len(missing_in_nav)}")
    if missing_in_nav:
        print(missing_in_nav[:50])
    print(f"Codes in nav_history missing from fund_master: {len(missing_in_master)}")
    if missing_in_master:
        print(missing_in_master[:50])


def main():
    ensure_directories()
    datasets = load_csv_datasets(RAW_DIR)
    fetch_all_nav(RAW_DIR)

    fund_master = datasets.get("fund_master")
    nav_history = datasets.get("nav_history")

    if fund_master is not None:
        explore_fund_master(fund_master)

    if fund_master is not None and nav_history is not None:
        validate_amfi_codes(fund_master, nav_history)
    elif fund_master is None:
        print("Fund master validation skipped because fund_master dataset is missing.")
    elif nav_history is None:
        print("NAV history validation skipped because nav_history dataset is missing.")


if __name__ == "__main__":
    main()
