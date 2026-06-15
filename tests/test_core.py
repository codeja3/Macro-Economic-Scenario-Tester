"""Unit tests for the core data engine of MEST."""

from pathlib import Path
import pytest
import polars as pl

from mest.core.data_loader import load_historical_data, DataLoaderError


def test_load_historical_data_success(temp_csv_files: dict[str, Path]) -> None:
    """Verifies that a valid CSV is loaded into a Polars DataFrame successfully."""
    valid_path = temp_csv_files["valid"]
    df = load_historical_data(valid_path)

    # Check it is a Polars DataFrame
    assert isinstance(df, pl.DataFrame)
    
    # Check shape
    assert df.height == 3
    assert df.width == 4

    # Check columns
    expected_cols = ["date", "sp500_tr_return", "cpi_index", "treasury_10yr_yield"]
    assert df.columns == expected_cols

    # Check datatypes
    assert df.schema["date"] == pl.String
    assert df.schema["sp500_tr_return"] == pl.Float64
    assert df.schema["cpi_index"] == pl.Float64
    assert df.schema["treasury_10yr_yield"] == pl.Float64


def test_load_historical_data_file_not_found() -> None:
    """Verifies that a non-existent file raises DataLoaderError."""
    non_existent = Path("does_not_exist_at_all.csv")
    with pytest.raises(DataLoaderError) as exc_info:
        load_historical_data(non_existent)
    assert "not found" in str(exc_info.value).lower()


def test_load_historical_data_missing_columns(temp_csv_files: dict[str, Path]) -> None:
    """Verifies that a CSV missing required columns raises DataLoaderError."""
    invalid_path = temp_csv_files["invalid_cols"]
    with pytest.raises(DataLoaderError) as exc_info:
        load_historical_data(invalid_path)
    assert "missing columns" in str(exc_info.value).lower()


def test_load_historical_data_invalid_types(temp_csv_files: dict[str, Path]) -> None:
    """Verifies that a CSV with invalid non-numeric types raises DataLoaderError."""
    invalid_path = temp_csv_files["invalid_types"]
    with pytest.raises(DataLoaderError) as exc_info:
        load_historical_data(invalid_path)
    assert "invalid data types" in str(exc_info.value).lower()
