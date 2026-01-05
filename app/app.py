# app/app.py
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="USA Flight Delay Analytics (2024)", layout="wide")

REPO_ROOT = Path(__file__).resolve().parents[1]
DASH_DIR = REPO_ROOT / "data" / "processed" / "dashboard"

@st.cache_data
def load_tables():
    kpi = pd.read_csv(DASH_DIR / "kpi_overview.csv")
    core = pd.read_csv(DASH_DIR / "cube_core.csv")
    hour = pd.read_csv(DASH_DIR / "cube_hour.csv")
    cause = pd.read_csv(DASH_DIR / "cube_cause.csv")
    airport = pd.read_csv(DASH_DIR / "cube_airport_top.csv")

    # Ensure sorting fields
    for df in [core, hour, cause, airport]:
        if "month" in df.columns:
            df["month"] = pd.to_numeric(df["month"], errors="coerce")
    return kpi, core, hour, cause, airport

def ensure_files_exist():
    needed = [
        "kpi_overview.csv", "cube_core.csv", "cube_hour.csv", "cube_cause.csv", "cube_airport_top.csv"
    ]
    missing = [f for f in needed if not (DASH_DIR / f).exists()]
    if missing:
        st.error("Missing dashboard tables. Generate them first:")
        st.code(
            "python scripts/build_dashboard_tables.py "
            "--infile data/processed/flight_clean_data_2024.csv "
            "--outdir data/processed/dashboard",
            language="bash"
        )
        st.write("Missing files:", missing)
        st.stop()

ensure_files_exist()
kpi, core, hour, cause, airport = load_tables()

st.title("USA Flight Delay Analytics (2024) ✈️📊")
st.caption("Interactive dashboard built with Streamlit + Plotly (hosted using small aggregated tables).")

# ----------------------------
# Sidebar filters (global)
# ----------------------------
st.sidebar.header("Filters")

months = sorted(core["month_name"].dropna().unique().tolist())
airlines = sorted(core["operating_airline"].dropna().unique().tolist())
states = sorted(core["origin_state_abbr"].dropna().unique().tolist())

sel_months = st.sidebar.multiselect("Month", months, default=months)
sel_airlines = st.sidebar.multiselect("Airline", airlines, default=airlines)
sel_states = st.sidebar.multiselect("Origin State", states, default=states)

cause_opts = sorted(cause["primary_delay_cause"].dropna().unique().tolist())
sel_causes = st.sidebar.multiselect("Primary Delay Cause", cause_opts, default=cause_opts)

hour_opts = sorted(hour["scheduled_departure_hour"].dropna().unique().tolist())
sel_hours = st.sidebar.multiselect("Scheduled Departure Hour", hour_opts, default=hour_opts)

# Filter helper
def apply_core_filters(df: pd.DataFrame) -> pd.DataFrame:
    out = df[
        df["month_name"].isin(sel_months)
        & df["operating_airline"].isin(sel_airlines)
        & df["origin_state_abbr"].isin(sel_states)
    ].copy()
    return out

core_f = apply_core_filters(core)
hour_f = hour[
    hour["month_name"].isin(sel_months)
    & hour["operating_airline"].isin(sel_airlines)
    & hour["origin_state_abbr"].isin(sel_states)
    & hour["scheduled_departure_hour"].isin(sel_hours)
].copy()

cause_f = cause[
    cause["month_name"].isin(sel_months)
    & cause["operating_airline"].isin(sel_airlines)
    & cause["origin_state_abbr"].isin(sel_states)
    & cause["primary_delay_cause"].isin(sel_causes)
].copy()

airport_f = airport[
    airport["month_name"].isin(sel_months)
    & airport["operating_airline"].isin(sel_airlines)
    & airport["origin_state_abbr"].isin(sel_states)
].copy()

