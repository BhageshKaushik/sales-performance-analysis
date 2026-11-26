"""
app.py — Interactive Streamlit BI Dashboard
Sales Performance Analysis System

Professional enterprise-grade business intelligence dashboard with:
- Dark navy/teal color scheme
- KPI cards with dynamic filtering
- Interactive Plotly charts
- 6 analytical sections
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Path bootstrap ────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from database import connect_db, get_analytical_dataset
from analysis import SalesAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Page Config
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Sales Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# Custom CSS — Dark Enterprise Theme
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Root theme ── */
:root {
    --bg-primary: #0F1923;
    --bg-secondary: #162032;
    --bg-card: #1A2840;
    --bg-card-hover: #1E3050;
    --accent: #00C2CC;
    --accent2: #2E86AB;
    --positive: #27AE60;
    --negative: #E74C3C;
    --warning: #F39C12;
    --text-primary: #E8F0FE;
    --text-secondary: #A0AEC0;
    --border: #2D3748;
    --gradient1: linear-gradient(135deg, #1E3A5F 0%, #0F1923 100%);
    --gradient2: linear-gradient(135deg, #00C2CC 0%, #2E86AB 100%);
}

/* ── App background ── */
.stApp {
    background: var(--bg-primary);
    color: var(--text-primary);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--accent) !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    transition: all 0.2s ease;
}
[data-testid="stMetric"]:hover {
    background: var(--bg-card-hover);
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0,194,204,0.15);
}
[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

/* ── Section headers ── */
.section-header {
    background: linear-gradient(90deg, #1E3A5F, #0F1923);
    border-left: 4px solid #00C2CC;
    padding: 10px 16px;
    border-radius: 0 8px 8px 0;
    margin: 20px 0 16px 0;
}
.section-header h2 {
    margin: 0;
    color: #E8F0FE;
    font-size: 1.2rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}

/* ── Info callout ── */
.insight-box {
    background: rgba(0, 194, 204, 0.08);
    border: 1px solid rgba(0, 194, 204, 0.3);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 10px 0;
    color: var(--text-secondary);
    font-size: 0.85rem;
    line-height: 1.6;
}

/* ── Plotly chart containers ── */
.js-plotly-plot .plotly {
    border-radius: 10px;
    overflow: hidden;
}

/* ── Tabs ── */
[data-testid="stTabs"] {
    background: var(--bg-secondary);
    border-radius: 10px;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary);
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}

/* ── Tables ── */
.stDataFrame {
    background: var(--bg-card);
    border-radius: 8px;
}

/* ── Divider ── */
hr {
    border-color: var(--border);
    margin: 1.5rem 0;
}

/* ── Title banner ── */
.dashboard-title {
    background: linear-gradient(135deg, #1E3A5F 0%, #162032 60%, #0F1923 100%);
    border-bottom: 2px solid #00C2CC;
    padding: 20px 24px 16px;
    margin-bottom: 20px;
    border-radius: 10px;
}
.dashboard-title h1 {
    color: #E8F0FE;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.02em;
}
.dashboard-title p {
    color: #A0AEC0;
    font-size: 0.85rem;
    margin: 4px 0 0 0;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# Plotly chart theme
# ═══════════════════════════════════════════════════════════════
PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(26,40,64,0.95)",
        plot_bgcolor="rgba(22,32,50,0.9)",
        font=dict(color="#E8F0FE", family="system-ui, -apple-system, sans-serif"),
        title=dict(font=dict(size=14, color="#E8F0FE")),
        colorway=["#2E86AB", "#00C2CC", "#27AE60", "#F39C12",
                  "#E74C3C", "#8E44AD", "#16A085", "#D35400", "#1E3A5F"],
        xaxis=dict(gridcolor="#2D3748", zerolinecolor="#2D3748", linecolor="#2D3748"),
        yaxis=dict(gridcolor="#2D3748", zerolinecolor="#2D3748", linecolor="#2D3748"),
        legend=dict(bgcolor="rgba(26,40,64,0.8)", bordercolor="#2D3748", borderwidth=1),
        margin=dict(l=40, r=20, t=50, b=40),
    )
)

CHART_COLORS = ["#2E86AB", "#00C2CC", "#27AE60", "#F39C12",
                "#E74C3C", "#8E44AD", "#16A085", "#D35400", "#1E3A5F", "#F4D03F"]


# ═══════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner="Loading analytical dataset...")
def load_data() -> pd.DataFrame:
    """Load and prepare the analytical DataFrame from SQLite."""
    try:
        conn = connect_db()
        df = get_analytical_dataset(conn)
        conn.close()
    except Exception as exc:
        st.error(f"Database error: {exc}")
        st.stop()

    # Parse dates and compute shipping_duration
    for col in ["order_date", "ship_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "order_date" in df.columns and "ship_date" in df.columns:
        df["shipping_duration"] = (df["ship_date"] - df["order_date"]).dt.days

    for col in ["sales", "profit", "quantity", "discount", "unit_price", "profit_margin"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "order_date" in df.columns:
        df["year_month"] = df["order_date"].dt.to_period("M").astype(str)

    return df


# ═══════════════════════════════════════════════════════════════
# Sidebar Filters
# ═══════════════════════════════════════════════════════════════
def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters and return filtered DataFrame."""
    with st.sidebar:
        st.markdown("## ⚙️ Filters")
        st.markdown("---")

        # Date range
        st.markdown("**📅 Date Range**")
        min_date = df["order_date"].min().date()
        max_date = df["order_date"].max().date()
        date_range = st.date_input(
            "Select range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            label_visibility="collapsed",
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_date, end_date = date_range
            df = df[
                (df["order_date"].dt.date >= start_date) &
                (df["order_date"].dt.date <= end_date)
            ]

        st.markdown("---")

        # Region filter
        st.markdown("**🗺️ Region**")
        all_regions = sorted(df["region"].dropna().unique())
        selected_regions = st.multiselect(
            "Regions", all_regions, default=all_regions,
            label_visibility="collapsed",
        )
        if selected_regions:
            df = df[df["region"].isin(selected_regions)]

        # State filter
        st.markdown("**📍 State**")
        all_states = sorted(df["state"].dropna().unique())
        selected_states = st.multiselect(
            "States", all_states, default=None,
            placeholder="All states",
            label_visibility="collapsed",
        )
        if selected_states:
            df = df[df["state"].isin(selected_states)]

        # Category filter
        st.markdown("**🗂️ Category**")
        all_cats = sorted(df["category"].dropna().unique())
        selected_cats = st.multiselect(
            "Categories", all_cats, default=all_cats,
            label_visibility="collapsed",
        )
        if selected_cats:
            df = df[df["category"].isin(selected_cats)]

        # Sub-category filter
        st.markdown("**📦 Sub-Category**")
        all_subcats = sorted(df["sub_category"].dropna().unique())
        selected_subcats = st.multiselect(
            "Sub-Categories", all_subcats, default=None,
            placeholder="All sub-categories",
            label_visibility="collapsed",
        )
        if selected_subcats:
            df = df[df["sub_category"].isin(selected_subcats)]

        # Ship Mode filter
        st.markdown("**🚚 Ship Mode**")
        all_modes = sorted(df["ship_mode"].dropna().unique())
        selected_modes = st.multiselect(
            "Ship Modes", all_modes, default=all_modes,
            label_visibility="collapsed",
        )
        if selected_modes:
            df = df[df["ship_mode"].isin(selected_modes)]

        # Segment filter
        st.markdown("**👥 Segment**")
        all_segs = sorted(df["segment"].dropna().unique())
        selected_segs = st.multiselect(
            "Segments", all_segs, default=all_segs,
            label_visibility="collapsed",
        )
        if selected_segs:
            df = df[df["segment"].isin(selected_segs)]

        st.markdown("---")
        st.markdown(
            f"<div style='color:#A0AEC0;font-size:0.75rem;text-align:center;'>"
            f"Showing {len(df):,} of {st.session_state.get('total_rows', len(df)):,} rows</div>",
            unsafe_allow_html=True,
        )

    return df


# ═══════════════════════════════════════════════════════════════
# Section Helpers
# ═══════════════════════════════════════════════════════════════
def section_header(icon: str, title: str):
    st.markdown(
        f'<div class="section-header"><h2>{icon} {title}</h2></div>',
        unsafe_allow_html=True,
    )


def insight(text: str):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)


