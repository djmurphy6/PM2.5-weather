"""
Data preprocessing and cleaning utilities.

This module provides functions for cleaning, aligning, and merging
PM2.5 and weather data for analysis.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
import warnings
from scipy import stats


class DataCleaner:
    """Clean and validate air quality and weather data."""
    
    def __init__(self, 
                 pm25_max: float = 1000.0,
                 temp_range: Tuple[float, float] = (-40, 120),
                 humidity_range: Tuple[float, float] = (0, 100)):
        """
        Initialize data cleaner with validation thresholds.
        
        Args:
            pm25_max: Maximum reasonable PM2.5 value (μg/m³)
            temp_range: (min, max) temperature in Fahrenheit
            humidity_range: (min, max) relative humidity (%)
        """
        self.pm25_max = pm25_max
        self.temp_range = temp_range
        self.humidity_range = humidity_range
        
    def clean_purpleair_data(self, df: pd.DataFrame,
                             apply_lrapa: bool = True,
                             drop_ab_flagged: bool = True) -> pd.DataFrame:
        """
        Clean Purple Air sensor data.

        Steps:
          1. A/B channel QC — flag and optionally drop disagreeing readings
          2. Apply LRAPA correction to cf_1_a → pm2.5_lrapa
          3. Remove out-of-range PM2.5 values
          4. Remove duplicate timestamps per sensor
          5. Sort by timestamp

        Args:
            df: Raw Purple Air DataFrame
            apply_lrapa: Apply the LRAPA correction formula
            drop_ab_flagged: Drop rows flagged by A/B QC

        Returns:
            Cleaned DataFrame with 'pm2.5_lrapa' as the primary PM2.5 column
        """
        df = df.copy()

        # Step 1 — A/B channel QC
        df = self.flag_ab_channel_disagreement(df)
        if drop_ab_flagged and 'ab_channel_flag' in df.columns:
            n_before = len(df)
            df = df[~df['ab_channel_flag']].copy()
            print(f"Dropped {n_before - len(df)} A/B-flagged records")

        # Step 2 — LRAPA correction
        if apply_lrapa:
            df = self.apply_lrapa_correction(df)

        # Step 3 — range check on the primary PM2.5 column
        pm25_col = self._find_pm25_column(df)
        if pm25_col is None:
            warnings.warn("No PM2.5 column found")
            return df

        initial_count = len(df)
        df = df[(df[pm25_col] >= 0) & (df[pm25_col] <= self.pm25_max)]
        removed = initial_count - len(df)
        if removed > 0:
            print(f"Removed {removed} records with invalid PM2.5 values")

        # Step 4 — deduplicate
        if 'sensor_id' in df.columns and 'timestamp' in df.columns:
            duplicates = df.duplicated(subset=['sensor_id', 'timestamp'], keep='first')
            df = df[~duplicates]
            if duplicates.sum() > 0:
                print(f"Removed {duplicates.sum()} duplicate timestamps")

        # Step 5 — sort
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)

        return df
    
    def clean_noaa_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean NOAA weather data.
        
        Args:
            df: Raw NOAA DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Replace common missing value indicators
        df = df.replace([9999, 999.9, -9999, -999.9], np.nan)
        df = df.replace(['M', 'm', '*', ''], np.nan)
        
        # Validate temperature
        if 'temperature_f' in df.columns:
            df.loc[~df['temperature_f'].between(*self.temp_range), 'temperature_f'] = np.nan
        
        # Validate humidity
        if 'humidity' in df.columns:
            df.loc[~df['humidity'].between(*self.humidity_range), 'humidity'] = np.nan
        
        # Remove duplicate timestamps
        if 'timestamp' in df.columns:
            duplicates = df.duplicated(subset=['timestamp'], keep='first')
            df = df[~duplicates]
            if duplicates.sum() > 0:
                print(f"Removed {duplicates.sum()} duplicate timestamps")
        
        # Sort by timestamp
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def remove_outliers(self, 
                       df: pd.DataFrame, 
                       columns: List[str],
                       method: str = 'iqr',
                       threshold: float = 3.0) -> pd.DataFrame:
        """
        Remove statistical outliers from specified columns.
        
        Args:
            df: DataFrame
            columns: List of column names to check for outliers
            method: 'iqr' (interquartile range) or 'zscore'
            threshold: IQR multiplier (default 3.0) or z-score threshold
            
        Returns:
            DataFrame with outliers removed
        """
        df = df.copy()
        initial_count = len(df)
        
        for col in columns:
            if col not in df.columns:
                continue
            
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                df = df[(df[col] >= lower) & (df[col] <= upper)]
            
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(df[col].dropna()))
                df = df[z_scores < threshold]
        
        removed = initial_count - len(df)
        if removed > 0:
            print(f"Removed {removed} outlier records")
        
        return df
    
    def apply_lrapa_correction(self, df: pd.DataFrame,
                               cf1_col: str = 'pm2.5_cf_1_a') -> pd.DataFrame:
        """Apply the LRAPA correction formula to PurpleAir CF=1 readings.

        Formula (Lane Regional Air Protection Agency):
            PM2.5_corrected = 0.5 × CF_1 - 0.66

        Developed for the Eugene/Lane County area and validated against
        regulatory-grade monitors during wildfire smoke events. Results
        are clipped to ≥ 0.

        Args:
            df: DataFrame containing the CF=1 PM2.5 column
            cf1_col: Name of the CF=1 channel A column

        Returns:
            DataFrame with new 'pm2.5_lrapa' column added
        """
        df = df.copy()
        if cf1_col not in df.columns:
            warnings.warn(f"Column '{cf1_col}' not found; skipping LRAPA correction")
            return df
        df['pm2.5_lrapa'] = (0.5 * df[cf1_col] - 0.66).clip(lower=0)
        print(f"Applied LRAPA correction to '{cf1_col}' → 'pm2.5_lrapa'")
        return df

    def flag_ab_channel_disagreement(self, df: pd.DataFrame,
                                     col_a: str = 'pm2.5_cf_1_a',
                                     col_b: str = 'pm2.5_cf_1_b',
                                     diff_threshold: float = 5.0,
                                     ratio_threshold: float = 0.70) -> pd.DataFrame:
        """Flag rows where A and B laser channels disagree significantly.

        A reading is flagged when BOTH conditions hold:
          - |A - B| > diff_threshold  (absolute difference, µg/m³)
          - min(A,B) / max(A,B) < ratio_threshold  (channels differ by > 30%)

        Flagged rows should be excluded from analysis. The flag column
        'ab_channel_flag' is True where disagreement is detected.

        Args:
            df: DataFrame with both channel columns
            col_a: Channel A column name
            col_b: Channel B column name
            diff_threshold: Maximum acceptable absolute difference (µg/m³)
            ratio_threshold: Minimum acceptable A/B ratio (0–1)

        Returns:
            DataFrame with 'ab_channel_flag' boolean column added
        """
        df = df.copy()
        if col_a not in df.columns or col_b not in df.columns:
            warnings.warn(f"Columns '{col_a}' and/or '{col_b}' not found; skipping A/B QC")
            return df

        abs_diff = (df[col_a] - df[col_b]).abs()
        max_val  = df[[col_a, col_b]].max(axis=1).replace(0, np.nan)
        min_val  = df[[col_a, col_b]].min(axis=1)
        ratio    = min_val / max_val

        df['ab_channel_flag'] = (abs_diff > diff_threshold) & (ratio < ratio_threshold)
        n_flagged = df['ab_channel_flag'].sum()
        if n_flagged > 0:
            print(f"A/B QC: flagged {n_flagged} records ({n_flagged/len(df)*100:.1f}%) "
                  f"with channel disagreement")
        return df

    def _find_pm25_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the primary PM2.5 column in the DataFrame.

        Prefers LRAPA-corrected value if already computed, then cf_1_a
        (used as input to LRAPA correction), then other known names.
        """
        pm25_cols = [
            'pm2.5_lrapa', 'pm25',
            'pm2.5_cf_1_a', 'pm2.5_cf_1',
            'pm2.5_atm_a',  'pm2.5_atm',
            'pm2.5_alt_a',  'pm2.5',
            'PM2.5_CF_1_ug/m3',
        ]
        for col in pm25_cols:
            if col in df.columns:
                return col
        return None


