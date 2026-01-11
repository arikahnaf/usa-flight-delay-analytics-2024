import pandas as pd
import streamlit as st

ABBR_TO_STATE = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado",
    "CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia",
    "HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky",
    "LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota",
    "MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire",
    "NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio",
    "OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota",
    "TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington",
    "WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
}

STATE_TO_ABBR = {v: k for k, v in ABBR_TO_STATE.items()}

def _safe_div(num: float, den: float) -> float:
    return (num / den) if den else 0.0

def _pct(num: float, den: float) -> float:
    return _safe_div(num, den) * 100.0

def _to_state_abbr(s: pd.Series) -> pd.Series:
    """
    Accepts either abbreviations (CA) or full names (California).
    Returns uppercase abbreviations, unknowns become NA.
    """
    x = s.astype(str).str.strip()
    x = x.replace({"nan": "", "None": "", "none": ""})

    is_abbr = x.str.len().eq(2)
    out = pd.Series(pd.NA, index=x.index, dtype="string")

    out[is_abbr] = x[is_abbr].str.upper()
    out[~is_abbr] = x[~is_abbr].map(STATE_TO_ABBR)

    return out

def _build_state_scorecard(routes_f: pd.DataFrame, state_col: str) -> pd.DataFrame:
    needed = {
        state_col,
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
        state_col,
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
    tmp[state_col] = tmp[state_col].astype(str).str.strip()
    tmp = tmp[tmp[state_col].notna() & (tmp[state_col] != "")]
    tmp = tmp[~tmp[state_col].str.lower().isin({"nan", "none"})]

    tmp["StateAbbr"] = _to_state_abbr(tmp[state_col])
    tmp = tmp[tmp["StateAbbr"].notna()]

    agg = tmp.groupby("StateAbbr", dropna=False).sum(numeric_only=True).reset_index()

    # State full name
    agg["State"] = agg["StateAbbr"].map(ABBR_TO_STATE).fillna(agg["StateAbbr"])

    # Percent columns (based on Flights for that state)
    agg["On-time %"] = agg.apply(lambda r: _pct(r["on_time_flights"], r["flights"]), axis=1)
    agg["Dep Delayed %"] = agg.apply(lambda r: _pct(r["dep_delayed_any"], r["flights"]), axis=1)
    agg["Arr Delayed %"] = agg.apply(lambda r: _pct(r["arr_delayed_any"], r["flights"]), axis=1)
    agg["Cancelled %"] = agg.apply(lambda r: _pct(r["cancelled_flights"], r["flights"]), axis=1)

    # Avg delay minutes if sums exist
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

    out = agg[
        [
            "State",
            "flights",
            "On-time %",
            "Dep Delayed %",
            "Arr Delayed %",
            "Cancelled %",
            "Avg Dep Delay (min)",
            "Avg Arr Delay (min)",
        ]
    ].rename(columns={"flights": "Flights"}).copy()

    out["Flights"] = pd.to_numeric(out["Flights"], errors="coerce").fillna(0).round(0).astype(int)

    # Sort: biggest states first
    out = out.sort_values("Flights", ascending=False).reset_index(drop=True)
    return out

def _render_bordered_table(title: str, df: pd.DataFrame, key: str, height: int = 420) -> None:
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    if df.empty:
        st.info("No data for the current filters.")
        return

    try:
        box = st.container(border=True)
        with box:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=height,
                column_config={
                    "State": st.column_config.TextColumn(),
                    "Flights": st.column_config.NumberColumn(format="%d"),
                    "On-time %": st.column_config.NumberColumn(format="%.1f"),
                    "Dep Delayed %": st.column_config.NumberColumn(format="%.1f"),
                    "Arr Delayed %": st.column_config.NumberColumn(format="%.1f"),
                    "Cancelled %": st.column_config.NumberColumn(format="%.1f"),
                    "Avg Dep Delay (min)": st.column_config.NumberColumn(format="%.1f"),
                    "Avg Arr Delay (min)": st.column_config.NumberColumn(format="%.1f"),
                },
                key=key,
            )
    except TypeError:
        st.markdown(
            "<div style='border:1px solid rgba(255,255,255,0.14); border-radius:12px; padding:10px;'>",
            unsafe_allow_html=True,
        )
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=height,
            column_config={
                "State": st.column_config.TextColumn(),
                "Flights": st.column_config.NumberColumn(format="%d"),
                "On-time %": st.column_config.NumberColumn(format="%.1f"),
                "Dep Delayed %": st.column_config.NumberColumn(format="%.1f"),
                "Arr Delayed %": st.column_config.NumberColumn(format="%.1f"),
                "Cancelled %": st.column_config.NumberColumn(format="%.1f"),
                "Avg Dep Delay (min)": st.column_config.NumberColumn(format="%.1f"),
                "Avg Arr Delay (min)": st.column_config.NumberColumn(format="%.1f"),
            },
            key=key,
        )
        st.markdown("</div>", unsafe_allow_html=True)

def render_state_scorecards(routes_f: pd.DataFrame) -> None:
    """
    Two tables underneath one another:
      - Origin State Scorecard (origin_state)
      - Destination State Scorecard (destination_state)
    """
    origin_df = _build_state_scorecard(routes_f, "origin_state")
    _render_bordered_table("Origin State Scorecard", origin_df, key="tbl_origin_state", height=420)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    dest_df = _build_state_scorecard(routes_f, "destination_state")
    _render_bordered_table("Destination State Scorecard", dest_df, key="tbl_dest_state", height=420)
