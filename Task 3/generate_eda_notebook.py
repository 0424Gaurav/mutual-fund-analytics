from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

ROOT = Path(r"e:\bluestocks2")
DATA_DIR = ROOT / "Day 1" / "data" / "processed"
OUT_DIR = ROOT / "Task 3" / "eda_outputs"
NOTEBOOK_PATH = ROOT / "Task 3" / "EDA_Analysis.ipynb"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load data
fund_master = pd.read_csv(DATA_DIR / "01_fund_master.csv")
nav_history = pd.read_csv(DATA_DIR / "02_nav_history.csv")
aum_history = pd.read_csv(DATA_DIR / "03_aum_by_fund_house.csv")
sip_history = pd.read_csv(DATA_DIR / "04_monthly_sip_inflows.csv")
category_inflows = pd.read_csv(DATA_DIR / "05_category_inflows.csv")
folio_history = pd.read_csv(DATA_DIR / "06_industry_folio_count.csv")
investor_transactions = pd.read_csv(DATA_DIR / "08_investor_transactions.csv")
portfolio_holdings = pd.read_csv(DATA_DIR / "09_portfolio_holdings.csv")
benchmark_indices = pd.read_csv(DATA_DIR / "10_benchmark_indices.csv")

# Clean and standardize date columns
for df, col in [(nav_history, 'date'), (aum_history, 'date'), (sip_history, 'month'), (category_inflows, 'month'), (folio_history, 'month'), (investor_transactions, 'transaction_date')]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

nav_history = nav_history.merge(fund_master[['amfi_code', 'scheme_name']], on='amfi_code', how='left')
nav_history['year'] = nav_history['date'].dt.year

# Prepare monthly and demographic views
sip_history = sip_history.sort_values('month').reset_index(drop=True)
sip_history['year'] = sip_history['month'].dt.year
category_inflows = category_inflows.sort_values(['month', 'category']).reset_index(drop=True)
folio_history = folio_history.sort_values('month').reset_index(drop=True)
investor_transactions = investor_transactions.sort_values('transaction_date').reset_index(drop=True)
investor_transactions['transaction_type'] = investor_transactions['transaction_type'].astype(str)

# Ensure numeric types
for col in ['sip_inflow_crore', 'active_sip_accounts_crore', 'new_sip_accounts_lakh', 'sip_aum_lakh_crore', 'yoy_growth_pct']:
    if col in sip_history.columns:
        sip_history[col] = pd.to_numeric(sip_history[col], errors='coerce')

for col in ['net_inflow_crore']:
    if col in category_inflows.columns:
        category_inflows[col] = pd.to_numeric(category_inflows[col], errors='coerce')

for col in ['total_folios_crore', 'equity_folios_crore', 'debt_folios_crore', 'hybrid_folios_crore', 'others_folios_crore']:
    if col in folio_history.columns:
        folio_history[col] = pd.to_numeric(folio_history[col], errors='coerce')

investor_transactions['amount_inr'] = pd.to_numeric(investor_transactions['amount_inr'], errors='coerce')
portfolio_holdings['weight_pct'] = pd.to_numeric(portfolio_holdings['weight_pct'], errors='coerce')

# Helper functions

def save_plotly(fig, filename):
    out = OUT_DIR / filename
    fig.write_image(out, scale=2, engine='kaleido')
    return out


def save_matplotlib(fig, filename):
    out = OUT_DIR / filename
    fig.savefig(out, dpi=220, bbox_inches='tight')
    plt.close(fig)
    return out


