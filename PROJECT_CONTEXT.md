# Project Context — PM2.5 & Weather, Eugene OR

> This document gives an AI assistant (or any new collaborator) instant context about what this project is, where it stands, and what comes next. Update it as the project evolves.

---

## What This Project Is

A **Bachelor of Science thesis** for the **Department of Computer Science** at the **University of Oregon Clark Honors College**, planned defense **Spring 2026**.

**Research question:** Can measurable links be identified between PM2.5 concentrations — particularly from wildfire smoke — and short-term **weather changes** in the Eugene, Oregon area?

**Causal direction:** PM2.5 → weather (not weather → PM2.5). We are testing whether smoke aerosols are associated with subsequent meteorological changes, consistent with known physical mechanisms (radiation, boundary layer, CCN). This is observational — not a causal proof.

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
| **PurpleAir** (community sensors, Eugene area) | CSV, 60-min average | **Downloaded for both events** (see below) |
| **LRAPA** (Lane Regional Air Protection Agency) | Excel (.xlsx) | Downloaded for **both 2020 and 2022** |
| **NOAA / Iowa State Mesonet METAR** (KEUG = Eugene Airport, 77S = Creswell) | CSV | Downloaded for **both events** |

### Two fire events — both now in `analysis_data.csv`

| Event | Date Range | PurpleAir Sensors | Max PM2.5 | Notes |
|-------|-----------|-------------------|-----------|-------|
| **Holiday Farm Fire 2020** | Aug 1 – Oct 15, 2020 | 22 sensors (16 full-window) | ~502 µg/m³ | Record-breaking; AQI 457 on Sep 13 |
| **Cedar Creek Fire 2022** | Aug 1 – Sep 30, 2022 | 57 sensors | ~125 µg/m³ | Moderate smoke event |

**Combined dataset:** 3,240 hourly rows with an `event` column labeling each row.

### File locations

```
data/raw/purpleair/
  PurpleAir Download 5-5-2026/    ← 2022 sensors (57 files)
  PurpleAir Download 5-17-2026/   ← 2020 sensors (22 files, merged with cf_1_a)
  download_list.csv               ← sensor IDs for 2022 download
  download_list_2020.csv          ← sensor IDs for 2020 download
  eugene_sensors.csv              ← full sensor metadata from API

data/raw/noaa/
  noaa_77S_EUG_080120_101520.csv  ← Aug–Oct 2020 (EUG + 77S stations)
  noaa_77S_EUG_080122_113022.csv  ← Aug–Nov 2022 (EUG + 77S stations)

data/raw/lrapa/
  LRAPAHourlyDataExport05052026-2.xlsx  ← 2022 regulatory data
  LRAPAHourlyDataExport05172026-2.xlsx  ← 2020 regulatory data
```

**Important note on 2020 PurpleAir files:** Older download tool exports used `pm2.5_cf_1` (no `_a` suffix) instead of `pm2.5_cf_1_a`. The 2020 files were manually merged with a second download that added the `pm2.5_cf_1_a` column. The preprocessing pipeline also has a per-row coalesce fallback as a safety net.

**Only use NOAA station `EUG`** (Eugene Airport) for analysis — filter out `77S` (Creswell) in the pipeline.

---

## Statistical Approach

**Direction: PM2.5 (lagged) → weather outcomes**

We use **lagged PM2.5** (e.g. `pm2.5_lrapa_lag_6h`) as the exposure variable so it strictly precedes the weather outcome being measured.

**Models used:**

| Notebook | Model | Outcomes | Exposure |
|----------|-------|----------|----------|
| **04** | `pygam` LinearGAM | temperature_f, humidity, wind_speed_mph, pressure_hpa | lagged PM2.5 + hour + dayofyear controls |
| **05** | sklearn RidgeCV + TimeSeriesSplit CV | humidity, dewpoint_depression_f, visibility_km | lagged PM2.5; nested M0 vs M1 comparison |

**Key modeling decisions:**
- Temporal 80/20 train/test split (not random) to avoid data leakage
- `TimeSeriesSplit` CV in notebook 05 for stable out-of-sample estimates
- Nested model comparison (M0 = controls only vs M1 = controls + PM2.5 lag) to isolate PM2.5's contribution
- Both pooled (all data) and **per-event** models to check consistency across fire events

**Controls used:** `hour`, `dayofyear` (absorb diurnal and seasonal patterns)

**Meteorological variables:** temperature, relative humidity, dewpoint depression (T−Td), wind speed, wind direction (as sin/cos), precipitation, atmospheric pressure, visibility

---

## Current Pipeline Status

**All notebooks runnable as of May 17, 2026.**

### Notebook execution order
1. `02_data_cleaning.ipynb` — must run first; produces `data/processed/analysis_data.csv`
2. `01_data_exploration.ipynb` — raw data inspection (optional, run separately)
3. `03_initial_analysis.ipynb` — EDA with side-by-side event comparisons
4. `04_gam_modeling.ipynb` — GAM: lagged PM2.5 → weather (pooled + per-event)
5. `05_moisture_ccn_hypothesis.ipynb` — moisture/CCN focus with CV (pooled + per-event)

