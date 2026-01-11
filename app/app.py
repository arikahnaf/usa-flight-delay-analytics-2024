import streamlit as st
from data_loader import (
    get_dash_dir,
    ensure_files_exist,
    load_core_table,
    load_routes_table,
    load_airlines_lookup,
)
from lookups import build_airline_mappers
from sections.filters import render_filters
from sections.kpis import render_kpis
from sections.pies import render_pies
from sections.lines import render_delay_lines
from sections.maps import render_state_delay_maps
from sections.bars import render_airline_delay_bars
from sections.monthly_table import render_monthly_summary
from sections.airline_scorecard import render_airline_scorecard
from sections.state_scorecards import render_state_scorecards

st.set_page_config(page_title="Flight Delay Dashboard", layout="wide")

# Global UI styling (dark sidebar + nicer multiselect)
st.markdown(
    """
    <style>
      /* Reduce top whitespace above the page content */
      .block-container {
        padding-top: 2.5rem !important;   /* try 0.6rem, 0.8rem, 1.0rem */
      }
      
      /* Sidebar background + scroll */
      section[data-testid="stSidebar"] {
        background-color: #2d2d2d;
      }
      section[data-testid="stSidebar"] > div {
        height: 100vh;
        overflow-y: auto;
      }

      /* Multiselect / Select styling (BaseWeb) */

      /* Input box */
      section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-radius: 10px !important;
      }

      /* Selected chips/tags (dark theme) */
      section[data-testid="stSidebar"] [data-baseweb="tag"] {
        background-color: rgba(0,0,0,0.55) !important;      /* dark chip */
        border: 1px solid rgba(255,255,255,0.14) !important;/* subtle outline */
        color: rgba(255,255,255,0.92) !important;
        margin: 2px 6px 2px 0 !important;                   /* spacing between chips */
      }
      section[data-testid="stSidebar"] [data-baseweb="tag"] span {
        color: rgba(255,255,255,0.92) !important;
      }
      section[data-testid="stSidebar"] [data-baseweb="tag"] svg {
        fill: rgba(255,255,255,0.80) !important;            /* close "x" */
      }

      /* Dropdown popover (border + shadow so it doesn't blend in) */
      [data-baseweb="popover"] > div {
        background: #1f1f1f !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.55) !important;
      }

      /* Make dropdown list scroll instead of covering the whole sidebar */
      [data-baseweb="menu"] {
        max-height: 260px !important;
        overflow-y: auto !important;
      }

      /* Option hover/selected state (neutral dark, no blue) */
      [data-baseweb="menu"] [role="option"]:hover {
        background-color: rgba(255,255,255,0.06) !important;
      }
      [data-baseweb="menu"] [aria-selected="true"] {
        background-color: rgba(255,255,255,0.10) !important;
      }

      /* Section titles (match KPI title shade) */
      .section-title {
        color: #EFEFEF;
        font-weight: 600;
        font-size: 1.50rem;
        margin: 0 0 8px 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header
# -----------------------------
st.title("USA Flight Delay Dashboard (2024) ✈️")
st.markdown(
    "<div style='font-size:20px; opacity:0.85; margin-top:-10px;'>by <b>Arik Ahnaf</b></div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<hr style='border: none; height: 1px; background: rgba(255,255,255,0.15); margin: 12px 0 30px 0;'/>",
    unsafe_allow_html=True,
)

# -----------------------------
# Load data
# -----------------------------
dash_dir = get_dash_dir()
ensure_files_exist(dash_dir)

core = load_core_table(dash_dir)
routes = load_routes_table(dash_dir)

# -----------------------------
# Lookups (airline labels)
# -----------------------------
air_lu = load_airlines_lookup()
# Save code->name for charts (donut legend)
air_lu["operating_airline"] = air_lu["operating_airline"].astype(str).str.strip()
air_lu["airline_name"] = air_lu["airline_name"].astype(str).str.strip()
st.session_state["CODE_TO_NAME"] = dict(zip(air_lu["operating_airline"], air_lu["airline_name"]))
_, airline_label, label_to_code = build_airline_mappers(air_lu)

# -----------------------------
# Filters + filtered frames
# -----------------------------
core_f, routes_f = render_filters(core, routes, airline_label, label_to_code)

# -----------------------------
# KPIs
# -----------------------------
render_kpis(routes_f)

st.markdown("---")

# -----------------------------
# Pie and Donut Charts
# -----------------------------
render_pies(routes_f)

st.markdown("---")

# -----------------------------
# Line Charts
# -----------------------------
render_delay_lines(routes_f)

st.markdown("---")

# -----------------------------
# Choropleth Maps
# -----------------------------
render_state_delay_maps(routes_f)

st.markdown("---")

# -----------------------------
# Vertical Bar Charts
# -----------------------------
render_airline_delay_bars(routes_f)

st.markdown("---")

# -----------------------------
# Month Table
# -----------------------------
render_monthly_summary(routes_f)

st.markdown("---")

# -----------------------------
# Airline Table
# -----------------------------
render_airline_scorecard(routes_f)

st.markdown("---")

# -----------------------------
# State Tables
# -----------------------------
render_state_scorecards(routes_f)
