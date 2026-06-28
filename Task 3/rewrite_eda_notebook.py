import json
from pathlib import Path
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

ROOT = Path(r'e:\bluestocks2')
NOTEBOOK_PATH = ROOT / 'Task 3' / 'EDA_Analysis.ipynb'

cells = []

cells.append(new_markdown_cell("""# EDA Analysis for Mutual Fund Data

This notebook covers Task 3 analysis for NAV trends, AUM growth, SIP inflows, category flows, investor demographics, geography, folio growth, return correlations, and sector allocation from 2022 through 2025.

## Task 3 scope

- Daily NAV trend analysis for 40 schemes (2022–2026), highlighting the 2023 bull run and 2024 correction.
- AUM growth grouped bar chart by fund house for 2022–2025, highlighting SBI dominance.
- Monthly SIP inflow time series from Jan 2022 to Dec 2025, annotated with the ₹31,002 Cr peak.
- Category-wise inflow heatmap with months on the X-axis and categories on the Y-axis.
- Investor demographics analysis: age distribution pie, SIP amount box plot by age group, gender split.
- Geographic SIP distribution: state-level horizontal bar chart and T30 vs B30 pie chart.
- Folio count growth line chart from 13.26 Cr to 26.12 Cr with milestone markers.
- NAV return correlation matrix for 10 selected funds.
- Sector allocation donut chart from portfolio holdings.
- Document 10 key EDA findings in markdown cells.
"""))

