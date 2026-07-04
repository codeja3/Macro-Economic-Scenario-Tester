"""Script to download and parse historical macroeconomic data.

This script fetches Robert Shiller's U.S. Stock Markets historical dataset,
extracts and calculates the S&P 500 total return (monthly), CPI monthly change
(inflation), and 10-Year Treasury yield, and saves them to a CSV file.
"""

import io
import os
from pathlib import Path
import pandas as pd
import requests


def download_and_parse_shiller_data(url: str) -> pd.DataFrame:
    """Downloads Robert Shiller's Excel spreadsheet and reads it into a DataFrame.

    Args:
        url: The HTTP URL of the Shiller Excel dataset.

    Returns:
        A pandas DataFrame containing the raw data sheet.
    """
    print(f"Downloading Shiller data from {url}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    print("Parsing Excel workbook sheet 'Data'...")
    # Skip the first 7 rows as they contain title information and metadata notes.
    df = pd.read_excel(io.BytesIO(response.content), sheet_name="Data", skiprows=7)
    return df


def process_historical_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans, converts, and formats the historical economic data.

    Args:
        df: Raw pandas DataFrame parsed from the Shiller spreadsheet.

    Returns:
        A cleaned DataFrame containing date, sp500_tr_return, cpi_index,
        and treasury_10yr_yield.
    """
    # Drop rows where 'Date' is NaN and coerce to numeric
    df = df.dropna(subset=["Date"])
    df["Date"] = pd.to_numeric(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # Ensure required columns are numeric
    cols_to_coerce = ["P", "D", "E", "CPI", "Rate GS10"]
    for col in cols_to_coerce:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows that ended up with NaNs in our required variables after coercion
    df = df.dropna(subset=cols_to_coerce)

    # Sort sequentially by Date
    df = df.sort_values("Date").reset_index(drop=True)

    # Parse date float (e.g. 1928.01) to 'YYYY-MM-DD'
    def float_to_date_str(val: float) -> str:
        val_str = f"{val:.2f}"
        year, month = val_str.split(".")
        return f"{year}-{month}-01"

    df["date"] = df["Date"].apply(float_to_date_str)

    # Calculate S&P 500 Total Return (monthly rate):
    # R_t = (P_t + D_t/12) / P_{t-1} - 1
    df["sp500_tr_return"] = (df["P"] + df["D"] / 12.0) / df["P"].shift(1) - 1.0

    # Calculate CPI monthly inflation change:
    # cpi_change_t = (CPI_t - CPI_{t-1}) / CPI_{t-1}
    df["cpi_index"] = (df["CPI"] - df["CPI"].shift(1)) / df["CPI"].shift(1)

    # Convert 10-Yr Treasury yield from percentage rate to decimal fraction (e.g. 3.5% -> 0.035)
    df["treasury_10yr_yield"] = df["Rate GS10"] / 100.0

    # Drop the first row as it has NaN returns from shift(1)
    df_clean = df.dropna(subset=["sp500_tr_return", "cpi_index"])

    return df_clean[["date", "sp500_tr_return", "cpi_index", "treasury_10yr_yield"]]


def main() -> None:
    """Main execution function for the script."""
    shiller_url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    output_path = Path("data") / "historical_regimes.csv"

    # Create target directory if it does not exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        raw_df = download_and_parse_shiller_data(shiller_url)
        clean_df = process_historical_data(raw_df)

        print(f"Processed {len(clean_df)} monthly economic records.")
        print(f"Date range: {clean_df['date'].min()} to {clean_df['date'].max()}")

        clean_df.to_csv(output_path, index=False)
        print(f"Successfully saved clean dataset to {output_path}")

    except Exception as e:
        print(f"Error executing historical data generation: {e}")
        raise


if __name__ == "__main__":
    main()
