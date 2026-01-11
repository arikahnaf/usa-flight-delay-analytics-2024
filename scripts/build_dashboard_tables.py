import argparse
from pathlib import Path
from dashboard_agg.pipeline import build_tables

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True)
    ap.add_argument("--outdir", default="data/processed/dashboard")
    ap.add_argument("--chunksize", type=int, default=500_000)
    ap.add_argument("--top_airports", type=int, default=150)
    args = ap.parse_args()

    build_tables(
        infile=Path(args.infile),
        outdir=Path(args.outdir),
        chunksize=args.chunksize,
        top_airports=args.top_airports,
    )

    print(f"Done. Wrote dashboard tables to: {args.outdir}")

if __name__ == "__main__":
    main()
