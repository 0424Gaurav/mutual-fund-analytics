
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
