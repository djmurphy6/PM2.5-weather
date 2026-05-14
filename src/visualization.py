"""
Visualization utilities for PM2.5 and weather data analysis.

This module provides plotting functions for exploratory data analysis
and results visualization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List, Tuple, Union
import warnings

# Set default style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class TimeSeriesPlotter:
    """Create time series visualizations."""
    
    def __init__(self, figsize: Tuple[int, int] = (14, 6)):
        """
        Initialize time series plotter.
        
        Args:
            figsize: Default figure size (width, height)
        """
        self.figsize = figsize
        
    def plot_single_variable(self,
                            df: pd.DataFrame,
                            timestamp_col: str,
                            value_col: str,
                            title: Optional[str] = None,
                            ylabel: Optional[str] = None,
                            color: str = 'steelblue',
                            ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot a single variable over time.
        
        Args:
            df: DataFrame with data
            timestamp_col: Name of timestamp column
            value_col: Name of value column to plot
            title: Plot title
            ylabel: Y-axis label
            color: Line color
            ax: Matplotlib axes (optional)
            
        Returns:
            Matplotlib axes
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        
        ax.plot(df[timestamp_col], df[value_col], color=color, alpha=0.7, linewidth=1)
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel(ylabel or value_col, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return ax
    
    def plot_dual_axis(self,
                      df: pd.DataFrame,
                      timestamp_col: str,
                      left_col: str,
                      right_col: str,
                      left_label: Optional[str] = None,
                      right_label: Optional[str] = None,
                      title: Optional[str] = None,
                      left_color: str = 'steelblue',
                      right_color: str = 'coral') -> plt.Figure:
        """
        Plot two variables with separate y-axes.
        
        Args:
            df: DataFrame with data
            timestamp_col: Name of timestamp column
            left_col: Column for left y-axis
            right_col: Column for right y-axis
            left_label: Left y-axis label
            right_label: Right y-axis label
            title: Plot title
            left_color: Color for left variable
            right_color: Color for right variable
            
        Returns:
            Matplotlib figure
        """
        fig, ax1 = plt.subplots(figsize=self.figsize)
        
        # Left axis
        ax1.plot(df[timestamp_col], df[left_col], 
                color=left_color, linewidth=1.5, label=left_label or left_col)
        ax1.set_xlabel('Time', fontsize=12)
        ax1.set_ylabel(left_label or left_col, fontsize=12, color=left_color)
        ax1.tick_params(axis='y', labelcolor=left_color)
        ax1.grid(True, alpha=0.3)
        
        # Right axis
        ax2 = ax1.twinx()
        ax2.plot(df[timestamp_col], df[right_col], 
                color=right_color, linewidth=1.5, label=right_label or right_col)
        ax2.set_ylabel(right_label or right_col, fontsize=12, color=right_color)
        ax2.tick_params(axis='y', labelcolor=right_color)
        
        if title:
            ax1.set_title(title, fontsize=14, fontweight='bold')
        
        # Add legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        return fig
    
    def plot_multiple_variables(self,
                               df: pd.DataFrame,
                               timestamp_col: str,
                               value_cols: List[str],
                               title: Optional[str] = None,
                               subplot_layout: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        Plot multiple variables in subplots.
        
        Args:
            df: DataFrame with data
            timestamp_col: Name of timestamp column
            value_cols: List of columns to plot
            title: Overall title
            subplot_layout: (rows, cols) for subplots (auto if None)
            
        Returns:
            Matplotlib figure
        """
        n_vars = len(value_cols)
        
        if subplot_layout is None:
            n_cols = 1
            n_rows = n_vars
        else:
            n_rows, n_cols = subplot_layout
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(self.figsize[0], 4*n_rows))
        
        if n_vars == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        colors = plt.cm.Set2(np.linspace(0, 1, n_vars))
        
        for i, (col, color) in enumerate(zip(value_cols, colors)):
            if col not in df.columns:
                continue
            
            axes[i].plot(df[timestamp_col], df[col], color=color, linewidth=1)
            axes[i].set_title(col, fontsize=12, fontweight='bold')
            axes[i].set_xlabel('Time')
            axes[i].set_ylabel(col)
            axes[i].grid(True, alpha=0.3)
        
        # Hide extra subplots
        for i in range(n_vars, len(axes)):
            axes[i].set_visible(False)
        
        if title:
            fig.suptitle(title, fontsize=16, fontweight='bold', y=1.00)
        
        plt.tight_layout()
        return fig
    
    def plot_seasonal_pattern(self,
                             df: pd.DataFrame,
                             timestamp_col: str,
                             value_col: str,
                             season_col: str = 'season',
                             title: Optional[str] = None) -> plt.Figure:
        """
        Plot variable patterns by season.
        
        Args:
            df: DataFrame with data and season column
            timestamp_col: Name of timestamp column
            value_col: Column to plot
            season_col: Column with season labels
            title: Plot title
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        seasons = df[season_col].unique()
        colors = {'winter': 'steelblue', 'spring': 'green', 
                 'summer': 'orange', 'fall': 'brown'}
        
        for season in seasons:
            season_data = df[df[season_col] == season]
            ax.plot(season_data[timestamp_col], season_data[value_col],
                   label=season.capitalize(), 
                   color=colors.get(season, 'gray'),
                   alpha=0.6, linewidth=1)
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel(value_col, fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig


class CorrelationPlotter:
    """Create correlation visualizations."""
    
    def __init__(self, figsize: Tuple[int, int] = (10, 8)):
        """
        Initialize correlation plotter.
        
        Args:
            figsize: Default figure size
        """
        self.figsize = figsize
        
    def plot_correlation_matrix(self,
                                df: pd.DataFrame,
                                columns: Optional[List[str]] = None,
                                method: str = 'pearson',
                                title: Optional[str] = None,
                                annot: bool = True) -> plt.Figure:
        """
        Plot correlation heatmap.
        
        Args:
            df: DataFrame with data
            columns: Columns to include (default: all numeric)
            method: Correlation method ('pearson', 'spearman', 'kendall')
            title: Plot title
            annot: Whether to annotate cells with values
            
        Returns:
            Matplotlib figure
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Calculate correlation
        corr = df[columns].corr(method=method)
        
        # Create plot
        fig, ax = plt.subplots(figsize=self.figsize)
        
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        sns.heatmap(corr, mask=mask, annot=annot, fmt='.2f',
                   cmap='coolwarm', center=0, vmin=-1, vmax=1,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                   ax=ax)
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        return fig
    
    def plot_scatter_matrix(self,
                           df: pd.DataFrame,
                           columns: List[str],
                           hue: Optional[str] = None) -> plt.Figure:
        """
        Create scatter plot matrix (pairplot).
        
        Args:
            df: DataFrame with data
            columns: Columns to include
            hue: Column for color coding
            
        Returns:
            Seaborn PairGrid figure
        """
        if hue and hue not in df.columns:
            warnings.warn(f"Hue column '{hue}' not found, ignoring")
            hue = None
        
        g = sns.pairplot(df[columns + ([hue] if hue else [])],
                        hue=hue, diag_kind='kde', plot_kws={'alpha': 0.6})
        
        return g.fig
    
    def plot_scatter_with_trend(self,
                               df: pd.DataFrame,
                               x_col: str,
                               y_col: str,
                               title: Optional[str] = None,
                               show_stats: bool = True) -> plt.Figure:
        """
        Create scatter plot with trend line and statistics.
        
        Args:
            df: DataFrame with data
            x_col: X-axis column
            y_col: Y-axis column
            title: Plot title
            show_stats: Whether to display correlation statistics
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Scatter plot
        ax.scatter(df[x_col], df[y_col], alpha=0.5, s=20, color='steelblue')
        
        # Trend line
        z = np.polyfit(df[x_col].dropna(), df[y_col].dropna(), 1)
        p = np.poly1d(z)
        ax.plot(df[x_col], p(df[x_col]), "r--", alpha=0.8, linewidth=2, label='Trend')
        
        # Statistics
        if show_stats:
            corr = df[[x_col, y_col]].corr().iloc[0, 1]
            ax.text(0.05, 0.95, f'Correlation: {corr:.3f}',
                   transform=ax.transAxes, fontsize=12,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig


class DistributionPlotter:
    """Create distribution visualizations."""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 5)):
        """
        Initialize distribution plotter.
        
        Args:
            figsize: Default figure size
        """
        self.figsize = figsize
        
    def plot_histogram_with_kde(self,
                               df: pd.DataFrame,
                               column: str,
                               bins: int = 50,
                               title: Optional[str] = None) -> plt.Figure:
        """
        Plot histogram with kernel density estimate.
        
        Args:
            df: DataFrame with data
            column: Column to plot
            bins: Number of histogram bins
            title: Plot title
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Histogram
        ax.hist(df[column].dropna(), bins=bins, alpha=0.6, 
               color='steelblue', density=True, label='Histogram')
        
        # KDE
        df[column].dropna().plot(kind='kde', ax=ax, color='red',
                                linewidth=2, label='KDE')
        
        ax.set_xlabel(column, fontsize=12)
        ax.set_ylabel('Density', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def plot_boxplot_by_category(self,
                                 df: pd.DataFrame,
                                 value_col: str,
                                 category_col: str,
                                 title: Optional[str] = None) -> plt.Figure:
        """
        Create boxplot grouped by category.
        
        Args:
            df: DataFrame with data
            value_col: Column with values to plot
            category_col: Column with categories
            title: Plot title
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        sns.boxplot(data=df, x=category_col, y=value_col, ax=ax)
        
        ax.set_xlabel(category_col, fontsize=12)
        ax.set_ylabel(value_col, fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def plot_violin_plot(self,
                        df: pd.DataFrame,
                        value_col: str,
                        category_col: str,
                        title: Optional[str] = None) -> plt.Figure:
        """
        Create violin plot grouped by category.
        
        Args:
            df: DataFrame with data
            value_col: Column with values
            category_col: Column with categories
            title: Plot title
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        sns.violinplot(data=df, x=category_col, y=value_col, ax=ax)
        
        ax.set_xlabel(category_col, fontsize=12)
        ax.set_ylabel(value_col, fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig


class GeographicPlotter:
    """Create geographic visualizations (requires folium)."""
    
    def __init__(self):
        """Initialize geographic plotter."""
        try:
            import folium
            self.folium = folium
            self.available = True
        except ImportError:
            warnings.warn("folium not installed, geographic plotting unavailable")
            self.available = False
    
    def plot_sensor_locations(self,
                             df: pd.DataFrame,
                             lat_col: str = 'latitude',
                             lon_col: str = 'longitude',
                             value_col: Optional[str] = None,
                             center: Optional[Tuple[float, float]] = None):
        """
        Create interactive map of sensor locations.
        
        Args:
            df: DataFrame with sensor location data
            lat_col: Latitude column name
            lon_col: Longitude column name
            value_col: Column for color coding markers (optional)
            center: (lat, lon) for map center (auto if None)
            
        Returns:
            Folium map object
        """
        if not self.available:
            raise ImportError("folium required for geographic plotting")
        
        # Calculate center if not provided
        if center is None:
            center = (df[lat_col].mean(), df[lon_col].mean())
        
        # Create map
        m = self.folium.Map(location=center, zoom_start=12)
        
        # Add markers
        for idx, row in df.iterrows():
            if pd.isna(row[lat_col]) or pd.isna(row[lon_col]):
                continue
            
            popup_text = f"Lat: {row[lat_col]:.4f}, Lon: {row[lon_col]:.4f}"
            if value_col and value_col in df.columns:
                popup_text += f"<br>{value_col}: {row[value_col]:.2f}"
            
            self.folium.Marker(
                location=[row[lat_col], row[lon_col]],
                popup=popup_text,
                icon=self.folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        
        return m


def create_eda_report(df: pd.DataFrame,
                     timestamp_col: str = 'timestamp',
                     pm25_col: str = 'pm25',
                     weather_cols: Optional[List[str]] = None) -> None:
    """
    Create comprehensive EDA report with multiple visualizations.
    
    Args:
        df: Analysis DataFrame
        timestamp_col: Timestamp column name
        pm25_col: PM2.5 column name
        weather_cols: List of weather variables to plot
    """
    if weather_cols is None:
        weather_cols = ['temperature_f', 'humidity', 'pressure_hpa', 'wind_speed_mph']
    
    # Filter to available columns
    weather_cols = [col for col in weather_cols if col in df.columns]
    
    # Initialize plotters
    ts_plotter = TimeSeriesPlotter()
    corr_plotter = CorrelationPlotter()
    dist_plotter = DistributionPlotter()
    
    print("Creating EDA visualizations...")
    
    # 1. PM2.5 time series
    print("1. PM2.5 time series")
    ts_plotter.plot_single_variable(
        df, timestamp_col, pm25_col,
        title='PM2.5 Concentration Over Time',
        ylabel='PM2.5 (μg/m³)'
    )
    plt.show()
    
    # 2. Weather variables
    if weather_cols:
        print("2. Weather variables")
        ts_plotter.plot_multiple_variables(
            df, timestamp_col, weather_cols,
            title='Weather Variables Over Time'
        )
        plt.show()
    
    # 3. PM2.5 vs Temperature
    if 'temperature_f' in df.columns:
        print("3. PM2.5 vs Temperature")
        ts_plotter.plot_dual_axis(
            df, timestamp_col, pm25_col, 'temperature_f',
            left_label='PM2.5 (μg/m³)', right_label='Temperature (°F)',
            title='PM2.5 and Temperature Over Time'
        )
        plt.show()
    
    # 4. Correlation matrix
    print("4. Correlation matrix")
    corr_cols = [pm25_col] + weather_cols
    corr_plotter.plot_correlation_matrix(
        df, columns=corr_cols,
        title='Correlation Matrix: PM2.5 and Weather Variables'
    )
    plt.show()
    
    # 5. PM2.5 distribution
    print("5. PM2.5 distribution")
    dist_plotter.plot_histogram_with_kde(
        df, pm25_col,
        title='PM2.5 Concentration Distribution'
    )
    plt.show()
    
    # 6. Seasonal patterns
    if 'season' in df.columns:
        print("6. Seasonal PM2.5 patterns")
        dist_plotter.plot_boxplot_by_category(
            df, pm25_col, 'season',
            title='PM2.5 Concentration by Season'
        )
        plt.show()
    
    print("EDA report complete!")
