# Data Collection Guide

This document provides guidance on collecting PM2.5 and weather data for the Eugene, OR area.

## Data Sources

### 1. Purple Air PM2.5 Sensors

**What is Purple Air?**
Purple Air is a network of community-operated air quality sensors that measure PM2.5 (particulate matter smaller than 2.5 micrometers).

**API Access:**
- **API Documentation**: https://api.purpleair.com/
- **Registration**: You need to request an API key at https://develop.purpleair.com/
- **Rate Limits**: Free tier allows reasonable data collection for research

**Finding Eugene Sensors:**
1. Visit https://map.purpleair.com/
2. Navigate to Eugene, OR area
3. Click on sensors to get their Sensor IDs
4. Recommended: Select 5-10 sensors across different parts of Eugene for spatial coverage

**Key Sensor IDs for Eugene Area** (examples - verify these are still active):
- You'll need to identify current active sensors in the Eugene area
- Look for sensors with consistent data history (at least 1 year)
- Prioritize outdoor sensors over indoor

**Data Fields Available:**
- `timestamp`: UTC timestamp of measurement
- `pm2.5_cf_1`: PM2.5 concentration (μg/m³) using CF=1 correction
- `pm2.5_atm`: PM2.5 concentration (μg/m³) using atmospheric correction
- `temperature`: Temperature in Fahrenheit
- `humidity`: Relative humidity (%)
- `pressure`: Atmospheric pressure (millibars)
- `sensor_index`: Unique sensor identifier
- `latitude`, `longitude`: Sensor location

**Recommended API Endpoint:**
```
GET https://api.purpleair.com/v1/sensors/{sensor_index}/history
```

**Query Parameters:**
- `start_timestamp`: Unix timestamp for start of data range
- `end_timestamp`: Unix timestamp for end of data range
- `average`: Time averaging (0=real-time, 10=10min, 60=1hour, 360=6hour, 1440=1day)
- `fields`: Comma-separated list of fields to retrieve

**Example Request:**
```bash
curl -X GET "https://api.purpleair.com/v1/sensors/12345/history?start_timestamp=1609459200&end_timestamp=1640995200&average=60&fields=pm2.5_cf_1,temperature,humidity" \
  -H "X-API-Key: YOUR_API_KEY"
```

### 2. NOAA Weather Data

**What Station to Use:**
- **Station**: KEUG (Mahlon Sweet Airport, Eugene, OR)
- **Coordinates**: 44.12°N, 123.21°W
- **Elevation**: 364 ft

**Data Source Options:**

#### Option A: NOAA ISD (Integrated Surface Database)
- **Website**: https://www.ncei.noaa.gov/access/search/data-search/global-hourly
- **Format**: CSV or NetCDF
- **Temporal Resolution**: Hourly observations
- **Data Coverage**: Comprehensive meteorological data

**Key Variables:**
- `TMP`: Air temperature (°C)
- `DEW`: Dew point temperature (°C)
- `SLP`: Sea level pressure (hPa)
- `WND`: Wind speed and direction
- `VIS`: Visibility (m)
- `AA1-AA4`: Precipitation data
- `GF1`: Sky cover/cloud data

#### Option B: NOAA LCD (Local Climatological Data)
- **Website**: https://www.ncdc.noaa.gov/cdo-web/datatools/lcd
- **Format**: CSV
- **Temporal Resolution**: Hourly or daily
- **Advantage**: Pre-processed, easier to use

**Recommended Variables to Collect:**
- Temperature (hourly average, min, max)
- Dew point
- Relative humidity
- Wind speed and direction
- Atmospheric pressure (sea level and station)
- Precipitation
- Visibility
- Cloud cover
- Weather conditions (present weather codes)

#### Option C: METAR/ASOS Data
- **Source**: Aviation weather reports
- **Access**: https://mesonet.agron.iastate.edu/request/download.phtml
- **Format**: CSV
- **Advantage**: Standardized format, easy to parse

**Example Download from Iowa State Mesonet:**
1. Visit: https://mesonet.agron.iastate.edu/request/download.phtml?network=OR_ASOS
2. Select station: KEUG
3. Select date range
4. Select variables
5. Download CSV

## Data Collection Workflow

### Step 1: Determine Time Period
- **Recommendation**: At least 1 full year of data to capture seasonal patterns
- **Consider**: 2019-2023 for recent conditions (avoiding COVID-19 anomalies if not relevant)
- **Wildfire Impact**: Oregon has wildfire season (summer/fall) - ensure coverage

### Step 2: Purple Air Data Collection
1. Register for API key
2. Identify 5-10 active Eugene area sensors
3. Download historical data (hourly average recommended)
4. Save raw data to `data/raw/purpleair/`
5. File naming: `purpleair_sensor{ID}_{start_date}_{end_date}.csv`

### Step 3: NOAA Data Collection
1. Visit NOAA data portal
2. Select KEUG station
3. Select same time period as Purple Air data
4. Download hourly observations
5. Save to `data/raw/noaa/`
6. File naming: `noaa_keug_{start_date}_{end_date}.csv`

### Step 4: Data Organization
```
data/
├── raw/
│   ├── purpleair/
│   │   ├── purpleair_sensor12345_20220101_20221231.csv
│   │   ├── purpleair_sensor67890_20220101_20221231.csv
│   │   └── sensor_locations.csv (sensor metadata)
│   └── noaa/
│       └── noaa_keug_20220101_20221231.csv
└── processed/
    └── (cleaned and merged datasets will go here)
```

## Data Quality Considerations

### Purple Air:
- **Missing Data**: Sensors go offline occasionally
- **Outliers**: Extreme values during wildfires (legitimate data, not errors)
- **Calibration**: Some sensors may drift over time
- **Spatial Variation**: PM2.5 can vary significantly across short distances

### NOAA:
- **Missing Values**: Coded as 9999 or similar
- **Data Quality Flags**: Check for quality flags in the data
- **Timezone**: Usually in UTC, need to convert to Pacific Time
- **Units**: Various units used, need standardization

## Recommended Time Alignment

1. **Choose Base Timezone**: Pacific Time (America/Los_Angeles)
2. **Temporal Resolution**: Hourly averages (good balance of detail and manageability)
3. **Alignment Strategy**: 
   - Round/floor timestamps to nearest hour
   - Interpolate missing values where appropriate
   - Flag data gaps

## Important Variables Summary

| Source | Variable | Unit | Importance |
|--------|----------|------|------------|
| Purple Air | PM2.5 | μg/m³ | Primary air quality metric |
| Purple Air | Temperature | °F | Sensor temperature (compare with NOAA) |
| Purple Air | Humidity | % | Affects PM2.5 measurements |
| NOAA | Temperature | °C or °F | Official weather observations |
| NOAA | Dew Point | °C or °F | Moisture content |
| NOAA | Pressure | hPa | Atmospheric stability |
| NOAA | Wind Speed | m/s or mph | Dispersion of particles |
| NOAA | Wind Direction | degrees | Air mass transport |
| NOAA | Precipitation | mm or inches | Wet deposition of particles |
| NOAA | Cloud Cover | oktas or % | Solar radiation, temperature |

## Next Steps

1. Obtain Purple Air API key
2. Identify and document Eugene area sensor IDs
3. Download sample data (1 month) to test pipeline
4. Run `01_data_exploration.ipynb` to examine data structure
5. Expand to full date range once pipeline is working
