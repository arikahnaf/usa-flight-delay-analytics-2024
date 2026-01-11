import pandas as pd
from typing import Callable, Dict, Tuple


def build_airline_mappers(
    air_lu: pd.DataFrame,
) -> Tuple[Dict[str, str], Callable[[str], str], Callable[[str], str]]:
    """
    Returns:
      code_to_name: dict[code -> airline_name]
      airline_label(code) -> "Airline Name" (falls back to code)
      label_to_code(label) -> "CODE" (via reverse lookup; falls back to label)
    """
    df = air_lu.copy()

    # Validate expected columns
    expected = {"operating_airline", "airline_name"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"airlines lookup missing columns: {sorted(missing)}")

    # Clean & normalize
    df["operating_airline"] = df["operating_airline"].astype(str).str.strip()
    df["airline_name"] = df["airline_name"].astype(str).str.strip()

    # Turn "nan"/"None" strings into empty
    df["airline_name"] = df["airline_name"].replace(
        {"nan": "", "None": "", "none": "", "NaN": ""}
    )

    # Drop rows with no code
    df = df[df["operating_airline"].ne("")]

    # Build maps (prefer non-empty names if duplicates exist)
    code_to_name: Dict[str, str] = {}
    for code, name in zip(df["operating_airline"], df["airline_name"]):
        code = (code or "").strip()
        name = (name or "").strip()
        if not code:
            continue
        # If we already have a name, don't overwrite with blank
        if code not in code_to_name or (not code_to_name[code] and name):
            code_to_name[code] = name

    # Reverse map: name -> code
    name_to_code: Dict[str, str] = {}
    for code, name in code_to_name.items():
        if name and name not in name_to_code:
            name_to_code[name] = code

    def airline_label(code: str) -> str:
        code = (code or "").strip()
        name = (code_to_name.get(code) or "").strip()
        return name if name else code

    def label_to_code(label: str) -> str:
        label = (label or "").strip()
        return name_to_code.get(label, label)

    return code_to_name, airline_label, label_to_code
