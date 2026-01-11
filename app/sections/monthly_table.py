import pandas as pd
import streamlit as st

MONTH_ORDER = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]

def _safe_div(num: float, den: float) -> float:
    return (num / den) if den else 0.0

def _pct(num: float, den: float) -> float:
    return _safe_div(num, den) * 100.0

def _build_monthly_summary(routes_f: pd.DataFrame) -> pd.DataFrame:
    needed = {
        "month_name",
        "flights",
        "on_time_flights",
        "cancelled_flights",
        "dep_delayed_any",
        "arr_delayed_any",
    }
    if routes_f is None or len(routes_f) == 0 or not needed.issubset(set(routes_f.columns)):
        return pd.DataFrame()

    has_sum_dep = "sum_departure_delay_min" in routes_f.columns
    has_sum_arr = "sum_arrival_delay_min" in routes_f.columns

    cols = [
        "month_name",
        "flights",
        "on_time_flights",
        "cancelled_flights",
        "dep_delayed_any",
        "arr_delayed_any",
    ]
    if has_sum_dep:
        cols.append("sum_departure_delay_min")
    if has_sum_arr:
        cols.append("sum_arrival_delay_min")

    tmp = routes_f[cols].copy()
    tmp["month_name"] = tmp["month_name"].astype(str).str.strip()
    tmp = tmp[tmp["month_name"].isin(MONTH_ORDER)]

    agg = tmp.groupby("month_name", dropna=False).sum(numeric_only=True).reset_index()
    agg = agg.rename(columns={"month_name": "Month"})

    # enforce calendar order and keep only months present
    present = [m for m in MONTH_ORDER if m in set(agg["Month"])]
    agg = agg.set_index("Month").reindex(present, fill_value=0).reset_index()

    # percentages
    agg["On-time %"] = agg.apply(lambda r: _pct(r["on_time_flights"], r["flights"]), axis=1)
    agg["Dep Delayed %"] = agg.apply(lambda r: _pct(r["dep_delayed_any"], r["flights"]), axis=1)
    agg["Arr Delayed %"] = agg.apply(lambda r: _pct(r["arr_delayed_any"], r["flights"]), axis=1)
    agg["Cancelled %"] = agg.apply(lambda r: _pct(r["cancelled_flights"], r["flights"]), axis=1)

    # averages (if available)
    if has_sum_dep:
        agg["Avg Dep Delay (min)"] = agg.apply(
            lambda r: _safe_div(r["sum_departure_delay_min"], r["flights"]), axis=1
        )
    else:
        agg["Avg Dep Delay (min)"] = 0.0

    if has_sum_arr:
        agg["Avg Arr Delay (min)"] = agg.apply(
            lambda r: _safe_div(r["sum_arrival_delay_min"], r["flights"]), axis=1
        )
    else:
        agg["Avg Arr Delay (min)"] = 0.0

    out = agg[[
        "Month",
        "flights",
        "On-time %",
        "Dep Delayed %",
        "Arr Delayed %",
        "Cancelled %",
        "Avg Dep Delay (min)",
        "Avg Arr Delay (min)",
    ]].rename(columns={"flights": "Flights"})

    out["Flights"] = pd.to_numeric(out["Flights"], errors="coerce").fillna(0).round(0).astype(int)
    return out

def render_monthly_summary(routes_f: pd.DataFrame) -> None:
    """
    Monthly Summary table (bordered) for the current filters.
    """
    st.markdown("<div class='section-title'>Monthly Summary</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    df = _build_monthly_summary(routes_f)
    if df.empty:
        st.info("Monthly summary not available for the current filters.")
        return

    # Bordered container
    try:
        box = st.container(border=True)
        with box:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=380,
                column_config={
                    "Flights": st.column_config.NumberColumn(format="%d"),
                    "On-time %": st.column_config.NumberColumn(format="%.1f"),
                    "Dep Delayed %": st.column_config.NumberColumn(format="%.1f"),
                    "Arr Delayed %": st.column_config.NumberColumn(format="%.1f"),
                    "Cancelled %": st.column_config.NumberColumn(format="%.1f"),
                    "Avg Dep Delay (min)": st.column_config.NumberColumn(format="%.1f"),
                    "Avg Arr Delay (min)": st.column_config.NumberColumn(format="%.1f"),
                },
            )
    except TypeError:
        # Fallback border
        st.markdown(
            "<div style='border:1px solid rgba(255,255,255,0.14); border-radius:12px; padding:10px;'>",
            unsafe_allow_html=True,
        )
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=380,
            column_config={
                "Flights": st.column_config.NumberColumn(format="%d"),
                "On-time %": st.column_config.NumberColumn(format="%.1f"),
                "Dep Delayed %": st.column_config.NumberColumn(format="%.1f"),
                "Arr Delayed %": st.column_config.NumberColumn(format="%.1f"),
                "Cancelled %": st.column_config.NumberColumn(format="%.1f"),
                "Avg Dep Delay (min)": st.column_config.NumberColumn(format="%.1f"),
                "Avg Arr Delay (min)": st.column_config.NumberColumn(format="%.1f"),
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)
