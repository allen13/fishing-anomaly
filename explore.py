#!/usr/bin/env python3
"""
Compare different aggregation strategies for fishing vessel data:
1. Vessel-level aggregation (current approach)
2. Time-based aggregation (vessel + date)
3. Spatial aggregation (vessel + grid cell)

This script will print row counts for each strategy to help determine
which approach provides sufficient detail for anomaly detection.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('aggregation_analysis')

def load_data(filepath):
    """Load vessel data from CSV file"""
    logger.info(f"Loading data from: {filepath}")
    df = pd.read_csv(filepath)
    
    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    
    logger.info(f"Original data: {len(df):,} rows, {df['mmsi'].nunique():,} unique vessels")
    return df

def strategy_1_vessel_aggregation(df):
    """Current strategy: Aggregate all data by vessel"""
    logger.info("Strategy 1: Full vessel-level aggregation")
    
    agg_df = df.groupby('mmsi').agg(
        position_count=('mmsi', 'count'),
        avg_speed=('speed', 'mean'),
        speed_std=('speed', 'std'),
        min_speed=('speed', 'min'),
        max_speed=('speed', 'max'),
        avg_course=('course', 'mean'),
        avg_lat=('lat', 'mean'),
        avg_lon=('lon', 'mean'),
        min_lat=('lat', 'min'),
        max_lat=('lat', 'max'),
        min_lon=('lon', 'min'),
        max_lon=('lon', 'max')
    ).reset_index()
    
    logger.info(f"Vessel aggregation: {len(agg_df):,} rows ({len(agg_df)/len(df):.2%} of original)")
    return agg_df

def strategy_2_time_aggregation(df):
    """Strategy 2: Aggregate by vessel and date"""
    logger.info("Strategy 2: Time-based aggregation (vessel + date)")
    
    # Extract date component
    df['date'] = df['timestamp'].dt.date
    
    time_agg_df = df.groupby(['mmsi', 'date']).agg(
        position_count=('mmsi', 'count'),
        avg_speed=('speed', 'mean'),
        speed_std=('speed', 'std'),
        avg_course=('course', 'mean'),
        avg_lat=('lat', 'mean'),
        avg_lon=('lon', 'mean')
    ).reset_index()
    
    logger.info(f"Time aggregation: {len(time_agg_df):,} rows ({len(time_agg_df)/len(df):.2%} of original)")
    logger.info(f"Average positions per vessel-day: {time_agg_df['position_count'].mean():.1f}")
    return time_agg_df

def strategy_3_spatial_aggregation(df, grid_size=1.0):
    """Strategy 3: Aggregate by vessel and spatial grid cell"""
    logger.info(f"Strategy 3: Spatial aggregation (vessel + {grid_size}° grid cells)")
    
    # Create grid cells (round to nearest grid_size)
    df['grid_lat'] = np.floor(df['lat'] / grid_size) * grid_size
    df['grid_lon'] = np.floor(df['lon'] / grid_size) * grid_size
    
    spatial_agg_df = df.groupby(['mmsi', 'grid_lat', 'grid_lon']).agg(
        position_count=('mmsi', 'count'),
        avg_speed=('speed', 'mean'),
        speed_std=('speed', 'std'),
        avg_course=('course', 'mean'),
        first_seen=('timestamp', 'min'),
        last_seen=('timestamp', 'max')
    ).reset_index()
    
    # Calculate time spent in grid cell
    spatial_agg_df['time_in_cell_hours'] = (spatial_agg_df['last_seen'] - 
                                          spatial_agg_df['first_seen']).dt.total_seconds() / 3600
    
    logger.info(f"Spatial aggregation: {len(spatial_agg_df):,} rows ({len(spatial_agg_df)/len(df):.2%} of original)")
    logger.info(f"Unique grid cells: {spatial_agg_df[['grid_lat', 'grid_lon']].drop_duplicates().shape[0]:,}")
    return spatial_agg_df

def main():
    parser = argparse.ArgumentParser(description='Explore aggregation strategies for vessel data')
    parser.add_argument('filepath', help='Path to CSV file with vessel data', default='./data/drifting_vessels.csv')
    parser.add_argument('--grid-size', type=float, default=1.0, 
                        help='Grid size in degrees for spatial aggregation (default: 1.0)')
    args = parser.parse_args()
    
    if not os.path.exists(args.filepath):
        logger.error(f"File not found: {args.filepath}")
        sys.exit(1)
    
    # Load the data
    df = load_data(args.filepath)
    
    # If data is very large, use a sample
    if len(df) > 1000000:
        sample_size = 1000000
        logger.info(f"Data is large. Using {sample_size:,} row sample for analysis")
        df = df.sample(sample_size, random_state=42)
    
    # Apply each strategy and get row counts
    vessel_agg = strategy_1_vessel_aggregation(df)
    time_agg = strategy_2_time_aggregation(df)
    spatial_agg = strategy_3_spatial_aggregation(df, args.grid_size)
    
    # Print summary comparison
    logger.info("\n=== SUMMARY ===")
    logger.info(f"Original data: {len(df):,} rows, {df['mmsi'].nunique():,} vessels")
    logger.info(f"Strategy 1 (Vessel aggregation): {len(vessel_agg):,} rows ({len(vessel_agg)/len(df):.2%} of original)")
    logger.info(f"Strategy 2 (Time aggregation): {len(time_agg):,} rows ({len(time_agg)/len(df):.2%} of original)")
    logger.info(f"Strategy 3 (Spatial aggregation): {len(spatial_agg):,} rows ({len(spatial_agg)/len(df):.2%} of original)")
    
    # Save samples
    vessel_agg.head(5).to_csv("sample_vessel_agg.csv", index=False)
    time_agg.head(5).to_csv("sample_time_agg.csv", index=False)
    spatial_agg.head(5).to_csv("sample_spatial_agg.csv", index=False)
    logger.info("Saved sample outputs to CSV files")

if __name__ == "__main__":
    main()