class TimeAligner:
    """Align time series data to common temporal grid."""
    
    def __init__(self, freq: str = '1H'):
        """
        Initialize time aligner.
        
        Args:
            freq: Pandas frequency string (e.g., '1H' for hourly, '1D' for daily)
        """
        self.freq = freq
        
    def resample_to_hourly(self, 
                           df: pd.DataFrame, 
                           timestamp_col: str = 'timestamp',
                           agg_dict: Optional[dict] = None) -> pd.DataFrame:
        """
        Resample data to hourly frequency.
        
        Args:
            df: DataFrame with timestamp column
            timestamp_col: Name of timestamp column
            agg_dict: Dictionary mapping column names to aggregation functions
                     (default: mean for numeric columns)
            
        Returns:
            Resampled DataFrame
        """
        if timestamp_col not in df.columns:
            raise ValueError(f"Timestamp column '{timestamp_col}' not found")
        
        df = df.copy()
        df = df.set_index(timestamp_col)
        
        # Default aggregation: mean for numeric columns
        if agg_dict is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            agg_dict = {col: 'mean' for col in numeric_cols}
        
        # Resample
        df_resampled = df.resample(self.freq).agg(agg_dict)
        df_resampled = df_resampled.reset_index()
        
        return df_resampled
    
    def aggregate_sensors(self,
                         df: pd.DataFrame,
                         timestamp_col: str = 'timestamp',
                         sensor_col: str = 'sensor_id',
                         value_cols: Optional[List[str]] = None,
                         agg_func: str = 'mean') -> pd.DataFrame:
        """
        Aggregate multiple sensors to single value per timestamp.
        
        Args:
            df: DataFrame with multiple sensors
            timestamp_col: Name of timestamp column
            sensor_col: Name of sensor ID column
            value_cols: Columns to aggregate (default: all numeric)
            agg_func: Aggregation function ('mean', 'median', etc.)
            
        Returns:
            Aggregated DataFrame with one row per timestamp
        """
        if value_cols is None:
            value_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Group by timestamp and aggregate
        agg_dict = {col: agg_func for col in value_cols if col in df.columns}
        df_agg = df.groupby(timestamp_col).agg(agg_dict).reset_index()
        
        # Add count of sensors per timestamp
        sensor_counts = df.groupby(timestamp_col)[sensor_col].nunique().reset_index()
        sensor_counts = sensor_counts.rename(columns={sensor_col: 'n_sensors'})
        df_agg = df_agg.merge(sensor_counts, on=timestamp_col, how='left')
        
        return df_agg
    
    def align_timestamps(self,
                        df1: pd.DataFrame,
                        df2: pd.DataFrame,
                        timestamp_col: str = 'timestamp',
                        method: str = 'inner') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Align two DataFrames to have matching timestamps.
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            timestamp_col: Name of timestamp column
            method: 'inner' (intersection) or 'outer' (union)
            
        Returns:
            Tuple of aligned (df1, df2)
        """
        # Get unique timestamps from each
        ts1 = set(df1[timestamp_col])
        ts2 = set(df2[timestamp_col])
        
        if method == 'inner':
            common_ts = ts1 & ts2
        elif method == 'outer':
            common_ts = ts1 | ts2
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Filter to common timestamps
        df1_aligned = df1[df1[timestamp_col].isin(common_ts)].copy()
        df2_aligned = df2[df2[timestamp_col].isin(common_ts)].copy()
        
        print(f"Aligned to {len(common_ts)} common timestamps")
        
        return df1_aligned, df2_aligned


class DataMerger:
    """Merge Purple Air and NOAA datasets."""
    
    def __init__(self, timestamp_col: str = 'timestamp'):
        """
        Initialize data merger.
        
        Args:
            timestamp_col: Name of timestamp column
        """
        self.timestamp_col = timestamp_col
        
    def merge_datasets(self,
                      purpleair_df: pd.DataFrame,
                      noaa_df: pd.DataFrame,
                      how: str = 'inner',
                      suffixes: Tuple[str, str] = ('_pa', '_noaa')) -> pd.DataFrame:
        """
        Merge Purple Air and NOAA data on timestamp.
        
        Args:
            purpleair_df: Purple Air DataFrame
            noaa_df: NOAA DataFrame
            how: Merge type ('inner', 'outer', 'left', 'right')
            suffixes: Suffixes for overlapping column names
            
        Returns:
            Merged DataFrame
        """
        if self.timestamp_col not in purpleair_df.columns:
            raise ValueError(f"'{self.timestamp_col}' not in Purple Air data")
        if self.timestamp_col not in noaa_df.columns:
            raise ValueError(f"'{self.timestamp_col}' not in NOAA data")
        
        # Merge on timestamp
        merged = pd.merge(
            purpleair_df,
            noaa_df,
            on=self.timestamp_col,
            how=how,
            suffixes=suffixes
        )
        
        print(f"Merged dataset: {len(merged)} records")
        print(f"Date range: {merged[self.timestamp_col].min()} to {merged[self.timestamp_col].max()}")
        
        return merged
    
    def add_wind_components(self, df: pd.DataFrame,
                            direction_col: str = 'wind_direction') -> pd.DataFrame:
        """Convert wind direction (degrees) to sine and cosine components.

        Wind direction is a circular variable and cannot be used directly in
        linear/GAM models. Sine and cosine components preserve the circular
        structure (e.g. 1° and 359° are treated as nearly identical).

        Args:
            df: DataFrame containing wind direction column
            direction_col: Name of the wind direction column (degrees, 0–360)

        Returns:
            DataFrame with 'wind_dir_sin' and 'wind_dir_cos' columns added
        """
        df = df.copy()
        if direction_col not in df.columns:
            warnings.warn(f"Column '{direction_col}' not found; skipping wind components")
            return df
        rad = np.deg2rad(df[direction_col])
        df['wind_dir_sin'] = np.sin(rad)
        df['wind_dir_cos'] = np.cos(rad)
        return df

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add temporal features to dataset.
        
        Args:
            df: DataFrame with timestamp column
            
        Returns:
            DataFrame with additional time features
        """
        df = df.copy()
        
        if self.timestamp_col not in df.columns:
            raise ValueError(f"'{self.timestamp_col}' not in DataFrame")
        
        ts = df[self.timestamp_col]
        
        # Basic temporal features
        df['year'] = ts.dt.year
        df['month'] = ts.dt.month
        df['day'] = ts.dt.day
        df['hour'] = ts.dt.hour
        df['dayofweek'] = ts.dt.dayofweek
        df['dayofyear'] = ts.dt.dayofyear
        df['week'] = ts.dt.isocalendar().week
        
        # Season (meteorological)
        df['season'] = df['month'].map({
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'fall', 10: 'fall', 11: 'fall'
        })
        
        # Weekend flag
        df['is_weekend'] = df['dayofweek'].isin([5, 6]).astype(int)
        
        return df
    
    def add_rolling_features(self,
                            df: pd.DataFrame,
                            columns: List[str],
                            windows: List[int] = [6, 12, 24]) -> pd.DataFrame:
        """
        Add rolling average features.
        
        Args:
            df: DataFrame (must be sorted by timestamp)
            columns: Columns to create rolling features for
            windows: List of window sizes (in number of records)
            
        Returns:
            DataFrame with rolling features
        """
        df = df.copy()
        
        for col in columns:
            if col not in df.columns:
                continue
            
            for window in windows:
                # Rolling mean
                df[f'{col}_rolling_mean_{window}h'] = (
                    df[col].rolling(window=window, min_periods=1).mean()
                )
                
                # Rolling std
                df[f'{col}_rolling_std_{window}h'] = (
                    df[col].rolling(window=window, min_periods=1).std()
                )
        
        return df
    
    def add_lag_features(self,
                        df: pd.DataFrame,
                        columns: List[str],
                        lags: List[int] = [1, 6, 12, 24]) -> pd.DataFrame:
        """
        Add lagged features.
        
        Args:
            df: DataFrame (must be sorted by timestamp)
            columns: Columns to create lag features for
            lags: List of lag periods (in number of records)
            
        Returns:
            DataFrame with lag features
        """
        df = df.copy()
        
        for col in columns:
            if col not in df.columns:
                continue
            
            for lag in lags:
                df[f'{col}_lag_{lag}h'] = df[col].shift(lag)
        
        return df


