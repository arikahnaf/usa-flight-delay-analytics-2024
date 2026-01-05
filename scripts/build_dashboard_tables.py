import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional

US_STATE_TO_ABBR = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO",
    "Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL","Georgia":"GA",
    "Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY",
    "Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN",
    "Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH",
    "New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH",
    "Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",
    "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV",
    "Wisconsin":"WI","Wyoming":"WY"
}

METRIC_COLS = ["flights", "delayed_flights", "sum_arrival_delay_min", "sum_total_delay_min"]

def _ensure_columns(chunk: pd.DataFrame) -> pd.DataFrame:
    # Ensure required fields exist
    if "month" not in chunk.columns or "month_name" not in chunk.columns:
        if "flight_date" in chunk.columns:
            dt = pd.to_datetime(chunk["flight_date"], errors="coerce")
            chunk["month"] = dt.dt.month.astype("Int64")
            chunk["month_name"] = dt.dt.month_name()
        else:
            chunk["month"] = pd.NA
            chunk["month_name"] = pd.NA

    # State abbreviations (for map)
    if "origin_state_abbr" not in chunk.columns:
        if "origin_state" in chunk.columns:
            s = chunk["origin_state"].astype(str).str.strip()
            chunk["origin_state_abbr"] = s.map(US_STATE_TO_ABBR)
        else:
            chunk["origin_state_abbr"] = pd.NA

    # Fill missing engineered fields safely
    for col, default in [
        ("operating_airline", pd.NA),
        ("origin_airport", pd.NA),
        ("scheduled_departure_hour", pd.NA),
        ("primary_delay_cause", "No Delay"),
        ("is_delayed_15", False),
        ("arrival_delay_min", 0),
        ("total_delay_min", 0),
    ]:
        if col not in chunk.columns:
            chunk[col] = default

    # Ensure numeric types
    chunk["arrival_delay_min"] = pd.to_numeric(chunk["arrival_delay_min"], errors="coerce").fillna(0)
    chunk["total_delay_min"] = pd.to_numeric(chunk["total_delay_min"], errors="coerce").fillna(0)

    # Ensure boolean
    chunk["is_delayed_15"] = chunk["is_delayed_15"].fillna(False).astype(bool)

    return chunk

def _agg(chunk: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    # Metric basis
    tmp = chunk.copy()
    tmp["flights"] = 1
    tmp["delayed_flights"] = tmp["is_delayed_15"].astype(int)
    tmp["sum_arrival_delay_min"] = tmp["arrival_delay_min"]
    tmp["sum_total_delay_min"] = tmp["total_delay_min"]

    g = (
        tmp.groupby(keys, dropna=False)[METRIC_COLS]
        .sum()
        .reset_index()
    )
    return g

def _accumulate(acc: Optional[pd.DataFrame], g: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    g_idx = g.set_index(keys)[METRIC_COLS]
    if acc is None:
        return g_idx
    return acc.add(g_idx, fill_value=0)

def _finalize(acc_idx: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    out = acc_idx.reset_index()
    out["delay_rate"] = np.where(out["flights"] > 0, out["delayed_flights"] / out["flights"], 0.0)
    out["avg_arrival_delay_min"] = np.where(out["flights"] > 0, out["sum_arrival_delay_min"] / out["flights"], 0.0)
    out["avg_total_delay_min"] = np.where(out["flights"] > 0, out["sum_total_delay_min"] / out["flights"], 0.0)

    # Sort month properly if present
    if "month" in out.columns:
        out = out.sort_values(["month"], kind="stable")

    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True, help="Path to full cleaned CSV (data/processed/flight_clean_data_2024.csv)")
    ap.add_argument("--outdir", default="data/processed/dashboard", help="Output directory for aggregated tables")
    ap.add_argument("--chunksize", type=int, default=500_000)
    ap.add_argument("--top_airports", type=int, default=150, help="Keep only top N airports by total flights in airport table")
    args = ap.parse_args()

    infile = Path(args.infile)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Accumulators (MultiIndex dataframes of METRIC_COLS)
    acc_core = None   # month x airline x state
    acc_hour = None   # month x airline x state x hour
    acc_cause = None  # month x airline x state x cause
    acc_airport = None  # month x airline x state x airport

    # Overall KPI counters
    total_flights = 0
    total_delayed = 0
    sum_arr_delay = 0.0
    sum_total_delay = 0.0

    core_keys = ["month", "month_name", "origin_state_abbr", "operating_airline"]
    hour_keys = core_keys + ["scheduled_departure_hour"]
    cause_keys = core_keys + ["primary_delay_cause"]
    airport_keys = core_keys + ["origin_airport"]

    for chunk in pd.read_csv(infile, chunksize=args.chunksize, low_memory=False):
        chunk = _ensure_columns(chunk)

        # Update KPIs
        total_flights += len(chunk)
        total_delayed += int(chunk["is_delayed_15"].sum())
        sum_arr_delay += float(chunk["arrival_delay_min"].sum())
        sum_total_delay += float(chunk["total_delay_min"].sum())

        # Aggregate
        g_core = _agg(chunk, core_keys)
        g_hour = _agg(chunk, hour_keys)
        g_cause = _agg(chunk, cause_keys)
        g_airport = _agg(chunk, airport_keys)

        acc_core = _accumulate(acc_core, g_core, core_keys)
        acc_hour = _accumulate(acc_hour, g_hour, hour_keys)
        acc_cause = _accumulate(acc_cause, g_cause, cause_keys)
        acc_airport = _accumulate(acc_airport, g_airport, airport_keys)

    # Export KPI table
    kpi = pd.DataFrame([{
        "flights": total_flights,
        "delayed_flights": total_delayed,
        "delay_rate": (total_delayed / total_flights) if total_flights else 0.0,
        "avg_arrival_delay_min": (sum_arr_delay / total_flights) if total_flights else 0.0,
        "sum_arrival_delay_min": sum_arr_delay,
        "sum_total_delay_min": sum_total_delay
    }])
    kpi.to_csv(outdir / "kpi_overview.csv", index=False)

    # Export cubes
    core = _finalize(acc_core, core_keys)
    core.to_csv(outdir / "cube_core.csv", index=False)

    hour = _finalize(acc_hour, hour_keys)
    hour.to_csv(outdir / "cube_hour.csv", index=False)

    cause = _finalize(acc_cause, cause_keys)
    cause.to_csv(outdir / "cube_cause.csv", index=False)

    airport = _finalize(acc_airport, airport_keys)

    # Keep only top N airports by total flights (to keep file small for hosting)
    airport_totals = airport.groupby("origin_airport", dropna=False)["flights"].sum().sort_values(ascending=False)
    top_airports = set(airport_totals.head(args.top_airports).index.tolist())
    airport = airport[airport["origin_airport"].isin(top_airports)]
    airport.to_csv(outdir / "cube_airport_top.csv", index=False)

    print(f"Done. Wrote dashboard tables to: {outdir}")
    print("Files:")
    for f in ["kpi_overview.csv", "cube_core.csv", "cube_hour.csv", "cube_cause.csv", "cube_airport_top.csv"]:
        print(" -", f)

if __name__ == "__main__":
    main()
