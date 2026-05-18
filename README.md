# PM2.5 & Weather — Eugene, OR

**Bachelor of Science Thesis** · University of Oregon Clark Honors College  
Department of Computer Science · Planned defense Spring 2026

---

## Research Question

> Can measurable links be identified between PM2.5 concentrations from wildfire smoke and short-term **weather changes** in the Eugene, Oregon area?

The causal direction is **PM2.5 → weather** (not weather → PM2.5). The analysis tests whether smoke aerosols are associated with subsequent meteorological changes consistent with three known physical mechanisms:

| Mechanism | Expected signal |
|---|---|
| **Radiation suppression** | Narrower diurnal temperature range (DTR) on smoke days |
| **Boundary layer suppression** | Lower wind speeds during and after heavy smoke |
| **Cloud condensation nuclei (CCN)** | Higher relative humidity / smaller dewpoint depression |

This is an observational study — not a causal proof.

---

## Fire Events Studied

| Event | Date Range | PurpleAir Sensors | Peak PM2.5 |
|---|---|---|---|
| **Holiday Farm Fire 2020** | Aug 1 – Oct 15, 2020 | 22 sensors | ~502 µg/m³ (AQI 457 on Sep 13) |
| **Cedar Creek Fire 2022** | Aug 1 – Sep 30, 2022 | 57 sensors | ~125 µg/m³ |

The 2020 event is the primary focus — it produced extreme exposures over 13 smoke days, creating enough statistical power to detect surface-level aerosol effects.

---

## Key Findings (Holiday Farm Fire 2020)