def aggregate_purpleair_sensors(pa_clean: pd.DataFrame) -> pd.DataFrame:
    """Aggregate cleaned multi-sensor PurpleAir data to one row per timestamp.

    Computes mean, std, and sensor count across all sensors for each hourly
    timestamp. Input must already have 'pm2.5_lrapa' from apply_lrapa_correction.

    Args:
        pa_clean: Cleaned PurpleAir DataFrame (long format, one row per sensor-hour)

    Returns:
        Wide DataFrame with one row per timestamp and aggregated PM2.5 columns
    """
    agg_cols = {}
    for col in ['pm2.5_lrapa', 'pm2.5_cf_1_a', 'pm2.5_alt_a', 'pm2.5_atm_a']:
        if col in pa_clean.columns:
            agg_cols[col] = ['mean', 'std']
    if not agg_cols:
        raise ValueError("No PM2.5 columns found in cleaned PurpleAir data")

    agg = pa_clean.groupby('timestamp').agg(agg_cols)

    # Flatten multi-level column names
    agg.columns = ['_'.join(c).strip('_') for c in agg.columns]
    agg = agg.rename(columns={
        'pm2.5_lrapa_mean': 'pm2.5_lrapa',
        'pm2.5_lrapa_std':  'pm2.5_lrapa_std',
        'pm2.5_cf_1_a_mean': 'pm2.5_cf1_raw',
        'pm2.5_cf_1_a_std':  'pm2.5_cf1_raw_std',
        'pm2.5_alt_a_mean':  'pm2.5_alt',
        'pm2.5_atm_a_mean':  'pm2.5_atm',
    })

    # Sensor count per timestamp
    agg['n_sensors'] = pa_clean.groupby('timestamp')['sensor_id'].nunique()
    agg = agg.reset_index()

    print(f"Aggregated {pa_clean['sensor_id'].nunique()} sensors → "
          f"{len(agg)} hourly timestamps")
    return agg


