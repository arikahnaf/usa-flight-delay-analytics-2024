import pandas as pd
import streamlit as st
import plotly.express as px

DEP_COLOR = "#B8860B"  # dark goldenrod
ARR_COLOR = "#9B2C2C"  # dark red


def _airline_name_only(code: str) -> str:
    """
    Map airline code -> airline NAME only (no "(AA)" code).
    Falls back to the code if name is missing.
    """
    code = (code or "").strip().upper()
    code_to_name = st.session_state.get("CODE_TO_NAME", {})
    name = (code_to_name.get(code) or "").strip()
    return name if name else code


def _agg_airline(routes_f: pd.DataFrame, col: str, top_n: int = 12) -> pd.DataFrame:
    """
    Aggregate delayed counts by airline code.
    Returns columns: AirlineCode, AirlineName, Count
    """
    if routes_f is None or len(routes_f) == 0:
        return pd.DataFrame(columns=["AirlineCode", "AirlineName", "Count"])

    needed = {"operating_airline", col}
    if not needed.issubset(set(routes_f.columns)):
        return pd.DataFrame(columns=["AirlineCode", "AirlineName", "Count"])

    tmp = routes_f[["operating_airline", col]].copy()
    tmp["operating_airline"] = tmp["operating_airline"].astype(str).str.strip()
    tmp = tmp[tmp["operating_airline"].notna() & (tmp["operating_airline"] != "")]
    tmp = tmp[~tmp["operating_airline"].str.lower().isin({"nan", "none"})]

    agg = (
        tmp.groupby("operating_airline", dropna=False)[col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"operating_airline": "AirlineCode", col: "Count"})
    )

    agg["Count"] = pd.to_numeric(agg["Count"], errors="coerce").fillna(0).round(0).astype(int)

    if len(agg) > top_n:
        top = agg.head(top_n).copy()
        other_sum = int(agg["Count"].iloc[top_n:].sum())
        if other_sum > 0:
            top = pd.concat(
                [top, pd.DataFrame([{"AirlineCode": "OTHER", "Count": other_sum}])],
                ignore_index=True,
            )
        agg = top

    agg["AirlineName"] = agg["AirlineCode"].apply(_airline_name_only)

    # Ensure the "Other" label is clean
    agg.loc[agg["AirlineCode"].str.upper().eq("OTHER"), "AirlineName"] = "Other"

    return agg


def _bar_chart(df: pd.DataFrame, title: str, color_hex: str, key: str, height: int = 380) -> None:
    if df.empty or int(df["Count"].sum()) == 0:
        st.info("No data for the current filters.")
        return

    total = float(df["Count"].sum())
    df = df.copy()
    df["Share"] = df["Count"].apply(lambda x: (x / total * 100.0) if total else 0.0)

    fig = px.bar(
        df,
        x="AirlineName",
        y="Count",
        template="plotly_dark",
    )

    fig.update_traces(
        marker=dict(color=color_hex, line=dict(color="rgba(255,255,255,0.10)", width=1)),
        hovertemplate=(
            "Airline = %{x}<br>"
            "Delayed Flights = %{y:,}<br>"
            "% of Total = %{customdata[0]:.1f}%"
            "<extra></extra>"
        ),
        customdata=df[["Share"]].values,
    )

    fig.update_layout(
        height=height,
        title=dict(text=title, x=0.0, xanchor="left", font=dict(color="#EFEFEF", size=18)),
        margin=dict(l=10, r=10, t=50, b=70),
        xaxis_title="",
        yaxis_title="Delayed Flights",
        xaxis=dict(tickangle=-35, automargin=True),
        yaxis=dict(tickformat=","),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_layout(
        shapes=[
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                line=dict(color="rgba(255,255,255,0.14)", width=1),
                fillcolor="rgba(0,0,0,0)",
            )
        ]
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def render_airline_delay_bars(routes_f: pd.DataFrame) -> None:
    """
    Two bar charts side-by-side:
      - Departure delayed flights by airline
      - Arrival delayed flights by airline
    """
    st.markdown("<div class='section-title'>Delayed Flights by Airline</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")

    with c1:
        dep_df = _agg_airline(routes_f, "dep_delayed_any", top_n=12)
        _bar_chart(dep_df, "Departure Delays", DEP_COLOR, "bar_dep_delayed_airline")

    with c2:
        arr_df = _agg_airline(routes_f, "arr_delayed_any", top_n=12)
        _bar_chart(arr_df, "Arrival Delays", ARR_COLOR, "bar_arr_delayed_airline")
