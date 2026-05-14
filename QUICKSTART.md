# Quick Start Guide

## Step 1: Set Up Environment

```bash
# Clone or navigate to the project
cd PM2.5-weather

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Collect Data

### Purple Air Data

1. **Get API Key**
   - Register at https://develop.purpleair.com/
   - Request free API key for research

2. **Find Sensors**
   - Visit https://map.purpleair.com/
   - Search for "Eugene, OR"
   - Click sensors to get their IDs
   - Recommended: Choose 5-10 outdoor sensors

3. **Download Data**
   - Use API to download historical data
   - Save as CSV in `data/raw/purpleair/`
   - Naming: `purpleair_sensor{ID}_{start_date}_{end_date}.csv`

### NOAA Weather Data

1. **Visit Iowa State Mesonet**
   - URL: https://mesonet.agron.iastate.edu/request/download.phtml?network=OR_ASOS
   
2. **Select Options**
   - Station: KEUG (Eugene Airport)
   - Date range: Match your Purple Air data
   - Variables: All weather variables
   - Format: CSV

3. **Save Data**
   - Save to `data/raw/noaa/`
   - Naming: `noaa_keug_{start_date}_{end_date}.csv`

## Step 3: Run Analysis

Start Jupyter:

```bash
jupyter notebook
```

Follow notebooks in order:

1. **01_data_exploration.ipynb** - Explore your data
2. **02_data_cleaning.ipynb** - Clean and merge datasets
3. **03_initial_analysis.ipynb** - Analyze relationships

## Step 4: Explore Results

The analysis will create:
- Cleaned dataset in `data/processed/`
- Visualizations showing PM2.5 and weather patterns
- Correlation statistics
- Seasonal analysis

## Example Analysis Code

```python
# In Jupyter notebook
from src.data_loader import PurpleAirLoader, NOAALoader
from src.preprocessing import create_analysis_dataset
from src.visualization import create_eda_report

# Load data
pa_loader = PurpleAirLoader()
pa_data = pa_loader.load_all_sensors_in_directory()

noaa_loader = NOAALoader()
noaa_data = noaa_loader.load_all_weather_data()

# Create analysis dataset
analysis_data = create_analysis_dataset(
    purpleair_df=pa_data,
    noaa_df=noaa_data,
    freq='1H',
    add_features=True
)

# Generate visualizations
create_eda_report(analysis_data)
```

## Troubleshooting

**No data files found:**
- Check files are in correct directories
- Verify file extensions (.csv or .json)
- See `data/README.md` for naming conventions

**Import errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python version (3.9+)

**Memory issues:**
- Start with smaller date range
- Use monthly data chunks
- Process one sensor at a time

## Next Steps

After initial analysis:
- Identify interesting patterns
- Formulate specific hypotheses
- Design appropriate statistical tests
- Consider advanced modeling approaches

## Need Help?

- Review `data/README.md` for data collection details
- Check main `README.md` for package documentation
- Look at example code in notebooks