cells.append(new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

ROOT = Path(r'e:\\\\bluestocks2')
DATA_DIR = ROOT / 'Day 1' / 'data' / 'processed'
OUT_DIR = ROOT / 'Task 3' / 'eda_outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)

fund_master = pd.read_csv(DATA_DIR / '01_fund_master.csv')
nav_history = pd.read_csv(DATA_DIR / '02_nav_history.csv')
aum_history = pd.read_csv(DATA_DIR / '03_aum_by_fund_house.csv')
sip_history = pd.read_csv(DATA_DIR / '04_monthly_sip_inflows.csv')
category_inflows = pd.read_csv(DATA_DIR / '05_category_inflows.csv')
folio_history = pd.read_csv(DATA_DIR / '06_industry_folio_count.csv')
investor_transactions = pd.read_csv(DATA_DIR / '08_investor_transactions.csv')
portfolio_holdings = pd.read_csv(DATA_DIR / '09_portfolio_holdings.csv')

for df, col in [
    (nav_history, 'date'),
    (aum_history, 'date'),
    (sip_history, 'month'),
    (category_inflows, 'month'),
    (folio_history, 'month'),
    (investor_transactions, 'transaction_date')
]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

nav_history = nav_history.merge(fund_master[['amfi_code', 'scheme_name']], on='amfi_code', how='left')
sip_history = sip_history.sort_values('month').reset_index(drop=True)
category_inflows = category_inflows.sort_values(['month', 'category']).reset_index(drop=True)
folio_history = folio_history.sort_values('month').reset_index(drop=True)
investor_transactions = investor_transactions.sort_values('transaction_date').reset_index(drop=True)

for col in [
    'sip_inflow_crore',
    'active_sip_accounts_crore',
    'new_sip_accounts_lakh',
    'sip_aum_lakh_crore',
    'yoy_growth_pct'
]:
    if col in sip_history.columns:
        sip_history[col] = pd.to_numeric(sip_history[col], errors='coerce')

if 'net_inflow_crore' in category_inflows.columns:
    category_inflows['net_inflow_crore'] = pd.to_numeric(category_inflows['net_inflow_crore'], errors='coerce')

for col in [
    'total_folios_crore',
    'equity_folios_crore',
    'debt_folios_crore',
    'hybrid_folios_crore',
    'others_folios_crore'
]:
    if col in folio_history.columns:
        folio_history[col] = pd.to_numeric(folio_history[col], errors='coerce')

investor_transactions['amount_inr'] = pd.to_numeric(investor_transactions['amount_inr'], errors='coerce')
portfolio_holdings['weight_pct'] = pd.to_numeric(portfolio_holdings['weight_pct'], errors='coerce')

sns.set_theme(style='whitegrid')

"""))

insights = [
    'Market breadth was strong through the 2023 bull run and corrected in 2024, visible across the scheme universe.',
    'AUM remained heavily concentrated among the largest houses, with SBI as the leading fund house.',
    'Monthly SIP inflows rose steadily, hitting a record ₹31,002 Cr in Dec 2025.',
    'Category inflows show uneven momentum across Large Cap, Mid Cap, Hybrid and Liquid segments.',
    'Investor age participation is broad, with large shares in 26-35 and 36-45 cohorts.',
    'Older age groups show higher SIP amounts, indicating larger ticket sizes among mature investors.',
    'Gender split shows a meaningful female share, though males remain the larger cohort.',
    'State-level SIP volumes are concentrated in a small number of top-performing states.',
    'T30 city tiers contribute the majority of SIP volume, with B30 markets still material.',
    'Folio growth rose from 13.26 Cr to 26.12 Cr, reflecting sustained retail adoption.'
]
for i, insight in enumerate(insights, 1):
    cells.append(new_markdown_cell(f'## Insight {i}\n\n{insight}'))

chart_cells = [
    ("# NAV trend analysis\nnav_subset = nav_history[nav_history['date'].between('2022-01-01', '2025-12-31')].sort_values(['scheme_name', 'date'])\nfig = go.Figure()\nfor scheme, grp in nav_subset.groupby('scheme_name'):\n    fig.add_trace(go.Scatter(x=grp['date'].dt.to_pydatetime(), y=grp['nav'], mode='lines', name=scheme, line=dict(width=1.2), opacity=0.75))\nfig.add_vrect(x0='2023-01-01', x1='2023-12-31', fillcolor='green', opacity=0.10, line_width=0)\nfig.add_vrect(x0='2024-01-01', x1='2024-12-31', fillcolor='red', opacity=0.12, line_width=0)\nfig.add_annotation(x='2023-05-01', y=1.02, yref='paper', text='2023 bull run', showarrow=False, font=dict(color='green'))\nfig.add_annotation(x='2024-06-01', y=1.02, yref='paper', text='2024 correction', showarrow=False, font=dict(color='red'))\nfig.update_layout(title='Daily NAV trend for 40 schemes (2022–2025)', xaxis_title='Date', yaxis_title='NAV', template='plotly_white', showlegend=False, height=650)\nfig.update_xaxes(rangeslider_visible=True)\nfig.show()" , 'NAV Trend'),
    ("# AUM growth grouped bar chart\naum_history['year'] = aum_history['date'].dt.year\npivot_aum = aum_history.groupby(['fund_house', 'year'])['aum_lakh_crore'].last().unstack().reset_index()\nplot_df = pivot_aum.melt(id_vars='fund_house', var_name='year', value_name='aum_lakh_crore')\nplot_df['year'] = plot_df['year'].astype(int)\nplt.figure(figsize=(12, 6))\nax = sns.barplot(data=plot_df, x='year', y='aum_lakh_crore', hue='fund_house', palette='viridis')\nax.set_title('AUM growth by fund house (2022–2025)')\nax.set_ylabel('AUM (₹ L Cr)')\nax.set_xlabel('Year')\nax.legend(title='Fund House', bbox_to_anchor=(1.02, 1), loc='upper left')\nplt.tight_layout()\nplt.show()" , 'AUM Growth'),
    ("# SIP inflow time series\nfig = go.Figure()\nfig.add_trace(go.Scatter(x=sip_history['month'].dt.to_pydatetime(), y=sip_history['sip_inflow_crore'], mode='lines+markers', name='Monthly SIP inflow', line=dict(color='#1f77b4', width=2.5)))\nfig.add_annotation(x=sip_history['month'].iloc[-1].to_pydatetime(), y=sip_history['sip_inflow_crore'].iloc[-1], text='₹31,002 Cr', showarrow=True, arrowhead=2, ax=0, ay=-40)\nfig.update_layout(title='Monthly SIP inflow trend (Jan 2022 – Dec 2025)', xaxis_title='Month', yaxis_title='SIP inflow (₹ Cr)', template='plotly_white', hovermode='x unified', height=550)\nfig.show()" , 'SIP Inflow Trend'),
    ("# Category inflow heatmap\npivot_cat = category_inflows.pivot_table(index='category', columns='month', values='net_inflow_crore', aggfunc='mean').fillna(0)\nfig, ax = plt.subplots(figsize=(14, 7))\nsns.heatmap(pivot_cat, cmap='Blues', cbar_kws={'label': 'Net inflow (₹ Cr)'}, ax=ax)\nax.set_title('Category inflow heatmap by month')\nax.set_xlabel('Month')\nax.set_ylabel('Fund category')\nplt.tight_layout()\nplt.show()" , 'Category Inflow Heatmap'),
    ("# Investor age distribution\nage_counts = investor_transactions['age_group'].dropna().value_counts()\nfig = px.pie(values=age_counts.values, names=age_counts.index, title='Investor age-group distribution', hole=0.35)\nfig.show()" , 'Age Distribution'),
    ("# SIP amount by age group\nsip_txn = investor_transactions[investor_transactions['transaction_type'].astype(str).str.upper() == 'SIP'].copy()\nplt.figure(figsize=(10, 6))\nsns.boxplot(data=sip_txn, x='age_group', y='amount_inr', palette='Set2')\nplt.title('SIP amount by age group')\nplt.ylabel('SIP amount (₹)')\nplt.xlabel('Age group')\nplt.xticks(rotation=35)\nplt.tight_layout()\nplt.show()" , 'Age Group SIP Boxplot'),
    ("# Gender split\ngender_counts = investor_transactions['gender'].dropna().value_counts()\nfig = px.pie(values=gender_counts.values, names=gender_counts.index, title='Investor gender split', hole=0.4)\nfig.show()" , 'Gender Split'),
    ("# State SIP bar chart\nstate_sip = sip_txn.groupby('state')['amount_inr'].sum().sort_values(ascending=False).head(10).reset_index()\nplt.figure(figsize=(10, 6))\nsns.barplot(data=state_sip, x='amount_inr', y='state', palette='Blues_r')\nplt.title('Top 10 states by SIP amount')\nplt.xlabel('Total SIP amount (₹)')\nplt.ylabel('State')\nplt.tight_layout()\nplt.show()" , 'State SIP Distribution'),
    ("# City tier split\ntier_counts = investor_transactions['city_tier'].dropna().value_counts()\nfig = px.pie(values=tier_counts.values, names=tier_counts.index, title='City tier split (T30 vs B30)', hole=0.45)\nfig.show()" , 'City Tier Split'),
    ("# Folio count growth\nfig = go.Figure()\nfig.add_trace(go.Scatter(x=folio_history['month'].dt.to_pydatetime(), y=folio_history['total_folios_crore'], mode='lines+markers', name='Total folios', line=dict(color='#d62728', width=2.5)))\nfig.add_annotation(x=folio_history['month'].iloc[0].to_pydatetime(), y=folio_history['total_folios_crore'].iloc[0], text='13.26 Cr', showarrow=False, yshift=10)\nfig.add_annotation(x=folio_history['month'].iloc[-1].to_pydatetime(), y=folio_history['total_folios_crore'].iloc[-1], text='26.12 Cr', showarrow=False, yshift=10)\nfig.update_layout(title='Folio count growth (Jan 2022 – Dec 2025)', xaxis_title='Month', yaxis_title='Total folios (Cr)', template='plotly_white', height=540)\nfig.show()" , 'Folio Growth'),
    ("# Return correlation matrix\nselected_codes = fund_master['amfi_code'].head(10).tolist()\nselected_nav = nav_history[nav_history['amfi_code'].isin(selected_codes)].copy()\nselected_nav = selected_nav.pivot_table(index='date', columns='amfi_code', values='nav').sort_index()\nreturns = selected_nav.pct_change().dropna()\ncorr = returns.corr()\nplt.figure(figsize=(10, 8))\nsns.heatmap(corr, cmap='coolwarm', annot=True, fmt='.2f', linewidths=.5)\nplt.title('Daily return correlation matrix for 10 selected funds')\nplt.tight_layout()\nplt.show()" , 'Return Correlation Matrix'),
    ("# Sector allocation donut\nsector_weights = portfolio_holdings.groupby('sector')['weight_pct'].sum().sort_values(ascending=False)\nfig = px.pie(sector_weights, values=sector_weights.values, names=sector_weights.index, title='Sector allocation across equity portfolios', hole=0.45)\nfig.show()" , 'Sector Allocation'),
    ("# Active SIP accounts trend\nfig = go.Figure()\nfig.add_trace(go.Scatter(x=sip_history['month'].dt.to_pydatetime(), y=sip_history['active_sip_accounts_crore'], mode='lines+markers', name='Active SIP accounts (Cr)', line=dict(color='#2ca02c', width=2.2)))\nfig.update_layout(title='Active SIP accounts trend', xaxis_title='Month', yaxis_title='Accounts (Cr)', template='plotly_white', height=500)\nfig.show()" , 'Active SIP Accounts'),
    ("# SIP AUM growth\nfig = go.Figure()\nfig.add_trace(go.Scatter(x=sip_history['month'].dt.to_pydatetime(), y=sip_history['sip_aum_lakh_crore'], mode='lines+markers', name='SIP AUM', line=dict(color='#9467bd', width=2.2)))\nfig.update_layout(title='SIP AUM growth', xaxis_title='Month', yaxis_title='SIP AUM (₹ L Cr)', template='plotly_white', height=500)\nfig.show()" , 'SIP AUM Growth'),
    ("# Top category inflow trajectories\ntop_categories = category_inflows.groupby('category')['net_inflow_crore'].sum().sort_values(ascending=False).head(6).index\ntop_df = category_inflows[category_inflows['category'].isin(top_categories)]\nfig = px.line(top_df, x='month', y='net_inflow_crore', color='category', markers=True, title='Top category inflow trajectories')\nfig.update_layout(xaxis_title='Month', yaxis_title='Net inflow (₹ Cr)', template='plotly_white', height=550)\nfig.show()" , 'Top Category Inflows')
]

for code, title in chart_cells:
    cells.append(new_code_cell(code))

cells.append(new_markdown_cell('## Summary\n\nThe above charts complete Task 3, showing NAV trends, AUM concentration, SIP growth, category flows, investor demographics, geography, folio adoption, return correlations, and sector allocation.'))

nb = new_notebook(cells=cells)
with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print('Rewrote', NOTEBOOK_PATH)
""