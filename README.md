# PM2.5 Weather Analysis Project

Thesis project analyzing the relationship between PM2.5 particulate matter and weather patterns in Eugene, OR.

## Project Overview

This project examines potential effects of PM2.5 particles on local weather by combining:
- **Purple Air sensor data**: Community air quality sensors measuring PM2.5 concentrations
- **NOAA weather data**: Official meteorological observations from Eugene Airport (KEUG)

The analysis explores correlations, patterns, and potential causal relationships between air quality and weather variables.

## Project Structure

```
PM2.5-weather/
├── data/
│   ├── raw/              # Raw downloaded data (Purple Air, NOAA)
│   ├── processed/        # Cleaned and merged datasets
│   └── README.md         # Data collection guide
├── notebooks/
│   ├── 01_data_exploration.ipynb    # Initial data exploration
│   ├── 02_data_cleaning.ipynb       # Data cleaning and merging
│   └── 03_initial_analysis.ipynb    # Statistical analysis
├── src/
│   ├── data_loader.py    # Data loading utilities
│   ├── preprocessing.py  # Data cleaning and feature engineering
│   └── visualization.py  # Plotting functions
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Getting Started

### 1. Installation

Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Data Collection

Before analysis, you need to collect PM2.5 and weather data. See [`data/README.md`](data/README.md) for detailed instructions on:

- Obtaining Purple Air API key
- Finding Eugene area sensor IDs
- Downloading NOAA weather data for KEUG station
- Recommended data formats and time periods

**Quick Start:**
- Purple Air: Register at https://develop.purpleair.com/ for API key
- NOAA: Download from Iowa State Mesonet: https://mesonet.agron.iastate.edu/request/download.phtml?network=OR_ASOS

Place data files in:
- `data/raw/purpleair/` - Purple Air sensor files
- `data/raw/noaa/` - NOAA weather files

### 3. Run Analysis

Follow the Jupyter notebooks in order:

```bash
jupyter notebook
```

1. **`01_data_exploration.ipynb`**: Explore raw data structure, check quality
2. **`02_data_cleaning.ipynb`**: Clean, align, and merge datasets
3. **`03_initial_analysis.ipynb`**: Perform statistical analysis and visualization

## Usage Examples

### Loading Data

```python
from src.data_loader import PurpleAirLoader, NOAALoader

# Load Purple Air data
pa_loader = PurpleAirLoader(data_dir='data/raw/purpleair')
pa_data = pa_loader.load_all_sensors_in_directory()

# Load NOAA data
noaa_loader = NOAALoader(data_dir='data/raw/noaa')
noaa_data = noaa_loader.load_all_weather_data()
```

### Creating Analysis Dataset

```python
from src.preprocessing import create_analysis_dataset

# Complete pipeline: clean, merge, add features
analysis_data = create_analysis_dataset(
    purpleair_df=pa_data,
    noaa_df=noaa_data,
    freq='1H',              # Hourly data
    add_features=True,      # Add temporal and rolling features
    remove_outliers=True    # Remove statistical outliers
)

# Save for later use
analysis_data.to_csv('data/processed/analysis_data.csv', index=False)
```

### Visualization

```python
from src.visualization import create_eda_report

# Create comprehensive EDA report
create_eda_report(
    df=analysis_data,
    timestamp_col='timestamp',
    pm25_col='pm25',
    weather_cols=['temperature_f', 'humidity', 'pressure_hpa', 'wind_speed_mph']
)
```

## Key Features

### Data Loading
- Automatic Purple Air CSV/JSON parsing
- Multiple NOAA format support (ISD, LCD, METAR)
- Timezone handling (Pacific Time)
- Data validation and quality checks

### Preprocessing
- Missing value handling
- Outlier detection and removal
- Temporal alignment and resampling
- Multi-sensor aggregation
- Feature engineering (rolling averages, lags, temporal features)

### Visualization
- Time series plots
- Correlation matrices
- Distribution analyses
- Seasonal patterns
- Dual-axis weather comparisons

## Data Variables

### PM2.5 (Purple Air)
- `pm25`: PM2.5 concentration (μg/m³)
- `temperature`: Sensor temperature
- `humidity`: Relative humidity
- `sensor_id`: Sensor identifier

### Weather (NOAA)
- `temperature_f`: Temperature (°F)
- `dewpoint_f`: Dew point (°F)
- `humidity`: Relative humidity (%)
- `pressure_hpa`: Atmospheric pressure (hPa)
- `wind_speed_mph`: Wind speed (mph)
- `wind_direction`: Wind direction (degrees)
- `precipitation`: Precipitation amount

## Analysis Approaches

Potential research questions to explore:

1. **Correlation Analysis**: How do PM2.5 levels correlate with weather variables?
2. **Seasonal Patterns**: Do PM2.5-weather relationships vary by season?
3. **Time-Lagged Effects**: Do PM2.5 changes precede weather changes?
4. **Extreme Events**: How do wildfires (high PM2.5) affect local weather?
5. **Predictive Modeling**: Can weather patterns predict PM2.5 levels?

## Dependencies

Main packages (see `requirements.txt` for complete list):
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `matplotlib`, `seaborn` - Visualization
- `scipy`, `statsmodels` - Statistical analysis
- `scikit-learn` - Machine learning
- `jupyter` - Interactive notebooks

## Contributing

This is a thesis project. For questions or suggestions, please contact the project maintainer.

## Future Work

- [ ] Implement API data collection scripts
- [ ] Add more sophisticated statistical models
- [ ] Develop causal inference framework
- [ ] Create interactive visualizations
- [ ] Expand to other Oregon cities

## References

- Purple Air API: https://api.purpleair.com/
- NOAA Data Access: https://www.ncdc.noaa.gov/
- Iowa State Mesonet: https://mesonet.agron.iastate.edu/

## License

This project is for academic research purposes.

---

**Note**: This repository currently uses static data for analysis. Live API integration will be added in future versions.
