# app/app.py
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Flight Delay Dashboard", layout="wide")

REPO_ROOT = Path(__file__).resolve().parents[1]
DASH_DIR = REPO_ROOT / "data" / "processed" / "dashboard"

REQUIRED_FILES = [
    "kpi_overview.csv",
    "cube_core.csv",
    "cube_hour.csv",
    "cube_cause.csv",
    "cube_airport_top.csv",
]

@st.cache_data
def load_tables():
    kpi = pd.read_csv(DASH_DIR / "kpi_overview.csv")
    core = pd.read_csv(DASH_DIR / "cube_core.csv")
    hour = pd.read_csv(DASH_DIR / "cube_hour.csv")
    cause = pd.read_csv(DASH_DIR / "cube_cause.csv")
    airport = pd.read_csv(DASH_DIR / "cube_airport_top.csv")

    for df in [core, hour, cause, airport]:
        if "month" in df.columns:
            df["month"] = pd.to_numeric(df["month"], errors="coerce")
    return kpi, core, hour, cause, airport

def ensure_files_exist():
    missing = [f for f in REQUIRED_FILES if not (DASH_DIR / f).exists()]
    if missing:
        st.error("Missing dashboard tables. Generate them first:")
        st.code(
            "python scripts/build_dashboard_tables.py "
            "--infile data/processed/flight_clean_data_2024.csv "
            "--outdir data/processed/dashboard",
            language="bash",
        )
        st.write("Missing files:", missing)
        st.stop()

def rerun():
    # compatible across Streamlit versions
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

ensure_files_exist()
kpi, core, hour, cause, airport = load_tables()

st.title("USA Flight Delay Dashboard (2024) ✈️")
st.caption("by Arik Ahnaf")

# ----------------------------
# Sidebar filters (global)
# ----------------------------
st.sidebar.header("Filters")

months_all = sorted(core["month_name"].dropna().unique().tolist())
airlines_all = sorted(core["operating_airline"].dropna().unique().tolist())
states_all = sorted(core["origin_state_abbr"].dropna().unique().tolist())

causes_all = sorted(cause["primary_delay_cause"].dropna().unique().tolist())
hours_all = sorted(hour["scheduled_departure_hour"].dropna().unique().tolist())

# Defaults
def _init_state():
    st.session_state.setdefault("f_months", months_all)
    st.session_state.setdefault("f_airlines", airlines_all)
    st.session_state.setdefault("f_states", states_all)
    st.session_state.setdefault("f_causes", causes_all)
    st.session_state.setdefault("f_hours", hours_all)
    st.session_state.setdefault("top_n_airlines", 12)
    st.session_state.setdefault("top_n_airports", 12)
    st.session_state.setdefault("map_metric", "Avg Arrival Delay (min)")

_init_state()

colA, colB = st.sidebar.columns([1, 1])
with colA:
    if st.button("Reset filters", use_container_width=True):
        st.session_state["f_months"] = months_all
        st.session_state["f_airlines"] = airlines_all
        st.session_state["f_states"] = states_all
        st.session_state["f_causes"] = causes_all
        st.session_state["f_hours"] = hours_all
        st.session_state["top_n_airlines"] = 12
        st.session_state["top_n_airports"] = 12
        st.session_state["map_metric"] = "Avg Arrival Delay (min)"
        rerun()

with colB:
    st.write("")

st.session_state["map_metric"] = st.sidebar.radio(
    "Map color metric",
    ["Avg Arrival Delay (min)", "Delay Rate (>15 min)"],
    index=0 if st.session_state["map_metric"] == "Avg Arrival Delay (min)" else 1,
)

st.session_state["top_n_airlines"] = st.sidebar.slider(
    "Top airlines to display",
    min_value=5, max_value=25, value=int(st.session_state["top_n_airlines"]), step=1
)

st.session_state["top_n_airports"] = st.sidebar.slider(
    "Top airports to display",
    min_value=5, max_value=25, value=int(st.session_state["top_n_airports"]), step=1
)

sel_months = st.sidebar.multiselect("Month", months_all, default=st.session_state["f_months"], key="f_months")
sel_airlines = st.sidebar.multiselect("Airline", airlines_all, default=st.session_state["f_airlines"], key="f_airlines")
sel_states = st.sidebar.multiselect("Origin State", states_all, default=st.session_state["f_states"], key="f_states")
sel_causes = st.sidebar.multiselect("Primary Delay Cause", causes_all, default=st.session_state["f_causes"], key="f_causes")
sel_hours = st.sidebar.multiselect("Scheduled Departure Hour", hours_all, default=st.session_state["f_hours"], key="f_hours")

# Guard against empty selections
if not sel_months or not sel_airlines or not sel_states:
    st.warning("Select at least one Month, Airline, and Origin State to display results.")
    st.stop()

# ----------------------------
# Apply filters
# ----------------------------
core_f = core[
    core["month_name"].isin(sel_months)
    & core["operating_airline"].isin(sel_airlines)
    & core["origin_state_abbr"].isin(sel_states)
].copy()

