import streamlit as st

def kpi_card(label: str, value: str):
    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 14px;
            padding: 18px 18px;
            background: rgba(255,255,255,0.03);
            ">
            <div style="font-size:14px; opacity:0.75; margin-bottom:6px;">{label}</div>
            <div style="font-size:34px; font-weight:700; line-height:1;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
