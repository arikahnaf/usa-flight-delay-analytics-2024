import pandas as pd
import streamlit as st
import plotly.express as px

STATE_TO_ABBR = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO",
    "Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL","Georgia":"GA",
    "Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY",
    "Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN",
    "Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH",
    "New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH",
    "Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",
    "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA",
    "West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY",
}

ABBR_TO_STATE = {abbr: state for state, abbr in STATE_TO_ABBR.items()}

def _to_state_abbr(s: pd.Series) -> pd.Series:
    """
    Accepts either state abbreviations (CA) or full names (California).
    Returns uppercase abbreviations, unknowns become NA.
    """
    x = s.astype(str).str.strip()
    x = x.replace({"nan": "", "None": "", "none": ""})

    is_abbr = x.str.len().eq(2)
    out = pd.Series(pd.NA, index=x.index, dtype="string")
    out[is_abbr] = x[is_abbr].str.upper()

    out[~is_abbr] = x[~is_abbr].map(STATE_TO_ABBR)
    return out

def _agg_state(routes_f: pd.DataFrame, state_col: str) -> pd.DataFrame:
    """
    Aggregate to state level for choropleths.
    Returns columns: StateAbbr, Flights, DepDelayed, ArrDelayed, DepShare, ArrShare
    """
    needed = {state_col, "flights", "dep_delayed_any", "arr_delayed_any"}
    if routes_f is None or len(routes_f) == 0 or not needed.issubset(set(routes_f.columns)):
        return pd.DataFrame()

    tmp = routes_f[[state_col, "flights", "dep_delayed_any", "arr_delayed_any"]].copy()
    tmp[state_col] = tmp[state_col].astype(str).str.strip()
    tmp = tmp[tmp[state_col].notna() & (tmp[state_col] != "")]
    tmp = tmp[~tmp[state_col].str.lower().isin({"nan", "none"})]

    tmp["StateAbbr"] = _to_state_abbr(tmp[state_col])
    tmp = tmp[tmp["StateAbbr"].notna()]

    agg = (
        tmp.groupby("StateAbbr", dropna=False)[["flights", "dep_delayed_any", "arr_delayed_any"]]
        .sum()
        .reset_index()
        .rename(columns={
            "flights": "Flights",
            "dep_delayed_any": "DepDelayed",
            "arr_delayed_any": "ArrDelayed",
        })
    )

    agg["StateName"] = agg["StateAbbr"].map(ABBR_TO_STATE).fillna(agg["StateAbbr"])

    dep_total = float(agg["DepDelayed"].sum()) if len(agg) else 0.0
    arr_total = float(agg["ArrDelayed"].sum()) if len(agg) else 0.0

    agg["DepShare"] = (agg["DepDelayed"] / dep_total * 100.0) if dep_total else 0.0
    agg["ArrShare"] = (agg["ArrDelayed"] / arr_total * 100.0) if arr_total else 0.0

    agg["DepRate"] = (agg["DepDelayed"] / agg["Flights"] * 100.0).where(agg["Flights"] > 0, 0.0)
    agg["ArrRate"] = (agg["ArrDelayed"] / agg["Flights"] * 100.0).where(agg["Flights"] > 0, 0.0)

    # Clean ints
    for c in ["Flights", "DepDelayed", "ArrDelayed"]:
        agg[c] = pd.to_numeric(agg[c], errors="coerce").fillna(0).round(0).astype(int)

    return agg

def _choropleth(
    df: pd.DataFrame,
    value_col: str,
    share_col: str,
    title: str,
    key: str,
    color_scale: str,
    height: int = 380,
) -> None:
    if df.empty or df[value_col].sum() == 0:
        st.info("No data for the current filters.")
        return

    custom_cols = ["StateName", "Flights", share_col]
    if value_col == "DepDelayed":
        custom_cols.append("DepRate")
    else:
        custom_cols.append("ArrRate")

    fig = px.choropleth(
        df,
        locations="StateAbbr",
        locationmode="USA-states",
        color=value_col,
        scope="usa",
        template="plotly_dark",
        color_continuous_scale=color_scale,
    )

    fig.update_traces(
        customdata=df[custom_cols].values,
        hovertemplate=(
            "State = %{customdata[0]}<br>"
            f"Delayed Flights = %{{z:,}}<br>"
            f"% of Total = %{{customdata[2]:.1f}}%<br>"
            "Flights = %{customdata[1]:,}<br>"
            + ("Delay Rate = %{customdata[3]:.1f}%<br>" if custom_cols[-1] in ("DepRate","ArrRate") else "")
            + "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=30, b=0),
        coloraxis_colorbar=dict(title="", ticksuffix="", tickformat=","),
        title=dict(text=title, x=0.0, xanchor="left", font=dict(color="#EFEFEF", size=18)),
    )

    fig.update_geos(
        bgcolor="rgba(66,66,66,0)",
        showcountries=False,
        showlakes=False,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)

def render_state_delay_maps(routes_f: pd.DataFrame) -> None:
    """
    4 USA choropleth maps:
      Row 1: Origin state (Departure delayed count, Arrival delayed count)
      Row 2: Destination state (Departure delayed count, Arrival delayed count)

    Hover includes % of total delayed flights across states (within current filters).
    """
    st.markdown("<div class='section-title'>Delayed Flights by State</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    if routes_f is None or len(routes_f) == 0:
        st.info("No data for the current filters.")
        return

    required = {"flights", "dep_delayed_any", "arr_delayed_any", "origin_state", "destination_state"}
    if not required.issubset(set(routes_f.columns)):
        st.info("State delay map data not available (missing required columns).")
        return

    origin_agg = _agg_state(routes_f, "origin_state")
    dest_agg = _agg_state(routes_f, "destination_state")

    # Row 1: origin
    r1c1, r1c2 = st.columns(2, gap="large")
    with r1c1:
        _choropleth(
            origin_agg,
            value_col="DepDelayed",
            share_col="DepShare",
            title="Origin: Departure Delays",
            key="map_origin_dep",
            color_scale="YlOrBr",
        )
    with r1c2:
        _choropleth(
            origin_agg,
            value_col="ArrDelayed",
            share_col="ArrShare",
            title="Origin: Arrival Delays",
            key="map_origin_arr",
            color_scale="Reds", 
        )

    # Row 2: destination
    r2c1, r2c2 = st.columns(2, gap="large")
    with r2c1:
        _choropleth(
            dest_agg,
            value_col="DepDelayed",
            share_col="DepShare",
            title="Destination: Departure Delayss",
            key="map_dest_dep",
            color_scale="YlOrBr",
        )
    with r2c2:
        _choropleth(
            dest_agg,
            value_col="ArrDelayed",
            share_col="ArrShare",
            title="Destination: Arrival Delays",
            key="map_dest_arr",
            color_scale="Reds",
        )
