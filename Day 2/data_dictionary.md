
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