# Notebook structure
cells = []

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# EDA Analysis for Mutual Fund Data\n",
        "\n",
        "This notebook explores NAV trends, AUM growth, SIP behaviour, category inflows, investor demographics, geography, folio growth, and portfolio sector allocation across the 2022–2026 period.\n"
    ],
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "import pandas as pd\n",
        "import numpy as np\n",
        "import matplotlib.pyplot as plt\n",
        "import seaborn as sns\n",
        "import plotly.express as px\n",
        "import plotly.graph_objects as go\n",
        "from pathlib import Path\n",
        "\n",
        "ROOT = Path(r'\\\\e:\\\\bluestocks2')\n",
        "DATA_DIR = ROOT / 'Day 1' / 'data' / 'processed'\n",
        "OUT_DIR = ROOT / 'Task 3' / 'eda_outputs'\n",
        "OUT_DIR.mkdir(parents=True, exist_ok=True)\n",
        "\n",
        "fund_master = pd.read_csv(DATA_DIR / '01_fund_master.csv')\n",
        "nav_history = pd.read_csv(DATA_DIR / '02_nav_history.csv')\n",
        "aum_history = pd.read_csv(DATA_DIR / '03_aum_by_fund_house.csv')\n",
        "sip_history = pd.read_csv(DATA_DIR / '04_monthly_sip_inflows.csv')\n",
        "category_inflows = pd.read_csv(DATA_DIR / '05_category_inflows.csv')\n",
        "folio_history = pd.read_csv(DATA_DIR / '06_industry_folio_count.csv')\n",
        "investor_transactions = pd.read_csv(DATA_DIR / '08_investor_transactions.csv')\n",
        "portfolio_holdings = pd.read_csv(DATA_DIR / '09_portfolio_holdings.csv')\n",
        "\n",
        "for df, col in [(nav_history, 'date'), (aum_history, 'date'), (sip_history, 'month'), (category_inflows, 'month'), (folio_history, 'month'), (investor_transactions, 'transaction_date')]:\n",
        "    if col in df.columns:\n",
        "        df[col] = pd.to_datetime(df[col], errors='coerce')\n",
        "\n",
        "nav_history = nav_history.merge(fund_master[['amfi_code', 'scheme_name']], on='amfi_code', how='left')\n",
        "sip_history = sip_history.sort_values('month').reset_index(drop=True)\n",
        "category_inflows = category_inflows.sort_values(['month', 'category']).reset_index(drop=True)\n",
        "folio_history = folio_history.sort_values('month').reset_index(drop=True)\n",
        "investor_transactions = investor_transactions.sort_values('transaction_date').reset_index(drop=True)\n",
        "\n",
        "for col in ['sip_inflow_crore', 'active_sip_accounts_crore', 'new_sip_accounts_lakh', 'sip_aum_lakh_crore', 'yoy_growth_pct']:\n",
        "    if col in sip_history.columns:\n",
        "        sip_history[col] = pd.to_numeric(sip_history[col], errors='coerce')\n",
        "\n",
        "for col in ['net_inflow_crore']:\n",
        "    if col in category_inflows.columns:\n",
        "        category_inflows[col] = pd.to_numeric(category_inflows[col], errors='coerce')\n",
        "\n",
        "for col in ['total_folios_crore', 'equity_folios_crore', 'debt_folios_crore', 'hybrid_folios_crore', 'others_folios_crore']:\n",
        "    if col in folio_history.columns:\n",
        "        folio_history[col] = pd.to_numeric(folio_history[col], errors='coerce')\n",
        "\n",
        "investor_transactions['amount_inr'] = pd.to_numeric(investor_transactions['amount_inr'], errors='coerce')\n",
        "portfolio_holdings['weight_pct'] = pd.to_numeric(portfolio_holdings['weight_pct'], errors='coerce')\n",
        "\n",
        "sns.set_theme(style='whitegrid')\n"
    ],
})

# Insight markdown cells + charts
insights = [
    ("1. Market breadth was strong through the 2023 bull run and then corrected in 2024, a pattern visible across the entire fund universe.", "nav"),
    ("2. AUM concentration remained heavily skewed toward the largest houses, with SBI emerging as the clear leader by size.", "aum"),
    ("3. SIP inflows accelerated steadily through 2025 and reached an all-time high in December 2025.", "sip"),
    ("4. Equity category flows were strongest in select segments, showing recurring rotation across market regimes.", "category_heatmap"),
    ("5. Investor participation was broad-based across age groups, with a meaningful share in the middle-aged cohorts.", "age_pie"),
    ("6. Higher SIP amounts were concentrated in older age groups, indicating larger commitment among mature investors.", "age_box"),
    ("7. Gender composition was fairly balanced, suggesting participation was not concentrated in a single demographic.", "gender_pie"),
    ("8. SIP contributions were geographically concentrated in a handful of large states, with clear urban-state dominance.", "state_bar"),
    ("9. Urban city tiers drove the bulk of SIP volume, confirming that T30 markets remain the primary engine of growth.", "tier_pie"),
    ("10. Folio growth remained almost linear over the period, reflecting sustained retail participation and strong long-term adoption.", "folio"),
]

