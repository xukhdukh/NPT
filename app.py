"""
ONGC NPT Intelligence Dashboard
Built with Dash + Plotly + SQLite
Based on PRD: ONGC_NPT_Intelligence_Dashboard_PRD.docx
"""
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc

DB_PATH = "npt_dashboard.db"


def get_data(filters=None):
    """Query SQLite with optional filters."""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM npt_events WHERE 1=1"
    params = []

    if filters:
        if filters.get("rig_name"):
            query += " AND rig_name IN ({})".format(",".join("?" * len(filters["rig_name"])))
            params.extend(filters["rig_name"])
        if filters.get("contractor"):
            query += " AND contractor IN ({})".format(",".join("?" * len(filters["contractor"])))
            params.extend(filters["contractor"])
        if filters.get("cause_category"):
            query += " AND cause_category IN ({})".format(",".join("?" * len(filters["cause_category"])))
            params.extend(filters["cause_category"])
        if filters.get("drilling_phase"):
            query += " AND drilling_phase IN ({})".format(",".join("?" * len(filters["drilling_phase"])))
            params.extend(filters["drilling_phase"])
        if filters.get("month"):
            query += " AND month IN ({})".format(",".join("?" * len(filters["month"])))
            params.extend(filters["month"])

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_filter_options():
    """Get unique values for filter dropdowns."""
    conn = sqlite3.connect(DB_PATH)
    options = {}
    for col in ["rig_name", "contractor", "cause_category", "drilling_phase", "month"]:
        cursor = conn.execute(f"SELECT DISTINCT {col} FROM npt_events ORDER BY {col}")
        options[col] = [row[0] for row in cursor.fetchall()]
    conn.close()
    return options


# Initialize app
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
app.title = "ONGC NPT Intelligence Dashboard"

options = get_filter_options()

# --- LAYOUT ---
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2("🛢️ ONGC NPT Intelligence Dashboard", className="text-warning mb-0"),
            html.P("Non-Productive Time Analysis | Jan–Jun 2024 | 6 Rigs",
                   className="text-muted small")
        ], width=12)
    ], className="py-3 border-bottom border-secondary mb-3"),

    # Filter Panel
    dbc.Row([
        dbc.Col([
            html.Label("Rig", className="text-light small"),
            dcc.Dropdown(id="filter-rig", options=[{"label": v, "value": v} for v in options["rig_name"]],
                         multi=True, placeholder="All Rigs", className="mb-2")
        ], md=2),
        dbc.Col([
            html.Label("Contractor", className="text-light small"),
            dcc.Dropdown(id="filter-contractor", options=[{"label": v, "value": v} for v in options["contractor"]],
                         multi=True, placeholder="All Contractors", className="mb-2")
        ], md=2),
        dbc.Col([
            html.Label("Cause Category", className="text-light small"),
            dcc.Dropdown(id="filter-cause", options=[{"label": v, "value": v} for v in options["cause_category"]],
                         multi=True, placeholder="All Causes", className="mb-2")
        ], md=3),
        dbc.Col([
            html.Label("Drilling Phase", className="text-light small"),
            dcc.Dropdown(id="filter-phase", options=[{"label": v, "value": v} for v in options["drilling_phase"]],
                         multi=True, placeholder="All Phases", className="mb-2")
        ], md=3),
        dbc.Col([
            html.Label("Month", className="text-light small"),
            dcc.Dropdown(id="filter-month", options=[{"label": v, "value": v} for v in options["month"]],
                         multi=True, placeholder="All Months", className="mb-2")
        ], md=2),
    ], className="bg-dark p-3 rounded mb-3"),

    # KPI Row
    dbc.Row(id="kpi-row", className="mb-3"),

    # Charts Row 1
    dbc.Row([
        dbc.Col([dcc.Graph(id="chart-cause-category")], md=6),
        dbc.Col([dcc.Graph(id="chart-rig")], md=6),
    ], className="mb-3"),

    # Charts Row 2
    dbc.Row([
        dbc.Col([dcc.Graph(id="chart-monthly-trend")], md=6),
        dbc.Col([dcc.Graph(id="chart-pareto")], md=6),
    ], className="mb-3"),

    # Drilldown Table
    dbc.Row([
        dbc.Col([
            html.H5("📋 Drilldown: Top NPT Events", className="text-light"),
            html.Div(id="drilldown-table")
        ], width=12)
    ], className="mb-4"),

    # Pain Point Summary
    dbc.Row([
        dbc.Col([
            html.H5("⚠️ Key Pain Points & Insights", className="text-warning"),
            html.Div(id="pain-points")
        ], width=12)
    ], className="mb-4"),

], fluid=True, className="bg-dark")


