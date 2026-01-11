import argparse
from pathlib import Path
import pandas as pd


def build_airline_lookup(clean_csv: Path, out_csv: Path, chunksize: int = 500_000) -> None:
    codes = set()

    for chunk in pd.read_csv(clean_csv, chunksize=chunksize, usecols=["operating_airline"], low_memory=False):
        codes.update(chunk["operating_airline"].dropna().astype(str).str.strip().unique().tolist())

    new_df = pd.DataFrame({"operating_airline": sorted(codes)})

    # If file exists, preserve airline_name values
    if out_csv.exists():
        old_df = pd.read_csv(out_csv)
        old_df["operating_airline"] = old_df["operating_airline"].astype(str).str.strip()

        if "airline_name" not in old_df.columns:
            old_df["airline_name"] = ""

        merged = new_df.merge(old_df[["operating_airline", "airline_name"]],
                              on="operating_airline", how="left")
        merged["airline_name"] = merged["airline_name"].fillna("")
        df = merged
    else:
        df = new_df.copy()
        df["airline_name"] = ""

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print("Wrote:", out_csv)


def build_airport_lookup(clean_csv: Path, out_csv: Path, chunksize: int = 500_000) -> None:
    cols = [
        "origin_airport", "origin_city", "origin_state",
        "destination_airport", "destination_city", "destination_state",
    ]

    rows = {}

    for chunk in pd.read_csv(clean_csv, chunksize=chunksize, usecols=cols, low_memory=False):
        o = chunk[["origin_airport", "origin_city", "origin_state"]].dropna()
        for a, c, s in o.itertuples(index=False, name=None):
            a = str(a).strip()
            rows[a] = (a, c, s)

        d = chunk[["destination_airport", "destination_city", "destination_state"]].dropna()
        for a, c, s in d.itertuples(index=False, name=None):
            a = str(a).strip()
            rows[a] = (a, c, s)

    df = pd.DataFrame(rows.values(), columns=["iata", "city", "state"])
    df = df.drop_duplicates(subset=["iata"]).sort_values("iata")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print("Wrote:", out_csv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", default="data/processed/flight_clean_data_2024.csv", help="Clean CSV path")
    ap.add_argument("--outdir", default="data/lookups", help="Output directory for lookups")
    ap.add_argument("--chunksize", type=int, default=500_000)
    args = ap.parse_args()

    clean_csv = Path(args.clean)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    build_airline_lookup(clean_csv, outdir / "airlines.csv", chunksize=args.chunksize)
    build_airport_lookup(clean_csv, outdir / "airports.csv", chunksize=args.chunksize)


if __name__ == "__main__":
    main()
