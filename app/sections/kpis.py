import streamlit as st
import pandas as pd
from ui_components import kpi_card

def render_kpis(routes_f: pd.DataFrame):
    total_flights = int(routes_f["flights"].sum()) if len(routes_f) else 0

    def pct_from_count(n: int) -> str:
        return f"{(n / total_flights * 100):.1f}%" if total_flights else "0.0%"

    def count_and_pct(n: int) -> str:
        return f"{n:,} ({pct_from_count(n)})"

    on_time = int(routes_f["on_time_flights"].sum()) if "on_time_flights" in routes_f.columns else 0
    cancelled = int(routes_f["cancelled_flights"].sum()) if "cancelled_flights" in routes_f.columns else 0

    sum_dep = routes_f["sum_departure_delay_min"].sum() if "sum_departure_delay_min" in routes_f.columns else 0.0
    sum_arr = routes_f["sum_arrival_delay_min"].sum() if "sum_arrival_delay_min" in routes_f.columns else 0.0

    avg_dep_min = (sum_dep / total_flights) if total_flights else 0.0
    avg_arr_min = (sum_arr / total_flights) if total_flights else 0.0

    dep_any = int(routes_f["dep_delayed_any"].sum()) if "dep_delayed_any" in routes_f.columns else 0
    dep_15  = int(routes_f["dep_delayed_15"].sum()) if "dep_delayed_15" in routes_f.columns else 0
    dep_30  = int(routes_f["dep_delayed_30"].sum()) if "dep_delayed_30" in routes_f.columns else 0
    dep_60  = int(routes_f["dep_delayed_60"].sum()) if "dep_delayed_60" in routes_f.columns else 0
    dep_120 = int(routes_f["dep_delayed_120"].sum()) if "dep_delayed_120" in routes_f.columns else 0

    arr_any = int(routes_f["arr_delayed_any"].sum()) if "arr_delayed_any" in routes_f.columns else 0
    arr_15  = int(routes_f["arr_delayed_15"].sum()) if "arr_delayed_15" in routes_f.columns else 0
    arr_30  = int(routes_f["arr_delayed_30"].sum()) if "arr_delayed_30" in routes_f.columns else 0
    arr_60  = int(routes_f["arr_delayed_60"].sum()) if "arr_delayed_60" in routes_f.columns else 0
    arr_120 = int(routes_f["arr_delayed_120"].sum()) if "arr_delayed_120" in routes_f.columns else 0

    # Row 1
    r1 = st.columns(5)
    with r1[0]:
        kpi_card("Total Flights", f"{total_flights:,}")
    with r1[1]:
        kpi_card("On-Time Flights %", pct_from_count(on_time))
    with r1[2]:
        kpi_card("Cancelled Flights %", pct_from_count(cancelled))
    with r1[3]:
        kpi_card("Average Departure Delay", f"{avg_dep_min:.1f} min")
    with r1[4]:
        kpi_card("Average Arrival Delay", f"{avg_arr_min:.1f} min")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Row 2
    r2 = st.columns(5)
    with r2[0]:
        kpi_card("Departure Delays", count_and_pct(dep_any))
    with r2[1]:
        kpi_card("Departure Delays (15+ min)", count_and_pct(dep_15))
    with r2[2]:
        kpi_card("Departure Delays (30+ min)", count_and_pct(dep_30))
    with r2[3]:
        kpi_card("Departure Delays (1+ hour)", count_and_pct(dep_60))
    with r2[4]:
        kpi_card("Departure Delays (2+ hour)", count_and_pct(dep_120))

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Row 3
    r3 = st.columns(5)
    with r3[0]:
        kpi_card("Arrival Delays", count_and_pct(arr_any))
    with r3[1]:
        kpi_card("Arrival Delays (15+ min)", count_and_pct(arr_15))
    with r3[2]:
        kpi_card("Arrival Delays (30+ min)", count_and_pct(arr_30))
    with r3[3]:
        kpi_card("Arrival Delays (1+ hour)", count_and_pct(arr_60))
    with r3[4]:
        kpi_card("Arrival Delays (2+ hour)", count_and_pct(arr_120))