# --- CALLBACKS ---
@callback(
    [Output("kpi-row", "children"),
     Output("chart-cause-category", "figure"),
     Output("chart-rig", "figure"),
     Output("chart-monthly-trend", "figure"),
     Output("chart-pareto", "figure"),
     Output("drilldown-table", "children"),
     Output("pain-points", "children")],
    [Input("filter-rig", "value"),
     Input("filter-contractor", "value"),
     Input("filter-cause", "value"),
     Input("filter-phase", "value"),
     Input("filter-month", "value")]
)
def update_dashboard(rig, contractor, cause, phase, month):
    filters = {}
    if rig: filters["rig_name"] = rig
    if contractor: filters["contractor"] = contractor
    if cause: filters["cause_category"] = cause
    if phase: filters["drilling_phase"] = phase
    if month: filters["month"] = month

    df = get_data(filters if filters else None)

    # --- KPIs ---
    total_npt = df["npt_hours"].sum()
    total_events = len(df)
    avg_npt = df["npt_hours"].mean() if len(df) > 0 else 0
    worst_rig = df.groupby("rig_name")["npt_hours"].sum().idxmax() if len(df) > 0 else "N/A"
    top_cause = df.groupby("cause_category")["npt_hours"].sum().idxmax() if len(df) > 0 else "N/A"
    peak_month = df.groupby("month")["npt_hours"].sum().idxmax() if len(df) > 0 else "N/A"

    kpi_cards = [
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{total_npt:.0f}", className="text-warning"),
            html.P("Total NPT Hours", className="text-muted small mb-0")
        ]), className="bg-secondary"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{total_events}", className="text-info"),
            html.P("Total Events", className="text-muted small mb-0")
        ]), className="bg-secondary"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{avg_npt:.1f} hrs", className="text-success"),
            html.P("Avg NPT/Event", className="text-muted small mb-0")
        ]), className="bg-secondary"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(worst_rig, className="text-danger", style={"fontSize": "1rem"}),
            html.P("Worst Rig", className="text-muted small mb-0")
        ]), className="bg-secondary"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(top_cause, className="text-danger", style={"fontSize": "1rem"}),
            html.P("Top Cause", className="text-muted small mb-0")
        ]), className="bg-secondary"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(peak_month, className="text-warning", style={"fontSize": "1rem"}),
            html.P("Peak Month", className="text-muted small mb-0")
        ]), className="bg-secondary"), md=2),
    ]

    # --- Chart: NPT by Cause Category ---
    cause_df = df.groupby("cause_category")["npt_hours"].sum().reset_index().sort_values("npt_hours", ascending=False)
    fig_cause = px.bar(cause_df, x="cause_category", y="npt_hours",
                       color="npt_hours", color_continuous_scale="Reds",
                       title="NPT Hours by Cause Category")
    fig_cause.update_layout(template="plotly_dark", showlegend=False,
                            xaxis_title="", yaxis_title="NPT Hours", height=350)

    # --- Chart: NPT by Rig ---
    rig_df = df.groupby("rig_name")["npt_hours"].sum().reset_index().sort_values("npt_hours", ascending=False)
    fig_rig = px.bar(rig_df, x="rig_name", y="npt_hours",
                     color="npt_hours", color_continuous_scale="Blues",
                     title="NPT Hours by Rig")
    fig_rig.update_layout(template="plotly_dark", showlegend=False,
                          xaxis_title="", yaxis_title="NPT Hours", height=350)

    # --- Chart: Monthly Trend ---
    monthly_df = df.groupby(["month_num", "month"])["npt_hours"].sum().reset_index().sort_values("month_num")
    fig_monthly = px.line(monthly_df, x="month", y="npt_hours",
                          markers=True, title="Monthly NPT Trend")
    fig_monthly.update_layout(template="plotly_dark", xaxis_title="", yaxis_title="NPT Hours", height=350)
    fig_monthly.update_traces(line_color="#ffc107", marker_size=8)

    # --- Chart: Pareto (Top Cause Details) ---
    detail_df = df.groupby("cause_detail")["npt_hours"].sum().reset_index().sort_values("npt_hours", ascending=False).head(10)
    detail_df["cumulative_pct"] = detail_df["npt_hours"].cumsum() / detail_df["npt_hours"].sum() * 100

    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(x=detail_df["cause_detail"], y=detail_df["npt_hours"],
                                name="NPT Hours", marker_color="#e74c3c"))
    fig_pareto.add_trace(go.Scatter(x=detail_df["cause_detail"], y=detail_df["cumulative_pct"],
                                    name="Cumulative %", yaxis="y2", mode="lines+markers",
                                    line=dict(color="#ffc107", width=2)))
    fig_pareto.update_layout(
        template="plotly_dark", title="Top 10 Cause Details (Pareto)",
        yaxis=dict(title="NPT Hours"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        height=350, showlegend=False, xaxis_tickangle=-30
    )

    # --- Drilldown Table (Top 15 events) ---
    top_events = df.nlargest(15, "npt_hours")[["date", "rig_name", "well_name", "contractor",
                                                "npt_hours", "cause_category", "cause_detail", "drilling_phase"]]
    table = dbc.Table.from_dataframe(top_events, striped=True, bordered=True, hover=True,
                                     size="sm", color="dark", className="small")

    # --- Pain Points ---
    insights = []
    if len(df) > 0:
        insights.append(f"• Total NPT: {total_npt:.0f} hours across {total_events} events (Avg {avg_npt:.1f} hrs/event)")
        insights.append(f"• Worst performing rig: {worst_rig}")
        insights.append(f"• Dominant cause category: {top_cause} ({cause_df.iloc[0]['npt_hours']:.0f} hrs)")
        insights.append(f"• Peak NPT month: {peak_month}")
        # Pareto insight
        top3_causes = detail_df.head(3)["cause_detail"].tolist()
        top3_pct = detail_df.head(3)["cumulative_pct"].iloc[-1]
        insights.append(f"• Top 3 cause details ({', '.join(top3_causes)}) account for {top3_pct:.0f}% of top-10 NPT")
        # Phase insight
        phase_df = df.groupby("drilling_phase")["npt_hours"].sum().sort_values(ascending=False)
        insights.append(f"• Most NPT-prone phase: {phase_df.index[0]} ({phase_df.iloc[0]:.0f} hrs)")

    pain_div = html.Div([html.P(i, className="text-light mb-1") for i in insights])

    return kpi_cards, fig_cause, fig_rig, fig_monthly, fig_pareto, table, pain_div


if __name__ == "__main__":
    print("Starting ONGC NPT Intelligence Dashboard...")
    print("Open http://127.0.0.1:8050 in your browser")
    app.run(debug=True, port=8050)