hour_f = hour[
    hour["month_name"].isin(sel_months)
    & hour["operating_airline"].isin(sel_airlines)
    & hour["origin_state_abbr"].isin(sel_states)
    & hour["scheduled_departure_hour"].isin(sel_hours if sel_hours else hours_all)
].copy()

cause_f = cause[
    cause["month_name"].isin(sel_months)
    & cause["operating_airline"].isin(sel_airlines)
    & cause["origin_state_abbr"].isin(sel_states)
    & cause["primary_delay_cause"].isin(sel_causes if sel_causes else causes_all)
].copy()

airport_f = airport[
    airport["month_name"].isin(sel_months)
    & airport["operating_airline"].isin(sel_airlines)
    & airport["origin_state_abbr"].isin(sel_states)
].copy()

# Filter summary
st.caption(
    f"Showing **{len(sel_months)} month(s)** • **{len(sel_airlines)} airline(s)** • **{len(sel_states)} state(s)**"
)

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
# Map + Trend
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

monthly = (
    core_f.groupby(["month", "month_name"], dropna=False)
    .agg(
        flights=("flights", "sum"),
        delayed=("delayed_flights", "sum"),
        sum_arr=("sum_arrival_delay_min", "sum"),
    )
    .reset_index()
    .sort_values("month")
)
monthly["delay_rate"] = monthly["delayed"] / monthly["flights"]
monthly["avg_arrival_delay_min"] = monthly["sum_arr"] / monthly["flights"]

map_col, trend_col = st.columns([1.3, 1])

with map_col:
    if st.session_state["map_metric"] == "Avg Arrival Delay (min)":
        color_col = "avg_arrival_delay_min"
        title = "Average Arrival Delay by Origin State"
        hover = {"flights": True, "delay_rate": ":.2%"}
    else:
        color_col = "delay_rate"
        title = "Delay Rate (>15 min) by Origin State"
        hover = {"flights": True, "avg_arrival_delay_min": ":.1f"}

    fig_map = px.choropleth(
        state_summary,
        locations="origin_state_abbr",
        locationmode="USA-states",
        color=color_col,
        hover_data=hover,
        scope="usa",
        title=title,
    )
    st.plotly_chart(fig_map, use_container_width=True)

with trend_col:
    fig_trend = px.line(
        monthly,
        x="month_name",
        y="avg_arrival_delay_min",
        title="Avg Arrival Delay by Month",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ----------------------------
# Airlines + Airports
# ----------------------------
left, right = st.columns(2)

with left:
    airline_summary = (
        core_f.groupby("operating_airline", dropna=False)
        .agg(
            flights=("flights", "sum"),
            delayed=("delayed_flights", "sum"),
            sum_arr=("sum_arrival_delay_min", "sum"),
        )
        .reset_index()
    )
    airline_summary["delay_rate"] = airline_summary["delayed"] / airline_summary["flights"]
    airline_summary["avg_arrival_delay_min"] = airline_summary["sum_arr"] / airline_summary["flights"]
    airline_summary = airline_summary.sort_values("avg_arrival_delay_min", ascending=False).head(int(st.session_state["top_n_airlines"]))

    fig_air = px.bar(
        airline_summary,
        x="operating_airline",
        y="avg_arrival_delay_min",
        hover_data={"flights": True, "delay_rate": ":.2%"},
        title=f"Top Airlines by Avg Arrival Delay (Top {int(st.session_state['top_n_airlines'])})",
    )
    st.plotly_chart(fig_air, use_container_width=True)

with right:
    airport_summary = (
        airport_f.groupby("origin_airport", dropna=False)
        .agg(
            flights=("flights", "sum"),
            delayed=("delayed_flights", "sum"),
            sum_arr=("sum_arrival_delay_min", "sum"),
        )
        .reset_index()
    )
    airport_summary["delay_rate"] = airport_summary["delayed"] / airport_summary["flights"]
    airport_summary["avg_arrival_delay_min"] = airport_summary["sum_arr"] / airport_summary["flights"]
    airport_summary = airport_summary.sort_values("avg_arrival_delay_min", ascending=False).head(int(st.session_state["top_n_airports"]))

    fig_airport = px.bar(
        airport_summary,
        x="origin_airport",
        y="avg_arrival_delay_min",
        hover_data={"flights": True, "delay_rate": ":.2%"},
        title=f"Top Airports by Avg Arrival Delay (Top {int(st.session_state['top_n_airports'])})",
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
        title="Primary Delay Cause Breakdown",
    )
    st.plotly_chart(fig_cause, use_container_width=True)

with b2:
    hour_summary = (
        hour_f.groupby("scheduled_departure_hour", dropna=False)
        .agg(
            flights=("flights", "sum"),
            delayed=("delayed_flights", "sum"),
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
        labels={"delay_rate": "Delay Rate"},
    )
    st.plotly_chart(fig_hour, use_container_width=True)
