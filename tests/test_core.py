"""Unit tests for the core data engine of MEST."""

from pathlib import Path
import pytest
import polars as pl

from mest.core.data_loader import load_historical_data, DataLoaderError
from mest.core.simulator import SimulationConfig, SimulationResults, run_simulation


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


def test_load_historical_data_corrupt_file(tmp_path: Path) -> None:
    """Verifies that a completely corrupt or unreadable file raises DataLoaderError."""
    corrupt_file = tmp_path / "corrupt.csv"
    corrupt_file.write_bytes(b"\x00\xff\x00\xff\r\n\xff\xff")
    with pytest.raises(DataLoaderError):
        load_historical_data(corrupt_file)


def test_load_historical_data_invalid_date_type(tmp_path: Path) -> None:
    """Verifies that if date is non-string (e.g. numeric), it raises DataLoaderError."""
    invalid_file = tmp_path / "invalid_date.csv"
    # Write date as numeric float which will be parsed as float, not string
    invalid_file.write_text(
        "date,sp500_tr_return,cpi_index,treasury_10yr_yield\n"
        "1928,0.012,-0.001,0.035\n"
    )
    with pytest.raises(DataLoaderError) as exc_info:
        load_historical_data(invalid_file)
    assert "must be string" in str(exc_info.value).lower()


def test_simulation_zero_withdrawals() -> None:
    """Validate that success rates are exactly 100% if withdrawals are $0."""
    config = SimulationConfig(
        starting_principal=100000.0,
        bridge_duration_months=12,
        bridge_monthly_withdrawal=0.0,
        post_bridge_monthly_withdrawal=0.0,
        simulation_duration_months=60,
        simulation_mode="stochastic",
        mean_return_annual=0.07,
        volatility_annual=0.15,
        inflation_annual=0.03,
        num_paths=100,
        seed=42
    )
    results = run_simulation(config)
    assert results.success_probability == 1.0
    assert results.median_ending_balance >= 100000.0
    assert results.average_failure_month == 0.0  # No failures


def test_simulation_immediate_depletion() -> None:
    """Check that success rate is 0% if withdrawals exceed starting principal on month 1."""
    config = SimulationConfig(
        starting_principal=10000.0,
        bridge_duration_months=12,
        bridge_monthly_withdrawal=15000.0,  # Exceeds principal
        post_bridge_monthly_withdrawal=0.0,
        simulation_duration_months=60,
        simulation_mode="stochastic",
        mean_return_annual=0.07,
        volatility_annual=0.15,
        inflation_annual=0.03,
        num_paths=100,
        seed=42
    )
    results = run_simulation(config)
    assert results.success_probability == 0.0
    assert results.average_failure_month == 1.0
    assert results.median_ending_balance == 0.0


def test_simulation_determinism() -> None:
    """Verifies that the stochastic simulation is deterministic with the same seed."""
    config1 = SimulationConfig(
        starting_principal=100000.0,
        bridge_duration_months=12,
        bridge_monthly_withdrawal=1000.0,
        post_bridge_monthly_withdrawal=500.0,
        simulation_duration_months=120,
        simulation_mode="stochastic",
        mean_return_annual=0.07,
        volatility_annual=0.15,
        inflation_annual=0.03,
        num_paths=500,
        seed=123
    )
    config2 = SimulationConfig(
        starting_principal=100000.0,
        bridge_duration_months=12,
        bridge_monthly_withdrawal=1000.0,
        post_bridge_monthly_withdrawal=500.0,
        simulation_duration_months=120,
        simulation_mode="stochastic",
        mean_return_annual=0.07,
        volatility_annual=0.15,
        inflation_annual=0.03,
        num_paths=500,
        seed=123
    )
    results1 = run_simulation(config1)
    results2 = run_simulation(config2)
    
    assert results1.success_probability == results2.success_probability
    assert results1.median_ending_balance == results2.median_ending_balance
    assert results1.percentile_10th_ending_balance == results2.percentile_10th_ending_balance
    assert results1.percentile_90th_ending_balance == results2.percentile_90th_ending_balance
    assert results1.average_failure_month == results2.average_failure_month