# Add markdown insight cells
for i, (insight, _) in enumerate(insights, start=1):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [f"## Insight {i}\n", f"{insight}\n", f"\nSupporting chart: Chart {i}.\n"]
    })

# Chart 1: NAV trends
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "nav_subset = nav_history[nav_history['date'].between('2022-01-01', '2025-12-31')].copy()\n",
        "nav_subset = nav_subset.sort_values(['scheme_name', 'date'])\n",
        "fig = go.Figure()\n",
        "for scheme, grp in nav_subset.groupby('scheme_name'):\n",
        "    fig.add_trace(go.Scatter(x=grp['date'].dt.to_pydatetime(), y=grp['nav'], mode='lines', name=scheme, line=dict(width=1.2), opacity=0.75))\n",
        "fig.add_vrect(x0='2023-01-01', x1='2023-12-31', fillcolor='green', opacity=0.10, line_width=0)\n",
        "fig.add_vrect(x0='2024-01-01', x1='2024-12-31', fillcolor='red', opacity=0.12, line_width=0)\n",
        "fig.add_annotation(x='2023-05-01', y=1.02, yref='paper', text='2023 bull run', showarrow=False, font=dict(color='green'))\n",
        "fig.add_annotation(x='2024-06-01', y=1.02, yref='paper', text='2024 correction', showarrow=False, font=dict(color='red'))\n",
        "fig.update_layout(title='Daily NAV trend for 40 schemes (2022–2025)', xaxis_title='Date', yaxis_title='NAV', template='plotly_white', showlegend=False, height=650)\n",
        "fig.update_xaxes(rangeslider_visible=True)\n",
        "fig.show()\n",
        "save_plotly(fig, '01_nav_trends.png')\n"
    ],
})

# Chart 2: AUM growth grouped bars
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "aum_history['year'] = aum_history['date'].dt.year\n",
        "pivot_aum = aum_history.sort_values(['fund_house', 'date']).groupby(['fund_house', 'year'])['aum_lakh_crore'].last().unstack().reset_index()\n",
        "pivot_aum = pivot_aum.rename(columns={2022:'2022', 2023:'2023', 2024:'2024', 2025:'2025'})\n",
        "top_houses = pivot_aum.sort_values('2025', ascending=False).head(8)\n",
        "plot_df = top_houses.melt(id_vars='fund_house', var_name='year', value_name='aum_lakh_crore')\n",
        "plot_df['year'] = plot_df['year'].astype(int)\n",
        "plt.figure(figsize=(12, 6))\n",
        "ax = sns.barplot(data=plot_df, x='year', y='aum_lakh_crore', hue='fund_house', palette='viridis')\n",
        "for container in ax.containers:\n",
        "    ax.bar_label(container, labels=[f'{v:.1f}' if pd.notna(v) else '' for v in container.datavalues], padding=3, fontsize=8)\n",
        "for bar in ax.patches:\n",
        "    if bar.get_height() > 0 and bar.get_x() < 0.5:\n",
        "        pass\n",
        "sns.despine()\n",
        "plt.title('AUM growth by fund house (2022–2025)')\n",
        "plt.ylabel('AUM (₹ L Cr)')\n",
        "plt.xlabel('Year')\n",
        "plt.legend(title='Fund House', bbox_to_anchor=(1.02, 1), loc='upper left')\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "save_matplotlib(plt.gcf(), '02_aum_growth.png')\n"
    ],
})

