"""Configuration and fixtures for pytest.

Includes mock CSV content fixtures and a global socket-blocking fixture to ensure
no real external or local network requests are made during test execution.
"""

from pathlib import Path
import socket
import pytest


@pytest.fixture(autouse=True)
def block_external_sockets() -> None:
    """Disable all network socket connects during test runs.

    This ensures that the test suite is 100% offline and that no accidental
    network requests are made to the local Ollama API or external services.
    """
    original_socket = socket.socket

    def socket_disabled(*args, **kwargs):
        raise RuntimeError(
            "Real network and socket connections are blocked in this test suite. "
            "Ensure all LLM or API requests are properly mocked."
        )

    socket.socket = socket_disabled
    yield
    socket.socket = original_socket


@pytest.fixture
def valid_csv_content() -> str:
    """Returns valid CSV content as a string."""
    return (
        "date,sp500_tr_return,cpi_index,treasury_10yr_yield\n"
        "1928-01-01,0.012,-0.001,0.035\n"
        "1928-02-01,0.008,0.002,0.036\n"
        "1928-03-01,-0.015,0.000,0.034\n"
    )


@pytest.fixture
def invalid_cols_csv_content() -> str:
    """Returns CSV content with missing required columns."""
    return (
        "date,sp500_tr_return,cpi_index\n"
        "1928-01-01,0.012,-0.001\n"
    )


@pytest.fixture
def invalid_types_csv_content() -> str:
    """Returns CSV content with invalid non-numeric values."""
    return (
        "date,sp500_tr_return,cpi_index,treasury_10yr_yield\n"
        "1928-01-01,not-a-number,-0.001,0.035\n"
    )


@pytest.fixture
def temp_csv_files(
    tmp_path: Path,
    valid_csv_content: str,
    invalid_cols_csv_content: str,
    invalid_types_csv_content: str,
) -> dict[str, Path]:
    """Creates temporary CSV files for testing and returns their paths."""
    valid_path = tmp_path / "valid.csv"
    invalid_cols_path = tmp_path / "invalid_cols.csv"
    invalid_types_path = tmp_path / "invalid_types.csv"

    valid_path.write_text(valid_csv_content)
    invalid_cols_path.write_text(invalid_cols_csv_content)
    invalid_types_path.write_text(invalid_types_csv_content)

    return {
        "valid": valid_path,
        "invalid_cols": invalid_cols_path,
        "invalid_types": invalid_types_path,
    }
