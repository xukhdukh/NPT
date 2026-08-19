"""
ONGC NPT Intelligence Dashboard — Streamlit Version
Built for Streamlit Cloud deployment
Data source: Copy of ONGC_NPT_Workshop_Dataset.xlsx → SQLite
"""
import sqlite3
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="ONGC NPT Intelligence Dashboard",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Database Setup ---
DB_PATH = "npt_dashboard.db"
EXCEL_PATH = "Copy of ONGC_NPT_Workshop_Dataset.xlsx"


def init_db():
    """Create SQLite DB from Excel if it doesn't exist."""
    if os.path.exists(DB_PATH):
        return
    df = pd.read_excel(EXCEL_PATH, sheet_name="NPT_Data", header=2)
    df.columns = [
        "date", "rig_name", "well_name", "contractor",
        "npt_hours", "cause_category", "cause_detail",
        "drilling_phase", "month", "month_num"
    ]
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["date", "rig_name", "npt_hours"])

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS npt_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            rig_name TEXT,
            well_name TEXT,
            contractor TEXT,
            npt_hours REAL,
            cause_category TEXT,
            cause_detail TEXT,
            drilling_phase TEXT,
            month TEXT,
            month_num INTEGER
        )
    """)
    df.to_sql("npt_events", conn, if_exists="append", index=False)
    conn.close()


@st.cache_data
def load_all_data():
    """Load all NPT data from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM npt_events", conn)
    conn.close()
    return df


def get_filtered_data(df, filters):
    """Apply filters to dataframe."""
    filtered = df.copy()
    if filters.get("rig_name"):
        filtered = filtered[filtered["rig_name"].isin(filters["rig_name"])]
    if filters.get("contractor"):
        filtered = filtered[filtered["contractor"].isin(filters["contractor"])]
    if filters.get("cause_category"):
        filtered = filtered[filtered["cause_category"].isin(filters["cause_category"])]
    if filters.get("drilling_phase"):
        filtered = filtered[filtered["drilling_phase"].isin(filters["drilling_phase"])]
    if filters.get("month"):
        filtered = filtered[filtered["month"].isin(filters["month"])]
    return filtered


# --- Initialize ---
init_db()
df_all = load_all_data()

# --- Header ---
st.markdown("## 🛢️ ONGC NPT Intelligence Dashboard")
st.caption("Non-Productive Time Analysis | Jan–Jun 2024 | 6 Rigs | Synthetic Workshop Data")
st.divider()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")

rig_options = sorted(df_all["rig_name"].unique())
contractor_options = sorted(df_all["contractor"].unique())
cause_options = sorted(df_all["cause_category"].unique())
phase_options = sorted(df_all["drilling_phase"].unique())
month_options = df_all.sort_values("month_num")["month"].unique().tolist()

sel_rig = st.sidebar.multiselect("Rig Name", rig_options)
sel_contractor = st.sidebar.multiselect("Contractor", contractor_options)
sel_cause = st.sidebar.multiselect("Cause Category", cause_options)
sel_phase = st.sidebar.multiselect("Drilling Phase", phase_options)
sel_month = st.sidebar.multiselect("Month", month_options)

filters = {}
if sel_rig: filters["rig_name"] = sel_rig
if sel_contractor: filters["contractor"] = sel_contractor
if sel_cause: filters["cause_category"] = sel_cause
if sel_phase: filters["drilling_phase"] = sel_phase
if sel_month: filters["month"] = sel_month

df = get_filtered_data(df_all, filters)

# --- KPI Row ---
if len(df) == 0:
    st.warning("No data matches the selected filters.")
    st.stop()

total_npt = df["npt_hours"].sum()
total_events = len(df)
avg_npt = df["npt_hours"].mean()
worst_rig = df.groupby("rig_name")["npt_hours"].sum().idxmax()
top_cause = df.groupby("cause_category")["npt_hours"].sum().idxmax()
peak_month = df.groupby("month")["npt_hours"].sum().idxmax()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total NPT Hours", f"{total_npt:,.0f}")
col2.metric("Total Events", f"{total_events}")
col3.metric("Avg NPT/Event", f"{avg_npt:.1f} hrs")
col4.metric("Worst Rig", worst_rig)
col5.metric("Top Cause", top_cause)
col6.metric("Peak Month", peak_month)

st.divider()

