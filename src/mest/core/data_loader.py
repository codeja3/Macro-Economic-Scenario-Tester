"""Data ingestion loader for historical macroeconomic regimes.

This module provides clean, type-safe data loading for the S&P 500 total return,
CPI change, and 10-Yr Treasury yield historical datasets using Polars.
"""

from pathlib import Path
import polars as pl


class DataLoaderError(Exception):
    """Custom exception raised when data loading or validation fails."""
    pass


def load_historical_data(file_path: Path) -> pl.DataFrame:
    """Loads and validates historical economic regime data from a CSV file.

    Args:
        file_path: Path to the CSV file to load.

    Returns:
        A Polars DataFrame containing columns: date (String),
        sp500_tr_return (Float64), cpi_index (Float64), and
        treasury_10yr_yield (Float64).

    Raises:
        DataLoaderError: If the file does not exist, required columns are
            missing, or data types are invalid.
    """
    # Defensive programming: fail-fast if path does not exist
    if not file_path.exists():
        raise DataLoaderError(f"File not found: {file_path}")

    try:
        # Ingest the CSV file using Polars
        df = pl.read_csv(file_path)
    except Exception as e:
        raise DataLoaderError(f"Error reading CSV file: {e}")

    # Check for missing required columns
    required_cols = {"date", "sp500_tr_return", "cpi_index", "treasury_10yr_yield"}
    actual_cols = set(df.columns)
    missing_cols = required_cols - actual_cols
    if missing_cols:
        raise DataLoaderError(f"Missing columns in CSV: {missing_cols}")

    # Validate data types
    if df.schema["date"] != pl.String:
        raise DataLoaderError(
            f"Invalid data types: 'date' column must be String, got {df.schema['date']}"
        )

    numeric_cols = ["sp500_tr_return", "cpi_index", "treasury_10yr_yield"]
    for col in numeric_cols:
        if df.schema[col] not in (pl.Float64, pl.Float32):
            raise DataLoaderError(
                f"Invalid data types: Column '{col}' must be float, got {df.schema[col]}"
            )

    return df
