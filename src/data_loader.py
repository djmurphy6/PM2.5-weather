"""
Data loading utilities for Purple Air and NOAA data.

This module provides functions to load, validate, and initially parse
PM2.5 sensor data from Purple Air and weather data from NOAA.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, List, Optional
import json
import warnings
from datetime import datetime
import pytz


class PurpleAirLoader:
    """Load and validate Purple Air sensor data."""
    
    def __init__(self, data_dir: Union[str, Path] = "data/raw/purpleair"):
        """
        Initialize Purple Air data loader.
        
        Args:
            data_dir: Directory containing Purple Air CSV/JSON files
        """
        self.data_dir = Path(data_dir)
        self.timezone = pytz.timezone('America/Los_Angeles')
        
    def load_sensor_data(self, 
                        filepath: Union[str, Path],
                        parse_dates: bool = True) -> pd.DataFrame:
        """
        Load data from a single Purple Air sensor file.
        
        Args:
            filepath: Path to CSV or JSON file
            parse_dates: Whether to parse timestamp columns
            
        Returns:
            DataFrame with sensor data
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Load based on file extension
        if filepath.suffix.lower() == '.csv':
            df = pd.read_csv(filepath)
        elif filepath.suffix.lower() == '.json':
            df = pd.read_json(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
        
        # Strip pipe-notation suffixes from column names (e.g. "pm2.5_alt_a|3.4" -> "pm2.5_alt_a")
        df = self._normalize_column_names(df)
        
        # Parse timestamps
        if parse_dates:
            df = self._parse_timestamps(df)
        
        # Validate required columns
        self._validate_columns(df)
        
        # Add sensor ID if not present
        if 'sensor_id' not in df.columns:
            sensor_id = self._extract_sensor_id(filepath)
            df['sensor_id'] = sensor_id
        
        return df
    
    def load_multiple_sensors(self, 
                             filepaths: List[Union[str, Path]]) -> pd.DataFrame:
        """
        Load and combine data from multiple sensors.
        
        Args:
            filepaths: List of paths to sensor data files
            
        Returns:
            Combined DataFrame with all sensor data
        """
        dfs = []
        for filepath in filepaths:
            try:
                df = self.load_sensor_data(filepath)
                dfs.append(df)
            except Exception as e:
                warnings.warn(f"Failed to load {filepath}: {e}")
        
        if not dfs:
            raise ValueError("No data files successfully loaded")
        
        combined = pd.concat(dfs, ignore_index=True)
        return combined
    
    def load_all_sensors_in_directory(self) -> pd.DataFrame:
        """
        Load all Purple Air sensor files in the data directory.
        Searches recursively into subdirectories (e.g. PurpleAir Download folders)
        but skips metadata files at the top level (download_list.csv, eugene_sensors.csv).
        
        Returns:
            Combined DataFrame with all sensor data
        """
        # rglob finds files in subdirectories; skip files sitting at the root level
        csv_files  = [f for f in self.data_dir.rglob("*.csv")  if f.parent != self.data_dir]
        json_files = [f for f in self.data_dir.rglob("*.json") if f.parent != self.data_dir]
        all_files  = csv_files + json_files
        
        if not all_files:
            raise FileNotFoundError(f"No sensor data files found under {self.data_dir}")
        
        print(f"Found {len(all_files)} sensor data files")
        return self.load_multiple_sensors(all_files)
    
    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strip pipe-notation suffixes from column names.
        
        The PurpleAir download tool encodes the CF constant in the column name,
        e.g. 'pm2.5_alt_a|3.4'. This strips everything after the pipe.
        """
        df.columns = [col.split('|')[0] for col in df.columns]
        return df

    def _parse_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse and standardize timestamp columns."""
        timestamp_cols = ['timestamp', 'time_stamp', 'date', 'datetime', 'created_at']
        
        for col in timestamp_cols:
            if col in df.columns:
                # Try to parse as datetime
                try:
                    df[col] = pd.to_datetime(df[col], utc=True)
                    # Convert to Pacific time
                    df[col] = df[col].dt.tz_convert(self.timezone)
                    # Standardize column name
                    if col != 'timestamp':
                        df['timestamp'] = df[col]
                    break
                except Exception as e:
                    warnings.warn(f"Failed to parse {col}: {e}")
        
        return df
    
    def _validate_columns(self, df: pd.DataFrame):
        """Validate that required columns are present."""
        pm25_cols = [
            'pm2.5', 'pm2.5_cf_1', 'pm2.5_cf_1_a', 'pm2.5_cf_1_b',
            'pm2.5_atm', 'pm2.5_atm_a', 'pm2.5_alt_a', 'PM2.5_CF_1_ug/m3',
        ]
        has_pm25 = any(col in df.columns for col in pm25_cols)
        
        if not has_pm25:
            warnings.warn("No PM2.5 column found in data")
        
        # Check for timestamp
        if 'timestamp' not in df.columns:
            warnings.warn("No timestamp column found")
    
    def _extract_sensor_id(self, filepath: Path) -> str:
        """Extract sensor ID from filename.
        
        Handles PurpleAir download tool naming convention:
            "2572 2022-08-01 2022-09-30 60-Minute Average.csv"
        and legacy underscore convention:
            "purpleair_sensor12345_....csv"
        """
        filename = filepath.stem
        # PurpleAir download tool: first token before a space is the numeric sensor index
        first_token = filename.split(' ')[0]
        if first_token.isdigit():
            return first_token
        # Legacy underscore format
        parts = filename.split('_')
        for part in parts:
            if 'sensor' in part.lower():
                return part.replace('sensor', '')
        return filename
    
    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """
        Get summary statistics for loaded sensor data.
        
        Args:
            df: DataFrame with sensor data
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'n_records': len(df),
            'n_sensors': df['sensor_id'].nunique() if 'sensor_id' in df.columns else 1,
            'date_range': (df['timestamp'].min(), df['timestamp'].max()) if 'timestamp' in df.columns else None,
            'columns': list(df.columns),
            'missing_data': df.isnull().sum().to_dict()
        }
        
        # PM2.5 statistics
        pm25_col = self._find_pm25_column(df)
        if pm25_col:
            summary['pm25_stats'] = {
                'mean': df[pm25_col].mean(),
                'median': df[pm25_col].median(),
                'min': df[pm25_col].min(),
                'max': df[pm25_col].max(),
                'std': df[pm25_col].std()
            }
        
        return summary
    
    def _find_pm25_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the primary PM2.5 column in the DataFrame.
        
        Prefers cf_1_a (used for LRAPA correction), then falls back to other known names.
        """
        pm25_cols = [
            'pm2.5_cf_1_a', 'pm2.5_cf_1', 'pm2.5_atm_a', 'pm2.5_atm',
            'pm2.5_alt_a', 'pm2.5', 'PM2.5_CF_1_ug/m3',
        ]
        for col in pm25_cols:
            if col in df.columns:
                return col
        return None


class NOAALoader:
    """Load and validate NOAA weather data."""
    
    def __init__(self, data_dir: Union[str, Path] = "data/raw/noaa"):
        """
        Initialize NOAA data loader.
        
        Args:
            data_dir: Directory containing NOAA CSV files
        """
        self.data_dir = Path(data_dir)
        self.timezone = pytz.timezone('America/Los_Angeles')
        
    def load_weather_data(self,
                         filepath: Union[str, Path],
                         data_source: str = 'auto') -> pd.DataFrame:
        """
        Load NOAA weather data from CSV file.
        
        Args:
            filepath: Path to CSV file
            data_source: Data format ('isd', 'lcd', 'metar', or 'auto' to detect)
            
        Returns:
            DataFrame with weather data
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Read CSV
        df = pd.read_csv(filepath, low_memory=False)
        
        # Auto-detect data source if needed
        if data_source == 'auto':
            data_source = self._detect_data_source(df)
            print(f"Detected data source: {data_source}")
        
        # Parse based on source
        if data_source == 'isd':
            df = self._parse_isd_data(df)
        elif data_source == 'lcd':
            df = self._parse_lcd_data(df)
        elif data_source == 'metar':
            df = self._parse_metar_data(df)
        else:
            warnings.warn(f"Unknown data source: {data_source}, attempting generic parsing")
            df = self._parse_generic_noaa(df)
        
        return df
    
    def _detect_data_source(self, df: pd.DataFrame) -> str:
        """Detect NOAA data source from column names."""
        columns_lower = [col.lower() for col in df.columns]
        
        # ISD typically has these columns
        if 'tmp' in columns_lower or 'slp' in columns_lower:
            return 'isd'
        
        # LCD has more readable column names
        if 'hourlydrybulbtemperature' in columns_lower or 'hourlywetbulbtemperature' in columns_lower:
            return 'lcd'
        
        # METAR/ASOS from Iowa State has these
        if 'station' in columns_lower and 'tmpf' in columns_lower:
            return 'metar'
        
        return 'generic'
    
    def _parse_isd_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse ISD (Integrated Surface Database) format."""
        # Parse date/time
        if 'DATE' in df.columns:
            df['timestamp'] = pd.to_datetime(df['DATE'], utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(self.timezone)
        
        # Temperature (tenths of degrees C)
        if 'TMP' in df.columns:
            df['temperature_c'] = pd.to_numeric(df['TMP'].astype(str).str.split(',').str[0], errors='coerce') / 10
            df['temperature_f'] = df['temperature_c'] * 9/5 + 32
        
        # Dew point (tenths of degrees C)
        if 'DEW' in df.columns:
            df['dewpoint_c'] = pd.to_numeric(df['DEW'].astype(str).str.split(',').str[0], errors='coerce') / 10
            df['dewpoint_f'] = df['dewpoint_c'] * 9/5 + 32
        
        # Sea level pressure (tenths of hPa)
        if 'SLP' in df.columns:
            df['pressure_hpa'] = pd.to_numeric(df['SLP'].astype(str).str.split(',').str[0], errors='coerce') / 10
        
        # Wind
        if 'WND' in df.columns:
            wnd_parts = df['WND'].astype(str).str.split(',')
            df['wind_direction'] = pd.to_numeric(wnd_parts.str[0], errors='coerce')
            df['wind_speed_mps'] = pd.to_numeric(wnd_parts.str[3], errors='coerce') / 10
            df['wind_speed_mph'] = df['wind_speed_mps'] * 2.237
        
        return df
    
    def _parse_lcd_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse LCD (Local Climatological Data) format."""
        # Parse date/time
        if 'DATE' in df.columns:
            df['timestamp'] = pd.to_datetime(df['DATE'], utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(self.timezone)
        
        # Temperature (already in proper format)
        if 'HourlyDryBulbTemperature' in df.columns:
            df['temperature_f'] = pd.to_numeric(df['HourlyDryBulbTemperature'], errors='coerce')
            df['temperature_c'] = (df['temperature_f'] - 32) * 5/9
        
        # Dew point
        if 'HourlyDewPointTemperature' in df.columns:
            df['dewpoint_f'] = pd.to_numeric(df['HourlyDewPointTemperature'], errors='coerce')
            df['dewpoint_c'] = (df['dewpoint_f'] - 32) * 5/9
        
        # Relative humidity
        if 'HourlyRelativeHumidity' in df.columns:
            df['humidity'] = pd.to_numeric(df['HourlyRelativeHumidity'], errors='coerce')
        
        # Pressure
        if 'HourlySeaLevelPressure' in df.columns:
            df['pressure_hpa'] = pd.to_numeric(df['HourlySeaLevelPressure'], errors='coerce') * 33.8639  # inHg to hPa
        
        # Wind
        if 'HourlyWindSpeed' in df.columns:
            df['wind_speed_mph'] = pd.to_numeric(df['HourlyWindSpeed'], errors='coerce')
            df['wind_speed_mps'] = df['wind_speed_mph'] * 0.44704
        
        if 'HourlyWindDirection' in df.columns:
            df['wind_direction'] = pd.to_numeric(df['HourlyWindDirection'], errors='coerce')
        
        # Precipitation
        if 'HourlyPrecipitation' in df.columns:
            df['precipitation_in'] = pd.to_numeric(df['HourlyPrecipitation'], errors='coerce')
            df['precipitation_mm'] = df['precipitation_in'] * 25.4
        
        return df
    
    def _parse_metar_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse METAR/ASOS data from Iowa State Mesonet."""
        # Parse date/time
        if 'valid' in df.columns:
            df['timestamp'] = pd.to_datetime(df['valid'], utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(self.timezone)
        
        # Temperature
        if 'tmpf' in df.columns:
            df['temperature_f'] = pd.to_numeric(df['tmpf'], errors='coerce')
            df['temperature_c'] = (df['temperature_f'] - 32) * 5/9
        
        # Dew point
        if 'dwpf' in df.columns:
            df['dewpoint_f'] = pd.to_numeric(df['dwpf'], errors='coerce')
            df['dewpoint_c'] = (df['dewpoint_f'] - 32) * 5/9
        
        # Relative humidity
        if 'relh' in df.columns:
            df['humidity'] = pd.to_numeric(df['relh'], errors='coerce')
        
        # Pressure
        if 'mslp' in df.columns:
            df['pressure_hpa'] = pd.to_numeric(df['mslp'], errors='coerce')
        
        # Wind
        if 'sknt' in df.columns:
            df['wind_speed_knots'] = pd.to_numeric(df['sknt'], errors='coerce')
            df['wind_speed_mph'] = df['wind_speed_knots'] * 1.15078
            df['wind_speed_mps'] = df['wind_speed_knots'] * 0.514444
        
        if 'drct' in df.columns:
            df['wind_direction'] = pd.to_numeric(df['drct'], errors='coerce')
        
        # Precipitation
        if 'p01i' in df.columns:
            df['precipitation_in'] = pd.to_numeric(df['p01i'], errors='coerce')
            df['precipitation_mm'] = df['precipitation_in'] * 25.4
        
        # Visibility
        if 'vsby' in df.columns:
            df['visibility_miles'] = pd.to_numeric(df['vsby'], errors='coerce')
            df['visibility_km'] = df['visibility_miles'] * 1.60934
        
        return df
    
    def _parse_generic_noaa(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generic parsing for NOAA data with common column patterns."""
        # Try to find and parse timestamp
        date_cols = ['DATE', 'date', 'Date', 'valid', 'time', 'datetime']
        for col in date_cols:
            if col in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df[col], utc=True)
                    df['timestamp'] = df['timestamp'].dt.tz_convert(self.timezone)
                    break
                except:
                    continue
        
        return df
    
    def load_all_weather_data(self) -> pd.DataFrame:
        """Load all NOAA weather files in the data directory."""
        csv_files = list(self.data_dir.glob("*.csv"))
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.data_dir}")
        
        dfs = []
        for filepath in csv_files:
            try:
                df = self.load_weather_data(filepath)
                dfs.append(df)
            except Exception as e:
                warnings.warn(f"Failed to load {filepath}: {e}")
        
        if not dfs:
            raise ValueError("No data files successfully loaded")
        
        combined = pd.concat(dfs, ignore_index=True)
        return combined
    
    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """Get summary statistics for loaded weather data."""
        summary = {
            'n_records': len(df),
            'date_range': (df['timestamp'].min(), df['timestamp'].max()) if 'timestamp' in df.columns else None,
            'columns': list(df.columns),
            'missing_data': df.isnull().sum().to_dict()
        }
        
        # Temperature statistics
        if 'temperature_f' in df.columns:
            summary['temperature_stats_f'] = {
                'mean': df['temperature_f'].mean(),
                'min': df['temperature_f'].min(),
                'max': df['temperature_f'].max(),
                'std': df['temperature_f'].std()
            }
        
        return summary


class LRAPALoader:
    """Load and parse LRAPA regulatory-grade PM2.5 monitoring data.

    LRAPA exports hourly data in wide Excel format with one column per
    monitoring station. This loader focuses on Eugene-area stations and
    produces a tidy DataFrame with a single averaged regulatory PM2.5 value.
    """

    # Stations in or immediately adjacent to Eugene — used for the area average
    EUGENE_STATIONS = [
        'Eugene - Amazon Park - Eugene',
        'Eugene - Highway 99 - Eugene',
        'Santa Clara - Madison Middle School - Eugene',
        'Springfield - City Hall - Springfield',
    ]

    # Human-readable short names for each station column
    STATION_SHORT_NAMES = {
        'Eugene - Amazon Park - Eugene':               'pm2.5_amazon_park',
        'Eugene - Highway 99 - Eugene':                'pm2.5_highway_99',
        'Santa Clara - Madison Middle School - Eugene': 'pm2.5_santa_clara',
        'Springfield - City Hall - Springfield':        'pm2.5_springfield',
        'Cottage Grove - Cottage Grove':               'pm2.5_cottage_grove',
        'Florence - Florence':                         'pm2.5_florence',
        'Oakridge - Oakridge':                         'pm2.5_oakridge',
    }

    def __init__(self, data_dir: Union[str, Path] = "data/raw/lrapa"):
        self.data_dir = Path(data_dir)
        self.timezone = pytz.timezone('America/Los_Angeles')

    def load_lrapa_data(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Load a single LRAPA hourly Excel export.

        Args:
            filepath: Path to the .xlsx file

        Returns:
            Tidy DataFrame with timestamp, individual station columns,
            and 'pm2.5_lrapa_regulatory' (mean of Eugene-area stations).
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        df = pd.read_excel(filepath, engine='openpyxl')

        # Parse timestamp — LRAPA exports are in Pacific time
        df['timestamp'] = pd.to_datetime(df['DateTime'])
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize(self.timezone,
                                                              ambiguous='infer',
                                                              nonexistent='shift_forward')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_convert(self.timezone)

        # Rename station columns to short names
        rename_map = {k: v for k, v in self.STATION_SHORT_NAMES.items() if k in df.columns}
        df = df.rename(columns=rename_map)

        # Convert all station value columns to numeric
        station_cols = list(rename_map.values())
        for col in station_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Compute Eugene-area mean across available stations
        eugene_short = [self.STATION_SHORT_NAMES[s] for s in self.EUGENE_STATIONS
                        if s in rename_map]
        if eugene_short:
            df['pm2.5_lrapa_regulatory'] = df[eugene_short].mean(axis=1)
        else:
            warnings.warn("No Eugene-area LRAPA stations found in file")

        # Drop raw columns we no longer need
        drop_cols = ['DateTime', 'Parameter']
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])

        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)

        print(f"Loaded {len(df)} LRAPA records from {filepath.name}")
        print(f"Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
        print(f"Eugene-area stations averaged: {eugene_short}")

        return df

    def load_all_lrapa_data(self) -> pd.DataFrame:
        """Load and concatenate all LRAPA Excel files in the data directory."""
        xlsx_files = list(self.data_dir.glob("*.xlsx"))
        if not xlsx_files:
            raise FileNotFoundError(f"No .xlsx files found in {self.data_dir}")

        dfs = []
        for f in xlsx_files:
            try:
                dfs.append(self.load_lrapa_data(f))
            except Exception as e:
                warnings.warn(f"Failed to load {f.name}: {e}")

        if not dfs:
            raise ValueError("No LRAPA files successfully loaded")

        combined = pd.concat(dfs, ignore_index=True)
        combined = combined.sort_values('timestamp').drop_duplicates('timestamp').reset_index(drop=True)
        return combined

    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """Summary statistics for loaded LRAPA data."""
        return {
            'n_records':  len(df),
            'date_range': (df['timestamp'].min(), df['timestamp'].max()),
            'columns':    list(df.columns),
            'missing':    df.isnull().sum().to_dict(),
            'pm2.5_regulatory_stats': df['pm2.5_lrapa_regulatory'].describe().to_dict()
                if 'pm2.5_lrapa_regulatory' in df.columns else {},
        }


def load_sample_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convenience function to load sample Purple Air and NOAA data.
    
    Returns:
        Tuple of (purpleair_df, noaa_df)
    """
    pa_loader = PurpleAirLoader()
    noaa_loader = NOAALoader()
    
    try:
        pa_data = pa_loader.load_all_sensors_in_directory()
        print(f"Loaded {len(pa_data)} Purple Air records")
    except Exception as e:
        warnings.warn(f"Could not load Purple Air data: {e}")
        pa_data = pd.DataFrame()
    
    try:
        noaa_data = noaa_loader.load_all_weather_data()
        print(f"Loaded {len(noaa_data)} NOAA records")
    except Exception as e:
        warnings.warn(f"Could not load NOAA data: {e}")
        noaa_data = pd.DataFrame()
    
    return pa_data, noaa_data
