import numpy as np
import pandas as pd
from typing import Optional
from .constants import METRIC_COLS

def agg_metrics(chunk: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    tmp = chunk.copy()
    tmp["flights"] = 1

    tmp["cancelled_flights"] = (tmp["is_cancelled"] == 1).astype(int)
    tmp["on_time_flights"] = ((tmp["arrival_delay_min"] == 0) & (tmp["is_cancelled"] == 0)).astype(int)

    tmp["dep_delayed_any"] = (tmp["departure_delay_min"] > 0).astype(int)
    tmp["dep_delayed_15"]  = (tmp["departure_delay_min"] >= 15).astype(int)
    tmp["dep_delayed_30"]  = (tmp["departure_delay_min"] >= 30).astype(int)
    tmp["dep_delayed_60"]  = (tmp["departure_delay_min"] >= 60).astype(int)
    tmp["dep_delayed_120"] = (tmp["departure_delay_min"] >= 120).astype(int)

    tmp["arr_delayed_any"] = (tmp["arrival_delay_min"] > 0).astype(int)
    tmp["arr_delayed_15"]  = (tmp["arrival_delay_min"] >= 15).astype(int)
    tmp["arr_delayed_30"]  = (tmp["arrival_delay_min"] >= 30).astype(int)
    tmp["arr_delayed_60"]  = (tmp["arrival_delay_min"] >= 60).astype(int)
    tmp["arr_delayed_120"] = (tmp["arrival_delay_min"] >= 120).astype(int)

    tmp["sum_departure_delay_min"] = tmp["departure_delay_min"]
    tmp["sum_arrival_delay_min"] = tmp["arrival_delay_min"]
    tmp["sum_total_delay_min"] = tmp["total_delay_min"]

    return tmp.groupby(keys, dropna=False)[METRIC_COLS].sum().reset_index()

def accumulate(acc: Optional[pd.DataFrame], g: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    g_idx = g.set_index(keys)[METRIC_COLS]
    if acc is None:
        return g_idx
    return acc.add(g_idx, fill_value=0)

def finalize(acc_idx: pd.DataFrame) -> pd.DataFrame:
    out = acc_idx.reset_index()

    out["arr_delay_rate_any"] = np.where(out["flights"] > 0, out["arr_delayed_any"] / out["flights"], 0.0)
    out["dep_delay_rate_any"] = np.where(out["flights"] > 0, out["dep_delayed_any"] / out["flights"], 0.0)
    out["cancel_rate"] = np.where(out["flights"] > 0, out["cancelled_flights"] / out["flights"], 0.0)

    out["avg_arrival_delay_min"] = np.where(out["flights"] > 0, out["sum_arrival_delay_min"] / out["flights"], 0.0)
    out["avg_departure_delay_min"] = np.where(out["flights"] > 0, out["sum_departure_delay_min"] / out["flights"], 0.0)
    out["avg_total_delay_min"] = np.where(out["flights"] > 0, out["sum_total_delay_min"] / out["flights"], 0.0)

    if "month" in out.columns:
        out = out.sort_values(["month"], kind="stable")

    return out
