# USA Flight Delay Analytics (2024) ✈️

### [🔗 View the Live Interactive Dashboard](https://public.tableau.com/views/TorontoTrafficCollisions_17591353959220/TrafficCollisionsDashboard?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

## Overview

This project analyzes U.S. flight delay data from **2024** to uncover trends in airline performance, airport congestion, and delay causes. The final output is an interactive **Tableau dashboard** designed for clear business and operational insights.

---

## Key Questions Answered

---

## Tools Used

- Tableau
- Python (Pandas, NumPy)
- Jupyter Notebook
- Kaggle Dataset

---

## ETL Pipeline Workflow

This project is built around a repeatable ETL (Extract, Transform, Load) pipeline to produce a Tableau-ready dataset from the raw Kaggle CSV.

### Extract

- The raw dataset is sourced from Kaggle (**Flight Data 2024**) and stored locally in:
  - `data/raw/flight_data_2024.csv` (full dataset)
  - `data/raw/flight_data_2024_sample.csv` (small sample used for development/testing)

### Transform

- The `notebooks/data_processing.ipynb` notebook documents the data preparation logic and validates the pipeline using the sample dataset. Key transformation steps include:

  - Renaming DOT/BTS-style column headers to business-friendly names
  - Dropping unnecessary operational fields to improve Tableau performance
  - Correcting data types (e.g., parsing `flight_date` and cleaning numeric delay fields)
  - Engineering dashboard-ready features such as:
    - `is_delayed_15` (standard delay flag: arrival delay > 15 minutes)
    - `delay_bucket` (binned delay severity)
    - `primary_delay_cause` (dominant delay reason for interactive breakdowns)
    - calendar fields (month name, day-of-week, week-of-year)
    - scheduled departure hour for time-of-day analysis

- The full dataset (~1.2GB) is processed using the chunk-based script:
  - `scripts/process_flight_data_in_chunks.py`  
    This avoids loading the entire file into memory and reliably generates the final output.

### Load

- The final cleaned dataset is saved as:
  - `data/processed/flight_clean_data_2024.csv`

This processed file serves as the direct data source for the Tableau dashboard.

---

## Project Structure

```
usa-flight-delay-analytics-2024/
├── data/
│   ├── processed/
│       ├── flight_clean_data_2024_sample.csv   # Processed sample output
│       └── flight_clean_data_2024.csv          # Tableau-ready output (not included due to size)
│   ├── raw/
│       ├── flight_data_2024_sample.csv         # Raw sample dataset
│       └── flight_data_2024.csv                # Full raw dataset (not included due to size)
├── notebooks/                                  # Data preparation workflow using Jupyter Notebook
├── scripts/                                    # Python script for processing full dataset in chunks
├── tableau/                                    # Workbook containing the dashboard
└── requirements.txt                            # Dependencies
```

---

## 📚 Kaggle Dataset

https://www.kaggle.com/datasets/hrishitpatil/flight-data-2024s

⚠️ The dataset is **not included** in this repository due to size constraints.