# --- Charts Row 1 ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    cause_df = df.groupby("cause_category")["npt_hours"].sum().reset_index().sort_values("npt_hours", ascending=False)
    fig_cause = px.bar(cause_df, x="cause_category", y="npt_hours",
                       color="npt_hours", color_continuous_scale="Reds",
                       title="NPT Hours by Cause Category")
    fig_cause.update_layout(xaxis_title="", yaxis_title="NPT Hours",
                            showlegend=False, height=380)
    st.plotly_chart(fig_cause, use_container_width=True)

with chart_col2:
    rig_df = df.groupby("rig_name")["npt_hours"].sum().reset_index().sort_values("npt_hours", ascending=False)
    fig_rig = px.bar(rig_df, x="rig_name", y="npt_hours",
                     color="npt_hours", color_continuous_scale="Blues",
                     title="NPT Hours by Rig")
    fig_rig.update_layout(xaxis_title="", yaxis_title="NPT Hours",
                          showlegend=False, height=380)
    st.plotly_chart(fig_rig, use_container_width=True)

# --- Charts Row 2 ---
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    monthly_df = df.groupby(["month_num", "month"])["npt_hours"].sum().reset_index().sort_values("month_num")
    fig_monthly = px.line(monthly_df, x="month", y="npt_hours",
                          markers=True, title="Monthly NPT Trend")
    fig_monthly.update_layout(xaxis_title="", yaxis_title="NPT Hours", height=380)
    fig_monthly.update_traces(line_color="#FF6B35", marker_size=8)
    st.plotly_chart(fig_monthly, use_container_width=True)

with chart_col4:
    detail_df = df.groupby("cause_detail")["npt_hours"].sum().reset_index() \
        .sort_values("npt_hours", ascending=False).head(10)
    detail_df["cumulative_pct"] = detail_df["npt_hours"].cumsum() / detail_df["npt_hours"].sum() * 100

    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(
        x=detail_df["cause_detail"], y=detail_df["npt_hours"],
        name="NPT Hours", marker_color="#e74c3c"
    ))
    fig_pareto.add_trace(go.Scatter(
        x=detail_df["cause_detail"], y=detail_df["cumulative_pct"],
        name="Cumulative %", yaxis="y2", mode="lines+markers",
        line=dict(color="#f39c12", width=2)
    ))
    fig_pareto.update_layout(
        title="Top 10 Cause Details (Pareto)",
        yaxis=dict(title="NPT Hours"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        height=380, showlegend=False, xaxis_tickangle=-30
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

st.divider()

# --- Drilldown Table ---
st.subheader("📋 Top NPT Events")
top_events = df.nlargest(20, "npt_hours")[
    ["date", "rig_name", "well_name", "contractor",
     "npt_hours", "cause_category", "cause_detail", "drilling_phase"]
]
st.dataframe(top_events, use_container_width=True, hide_index=True)

st.divider()

# --- Pain Points & Insights ---
st.subheader("⚠️ Key Pain Points & Insights")

insights = []
insights.append(f"**Total NPT:** {total_npt:,.0f} hours across {total_events} events (Avg {avg_npt:.1f} hrs/event)")
insights.append(f"**Worst performing rig:** {worst_rig}")

cause_top = cause_df.iloc[0]
insights.append(f"**Dominant cause category:** {cause_top['cause_category']} ({cause_top['npt_hours']:,.0f} hrs)")
insights.append(f"**Peak NPT month:** {peak_month}")

top3_causes = detail_df.head(3)["cause_detail"].tolist()
top3_pct = detail_df.head(3)["cumulative_pct"].iloc[-1]
insights.append(f"**Top 3 cause details** ({', '.join(top3_causes)}) account for {top3_pct:.0f}% of top-10 NPT")

phase_df = df.groupby("drilling_phase")["npt_hours"].sum().sort_values(ascending=False)
insights.append(f"**Most NPT-prone phase:** {phase_df.index[0]} ({phase_df.iloc[0]:,.0f} hrs)")

for insight in insights:
    st.markdown(f"- {insight}")

st.divider()

# --- Export ---
st.subheader("📥 Export Data")
col_exp1, col_exp2 = st.columns(2)
with col_exp1:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered Data (CSV)", csv, "npt_filtered_data.csv", "text/csv")
with col_exp2:
    csv_all = df_all.to_csv(index=False).encode("utf-8")
    st.download_button("Download Full Dataset (CSV)", csv_all, "npt_full_data.csv", "text/csv")

# --- Footer ---
st.divider()
st.caption("Source: ONGC NPT Workshop Dataset (Synthetic) | Built for MDP Workshop | IIM Kozhikode")
