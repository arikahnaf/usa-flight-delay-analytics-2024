from pathlib import Path
import pandas as pd
import streamlit as st

# Dashboard cube files required for the app to run
REQUIRED_DASH_FILES = ["cube_core.csv", "cube_routes.csv"]

# Lookup files
REQUIRED_LOOKUP_FILES = ["airlines.csv"]


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_dash_dir() -> Path:
    return get_repo_root() / "data" / "processed" / "dashboard"


def get_lookups_dir() -> Path:
    return get_repo_root() / "data" / "lookups"


def ensure_files_exist(dash_dir: Path) -> None:
    missing_dash = [f for f in REQUIRED_DASH_FILES if not (dash_dir / f).exists()]
    missing_lookup = [f for f in REQUIRED_LOOKUP_FILES if not (get_lookups_dir() / f).exists()]

    if missing_dash or missing_lookup:
        st.error("Missing required data files for the dashboard.")

        if missing_dash:
            st.write("Missing dashboard files:", missing_dash)
            st.code(
                "python scripts/build_dashboard_tables.py "
                "--infile data/processed/flight_clean_data_2024.csv "
                "--outdir data/processed/dashboard",
                language="bash",
            )

        if missing_lookup:
            st.write("Missing lookup files:", missing_lookup)
            st.code(
                "Make sure these exist in your repo: data/lookups/",
                language="text",
            )

        st.stop()


@st.cache_data
def load_airlines_lookup() -> pd.DataFrame:
    path = get_lookups_dir() / "airlines.csv"
    df = pd.read_csv(path)

    if "operating_airline" in df.columns:
        df["operating_airline"] = df["operating_airline"].astype(str).str.strip()
    if "airline_name" in df.columns:
        df["airline_name"] = df["airline_name"].astype(str).str.strip()

    return df


@st.cache_data
def load_core_table(dash_dir: Path) -> pd.DataFrame:
    return pd.read_csv(dash_dir / "cube_core.csv")


@st.cache_data
def load_routes_table(dash_dir: Path) -> pd.DataFrame:
    return pd.read_csv(dash_dir / "cube_routes.csv")
