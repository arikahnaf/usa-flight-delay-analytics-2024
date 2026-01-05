import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def hhmm_to_hour(series: pd.Series) -> pd.Series:
    s = series.apply(lambda x: np.nan if pd.isna(x) else str(int(float(x))).zfill(4))
    return s.apply(lambda x: np.nan if pd.isna(x) else int(x[:2])).astype("Int64")

def process_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    # Rename (same as notebook)
    rename_map = {
        "fl_date": "flight_date",
        "op_unique_carrier": "operating_airline",
        "op_carrier_fl_num": "operating_flight_number",
        "origin": "origin_airport",
        "origin_city_name": "origin_city",
        "origin_state_nm": "origin_state",
        "dest": "destination_airport",
        "dest_city_name": "destination_city",
        "dest_state_nm": "destination_state",
        "crs_dep_time": "scheduled_departure_hhmm",
        "crs_arr_time": "scheduled_arrival_hhmm",
        "dep_delay": "departure_delay_raw_min",
        "arr_delay": "arrival_delay_raw_min",
        "carrier_delay": "carrier_delay_min",
        "weather_delay": "weather_delay_min",
        "nas_delay": "nas_delay_min",
        "security_delay": "security_delay_min",
        "late_aircraft_delay": "late_aircraft_delay_min",
        "cancelled": "is_cancelled",
        "diverted": "is_diverted",
    }
    chunk = chunk.rename(columns={k: v for k, v in rename_map.items() if k in chunk.columns})

    # Drop unnecessary columns (optimize for Tableau)
    drop_cols = [
        "operating_flight_number",
        "dep_time","arr_time","wheels_off","wheels_on","taxi_out","taxi_in",
        "air_time","distance","crs_elapsed_time","actual_elapsed_time",
        "cancellation_code",
        "year","month","day_of_month","day_of_week"
    ]
    chunk = chunk.drop(columns=[c for c in drop_cols if c in chunk.columns])

    # Types
    chunk["flight_date"] = pd.to_datetime(chunk["flight_date"], errors="coerce")

    delay_cols = [
        "departure_delay_raw_min","arrival_delay_raw_min",
        "carrier_delay_min","weather_delay_min","nas_delay_min","security_delay_min","late_aircraft_delay_min"
    ]
    for c in delay_cols:
        if c in chunk.columns:
            chunk[c] = pd.to_numeric(chunk[c], errors="coerce").fillna(0)

    # Drop missing key dims
    core = ["flight_date","operating_airline","origin_airport","origin_city","origin_state"]
    chunk = chunk.dropna(subset=[c for c in core if c in chunk.columns])

    # Calendar fields
    chunk["year"] = chunk["flight_date"].dt.year.astype("Int64")
    chunk["month"] = chunk["flight_date"].dt.month.astype("Int64")
    chunk["month_name"] = chunk["flight_date"].dt.month_name()
    chunk["day_of_month"] = chunk["flight_date"].dt.day.astype("Int64")
    chunk["day_of_week_name"] = chunk["flight_date"].dt.day_name()
    chunk["week_of_year"] = chunk["flight_date"].dt.isocalendar().week.astype("Int64")

    # Scheduled departure hour
    if "scheduled_departure_hhmm" in chunk.columns:
        chunk["scheduled_departure_hour"] = hhmm_to_hour(chunk["scheduled_departure_hhmm"])

    # Engineered delay metrics
    cause_cols = ["carrier_delay_min","weather_delay_min","nas_delay_min","security_delay_min","late_aircraft_delay_min"]
    chunk["is_operated"] = True
    if "is_cancelled" in chunk.columns and "is_diverted" in chunk.columns:
        chunk["is_operated"] = (chunk["is_cancelled"] == 0) & (chunk["is_diverted"] == 0)

    chunk["arrival_delay_min"] = chunk["arrival_delay_raw_min"].clip(lower=0)
    chunk["departure_delay_min"] = chunk["departure_delay_raw_min"].clip(lower=0)
    chunk["is_delayed_15"] = chunk["is_operated"] & (chunk["arrival_delay_raw_min"] > 15)

    chunk["total_delay_min"] = chunk[cause_cols].sum(axis=1)

    bins = [-1, 15, 30, 60, 120, 10_000]
    labels = ["On time (≤15)", "16–30", "31–60", "61–120", "120+"]
    chunk["delay_bucket"] = pd.cut(chunk["arrival_delay_raw_min"].clip(lower=-1), bins=bins, labels=labels)

    cause_label = {
        "carrier_delay_min": "Carrier",
        "weather_delay_min": "Weather",
        "nas_delay_min": "NAS",
        "security_delay_min": "Security",
        "late_aircraft_delay_min": "Late Aircraft",
    }
    max_cause = chunk[cause_cols].idxmax(axis=1)
    chunk["primary_delay_cause"] = np.where(chunk["total_delay_min"] > 0, max_cause.map(cause_label), "No Delay")

    chunk["country"] = "United States"
    return chunk

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="Path to raw CSV (1.2GB)")
    ap.add_argument("--out", required=True, help="Path to output cleaned CSV")
    ap.add_argument("--chunksize", type=int, default=500_000)
    args = ap.parse_args()

    raw_path = Path(args.raw)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    first = True
    for chunk in pd.read_csv(raw_path, chunksize=args.chunksize):
        cleaned = process_chunk(chunk)
        cleaned.to_csv(out_path, mode="w" if first else "a", header=first, index=False)
        first = False

    print(f"Done. Wrote Tableau-ready dataset to: {out_path}")

if __name__ == "__main__":
    main()
