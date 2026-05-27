
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from bronze import load_bronze
from silver import load_silver, clean_data
from gold import build_gold, load_gold

# load_bronze=load_bronze
# clean_data=clean_data
# build_gold=build_gold
# load_gold=load_gold
# load_silver=load_silver


# ── Page Config ──────────────────────────────────────
st.set_page_config(
    page_title="Sales Pipeline Dashboard",
    page_icon="📊",
    layout="wide"
)

# ── Header ────────────────────────────────────────────
st.title("📊 Sales Data Pipeline Dashboard")
st.caption("Bronze → Silver → Gold | Python · Pandas · DuckDB · Streamlit")

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Pipeline Control")

    if st.button("▶ Run Full Pipeline", type="primary", use_container_width=True):
        with st.status("Running pipeline...", expanded=True) as status:
            st.write("📥 Loading Bronze layer...")
            b = load_bronze()
            st.write(f"✅ Bronze — {len(b):,} rows loaded")

            st.write("🔧 Building Silver layer...")
            s = clean_data(b)
            st.write(f"✅ Silver — {len(s):,} rows cleaned")

            st.write("🏗 Building Gold layer...")
            g = build_gold(s)
            st.write(f"✅ Gold — {len(g)} tables created")

            status.update(label="Pipeline complete! ✅", state="complete")

        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.header("🗂 View Layer")
    layer = st.radio(
        "Select",
        ["🏠 Dashboard", "🥉 Bronze", "🥈 Silver", "🥇 Gold"],
        label_visibility="collapsed"
    )

# ── Load Data ─────────────────────────────────────────
@st.cache_data
def get_all():
    return load_bronze(), load_silver(), load_gold()

bronze_df, silver_df, gold = get_all()

# ── DASHBOARD ─────────────────────────────────────────
if layer == "🏠 Dashboard":

    kpi = gold['kpi'].iloc[0]

    # KPI Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Revenue",       f"${kpi['total_revenue']:,.0f}")
    c2.metric("📈 Profit",        f"${kpi['total_profit']:,.0f}")
    c3.metric("📊 Margin",        f"{kpi['profit_margin_pct']}%")
    c4.metric("👥 Customers",     f"{kpi['total_customers']:,}")
    c5.metric("🛒 Orders",        f"{kpi['total_orders']:,}")

    st.divider()

    # Row 1 — Trend + Region
    col1, col2 = st.columns(2)

    with col1:
        trend = gold['monthly_trend']
        trend['period'] = trend['month_name'] + ' ' + trend['year'].astype(str)
        fig = px.line(
            trend, x='period', y=['total_sales', 'total_profit'],
            title='📅 Monthly Revenue & Profit Trend',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        region = gold['by_region'].groupby('region').agg(
            total_sales=('total_sales', 'sum'),
            total_profit=('total_profit', 'sum')
        ).reset_index()
        fig = px.bar(
            region, x='region', y=['total_sales', 'total_profit'],
            title='🗺 Sales & Profit by Region',
            barmode='group', color_discrete_sequence=['#636EFA', '#00CC96']
        )
        st.plotly_chart(fig, use_container_width=True)

    # Row 2 — Category + Top Products
    col3, col4 = st.columns(2)

    with col3:
        cat = gold['by_category'].groupby('category').agg(
            total_sales=('total_sales', 'sum')
        ).reset_index()
        fig = px.pie(
            cat, names='category', values='total_sales',
            title='🍩 Revenue Share by Category',
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        top = gold['top_products'].head(10)
        fig = px.bar(
            top, x='total_sales', y='product_name',
            orientation='h', color='category',
            title='🏆 Top 10 Products by Revenue'
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

# ── BRONZE ────────────────────────────────────────────
elif layer == "🥉 Bronze":
    st.subheader("🥉 Bronze Layer — Raw Ingested Data")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Rows",      f"{len(bronze_df):,}")
    c2.metric("Total Columns",   len(bronze_df.columns))
    c3.metric("Missing Values",  int(bronze_df.isnull().sum().sum()))

    st.subheader("⚠️ Data Quality Issues Found")
    missing = bronze_df.isnull().sum()
    missing = missing[missing > 0].reset_index()
    missing.columns = ['Column', 'Missing Count']
    if len(missing):
        st.dataframe(missing, use_container_width=True)
    else:
        st.success("No missing values found!")

    st.subheader("📄 Raw Data (first 200 rows)")
    st.dataframe(bronze_df.head(200), use_container_width=True)

# ── SILVER ────────────────────────────────────────────
elif layer == "🥈 Silver":
    st.subheader("🥈 Silver Layer — Cleaned & Enriched")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows",           f"{len(silver_df):,}")
    c2.metric("Columns",        len(silver_df.columns))
    c3.metric("Missing Values", int(silver_df.isnull().sum().sum()))
    c4.metric("New Columns",    "6 derived")

    st.info("New columns added: year · month · month_name · quarter · net_sales · profit_margin_pct")

    st.subheader("📄 Clean Data (first 200 rows)")
    st.dataframe(silver_df.head(200), use_container_width=True)

# ── GOLD ──────────────────────────────────────────────
elif layer == "🥇 Gold":
    st.subheader("🥇 Gold Layer — Business Aggregations (DuckDB SQL)")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 By Category", "🗺 By Region", "🏆 Top Products", "📈 Monthly Trend"
    ])

    with tab1:
        st.dataframe(gold['by_category'], use_container_width=True)
    with tab2:
        st.dataframe(gold['by_region'], use_container_width=True)
    with tab3:
        st.dataframe(gold['top_products'], use_container_width=True)
    with tab4:
        st.dataframe(gold['monthly_trend'], use_container_width=True)
