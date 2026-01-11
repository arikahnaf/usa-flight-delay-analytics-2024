from pathlib import Path
import pandas as pd

CODE_TO_NAME = {
    "9E": "Endeavor Air",
    "AA": "American Airlines",
    "AS": "Alaska Airlines",
    "B6": "JetBlue Airways",
    "DL": "Delta Air Lines",
    "F9": "Frontier Airlines",
    "G4": "Allegiant Air",
    "HA": "Hawaiian Airlines",
    "MQ": "Envoy Air",
    "NK": "Spirit Airlines",
    "OH": "PSA Airlines",
    "OO": "SkyWest Airlines",
    "UA": "United Airlines",
    "WN": "Southwest Airlines",
    "YX": "Republic Airways",
}

path = Path("data/lookups/airlines.csv")
df = pd.read_csv(path)

df["operating_airline"] = df["operating_airline"].astype(str).str.strip()
df["airline_name"] = df.get("airline_name", "").astype(str).str.strip()

# fill blanks from mapping
mask_blank = df["airline_name"].isin(["", "nan", "None"])
df.loc[mask_blank, "airline_name"] = df.loc[mask_blank, "operating_airline"].map(CODE_TO_NAME).fillna("")

missing = df[df["airline_name"].eq("")]["operating_airline"].tolist()
if missing:
    print("Still missing airline_name for:", missing)

df.to_csv(path, index=False)
print("Updated:", path)
