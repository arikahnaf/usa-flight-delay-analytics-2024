import streamlit as st
import pandas as pd
from typing import Callable, Tuple


def render_filters(
    core: pd.DataFrame,
    routes: pd.DataFrame,
    airline_label: Callable[[str], str],   # should return airline NAME (no code)
    label_to_code: Callable[[str], str],   # not used anymore, kept for compatibility
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    st.sidebar.header("Filters")

    # Column availability
    HAS_MONTH = "month_name" in core.columns
    HAS_AIRLINE = "operating_airline" in core.columns
    HAS_ORIGIN_STATE = "origin_state" in routes.columns
    HAS_DEST_STATE = "destination_state" in routes.columns
    HAS_CAUSE = "delay_cause" in routes.columns  

    # Options (sorted nicely)
    MONTH_ORDER = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    months_all = []
    if HAS_MONTH:
        present = set(core["month_name"].dropna().astype(str).tolist())
        months_all = [m for m in MONTH_ORDER if m in present]

    airlines_all_codes = []
    if HAS_AIRLINE:
        airlines_all_codes = (
            core["operating_airline"].dropna().astype(str).str.strip().unique().tolist()
        )
        airlines_all_codes = sorted(airlines_all_codes, key=lambda c: airline_label(c).lower())

    origin_states_all = (
        sorted(routes["origin_state"].dropna().astype(str).unique().tolist())
        if HAS_ORIGIN_STATE else []
    )
    dest_states_all = (
        sorted(routes["destination_state"].dropna().astype(str).unique().tolist())
        if HAS_DEST_STATE else []
    )

    # Delay causes (pin common buckets first)
    causes_all = []
    if HAS_CAUSE:
        raw = routes["delay_cause"].dropna().astype(str).str.strip().unique().tolist()
        raw = [c for c in raw if c and c.lower() not in {"nan", "none"}]
        raw = sorted(raw, key=lambda x: x.lower())

        pinned = ["On Time", "Unknown", "Cancelled"]
        pinned_present = [p for p in pinned if p in raw]
        for p in pinned_present:
            raw.remove(p)

        causes_all = pinned_present + raw

    # Init session state defaults
    if HAS_MONTH and "f_months" not in st.session_state:
        st.session_state["f_months"] = months_all

    if HAS_AIRLINE and "f_airlines" not in st.session_state:
        st.session_state["f_airlines"] = airlines_all_codes

    if HAS_ORIGIN_STATE and "f_origin_states" not in st.session_state:
        st.session_state["f_origin_states"] = origin_states_all

    if HAS_DEST_STATE and "f_dest_states" not in st.session_state:
        st.session_state["f_dest_states"] = dest_states_all

    if HAS_CAUSE and "f_causes" not in st.session_state:
        st.session_state["f_causes"] = causes_all

    # Reset
    def _reset():
        if HAS_MONTH:
            st.session_state["f_months"] = months_all
        if HAS_AIRLINE:
            st.session_state["f_airlines"] = airlines_all_codes
        if HAS_ORIGIN_STATE:
            st.session_state["f_origin_states"] = origin_states_all
        if HAS_DEST_STATE:
            st.session_state["f_dest_states"] = dest_states_all
        if HAS_CAUSE:
            st.session_state["f_causes"] = causes_all

    st.sidebar.button("Reset filters", use_container_width=True, on_click=_reset)

    # Widgets 
    if HAS_MONTH:
        st.sidebar.multiselect(
            "Month",
            options=months_all,
            key="f_months",
            placeholder="Choose month",
        )
    else:
        st.sidebar.info("Month filter not available (month_name not found).")

    if HAS_AIRLINE:
        st.sidebar.multiselect(
            "Airline",
            options=airlines_all_codes,         
            format_func=airline_label,           
            key="f_airlines",
            placeholder="Choose airline",
        )
    else:
        st.sidebar.info("Airline filter not available (operating_airline not found).")

    if HAS_ORIGIN_STATE:
        st.sidebar.multiselect(
            "Origin State",
            options=origin_states_all,
            key="f_origin_states",
            placeholder="Choose origin state",
        )
    else:
        st.sidebar.info("Origin State filter not available (origin_state not found).")

    if HAS_DEST_STATE:
        st.sidebar.multiselect(
            "Destination State",
            options=dest_states_all,
            key="f_dest_states",
            placeholder="Choose destination state",
        )
    else:
        st.sidebar.info("Destination State filter not available (destination_state not found).")

    if HAS_CAUSE:
        st.sidebar.multiselect(
            "Delay Cause",
            options=causes_all,
            key="f_causes",
            placeholder="Choose delay cause",
        )
    else:
        st.sidebar.info("Delay Cause filter not available (delay_cause not found).")

    # Validate
    if HAS_MONTH and not st.session_state["f_months"]:
        st.warning("Choose a month (or click Reset filters).")
        st.stop()

    if HAS_AIRLINE and not st.session_state["f_airlines"]:
        st.warning("Choose an airline (or click Reset filters).")
        st.stop()

    if HAS_ORIGIN_STATE and not st.session_state["f_origin_states"]:
        st.warning("Choose an origin state (or click Reset filters).")
        st.stop()

    if HAS_DEST_STATE and not st.session_state["f_dest_states"]:
        st.warning("Choose a destination state (or click Reset filters).")
        st.stop()

    if HAS_CAUSE and not st.session_state["f_causes"]:
        st.warning("Choose a delay cause (or click Reset filters).")
        st.stop()

    # Apply filters
    core_f = core.copy()
    if HAS_MONTH:
        core_f = core_f[core_f["month_name"].isin(st.session_state["f_months"])]
    if HAS_AIRLINE:
        core_f = core_f[core_f["operating_airline"].isin(st.session_state["f_airlines"])]

    routes_f = routes.copy()
    if HAS_MONTH:
        routes_f = routes_f[routes_f["month_name"].isin(st.session_state["f_months"])]
    if HAS_AIRLINE:
        routes_f = routes_f[routes_f["operating_airline"].isin(st.session_state["f_airlines"])]
    if HAS_ORIGIN_STATE:
        routes_f = routes_f[routes_f["origin_state"].isin(st.session_state["f_origin_states"])]
    if HAS_DEST_STATE:
        routes_f = routes_f[routes_f["destination_state"].isin(st.session_state["f_dest_states"])]
    if HAS_CAUSE:
        routes_f = routes_f[routes_f["delay_cause"].isin(st.session_state["f_causes"])]

    return core_f, routes_f