### What notebook 02 produces
- `data/processed/analysis_data.csv` — 3,240 rows, 87 columns, `event` column labels each row
- Key columns: `pm2.5_lrapa` (primary PM2.5), `pm2.5_lrapa_regulatory` (LRAPA reference), all weather variables, engineered features (rolling means, lags at 1h/3h/6h/12h/24h, wind sin/cos, calendar fields)

### What the analysis has found so far (run on 2022-only data)
- **Strongest contemporaneous correlation:** `pressure_hpa` vs PM2.5 (r ≈ −0.35) — but this is likely a **shared synoptic driver** (stagnant high-pressure → smoke pooling), not PM2.5 causing pressure changes
- **GAM (notebook 04, 2022 only):** high train R² (~0.42) but negative test R² — model overfits; not a stable out-of-sample signal
- **Moisture / CCN (notebook 05, 2022 only):** lagged PM2.5 does not improve CV prediction of RH or dewpoint depression above thermodynamic controls — signal not detected in 2022 alone
- **2020 data not yet incorporated into analysis notebooks** — run 02 first to regenerate `analysis_data.csv` with both events

---

## Codebase Structure

```
PM2.5-weather/
├── data/
│   ├── raw/
│   │   ├── noaa/        ← NOAA METAR CSVs (2020 + 2022)
│   │   ├── purpleair/   ← PurpleAir sensor CSVs (2020 + 2022)
│   │   └── lrapa/       ← LRAPA regulatory Excel files (2020 + 2022)
│   └── processed/       ← analysis_data.csv + figures (gitignored)
├── notebooks/
│   ├── 01_data_exploration.ipynb    ← raw data inspection
│   ├── 02_data_cleaning.ipynb       ← full ETL pipeline → analysis_data.csv
│   ├── 03_initial_analysis.ipynb    ← EDA, side-by-side event comparisons
│   ├── 04_gam_modeling.ipynb        ← GAM: PM2.5 lag → weather (pooled + per-event)
│   └── 05_moisture_ccn_hypothesis.ipynb  ← moisture/CCN focus, M0 vs M1 CV
├── scripts/
│   ├── find_purpleair_sensors.py    ← API query to build eugene_sensors.csv
│   └── prepare_download_list.py     ← builds download CSVs; --year 2020 or 2022
├── src/
│   ├── data_loader.py      ← PurpleAirLoader, NOAALoader, LRAPALoader
│   ├── preprocessing.py    ← DataCleaner, TimeAligner, DataMerger, create_full_analysis_dataset()
│   └── visualization.py    ← EDA plotting utilities
└── requirements.txt
```

### Key `src/` notes
- **`data_loader.py`:** `PurpleAirLoader` skips files with leading-space names (bogus exports); `LRAPALoader` averages 4 Eugene-area stations → `pm2.5_lrapa_regulatory`; supports both 2020 and 2022 LRAPA Excel formats
- **`preprocessing.py`:** `apply_lrapa_correction()` coalesces `pm2.5_cf_1_a` and `pm2.5_cf_1` per row (handles 2020 legacy column names); `create_full_analysis_dataset()` runs the full 3-way merge
- **`scripts/prepare_download_list.py`:** run with `--year 2020` or `--year 2022`

---

## Immediate Next Steps

1. **Re-run `02_data_cleaning.ipynb`** (Restart Kernel → Run All) to generate the combined 3,240-row `analysis_data.csv` with both fire events
2. **Run `03_initial_analysis.ipynb`** — will now show side-by-side event comparisons in all plots
3. **Run `04_gam_modeling.ipynb`** — pooled GAMs + per-event partial effect comparison
4. **Run `05_moisture_ccn_hypothesis.ipynb`** — pooled CV + per-event M0 vs M1 comparison
5. **Interpret results:** if signal appears in 2020 (much higher PM2.5) but not 2022, that establishes a minimum-exposure threshold argument; if neither, frame as a clean null result with identifiable detection limits

---

## Key Open Decisions

- Whether to add **diurnal temperature range** as an outcome (radiation/mixing mechanism — may be more detectable than RH)
- Final presentation format (Jupyter notebook + short paper)
- How to frame results: positive association, null result, or upper-bound-on-detectability

---

## Deliverables

- Well-documented, reproducible **Python code and Jupyter notebooks**
- A **short paper** presenting findings and conclusions

---

## Tech Stack

Python 3, pandas, numpy, matplotlib, seaborn, scipy, scikit-learn, pygam, Jupyter

---

## Key References

- Zhao et al. (2017) — aerosol–cloud feedback loops increasing PM2.5 by up to 25.1%
- Lu et al. (2025) — wildfire particles larger on average → stronger CCN effect
- Burke et al. (2023) — wildfire contribution to PM2.5 trends in the USA
- Rosenfeld et al. (2008) — aerosols, flood/drought, precipitation suppression
- Stone et al. (2011) — radiative forcing of wildfire smoke
- Oregon DEQ (2025) — wildfire smoke trends in Oregon