def test_simulation_historical_bootstrap() -> None:
    """Verifies that the historical bootstrap mode works with provided historical data."""
    # Create simple mock historical data
    mock_hist = pl.DataFrame({
        "date": ["2000-01-01", "2000-02-01", "2000-03-01"],
        "sp500_tr_return": [0.02, -0.01, 0.0],
        "cpi_index": [0.002, 0.003, 0.001],
        "treasury_10yr_yield": [0.05, 0.05, 0.05]
    })
    
    config = SimulationConfig(
        starting_principal=100000.0,
        bridge_duration_months=3,
        bridge_monthly_withdrawal=1000.0,
        post_bridge_monthly_withdrawal=1000.0,
        simulation_duration_months=60,
        simulation_mode="historical_bootstrap",
        mean_return_annual=0.0,
        volatility_annual=0.0,
        inflation_annual=0.0,
        num_paths=100,
        seed=42
    )
    
    results = run_simulation(config, historical_df=mock_hist)
    assert 0.0 <= results.success_probability <= 1.0
    assert len(results.monthly_paths) > 0
    
    # If historical_df is missing in bootstrap mode, it should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        run_simulation(config, historical_df=None)
    assert "historical data" in str(exc_info.value).lower()


def test_simulation_invalid_duration() -> None:
    """Verifies that simulation duration out of bounds raises ValueError."""
    config_low = SimulationConfig(
        starting_principal=100000.0,
        bridge_duration_months=12,
        bridge_monthly_withdrawal=1000.0,
        post_bridge_monthly_withdrawal=500.0,
        simulation_duration_months=12,  # Too low
        simulation_mode="stochastic",
        mean_return_annual=0.07,
        volatility_annual=0.15,
        inflation_annual=0.03
    )
    with pytest.raises(ValueError) as exc_info:
        run_simulation(config_low)
    assert "duration must be between" in str(exc_info.value).lower()

    config_high = SimulationConfig(
        starting_principal=100000.0,
        bridge_duration_months=12,
        bridge_monthly_withdrawal=1000.0,
        post_bridge_monthly_withdrawal=500.0,
        simulation_duration_months=400,  # Too high
        simulation_mode="stochastic",
        mean_return_annual=0.07,
        volatility_annual=0.15,
        inflation_annual=0.03
    )
    with pytest.raises(ValueError) as exc_info:
        run_simulation(config_high)
    assert "duration must be between" in str(exc_info.value).lower()


def test_simulation_invalid_mode() -> None:
    """Verifies that an unknown simulation mode raises ValueError."""
    config = SimulationConfig(
        starting_principal=100000.0,
        bridge_duration_months=12,
        bridge_monthly_withdrawal=1000.0,
        post_bridge_monthly_withdrawal=500.0,
        simulation_duration_months=120,
        simulation_mode="invalid_mode_here",  # type: ignore
        mean_return_annual=0.07,
        volatility_annual=0.15,
        inflation_annual=0.03
    )
    with pytest.raises(ValueError) as exc_info:
        run_simulation(config)
    assert "unknown simulation mode" in str(exc_info.value).lower()


def test_simulation_bootstrap_missing_cols() -> None:
    """Verifies that bootstrap mode raises ValueError if historical columns are missing."""
    mock_bad_cols = pl.DataFrame({
        "date": ["2000-01-01"],
        "some_random_column": [1.0]
    })
    config = SimulationConfig(
        starting_principal=100000.0,
        bridge_duration_months=12,
        bridge_monthly_withdrawal=1000.0,
        post_bridge_monthly_withdrawal=500.0,
        simulation_duration_months=120,
        simulation_mode="historical_bootstrap",
        mean_return_annual=0.0,
        volatility_annual=0.0,
        inflation_annual=0.0
    )
    with pytest.raises(ValueError) as exc_info:
        run_simulation(config, historical_df=mock_bad_cols)
    assert "missing required columns" in str(exc_info.value).lower()
