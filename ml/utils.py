import pandas as pd
import numpy as np

def normalize_data(df, columns):
    """Normalize specified columns to 0-1 range"""
    df_norm = df.copy()
    for col in columns:
        min_val = df[col].min()
        max_val = df[col].max()
        if max_val > min_val:
            df_norm[col] = (df[col] - min_val) / (max_val - min_val)
    return df_norm

def handle_missing_values(df, strategy='mean'):
    """Handle missing values in dataframe"""
    if strategy == 'mean':
        return df.fillna(df.mean())
    elif strategy == 'forward':
        return df.fillna(method='ffill')
    return df

def split_time_series(df, train_ratio=0.8):
    """Split time series data into train/test"""
    split_idx = int(len(df) * train_ratio)
    return df[:split_idx], df[split_idx:]

if __name__ == '__main__':
    print("ML utils module loaded")