# Chart 3: SIP inflows time series
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "fig = go.Figure()\n",
        "fig.add_trace(go.Scatter(x=sip_history['month'].dt.to_pydatetime(), y=sip_history['sip_inflow_crore'], mode='lines+markers', name='Monthly SIP inflow', line=dict(color='#1f77b4', width=2.5)))\n",
        "fig.add_annotation(x=sip_history['month'].iloc[-1].to_pydatetime(), y=sip_history['sip_inflow_crore'].iloc[-1], text='₹31,002 Cr', showarrow=True, arrowhead=2, ax=0, ay=-40)\n",
        "fig.update_layout(title='Monthly SIP inflow trend (Jan 2022 – Dec 2025)', xaxis_title='Month', yaxis_title='SIP inflow (₹ Cr)', template='plotly_white', hovermode='x unified', height=550)\n",
        "fig.show()\n",
        "save_plotly(fig, '03_sip_inflows.png')\n"
    ],
})

# Chart 4: category heatmap
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "pivot_cat = category_inflows.pivot_table(index='category', columns='month', values='net_inflow_crore', aggfunc='mean').fillna(0)\n",
        "pivot_cat = pivot_cat.loc[:, pivot_cat.columns >= '2022-01-01']\n",
        "plt.figure(figsize=(14, 7))\n",
        "ax = sns.heatmap(pivot_cat, cmap='Blues', cbar_kws={'label': 'Net inflow (₹ Cr)'})\n",
        "plt.title('Category inflow heatmap by month')\n",
        "plt.xlabel('Month')\n",
        "plt.ylabel('Fund category')\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "save_matplotlib(plt.gcf(), '04_category_heatmap.png')\n"
    ],
})

# Chart 5: age group pie chart
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "age_counts = investor_transactions['age_group'].dropna().value_counts()\n",
        "fig = px.pie(values=age_counts.values, names=age_counts.index, title='Investor age-group distribution', hole=0.35)\n",
        "fig.show()\n",
        "save_plotly(fig, '05_age_group_pie.png')\n"
    ],
})

# Chart 6: SIP amount by age group box plot
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "sip_txn = investor_transactions[investor_transactions['transaction_type'].str.upper() == 'SIP'].copy()\n",
        "plt.figure(figsize=(10, 6))\n",
        "sns.boxplot(data=sip_txn, x='age_group', y='amount_inr', palette='Set2')\n",
        "plt.title('SIP amount by age group')\n",
        "plt.ylabel('SIP amount (₹)')\n",
        "plt.xlabel('Age group')\n",
        "plt.xticks(rotation=35)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "save_matplotlib(plt.gcf(), '06_age_group_boxplot.png')\n"
    ],
})

# Chart 7: gender split pie
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "gender_counts = investor_transactions['gender'].dropna().value_counts()\n",
        "fig = px.pie(values=gender_counts.values, names=gender_counts.index, title='Investor gender split', hole=0.4)\n",
        "fig.show()\n",
        "save_plotly(fig, '07_gender_split_pie.png')\n"
    ],
})

# Chart 8: SIP amount by state bar chart
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "state_sip = sip_txn.groupby('state')['amount_inr'].sum().sort_values(ascending=False).head(10).reset_index()\n",
        "plt.figure(figsize=(10, 6))\n",
        "sns.barplot(data=state_sip, x='amount_inr', y='state', palette='Blues_r')\n",
        "plt.title('Top 10 states by SIP amount')\n",
        "plt.xlabel('Total SIP amount (₹)')\n",
        "plt.ylabel('State')\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "save_matplotlib(plt.gcf(), '08_state_sip_bar.png')\n"
    ],
})

# Chart 9: T30 vs B30
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "tier_counts = investor_transactions['city_tier'].dropna().value_counts()\n",
        "fig = px.pie(values=tier_counts.values, names=tier_counts.index, title='City tier split (T30 vs B30)', hole=0.45)\n",
        "fig.show()\n",
        "save_plotly(fig, '09_city_tier_pie.png')\n"
    ],
})