def fmt_currency(v: float) -> str:
    if abs(v) >= 1e6:
        return f"${v/1e6:.2f}M"
    elif abs(v) >= 1e3:
        return f"${v/1e3:.1f}K"
    return f"${v:,.2f}"


def plotly_bar(df, x, y, title, orientation="v", color=None, text=None, **kwargs):
    fig = px.bar(df, x=x, y=y, title=title, orientation=orientation,
                 color=color, text=text, color_discrete_sequence=CHART_COLORS, **kwargs)
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    fig.update_traces(marker_line_width=0)
    return fig


# ═══════════════════════════════════════════════════════════════
# Section 1: Overview KPIs
# ═══════════════════════════════════════════════════════════════
def render_overview(df: pd.DataFrame):
    section_header("📊", "Overview")

    analyzer = SalesAnalyzer(df)
    kpis = analyzer.sales_performance()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("💰 Total Revenue", fmt_currency(kpis["total_sales"]))
    c2.metric("📈 Total Profit", fmt_currency(kpis["total_profit"]))
    c3.metric("📋 Total Orders", f"{kpis['total_orders']:,}")
    c4.metric("📦 Units Sold", f"{kpis['total_quantity']:,}")
    c5.metric("📉 Profit Margin", f"{kpis['overall_profit_margin']:.1%}")
    c6.metric("🔄 Return Rate", f"{kpis['return_rate']:.1%}")