def create_full_analysis_dataset(purpleair_df: pd.DataFrame,
                                 noaa_df: pd.DataFrame,
                                 lrapa_df: pd.DataFrame,
                                 noaa_station: str = 'EUG',
                                 add_features: bool = True,
                                 remove_outliers: bool = False) -> pd.DataFrame:
    """Complete three-way pipeline: PurpleAir + NOAA + LRAPA → analysis dataset.

    Steps:
      1. Filter NOAA to target station; resample to hourly
      2. Clean PurpleAir (A/B QC, LRAPA correction); aggregate across sensors
      3. Inner-join all three on timestamp
      4. Add time features and wind components
      5. Optionally add rolling/lag features and remove outliers

    Args:
        purpleair_df: Raw PurpleAir DataFrame (long format, all sensors)
        noaa_df: Raw NOAA DataFrame
        lrapa_df: Cleaned LRAPA DataFrame from LRAPALoader
        noaa_station: NOAA station code to keep (default 'EUG')
        add_features: Add time, wind, rolling, lag features
        remove_outliers: Apply IQR outlier removal on PM2.5

    Returns:
        Merged, feature-engineered DataFrame ready for analysis
    """
    print("=== Creating Full Analysis Dataset ===\n")

    cleaner = DataCleaner()
    aligner = TimeAligner(freq='1h')
    merger  = DataMerger()

    # ── 1. NOAA ─────────────────────────────────────────────────────────────
    print("1. Cleaning NOAA data...")
    if 'station' in noaa_df.columns and noaa_station:
        noaa_filtered = noaa_df[noaa_df['station'] == noaa_station].copy()
        print(f"   Filtered to station '{noaa_station}': {len(noaa_filtered)} records")
    else:
        noaa_filtered = noaa_df.copy()
    noaa_clean    = cleaner.clean_noaa_data(noaa_filtered)
    noaa_hourly   = aligner.resample_to_hourly(noaa_clean)

    # ── 2. PurpleAir ────────────────────────────────────────────────────────
    print("\n2. Cleaning PurpleAir data (A/B QC + LRAPA correction)...")
    pa_clean  = cleaner.clean_purpleair_data(purpleair_df)
    pa_hourly = aggregate_purpleair_sensors(pa_clean)

    # ── 3. LRAPA ────────────────────────────────────────────────────────────
    print("\n3. Preparing LRAPA regulatory data...")
    lrapa_cols = ['timestamp', 'pm2.5_lrapa_regulatory']
    lrapa_keep = [c for c in lrapa_cols if c in lrapa_df.columns]
    lrapa_clean = lrapa_df[lrapa_keep].copy()
    print(f"   {len(lrapa_clean)} LRAPA hourly records")

    # ── 4. Merge ────────────────────────────────────────────────────────────
    print("\n4. Merging all three datasets on timestamp...")
    merged = pd.merge(pa_hourly, noaa_hourly,  on='timestamp', how='inner')
    merged = pd.merge(merged,    lrapa_clean,  on='timestamp', how='left')
    print(f"   Final dataset: {len(merged)} records")
    print(f"   Date range:    {merged['timestamp'].min()} → {merged['timestamp'].max()}")

    # ── 5. Feature engineering ───────────────────────────────────────────────
    if add_features:
        print("\n5. Adding features...")
        merged = merger.add_time_features(merged)
        merged = merger.add_wind_components(merged)
        merged = merger.add_rolling_features(
            merged, columns=['pm2.5_lrapa', 'temperature_f', 'humidity'],
            windows=[3, 6, 12, 24]
        )
        merged = merger.add_lag_features(
            merged, columns=['pm2.5_lrapa', 'temperature_f', 'humidity',
                             'wind_speed_mph', 'pressure_hpa'],
            lags=[1, 3, 6, 12, 24]
        )

    # ── 6. Outlier removal ──────────────────────────────────────────────────
    if remove_outliers:
        print("\n6. Removing statistical outliers...")
        merged = cleaner.remove_outliers(
            merged, columns=['pm2.5_lrapa', 'temperature_f'], method='iqr', threshold=3.0
        )

    missing = merged.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print(f"\nMissing values:\n{missing}")

    print(f"\n=== Done: {len(merged)} records, {len(merged.columns)} columns ===")
    return merged