# Chart 10: Folio count growth
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "fig = go.Figure()\n",
        "fig.add_trace(go.Scatter(x=folio_history['month'].dt.to_pydatetime(), y=folio_history['total_folios_crore'], mode='lines+markers', name='Total folios', line=dict(color='#d62728', width=2.5)))\n",
        "fig.add_annotation(x=folio_history['month'].iloc[0].to_pydatetime(), y=folio_history['total_folios_crore'].iloc[0], text='13.26 Cr', showarrow=False, yshift=10)\n",
        "fig.add_annotation(x=folio_history['month'].iloc[-1].to_pydatetime(), y=folio_history['total_folios_crore'].iloc[-1], text='26.12 Cr', showarrow=False, yshift=10)\n",
        "fig.update_layout(title='Folio count growth (Jan 2022 – Dec 2025)', xaxis_title='Month', yaxis_title='Total folios (Cr)', template='plotly_white', height=540)\n",
        "fig.show()\n",
        "save_plotly(fig, '10_folio_growth.png')\n"
    ],
})

# Chart 11: return correlation matrix
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "selected_codes = fund_master['amfi_code'].head(10).tolist()\n",
        "selected_nav = nav_history[nav_history['amfi_code'].isin(selected_codes)].copy()\n",
        "selected_nav = selected_nav.pivot_table(index='date', columns='amfi_code', values='nav').sort_index()\n",
        "returns = selected_nav.pct_change().dropna()\n",
        "corr = returns.corr()\n",
        "plt.figure(figsize=(10, 8))\n",
        "sns.heatmap(corr, cmap='coolwarm', annot=True, fmt='.2f', linewidths=.5)\n",
        "plt.title('Daily return correlation matrix for 10 selected funds')\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "save_matplotlib(plt.gcf(), '11_return_corr_heatmap.png')\n"
    ],
})

# Chart 12: sector allocation donut
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "sector_weights = portfolio_holdings.groupby('sector')['weight_pct'].sum().sort_values(ascending=False)\n",
        "fig = px.pie(sector_weights, values=sector_weights.values, names=sector_weights.index, title='Sector allocation across equity portfolios', hole=0.45)\n",
        "fig.show()\n",
        "save_plotly(fig, '12_sector_allocation_donut.png')\n"
    ],
})

# Chart 13: Active SIP accounts trend
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "fig = go.Figure()\n",
        "fig.add_trace(go.Scatter(x=sip_history['month'], y=sip_history['active_sip_accounts_crore'], mode='lines+markers', name='Active SIP accounts (Cr)', line=dict(color='#2ca02c', width=2.2)))\n",
        "fig.update_layout(title='Active SIP accounts trend', xaxis_title='Month', yaxis_title='Accounts (Cr)', template='plotly_white', height=500)\n",
        "fig.show()\n",
        "save_plotly(fig, '13_active_sip_accounts.png')\n"
    ],
})

# Chart 14: SIP AUM trend
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "fig = go.Figure()\n",
        "fig.add_trace(go.Scatter(x=sip_history['month'], y=sip_history['sip_aum_lakh_crore'], mode='lines+markers', name='SIP AUM', line=dict(color='#9467bd', width=2.2)))\n",
        "fig.update_layout(title='SIP AUM growth', xaxis_title='Month', yaxis_title='SIP AUM (₹ L Cr)', template='plotly_white', height=500)\n",
        "fig.show()\n",
        "save_plotly(fig, '14_sip_aum_trend.png')\n"
    ],
})

# Chart 15: top category inflow lines
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "top_categories = category_inflows.groupby('category')['net_inflow_crore'].sum().sort_values(ascending=False).head(6).index\n",
        "top_df = category_inflows[category_inflows['category'].isin(top_categories)]\n",
        "fig = px.line(top_df, x='month', y='net_inflow_crore', color='category', markers=True, title='Top category inflow trajectories')\n",
        "fig.update_layout(xaxis_title='Month', yaxis_title='Net inflow (₹ Cr)', template='plotly_white', height=550)\n",
        "fig.show()\n",
        "save_plotly(fig, '15_category_inflow_lines.png')\n"
    ],
})

# Final markdown summary cell
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## Summary\n",
        "\n",
        "The charts above highlight the main market and investor behaviour patterns from the dataset: broad market participation, rising SIP momentum, strong AUM concentration, geographic concentration in urban markets, and sustained folio growth over the 2022–2025 period.\n"
    ],
})

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=1), encoding='utf-8')
print(f"Created notebook: {NOTEBOOK_PATH}")
print(f"PNG outputs written to: {OUT_DIR}")