# ----------------------------
# KPI cards (from filtered core)
# ----------------------------
total_flights = int(core_f["flights"].sum())
delayed_flights = int(core_f["delayed_flights"].sum())
delay_rate = (delayed_flights / total_flights) if total_flights else 0.0
avg_arr_delay = (core_f["sum_arrival_delay_min"].sum() / total_flights) if total_flights else 0.0
total_delay_min = float(core_f["sum_total_delay_min"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Flights", f"{total_flights:,}")
c2.metric("Delay Rate (>15 min)", f"{delay_rate*100:.1f}%")
c3.metric("Avg Arrival Delay (min)", f"{avg_arr_delay:.1f}")
c4.metric("Total Delay Minutes", f"{total_delay_min:,.0f}")

st.divider()

# ----------------------------
# Map: Avg delay by state
# ----------------------------
state_summary = (
    core_f.groupby("origin_state_abbr", dropna=False)
    .agg(
        flights=("flights", "sum"),
        delayed=("delayed_flights", "sum"),
        sum_arr=("sum_arrival_delay_min", "sum"),
    )
    .reset_index()
)
state_summary["delay_rate"] = state_summary["delayed"] / state_summary["flights"]
state_summary["avg_arrival_delay_min"] = state_summary["sum_arr"] / state_summary["flights"]

map_col, trend_col = st.columns([1.3, 1])

with map_col:
    fig_map = px.choropleth(
        state_summary,
        locations="origin_state_abbr",
        locationmode="USA-states",
        color="avg_arrival_delay_min",
        hover_data={"flights": True, "delay_rate": ":.2%"},
        scope="usa",
        title="Average Arrival Delay by Origin State"
    )
    st.plotly_chart(fig_map, use_container_width=True)

with trend_col:
    monthly = (
        core_f.groupby(["month", "month_name"], dropna=False)
        .agg(
            flights=("flights", "sum"),
            delayed=("delayed_flights", "sum"),
            sum_arr=("sum_arrival_delay_min", "sum")
        )
        .reset_index()
        .sort_values("month")
    )
    monthly["delay_rate"] = monthly["delayed"] / monthly["flights"]
    monthly["avg_arrival_delay_min"] = monthly["sum_arr"] / monthly["flights"]

    fig_trend = px.line(
        monthly, x="month_name", y="avg_arrival_delay_min",
        title="Avg Arrival Delay by Month"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ----------------------------
# Airline + Airport
# ----------------------------
left, right = st.columns(2)

with left:
    airline_summary = (
        core_f.groupby("operating_airline", dropna=False)
        .agg(
            flights=("flights", "sum"),
            delayed=("delayed_flights", "sum"),
            sum_arr=("sum_arrival_delay_min", "sum")
        )
        .reset_index()
    )
    airline_summary["delay_rate"] = airline_summary["delayed"] / airline_summary["flights"]
    airline_summary["avg_arrival_delay_min"] = airline_summary["sum_arr"] / airline_summary["flights"]
    airline_summary = airline_summary.sort_values("avg_arrival_delay_min", ascending=False).head(12)

    fig_air = px.bar(
        airline_summary,
        x="operating_airline",
        y="avg_arrival_delay_min",
        hover_data={"flights": True, "delay_rate": ":.2%"},
        title="Top Airlines by Avg Arrival Delay (Top 12)"
    )
    st.plotly_chart(fig_air, use_container_width=True)

with right:
    airport_summary = (
        airport_f.groupby("origin_airport", dropna=False)
        .agg(
            flights=("flights", "sum"),
            delayed=("delayed_flights", "sum"),
            sum_arr=("sum_arrival_delay_min", "sum")
        )
        .reset_index()
    )
    airport_summary["delay_rate"] = airport_summary["delayed"] / airport_summary["flights"]
    airport_summary["avg_arrival_delay_min"] = airport_summary["sum_arr"] / airport_summary["flights"]
    airport_summary = airport_summary.sort_values("avg_arrival_delay_min", ascending=False).head(12)

    fig_airport = px.bar(
        airport_summary,
        x="origin_airport",
        y="avg_arrival_delay_min",
        hover_data={"flights": True, "delay_rate": ":.2%"},
        title="Top Airports by Avg Arrival Delay (Top 12, from top-airport set)"
    )
    st.plotly_chart(fig_airport, use_container_width=True)

st.divider()

# ----------------------------
# Cause + Hour distribution
# ----------------------------
b1, b2 = st.columns(2)

with b1:
    cause_summary = (
        cause_f.groupby("primary_delay_cause", dropna=False)
        .agg(flights=("flights", "sum"))
        .reset_index()
        .sort_values("flights", ascending=False)
    )
    fig_cause = px.pie(
        cause_summary,
        names="primary_delay_cause",
        values="flights",
        title="Primary Delay Cause Breakdown"
    )
    st.plotly_chart(fig_cause, use_container_width=True)

with b2:
    hour_summary = (
        hour_f.groupby("scheduled_departure_hour", dropna=False)
        .agg(
            flights=("flights", "sum"),
            delayed=("delayed_flights", "sum")
        )
        .reset_index()
        .sort_values("scheduled_departure_hour")
    )
    hour_summary["delay_rate"] = hour_summary["delayed"] / hour_summary["flights"]

    fig_hour = px.bar(
        hour_summary,
        x="scheduled_departure_hour",
        y="delay_rate",
        title="Delay Rate by Scheduled Departure Hour",
        labels={"delay_rate": "Delay Rate"}
    )
    st.plotly_chart(fig_hour, use_container_width=True)