# Project Context — PM2.5 & Weather, Eugene OR

> This document gives an AI assistant (or any new collaborator) instant context about what this project is, where it stands, and what comes next. Update it as the project evolves.

---

## What This Project Is

A **Bachelor of Science thesis** for the **Department of Computer Science** at the **University of Oregon Clark Honors College**, planned defense **Spring 2026**.

**Research question:** Can measurable links be identified between PM2.5 concentrations — particularly from wildfire smoke — and short-term weather changes in the Eugene, Oregon area?

The project is positioned in a gap in the literature: aerosol–weather interactions are well-documented at regional/global scales, but local-scale detection using dense community sensor networks (PurpleAir) is understudied. The increasing frequency and intensity of western US wildfires makes this timely.

**Future vision (beyond the thesis):** A reusable analytical tool that can ingest PurpleAir + NOAA data from anywhere in the United States.

---

## Scientific Background

Wildfire smoke affects local weather through three primary mechanisms:
1. **Radiation effects** — smoke scatters/absorbs solar radiation, producing cooler days and relatively warmer nights
2. **Boundary layer suppression** — heavy aerosol loads cap the atmosphere, trapping pollutants near the ground in a self-reinforcing feedback loop
3. **Cloud condensation nuclei (CCN)** — smoke particles act as seeds for cloud droplets, producing more numerous but smaller droplets that can alter clouds and suppress precipitation

---

## Data Sources

| Source | Type | Status |
|--------|------|--------|
| **PurpleAir** (community sensors, Eugene area) | CSV / JSON, sub-hourly | **Not yet collected** — sensor IDs not yet identified |
| **LRAPA** (Lane Regional Air Protection Agency) professional sensors | Excel (.xlsx) | Downloaded: `data/raw/lrapa/LRAPAHourlyDataExport05052026-2.xlsx` |
| **NOAA / Iowa State Mesonet METAR** (KEUG station) | CSV | One file checked in: `data/raw/noaa/noaa_77S_EUG_080122_113022.csv` (Aug–Nov 2022) |

**Notes on data:**
- Eugene has unusually dense PurpleAir coverage due to LRAPA, University of Oregon, and individual owners
- PurpleAir sensors are consumer-grade and can read PM2.5 up to ~2x higher than regulatory equipment (moisture/particle detection differences); **LRAPA correction algorithms** will be applied
- Quality control will include: outdoor-only sensors, threshold screening, cross-sensor agreement checks, ML-assisted anomaly flagging
- Wind direction will be transformed into **sine and cosine components** (circular variable) for regression
- All timestamps standardized to a common time zone; analysis at **hourly resolution**
- Final analysis **time period not yet finalized**

---

## Statistical Approach

**Primary model: Generalized Additive Model (GAM)**

GAMs are chosen because:
- They capture **nonlinear relationships** between PM2.5 and meteorological variables
- They remain **interpretable** (unlike black-box ML models)
- They allow **visualization of marginal effects** for each predictor

Model will include:
- **Lagged predictor variables** (PM2.5 and weather from previous hours/days)
- **Smooth temporal trend terms** for seasonal/long-term patterns
- Diagnostic residual checks

**Meteorological variables:** temperature, relative humidity, wind speed, wind direction (as sin/cos), precipitation, atmospheric pressure

---

## Codebase Structure

```
PM2.5-weather/
├── data/
│   ├── raw/
│   │   ├── noaa/          ← NOAA METAR CSVs
│   │   └── purpleair/     ← PurpleAir exports (empty — not yet collected)
│   └── processed/         ← Merged analysis CSVs (gitignored, not yet generated)
├── notebooks/
│   ├── 01_data_exploration.ipynb   ← Scaffold (not yet run with real data)
│   ├── 02_data_cleaning.ipynb      ← Scaffold
│   └── 03_initial_analysis.ipynb   ← Scaffold
├── src/
│   ├── data_loader.py      ← PurpleAirLoader, NOAALoader
│   ├── preprocessing.py    ← DataCleaner, TimeAligner, DataMerger
│   └── visualization.py    ← Time series, correlation, distribution plots
├── requirements.txt
├── README.md
└── QUICKSTART.md
```

### Key `src/` modules