# ═══════════════════════════════════════════════════════════════
# Section 2: Sales Analytics
# ═══════════════════════════════════════════════════════════════
def render_sales(df: pd.DataFrame):
    section_header("📈", "Sales Analytics")
    analyzer = SalesAnalyzer(df)

    # Monthly trend
    monthly = (
        df.groupby("year_month")
        .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
        .reset_index()
        .sort_values("year_month")
    )

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["total_sales"],
        name="Sales", mode="lines+markers",
        line=dict(color="#2E86AB", width=2.5),
        fill="tozeroy", fillcolor="rgba(46,134,171,0.1)",
        marker=dict(size=4),
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly["year_month"], y=monthly["total_profit"],
        name="Profit", mode="lines+markers",
        line=dict(color="#27AE60", width=2, dash="dash"),
        yaxis="y2",
        marker=dict(size=4),
    ))
    fig_trend.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title="Monthly Sales and Profit Trends",
        yaxis=dict(title="Sales (USD)", tickprefix="$", gridcolor="#2D3748"),
        yaxis2=dict(title="Profit (USD)", tickprefix="$", overlaying="y", side="right", gridcolor="#2D3748"),
        legend=dict(x=0, y=1.1, orientation="h"),
        height=400,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        # Category performance
        cat_data = analyzer.category_analysis()["by_category"]
        fig_cat = go.Figure(data=[
            go.Bar(name="Sales", x=cat_data["category"], y=cat_data["total_sales"],
                   marker_color="#2E86AB"),
            go.Bar(name="Profit", x=cat_data["category"], y=cat_data["total_profit"],
                   marker_color=["#27AE60" if p >= 0 else "#E74C3C" for p in cat_data["total_profit"]]),
        ])
        fig_cat.update_layout(**PLOTLY_TEMPLATE["layout"], title="Sales & Profit by Category",
                               barmode="group", height=350)
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        # Top 10 products
        top_prods = analyzer.top_products_by_sales(10)
        fig_prods = px.bar(
            top_prods.sort_values("total_sales"), x="total_sales", y="product_name",
            orientation="h", title="Top 10 Products by Sales",
            color_discrete_sequence=[CHART_COLORS[0]],
        )
        fig_prods.update_layout(**PLOTLY_TEMPLATE["layout"], height=350)
        fig_prods.update_traces(text=top_prods.sort_values("total_sales")["total_sales"].apply(fmt_currency),
                                 textposition="outside")
        st.plotly_chart(fig_prods, use_container_width=True)

    # Top 10 Customers
    top_cust = analyzer.top_customers_by_sales(10)
    fig_cust = px.bar(
        top_cust.sort_values("total_sales"), x="total_sales", y="customer_name",
        orientation="h", title="Top 10 Customers by Sales",
        color="total_sales", color_continuous_scale=["#1E3A5F", "#00C2CC"],
    )
    fig_cust.update_layout(**PLOTLY_TEMPLATE["layout"], height=350, coloraxis_showscale=False)
    st.plotly_chart(fig_cust, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# Section 3: Geographical Analytics
# ═══════════════════════════════════════════════════════════════
def render_geography(df: pd.DataFrame):
    section_header("🗺️", "Geographical Analytics")
    analyzer = SalesAnalyzer(df)
    geo = analyzer.geo_analysis()

    col1, col2 = st.columns(2)
    with col1:
        # Region donut
        region_data = geo["by_region"]
        fig_region = go.Figure(data=[go.Pie(
            labels=region_data["region"],
            values=region_data["total_sales"],
            hole=0.5,
            marker=dict(colors=CHART_COLORS[:len(region_data)],
                        line=dict(color="#0F1923", width=2)),
        )])
        fig_region.update_layout(**PLOTLY_TEMPLATE["layout"],
                                  title="Sales Distribution by Region", height=380)
        st.plotly_chart(fig_region, use_container_width=True)

    with col2:
        # Region profit bars
        fig_rp = go.Figure(data=[
            go.Bar(x=region_data["region"], y=region_data["total_profit"],
                   marker_color=["#27AE60" if p >= 0 else "#E74C3C" for p in region_data["total_profit"]],
                   text=[fmt_currency(p) for p in region_data["total_profit"]],
                   textposition="outside"),
        ])
        fig_rp.update_layout(**PLOTLY_TEMPLATE["layout"], title="Profit by Region", height=380)
        st.plotly_chart(fig_rp, use_container_width=True)

    # State treemap
    state_data = geo["by_state"].head(30)
    fig_state = px.treemap(
        state_data, path=["state"], values="total_sales",
        color="total_profit",
        color_continuous_scale=["#E74C3C", "#F39C12", "#27AE60"],
        title="State Sales Treemap (Color = Profit Level)",
    )
    fig_state.update_layout(**PLOTLY_TEMPLATE["layout"], height=420)
    st.plotly_chart(fig_state, use_container_width=True)

    # Top 20 states table
    st.markdown("**Top 20 States by Sales**")
    top_states = state_data[["state", "total_sales", "total_profit", "order_count"]].copy()
    top_states["total_sales"] = top_states["total_sales"].map(lambda v: f"${v:,.2f}")
    top_states["total_profit"] = top_states["total_profit"].map(lambda v: f"${v:,.2f}")
    st.dataframe(top_states, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Section 4: Product Analytics
# ═══════════════════════════════════════════════════════════════
def render_products(df: pd.DataFrame):
    section_header("📦", "Product Analytics")
    analyzer = SalesAnalyzer(df)

    # Sub-category profit
    subcat = analyzer.category_analysis()["by_sub_category"].sort_values("total_profit")
    fig_sc = go.Figure(go.Bar(
        x=subcat["total_profit"],
        y=subcat["sub_category"],
        orientation="h",
        marker_color=["#27AE60" if p >= 0 else "#E74C3C" for p in subcat["total_profit"]],
    ))
    fig_sc.add_vline(x=0, line_color="#A0AEC0", line_width=1)
    fig_sc.update_layout(**PLOTLY_TEMPLATE["layout"], title="Profit by Sub-Category", height=500)
    st.plotly_chart(fig_sc, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        # Return rates by category
        ret_cat = analyzer.return_analysis()["by_category"]
        fig_ret = px.bar(
            ret_cat, x="category", y="return_rate",
            title="Return Rate by Category",
            text=ret_cat["return_rate"].map(lambda v: f"{v:.1%}"),
            color_discrete_sequence=[CHART_COLORS[4]],
        )
        fig_ret.update_layout(**PLOTLY_TEMPLATE["layout"], height=350)
        fig_ret.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig_ret, use_container_width=True)

    with col2:
        # Discount vs Profit Margin scatter
        sample = df.dropna(subset=["discount", "profit_margin"]).sample(
            min(2000, len(df)), random_state=42
        )
        fig_disc = px.scatter(
            sample, x="discount", y="profit_margin",
            color="category", opacity=0.5,
            trendline="ols",
            title="Discount vs Profit Margin",
            color_discrete_sequence=CHART_COLORS,
        )
        fig_disc.update_layout(**PLOTLY_TEMPLATE["layout"], height=350)
        fig_disc.update_xaxes(tickformat=".0%")
        fig_disc.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig_disc, use_container_width=True)

    # Discount analysis table
    disc = analyzer.discount_analysis()
    st.markdown("**Discount Impact Analysis**")
    if disc["threshold"]:
        insight(f"Critical discount threshold: **{disc['threshold']}**. {disc['threshold_evidence']}")
    disc_tbl = disc["by_discount_range"].copy()
    disc_tbl["profit_margin"] = disc_tbl["profit_margin"].map(
        lambda v: f"{v:.2%}" if isinstance(v, float) and not np.isnan(v) else "N/A"
    )
    disc_tbl["total_sales"] = disc_tbl["total_sales"].map(lambda v: f"${v:,.2f}")
    disc_tbl["total_profit"] = disc_tbl["total_profit"].map(lambda v: f"${v:,.2f}")
    st.dataframe(disc_tbl, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Section 5: Shipping Analytics
# ═══════════════════════════════════════════════════════════════
def render_shipping(df: pd.DataFrame):
    section_header("🚚", "Shipping Analytics")
    analyzer = SalesAnalyzer(df)

    ship_data = analyzer.product_shipping_analysis()
    ship_df = df.dropna(subset=["shipping_duration", "ship_mode"])
    ship_df = ship_df[ship_df["shipping_duration"] >= 0]

    col1, col2 = st.columns(2)
    with col1:
        # Avg shipping duration by mode
        avg_ship = ship_df.groupby("ship_mode")["shipping_duration"].agg(
            ["mean", "median", "std"]
        ).reset_index().sort_values("mean")
        fig_ship = go.Figure(go.Bar(
            x=avg_ship["ship_mode"], y=avg_ship["mean"],
            error_y=dict(type="data", array=avg_ship["std"].fillna(0).tolist()),
            marker_color=CHART_COLORS[:len(avg_ship)],
            text=[f"{v:.1f}d" for v in avg_ship["mean"]],
            textposition="outside",
        ))
        fig_ship.update_layout(**PLOTLY_TEMPLATE["layout"],
                                title="Avg Shipping Duration by Mode (± Std Dev)", height=380)
        fig_ship.update_yaxes(title="Days")
        st.plotly_chart(fig_ship, use_container_width=True)

    with col2:
        # Shipping mode count / sales split
        mode_sales = ship_df.groupby("ship_mode")["sales"].sum().reset_index()
        fig_ms = px.pie(
            mode_sales, names="ship_mode", values="sales",
            title="Sales by Shipping Mode",
            color_discrete_sequence=CHART_COLORS,
            hole=0.4,
        )
        fig_ms.update_layout(**PLOTLY_TEMPLATE["layout"], height=380)
        st.plotly_chart(fig_ms, use_container_width=True)

    # Regional shipping heatmap
    ship_stats = ship_data["shipping_stats"].dropna(subset=["avg_duration"])
    if not ship_stats.empty:
        pivot = ship_stats.pivot_table(
            index="ship_mode", columns="region", values="avg_duration", aggfunc="mean"
        ).fillna(0)
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
            colorscale=[[0, "#1E3A5F"], [0.5, "#00C2CC"], [1, "#F39C12"]],
            text=np.round(pivot.values, 1), texttemplate="%{text}d",
        ))
        fig_heat.update_layout(**PLOTLY_TEMPLATE["layout"],
                                title="Avg Shipping Duration by Mode & Region (days)", height=320)
        st.plotly_chart(fig_heat, use_container_width=True)

    # Return by ship mode table
    ret_ship = ship_data["return_by_ship_mode"]
    ret_ship["return_rate"] = ret_ship["return_rate"].map(lambda v: f"{v:.2%}")
    st.markdown("**Return Rate by Ship Mode & Region**")
    st.dataframe(ret_ship, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Section 6: Representative Analytics
# ═══════════════════════════════════════════════════════════════
def render_reps(df: pd.DataFrame):
    section_header("👤", "Representative Analytics")
    analyzer = SalesAnalyzer(df)
    reps = analyzer.rep_analysis()

    by_rep = reps["by_rep"].dropna(subset=["sales_rep"])
    if by_rep.empty:
        st.info("No sales representative data available for the current filter selection.")
        return

    col1, col2 = st.columns(2)
    with col1:
        fig_rep = go.Figure(data=[
            go.Bar(name="Sales", x=by_rep["sales_rep"], y=by_rep["total_sales"],
                   marker_color="#2E86AB"),
            go.Bar(name="Profit", x=by_rep["sales_rep"], y=by_rep["total_profit"],
                   marker_color=["#27AE60" if p >= 0 else "#E74C3C" for p in by_rep["total_profit"]]),
        ])
        fig_rep.update_layout(**PLOTLY_TEMPLATE["layout"], title="Rep Performance: Sales & Profit",
                               barmode="group", height=380)
        st.plotly_chart(fig_rep, use_container_width=True)

    with col2:
        # Strongest category per rep
        strongest = reps["strongest_category_per_rep"]
        st.markdown("**Strongest Category by Representative**")
        for _, row in strongest.iterrows():
            st.metric(
                label=str(row.get("sales_rep", "N/A")),
                value=str(row.get("strongest_category", "N/A")),
                delta=fmt_currency(row.get("total_sales", 0)),
            )

    # Rep by category heatmap
    rep_cat = reps["by_rep_category"].dropna(subset=["sales_rep"])
    if not rep_cat.empty:
        pivot = rep_cat.pivot_table(
            index="sales_rep", columns="category", values="total_sales", aggfunc="sum"
        ).fillna(0)
        fig_rc = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
            colorscale=[[0, "#1E3A5F"], [1, "#00C2CC"]],
            text=[[fmt_currency(v) for v in row] for row in pivot.values],
            texttemplate="%{text}",
        ))
        fig_rc.update_layout(**PLOTLY_TEMPLATE["layout"],
                              title="Sales by Representative and Category", height=350)
        st.plotly_chart(fig_rc, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# Main App
# ═══════════════════════════════════════════════════════════════
def main():
    # Banner
    st.markdown("""
    <div class="dashboard-title">
        <h1>📊 Sales Performance Intelligence Dashboard</h1>
        <p>Sample Superstore · Retail Analytics · Powered by Streamlit + Plotly</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    with st.spinner("Loading data..."):
        df = load_data()

    # Store total row count in session
    st.session_state["total_rows"] = len(df)

    # Sidebar filters
    df_filtered = render_sidebar(df)

    if df_filtered.empty:
        st.warning("No data matches the selected filters. Please adjust your filter criteria.")
        return

    # Navigation tabs
    tabs = st.tabs([
        "📊 Overview",
        "📈 Sales Analytics",
        "🗺️ Geography",
        "📦 Products",
        "🚚 Shipping",
        "👤 Representatives",
    ])

    with tabs[0]:
        render_overview(df_filtered)
    with tabs[1]:
        render_sales(df_filtered)
    with tabs[2]:
        render_geography(df_filtered)
    with tabs[3]:
        render_products(df_filtered)
    with tabs[4]:
        render_shipping(df_filtered)
    with tabs[5]:
        render_reps(df_filtered)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#4A5568;font-size:0.75rem;'>"
        "Sales Performance Analysis System · Built with Python, SQLite, Pandas, Plotly & Streamlit"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
