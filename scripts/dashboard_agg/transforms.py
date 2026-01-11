import numpy as np
import pandas as pd
from .constants import US_STATE_TO_ABBR


def ensure_columns(chunk: pd.DataFrame) -> pd.DataFrame:
    # Month fields
    if "month" not in chunk.columns or "month_name" not in chunk.columns:
        if "flight_date" in chunk.columns:
            dt = pd.to_datetime(chunk["flight_date"], errors="coerce")
            chunk["month"] = dt.dt.month.astype("Int64")
            chunk["month_name"] = dt.dt.month_name()
        else:
            chunk["month"] = pd.NA
            chunk["month_name"] = pd.NA

    # Origin state abbreviation (for map)
    if "origin_state_abbr" not in chunk.columns:
        if "origin_state" in chunk.columns:
            s = chunk["origin_state"].astype(str).str.strip()
            chunk["origin_state_abbr"] = s.map(US_STATE_TO_ABBR)
        else:
            chunk["origin_state_abbr"] = pd.NA

    # Required fields (safe defaults)
    defaults = [
        ("operating_airline", pd.NA),
        ("origin_state", pd.NA),
        ("destination_state", pd.NA),
        ("origin_airport", pd.NA),
        ("destination_airport", pd.NA),
        ("scheduled_departure_hour", pd.NA),
        ("primary_delay_cause", pd.NA),  # keep raw as NA
        ("is_delayed_15", False),
        ("is_cancelled", 0),
        ("arrival_delay_min", 0),
        ("departure_delay_min", 0),
        ("total_delay_min", 0),
    ]
    for col, default in defaults:
        if col not in chunk.columns:
            chunk[col] = default

    # Types
    chunk["arrival_delay_min"] = pd.to_numeric(chunk["arrival_delay_min"], errors="coerce").fillna(0)
    chunk["departure_delay_min"] = pd.to_numeric(chunk["departure_delay_min"], errors="coerce").fillna(0)
    chunk["total_delay_min"] = pd.to_numeric(chunk["total_delay_min"], errors="coerce").fillna(0)

    chunk["is_cancelled"] = pd.to_numeric(chunk["is_cancelled"], errors="coerce").fillna(0).astype(int)
    chunk["is_delayed_15"] = chunk["is_delayed_15"].fillna(False).astype(bool)

    # Clean strings (states)
    chunk["origin_state"] = chunk["origin_state"].astype("string").str.strip()
    chunk["destination_state"] = chunk["destination_state"].astype("string").str.strip()

    chunk["origin_state"] = chunk["origin_state"].replace(["nan", "None", "none", ""], pd.NA)
    chunk["destination_state"] = chunk["destination_state"].replace(["nan", "None", "none", ""], pd.NA)

    # Raw cause text normalized
    cause_raw = chunk["primary_delay_cause"].fillna("").astype(str).str.strip()

    # Turn weird placeholders into blank
    bad_tokens = {"", "nan", "none", "No Delay", "NO DELAY", "None"}
    cause_clean = cause_raw.mask(cause_raw.isin(bad_tokens), "")

    is_cancelled = chunk["is_cancelled"] == 1

    # Define On Time strictly
    is_on_time = (
        (~is_cancelled)
        & (chunk["departure_delay_min"] <= 0)
        & (chunk["arrival_delay_min"] <= 0)
    )

    # Define "Unknown" as: not on-time, and missing/blank cause
    # (includes delayed flights where cause isn't provided.)
    is_unknown = (~is_on_time) & (cause_clean == "")

    # Build final bucket column
    delay_cause = cause_clean.copy()
    delay_cause = np.where(is_on_time, "On Time", delay_cause)
    delay_cause = np.where(is_unknown, "Unknown", delay_cause)
    delay_cause = np.where(is_cancelled, "Cancelled", delay_cause)

    chunk["delay_cause"] = pd.Series(delay_cause, index=chunk.index).astype("string")

    return chunk
