import pandas as pd
import streamlit as st
import plotly.express as px


MONTH_ORDER = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]


def _monthly_counts(routes_f: pd.DataFrame, count_col: str) -> pd.DataFrame:
    """
    Returns a df with columns: Month, Count (ordered by calendar month).
    """
    if routes_f is None or len(routes_f) == 0:
        return pd.DataFrame({"Month": [], "Count": []})

    if "month_name" not in routes_f.columns or count_col not in routes_f.columns:
        return pd.DataFrame({"Month": [], "Count": []})

    tmp = routes_f[["month_name", count_col]].copy()
    tmp["month_name"] = tmp["month_name"].astype(str).str.strip()
    tmp = tmp[tmp["month_name"].isin(MONTH_ORDER)]

    agg = (
        tmp.groupby("month_name", dropna=False)[count_col]
        .sum()
        .reset_index()
        .rename(columns={"month_name": "Month", count_col: "Count"})
    )

    # Ensure all present months appear in correct order
    present = [m for m in MONTH_ORDER if m in set(agg["Month"])]
    agg = agg.set_index("Month").reindex(present, fill_value=0).reset_index()

    # Nice ints for display
    agg["Count"] = pd.to_numeric(agg["Count"], errors="coerce").fillna(0).round(0).astype(int)
    return agg


def render_delay_lines(routes_f: pd.DataFrame) -> None:
    """
    Two line charts, each on its own row:
      1) Departure delayed flights by month  (dep_delayed_any)
      2) Arrival delayed flights by month    (arr_delayed_any)
    """
    CHART_HEIGHT = 320

    # Departure delays by month
    st.markdown("<div class='section-title'>Departure Delays by Month</div>", unsafe_allow_html=True)

    dep_df = _monthly_counts(routes_f, "dep_delayed_any")
    if dep_df.empty:
        st.info("Departure delay data not available for the current filters.")
    else:
        fig = px.line(
            dep_df,
            x="Month",
            y="Count",
            markers=True,
            template="plotly_dark",
            category_orders={"Month": dep_df["Month"].tolist()},
        )
        fig.update_traces(
            line=dict(color="#B8860B", width=3),
            marker=dict(size=7, color="#B8860B"),
            hovertemplate="Month = %{x}<br>Delayed Flights = %{y:,}<extra></extra>",
        )
        fig.update_layout(
            height=CHART_HEIGHT,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="",
            yaxis_title="Delayed Flights",
        )
        fig.update_yaxes(tickformat=",")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="line_dep_delayed_by_month")

    # Arrival delays by month
    st.markdown("<div class='section-title'>Arrival Delays by Month</div>", unsafe_allow_html=True)

    arr_df = _monthly_counts(routes_f, "arr_delayed_any")
    if arr_df.empty:
        st.info("Arrival delay data not available for the current filters.")
    else:
        fig = px.line(
            arr_df,
            x="Month",
            y="Count",
            markers=True,
            template="plotly_dark",
            category_orders={"Month": arr_df["Month"].tolist()},
        )
        fig.update_traces(
            line=dict(color="#9B2C2C", width=3),
            marker=dict(size=7, color="#9B2C2C"),
            hovertemplate="Month = %{x}<br>Delayed Flights = %{y:,}<extra></extra>",
        )
        fig.update_layout(
            height=CHART_HEIGHT,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="",
            yaxis_title="Delayed Flights",
        )
        fig.update_yaxes(tickformat=",")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="line_arr_delayed_by_month")
