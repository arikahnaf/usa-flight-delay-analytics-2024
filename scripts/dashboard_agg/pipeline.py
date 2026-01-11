from pathlib import Path
import pandas as pd
from typing import Dict, Optional

from .transforms import ensure_columns
from .aggregations import agg_metrics, accumulate, finalize

def build_tables(
    infile: Path,
    outdir: Path,
    chunksize: int = 500_000,
    top_airports: int = 150,
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    acc_core = None
    acc_hour = None
    acc_cause = None
    acc_routes = None
    acc_airport = None

    core_keys = ["month", "month_name", "origin_state_abbr", "operating_airline"]
    hour_keys = core_keys + ["scheduled_departure_hour"]
    cause_keys = core_keys + ["delay_cause"]
    airport_keys = core_keys + ["origin_airport"]
    route_keys = ["month","month_name","operating_airline","origin_state","destination_state","delay_cause"]

    for chunk in pd.read_csv(infile, chunksize=chunksize, low_memory=False):
        chunk = ensure_columns(chunk)

        g_core = agg_metrics(chunk, core_keys)
        g_hour = agg_metrics(chunk, hour_keys)
        g_cause = agg_metrics(chunk, cause_keys)
        g_routes = agg_metrics(chunk, route_keys)
        g_airport = agg_metrics(chunk, airport_keys)

        acc_core = accumulate(acc_core, g_core, core_keys)
        acc_hour = accumulate(acc_hour, g_hour, hour_keys)
        acc_cause = accumulate(acc_cause, g_cause, cause_keys)
        acc_routes = accumulate(acc_routes, g_routes, route_keys)
        acc_airport = accumulate(acc_airport, g_airport, airport_keys)

    finalize(acc_core).to_csv(outdir / "cube_core.csv", index=False)
    finalize(acc_hour).to_csv(outdir / "cube_hour.csv", index=False)
    finalize(acc_cause).to_csv(outdir / "cube_cause.csv", index=False)
    finalize(acc_routes).to_csv(outdir / "cube_routes.csv", index=False)

    # airport cube
    airport = finalize(acc_airport)
    airport_totals = airport.groupby("origin_airport", dropna=False)["flights"].sum().sort_values(ascending=False)
    keep = set(airport_totals.head(top_airports).index.tolist())
    airport = airport[airport["origin_airport"].isin(keep)]
    airport.to_csv(outdir / "cube_airport_top.csv", index=False)