- **`data_loader.py`** — Loads PurpleAir (CSV/JSON) and NOAA (ISD / LCD / Iowa State METAR) into a common schema. Auto-detects format; parses timestamps to Pacific time.
- **`preprocessing.py`** — Cleans both datasets (sentinel values, bounds, deduplication), resamples to hourly, inner-joins on timestamp, adds calendar/rolling/lag features. Top-level `create_analysis_dataset()` runs the full pipeline.
- **`visualization.py`** — EDA plots: time series, dual-axis, correlation heatmaps, pairplots, seasonal boxplots, optional geographic map. Top-level `create_eda_report()` orchestrates a standard EDA run.

Notebooks are fully scaffolded with commented-out execution cells — they are ready to run once data is available.

---

## Project Timeline

| Phase | Quarter | Goals |
|-------|---------|-------|
| **Phase 1** | Winter 2026 | Refine question, review literature, confirm data sources, build data ingestion + cleaning pipeline |
| **Phase 2 & 3** | Spring 2026 | Statistical modeling (GAM), visualization, API/live data, scalability testing, **thesis defense** |

---

## Current Status

**Data collected — pipeline ready to run (May 2026).**

- **57 PurpleAir sensors** downloaded for **Aug 1 – Sep 30, 2022** (Cedar Creek Fire / smoke event)
  - Files live in `data/raw/purpleair/PurpleAir Download 5-5-2026/`
  - One CSV per sensor, named `{sensor_index} 2022-08-01 2022-09-30 60-Minute Average.csv`
  - Fields: `time_stamp`, `humidity_a`, `temperature_a`, `pressure_a`, `pm2.5_alt_a` (C=3.4), `pm2.5_atm_a`, `pm2.5_cf_1_a`, `pm2.5_cf_1_b`
- **NOAA data** for Aug 1 – Nov 30, 2022 already downloaded (`data/raw/noaa/noaa_77S_EUG_080122_113022.csv`)
- `LRAPALoader` added to `src/data_loader.py`:
  - Reads wide-format Excel, renames 7 station columns to short names
  - Averages Eugene-area stations (Amazon Park, Highway 99, Santa Clara, Springfield) → `pm2.5_lrapa_regulatory`
  - Timestamps localized to Pacific time
- `src/data_loader.py` updated to handle PurpleAir download tool format:
  - Recursive file discovery (subdirectories)
  - Strips `|3.4` pipe notation from column names
  - Extracts sensor ID from numeric filename prefix
  - Recognizes `pm2.5_cf_1_a`/`_b` column names
- `src/preprocessing.py` updated with:
  - `apply_lrapa_correction()` — `pm2.5_lrapa = 0.5 × CF_1_a - 0.66`, clipped to ≥ 0
  - `flag_ab_channel_disagreement()` — flags rows where A/B channels disagree (|diff| > 5 µg/m³ AND ratio < 70%)
  - `clean_purpleair_data()` now runs QC → LRAPA correction → range filter → deduplicate
- GAM modeling not yet started

---

## Analysis Time Period

**Aug 1 – Sep 30, 2022** — Cedar Creek Fire smoke event near Eugene, OR

- Pre-fire baseline: early August
- Smoke onset: mid-August
- Peak smoke: late August – mid September
- Clearing: late September

---

## Immediate Next Steps

1. **Run `01_data_exploration.ipynb`** to verify loading of all 57 sensors and NOAA data
2. **Run `02_data_cleaning.ipynb`** to produce cleaned merged dataset in `data/processed/`
3. **Run `03_initial_analysis.ipynb`** for EDA (correlations, time series, distributions)
4. **Implement GAM modeling** — not yet started in the codebase

---

## Key Open Decisions

- GAM library selection (likely `pygam`)
- Whether to include LRAPA professional sensor data as a third source for validation
- Final presentation format (Jupyter notebook + short paper)

---

## Deliverables

- Well-documented, reproducible **Python code and Jupyter notebooks**
- A **short paper** presenting findings and conclusions

---

## Tech Stack

Python 3, pandas, numpy, matplotlib, seaborn, plotly, scipy, statsmodels, scikit-learn, Jupyter

GAM library not yet selected (likely `pygam` or `statsmodels` GAM).

---

## Key References

- Zhao et al. (2017) — aerosol–cloud feedback loops increasing PM2.5 by up to 25.1%
- Lu et al. (2025) — wildfire particles larger on average → stronger CCN effect
- Burke et al. (2023) — wildfire contribution to PM2.5 trends in the USA
- Rosenfeld et al. (2008) — aerosols, flood/drought, precipitation suppression
- Stone et al. (2011) — radiative forcing of wildfire smoke
- Oregon DEQ (2025) — wildfire smoke trends in Oregon