def create_analysis_dataset(purpleair_df: pd.DataFrame,
                            noaa_df: pd.DataFrame,
                            freq: str = '1H',
                            add_features: bool = True,
                            remove_outliers: bool = True) -> pd.DataFrame:
    """
    Complete pipeline to create analysis-ready dataset.
    
    Args:
        purpleair_df: Raw Purple Air data
        noaa_df: Raw NOAA data
        freq: Temporal frequency for resampling
        add_features: Whether to add engineered features
        remove_outliers: Whether to remove statistical outliers
        
    Returns:
        Clean, merged, feature-engineered DataFrame
    """
    print("=== Creating Analysis Dataset ===")
    
    # Initialize utilities
    cleaner = DataCleaner()
    aligner = TimeAligner(freq=freq)
    merger = DataMerger()
    
    # Clean data
    print("\n1. Cleaning data...")
    pa_clean = cleaner.clean_purpleair_data(purpleair_df)
    noaa_clean = cleaner.clean_noaa_data(noaa_df)
    
    # Resample to common frequency
    print(f"\n2. Resampling to {freq} frequency...")
    pa_resampled = aligner.resample_to_hourly(pa_clean)
    noaa_resampled = aligner.resample_to_hourly(noaa_clean)
    
    # Align timestamps
    print("\n3. Aligning timestamps...")
    pa_aligned, noaa_aligned = aligner.align_timestamps(
        pa_resampled, noaa_resampled, method='inner'
    )
    
    # Merge datasets
    print("\n4. Merging datasets...")
    merged = merger.merge_datasets(pa_aligned, noaa_aligned, how='inner')
    
    # Add features
    if add_features:
        print("\n5. Adding temporal features...")
        merged = merger.add_time_features(merged)
        
        print("6. Adding rolling features...")
        merged = merger.add_rolling_features(
            merged,
            columns=['pm2.5_lrapa', 'temperature_f', 'humidity'],
            windows=[6, 12, 24]
        )
    
    # Remove outliers
    if remove_outliers:
        print("\n7. Removing outliers...")
        merged = cleaner.remove_outliers(
            merged,
            columns=['pm2.5_lrapa', 'temperature_f'],
            method='iqr',
            threshold=3.0
        )
    
    print(f"\n=== Final dataset: {len(merged)} records ===")
    print(f"Columns: {len(merged.columns)}")
    print(f"Missing data:\n{merged.isnull().sum()[merged.isnull().sum() > 0]}")
    
    return merged
