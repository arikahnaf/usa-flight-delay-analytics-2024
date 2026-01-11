import pandas as pd
import streamlit as st
import plotly.express as px
import hashlib


def render_pies(routes_f: pd.DataFrame) -> None:
    """
    3 charts side-by-side with ONLY thin vertical separators between them.
    Pie 1: Flight Status (On-time / Delayed / Cancelled)
    Pie 2: Delay Cause (excludes On Time / No Delay)
    Donut: Flights by Airline (Top N + Other) with dark-vivid palette
    """
    if routes_f is None or len(routes_f) == 0:
        st.info("No data for the current filters.")
        return

    CHART_HEIGHT = 360
    SEP_HEIGHT = 410

    total_flights = int(routes_f["flights"].sum()) if "flights" in routes_f.columns else 0
    on_time = int(routes_f["on_time_flights"].sum()) if "on_time_flights" in routes_f.columns else 0
    cancelled = int(routes_f["cancelled_flights"].sum()) if "cancelled_flights" in routes_f.columns else 0
    delayed = max(0, total_flights - on_time - cancelled)

    c1, sep1, c2, sep2, c3 = st.columns([1, 0.03, 1, 0.03, 1], gap="small")

    def _vline():
        st.markdown(
            f"<div style='width:1px;height:{SEP_HEIGHT}px;background:rgba(255,255,255,0.12);margin:0 auto;'></div>",
            unsafe_allow_html=True,
        )

    # Flight Status
    with c1:
        st.markdown("<div class='section-title'>Flight Status</div>", unsafe_allow_html=True)

        if total_flights == 0:
            st.info("No data for the current filters.")
        else:
            df = pd.DataFrame(
                {"Status": ["On-time", "Delayed", "Cancelled"], "Flights": [on_time, delayed, cancelled]}
            )

            fig = px.pie(df, names="Status", values="Flights", hole=0, template="plotly_dark")

            status_order = ["On-time", "Delayed", "Cancelled"]
            status_colors = {
                "On-time": "#1E7F4C",      # dark green
                "Delayed": "#B8860B",      # dark goldenrod
                "Cancelled": "#9B2C2C",    # dark red
            }

            fig.update_traces(
                sort=False,
                marker=dict(colors=[status_colors[s] for s in status_order]),
                textposition="auto",
                texttemplate="<b>%{label}</b><br>%{value:,}<br>%{percent:.1%}",
                textfont=dict(color="white"),
                hovertemplate=(
                    "Status = %{label}<br>"
                    "Flights = %{value:,}<br>"
                    "Share = %{percent:.1%}"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                height=CHART_HEIGHT,
                showlegend=True,
                legend_title_text="",
                legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
                uniformtext_minsize=10,
                uniformtext_mode="hide",
                margin=dict(l=0, r=0, t=30, b=45),
            )

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="pie_flight_status")

    with sep1:
        _vline()

    # Delay Cause (exclude On Time / No Delay)
    with c2:
        st.markdown("<div class='section-title'>Delay Cause</div>", unsafe_allow_html=True)

        cause_col = "delay_cause" if "delay_cause" in routes_f.columns else (
            "primary_delay_cause" if "primary_delay_cause" in routes_f.columns else None
        )

        if not cause_col:
            st.info("Delay cause data not available.")
        else:
            tmp = routes_f[[cause_col, "flights"]].copy()
            tmp[cause_col] = tmp[cause_col].astype(str).str.strip()
            tmp = tmp[tmp[cause_col].notna() & (tmp[cause_col] != "")]
            tmp = tmp[~tmp[cause_col].str.lower().isin({"nan", "none"})]

            on_time_labels = {"on time", "no delay", "on-time", "ontime"}
            tmp = tmp[~tmp[cause_col].str.lower().isin(on_time_labels)]

            if len(tmp) == 0 or int(tmp["flights"].sum()) == 0:
                st.info("No delay-cause breakdown for the current filters.")
            else:
                agg = (
                    tmp.groupby(cause_col, dropna=False)["flights"]
                    .sum()
                    .sort_values(ascending=False)
                    .reset_index()
                    .rename(columns={cause_col: "Cause", "flights": "Flights"})
                )

                TOP_N = 7
                if len(agg) > TOP_N:
                    top = agg.head(TOP_N).copy()
                    other_sum = int(agg["Flights"].iloc[TOP_N:].sum())
                    if other_sum > 0:
                        top = pd.concat([top, pd.DataFrame([{"Cause": "Other", "Flights": other_sum}])],
                                        ignore_index=True)
                    agg = top

                cause_colors = {
                    "Cancelled": "#9B2C2C",
                    "Unknown": "#3B3B3B",
                    "Weather": "#B8860B",
                    "Security": "#8e7cc3",
                    "NAS": "#5B6D92",
                    "Carrier": "#556B2F",
                    "Late Aircraft": "#7A4E2D",
                    "Other": "#4A4A4A",
                }
                fallback_palette = [
                    "#5B6D92", "#556B2F", "#7A4E2D", "#6B4F1D",
                    "#4A4A4A", "#3F5E5A", "#6A5D7B", "#5E4B4B",
                ]

                labels = agg["Cause"].tolist()
                colors = []
                fb_i = 0
                for lab in labels:
                    if lab in cause_colors:
                        colors.append(cause_colors[lab])
                    else:
                        colors.append(fallback_palette[fb_i % len(fallback_palette)])
                        fb_i += 1

                fig2 = px.pie(agg, names="Cause", values="Flights", hole=0, template="plotly_dark")

                fig2.update_traces(
                    sort=False,
                    marker=dict(colors=colors),
                    textposition="inside",
                    texttemplate="<b>%{value:,}</b><br>%{percent:.1%}",
                    textfont=dict(color="white"),
                    hovertemplate=(
                        "Cause = %{label}<br>"
                        "Flights = %{value:,}<br>"
                        "Share = %{percent:.1%}"
                        "<extra></extra>"
                    ),
                )

                fig2.update_layout(
                    height=CHART_HEIGHT,
                    showlegend=True,
                    legend_title_text="",
                    legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
                    uniformtext_minsize=10,
                    uniformtext_mode="hide",
                    margin=dict(l=0, r=0, t=30, b=45),
                )

                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False}, key="pie_delay_cause")

    with sep2:
        _vline()

    # Flights by Airline
    with c3:
        st.markdown("<div class='section-title'>Flights by Airline</div>", unsafe_allow_html=True)

        if "operating_airline" not in routes_f.columns or "flights" not in routes_f.columns:
            st.info("Airline data not available.")
        elif total_flights == 0:
            st.info("No data for the current filters.")
        else:
            tmp = routes_f[["operating_airline", "flights"]].copy()
            tmp["operating_airline"] = tmp["operating_airline"].astype(str).str.strip()
            tmp = tmp[tmp["operating_airline"].notna() & (tmp["operating_airline"] != "")]
            tmp = tmp[~tmp["operating_airline"].str.lower().isin({"nan", "none"})]

            agg = (
                tmp.groupby("operating_airline", dropna=False)["flights"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
                .rename(columns={"operating_airline": "Airline", "flights": "Flights"})
            )

            if len(agg) == 0 or int(agg["Flights"].sum()) == 0:
                st.info("No airline breakdown for the current filters.")
            else:
                TOP_N = 8
                if len(agg) > TOP_N:
                    top = agg.head(TOP_N).copy()
                    other_sum = int(agg["Flights"].iloc[TOP_N:].sum())
                    if other_sum > 0:
                        top = pd.concat([top, pd.DataFrame([{"Airline": "Other", "Flights": other_sum}])],
                                        ignore_index=True)
                    agg = top

                code_to_name = st.session_state.get("CODE_TO_NAME", {})

                def _airline_name(code: str) -> str:
                    name = (code_to_name.get(code) or "").strip()
                    return name if name else code

                agg["AirlineName"] = agg["Airline"].apply(_airline_name)

                dark_vivid_palette = [
                    "#2E7D32",  # deep green
                    "#C62828",  # deep red
                    "#6A1B9A",  # deep purple
                    "#1565C0",  # deep blue
                    "#EF6C00",  # deep orange
                    "#00838F",  # deep teal
                    "#AD1457",  # deep magenta
                    "#283593",  # deep indigo
                    "#4E342E",  # deep brown
                ]

                def color_for_airline_code(code: str) -> str:
                    code = (code or "").strip().upper()
                    if code == "OTHER":
                        return "#3B3B3B"
                    h = hashlib.md5(code.encode("utf-8")).hexdigest()
                    idx = int(h[:8], 16) % len(dark_vivid_palette)
                    return dark_vivid_palette[idx]

                # Use CODE for hashing so colors remain stable across filters
                agg["Color"] = agg["Airline"].apply(color_for_airline_code)
                colors = agg["Color"].tolist()

                fig3 = px.pie(
                    agg,
                    names="AirlineName",
                    values="Flights",
                    hole=0.55,
                    template="plotly_dark",
                )

                fig3.update_traces(
                    sort=False,
                    marker=dict(
                        colors=colors,
                        line=dict(color="rgba(255,255,255,0.10)", width=1),
                    ),
                    textposition="inside",
                    texttemplate="%{percent:.1%}",  # only percent
                    textfont=dict(color="white"),
                    hovertemplate=(
                        "Airline = %{label}<br>"
                        "Flights = %{value:,}<br>"
                        "Share = %{percent:.1%}"
                        "<extra></extra>"
                    ),
                )

                fig3.update_layout(
                    height=CHART_HEIGHT,
                    showlegend=True,
                    legend_title_text="",
                    legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
                    uniformtext_minsize=10,
                    uniformtext_mode="hide",
                    margin=dict(l=0, r=0, t=30, b=45),
                )

                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False}, key="donut_airlines")