- **DTR compressed by ~5°F on smoke days** (Welch's t-test p ≈ 0.046, medium effect size) — consistent with solar radiation being scattered and absorbed by smoke
- **Wind speeds lower during smoke hours** — consistent with reduced convective mixing in the boundary layer
- **Daily PM2.5 negatively correlated with DTR** (r ≈ −0.20) after controlling for seasonal trend via GAM
- **CCN/moisture signal not detected** — RH and dewpoint depression do not improve with lagged PM2.5 beyond thermodynamic controls; interpreted as a true null for this mechanism at the surface

---

## Project Structure

```
PM2.5-weather/
├── data/
│   ├── raw/
│   │   ├── noaa/        ← NOAA METAR CSVs (KEUG station, 2020 + 2022)
│   │   ├── purpleair/   ← PurpleAir sensor CSVs (2020 + 2022)
│   │   └── lrapa/       ← LRAPA regulatory reference Excel files
│   └── processed/       ← analysis_data.csv + saved figures
├── notebooks/
│   ├── 01_data_exploration.ipynb         ← raw data inspection
│   ├── 02_data_cleaning.ipynb            ← ETL pipeline → analysis_data.csv
│   ├── 03_initial_analysis.ipynb         ← EDA, side-by-side event comparisons
│   ├── 04_gam_modeling.ipynb             ← GAM: lagged PM2.5 → weather outcomes
│   ├── 05_moisture_ccn_hypothesis.ipynb  ← moisture/CCN focus, M0 vs M1 CV
│   ├── 06_radiation_dtr.ipynb            ← DTR and radiation suppression (primary result)
│   └── 07_boundary_layer.ipynb           ← wind speed, mixing, BL suppression
├── scripts/
│   ├── find_purpleair_sensors.py         ← query PurpleAir API → eugene_sensors.csv
│   └── prepare_download_list.py          ← build download CSVs (--year 2020 or 2022)
├── src/
│   ├── data_loader.py      ← PurpleAirLoader, NOAALoader, LRAPALoader
│   ├── preprocessing.py    ← DataCleaner, TimeAligner, DataMerger
│   └── visualization.py    ← EDA plotting utilities
├── requirements.txt
├── PROJECT_CONTEXT.md      ← detailed living project context document
└── README.md               ← this file
```

---

## Getting Started

### 1. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Data layout

Ensure data files are in place (see `PROJECT_CONTEXT.md` for exact filenames):

```
data/raw/purpleair/   ← PurpleAir 60-min average CSVs
data/raw/noaa/        ← NOAA METAR CSVs from Iowa State Mesonet
data/raw/lrapa/       ← LRAPA hourly data Excel files
```

**Data sources:**
- PurpleAir: [PurpleAir Data Download Tool](https://community.purpleair.com/t/data-download-tool/172) (requires API key from [develop.purpleair.com](https://develop.purpleair.com/))
- NOAA: [Iowa State Mesonet](https://mesonet.agron.iastate.edu/request/download.phtml?network=OR_ASOS) — station `KEUG`
- LRAPA: [LRAPA data portal](https://www.lrapa.org/) — Eugene-area stations

### 3. Run notebooks in order

```bash
jupyter notebook
```

| Step | Notebook | Purpose |
|---|---|---|
| 1 | `02_data_cleaning.ipynb` | Build `analysis_data.csv` — **run this first** |
| 2 | `03_initial_analysis.ipynb` | EDA with side-by-side event comparisons |
| 3 | `04_gam_modeling.ipynb` | GAMs: lagged PM2.5 → temperature, humidity, wind, pressure |
| 4 | `05_moisture_ccn_hypothesis.ipynb` | Moisture/CCN hypothesis with RidgeCV + TimeSeriesSplit |
| 5 | `06_radiation_dtr.ipynb` | Diurnal temperature range — primary result |
| 6 | `07_boundary_layer.ipynb` | Wind speed and boundary layer suppression |

---

## Statistical Methods

### Exposure
`pm2.5_lrapa` — LRAPA-corrected PurpleAir PM2.5 (µg/m³), averaged across Eugene-area sensors.  
Lagged versions (`_lag_1h` through `_lag_24h`) are used as predictors so the exposure strictly precedes the outcome.

### Models

**Generalized Additive Models (`pygam`)** — notebook 04 and 06  
`outcome ~ s(pm2.5_lag) + s(hour) + s(dayofyear)`  
Captures non-linear relationships and produces interpretable partial effects. Fit separately for pooled data and per fire event.

**Ridge Regression + TimeSeriesSplit CV (`sklearn`)** — notebook 05  
Nested model comparison: M0 (weather controls only) vs M1 (controls + lagged PM2.5).  
`TimeSeriesSplit` ensures no future data leaks into training folds.

**Welch's t-test + Cohen's d** — notebooks 06 and 07  
Smoke day vs clean day comparisons for DTR and wind speed, with effect size.

**Partial correlation** — notebook 07  
Controls for pressure as a confound (synoptic high pressure independently drives both smoke accumulation and light winds).

---

## Source Code

### `src/data_loader.py`
- `PurpleAirLoader` — loads and aggregates all PurpleAir sensor CSVs; skips corrupt exports
- `NOAALoader` — parses Iowa State Mesonet METAR format
- `LRAPALoader` — averages Eugene-area LRAPA stations into a single regulatory reference series

### `src/preprocessing.py`
- `DataCleaner` — LRAPA correction (`0.5 × CF1 − 0.66`), A/B channel QC, outlier removal
- Handles the 2020 PurpleAir column naming convention (`pm2.5_cf_1` vs `pm2.5_cf_1_a`) via per-row coalesce
- `create_full_analysis_dataset()` — end-to-end merge of all three data sources

### `scripts/prepare_download_list.py`
Generate a sensor download list for a specific fire season:
```bash
python scripts/prepare_download_list.py --year 2020
python scripts/prepare_download_list.py --year 2022
```

---

## Dependencies

```
pandas, numpy, matplotlib, seaborn   ← data and visualization
scipy, scikit-learn                   ← statistics and ML
pygam                                 ← generalized additive models
openpyxl                              ← reading LRAPA Excel files
jupyter                               ← notebook runner
```

See `requirements.txt` for pinned versions.

---

## References

- Stone et al. (2011) — radiative forcing of wildfire smoke
- Zhao et al. (2017) — aerosol–cloud feedbacks and PM2.5 amplification
- Burke et al. (2023) — wildfire contribution to PM2.5 trends in the USA
- Lu et al. (2025) — wildfire particle size and CCN effects
- Rosenfeld et al. (2008) — aerosols, precipitation suppression

---

*For detailed pipeline status, data inventory, and technical notes see `PROJECT_CONTEXT.md`.*
