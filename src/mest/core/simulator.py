"""Vectorized Monte Carlo and decumulation simulation engine using Polars.

This module implements the mathematical decumulation stress-testing engine
supporting both stochastic (lognormal) and historical bootstrap simulation modes.
"""

from dataclasses import dataclass
from typing import Literal
import numpy as np
import polars as pl


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration parameters for the decumulation simulation."""
    starting_principal: float
    bridge_duration_months: int
    bridge_monthly_withdrawal: float
    post_bridge_monthly_withdrawal: float
    simulation_duration_months: int            # Range: 60 - 360
    simulation_mode: Literal["stochastic", "historical_bootstrap"]
    mean_return_annual: float                  # Used in stochastic mode
    volatility_annual: float                   # Used in stochastic mode
    inflation_annual: float                    # Used in stochastic mode
    seed: int = 42
    num_paths: int = 10000


@dataclass(frozen=True)
class SimulationResults:
    """Result metrics from the decumulation simulation."""
    success_probability: float                  # Percentage of paths that did not hit 0
    median_ending_balance: float
    percentile_10th_ending_balance: float       # Worst 10% outcome
    percentile_90th_ending_balance: float       # Best 10% outcome
    average_failure_month: float                # Average month at which balance hit 0 (for failed paths only)
    monthly_paths: dict[str, list[float]]       # Polars representation of paths (for UI rendering)


def run_simulation(config: SimulationConfig, historical_df: pl.DataFrame | None = None) -> SimulationResults:
    """Executes the decumulation simulation based on the provided configuration.

    Args:
        config: Simulation parameters.
        historical_df: Optional Polars DataFrame containing historical returns
            (required for "historical_bootstrap" mode).

    Returns:
        SimulationResults containing statistical metrics and sample paths.

    Raises:
        ValueError: If configuration constraints are violated or historical data
            is missing in bootstrap mode.
    """
    # Validation of parameters
    if config.simulation_duration_months < 60 or config.simulation_duration_months > 360:
        raise ValueError("Simulation duration must be between 60 and 360 months.")

    # Number of months (M) and paths (N)
    m = config.simulation_duration_months
    n = config.num_paths

    # Generate monthly return matrix of shape (N, M)
    rng = np.random.default_rng(config.seed)

    if config.simulation_mode == "stochastic":
        # Monthly return generation under lognormal assumptions
        # monthly log std dev
        vol_monthly = config.volatility_annual / (12.0 ** 0.5)
        # monthly log mean
        mean_monthly = (config.mean_return_annual - 0.5 * config.volatility_annual ** 2) / 12.0
        
        # Draw log returns from normal distribution
        log_returns = rng.normal(loc=mean_monthly, scale=vol_monthly, size=(n, m))
        returns = np.exp(log_returns) - 1.0

    elif config.simulation_mode == "historical_bootstrap":
        if historical_df is None:
            raise ValueError("Historical data DataFrame must be provided for historical_bootstrap mode.")
        
        # Verify required columns are present in historical_df
        required_cols = {"sp500_tr_return", "treasury_10yr_yield"}
        missing = required_cols - set(historical_df.columns)
        if missing:
            raise ValueError(f"Historical data is missing required columns: {missing}")

        # Compute monthly yield from annual 10-Yr Treasury yield:
        # y_monthly = (1 + y_annual) ** (1/12) - 1
        treasury_annual = historical_df["treasury_10yr_yield"].to_numpy()
        treasury_monthly = (1.0 + treasury_annual) ** (1.0 / 12.0) - 1.0
        sp500_monthly = historical_df["sp500_tr_return"].to_numpy()

        # Combine returns assuming a default 60% S&P 500 and 40% Treasury portfolio
        combined_hist_returns = 0.60 * sp500_monthly + 0.40 * treasury_monthly

        # Sample from the historical returns with replacement
        indices = rng.choice(len(combined_hist_returns), size=(n, m), replace=True)
        returns = combined_hist_returns[indices]

    else:
        raise ValueError(f"Unknown simulation mode: {config.simulation_mode}")

    # Build the initial Polars DataFrame with starting balances
    # We represent the simulation where each row is a path (N rows)
    # We initialize the month_0 column with starting_principal
    data_dict = {
        "path_id": list(range(n)),
        "month_0": [config.starting_principal] * n,
    }
    
    # Load returns into the dictionary for vectorization
    for t in range(1, m + 1):
        data_dict[f"return_{t}"] = returns[:, t - 1].tolist()

    df = pl.DataFrame(data_dict)

    # Iterative simulation of monthly balances
    # Formula: S_t = max(0, (S_{t-1} - W_t) * (1 + R_t))
    # Withdrawals occur at the start of the month, growth is applied to the remainder.
    for t in range(1, m + 1):
        w_t = config.bridge_monthly_withdrawal if t <= config.bridge_duration_months else config.post_bridge_monthly_withdrawal
        
        # Vectorized Polars evaluation
        df = df.with_columns(
            pl.max_horizontal(
                (pl.col(f"month_{t - 1}") - w_t) * (1.0 + pl.col(f"return_{t}")),
                0.0
            ).alias(f"month_{t}")
        )

    # Extract ending balances (month_M)
    ending_balances = df[f"month_{m}"]

    # Calculate statistics
    success_probability = float((ending_balances > 0.0).mean())
    median_ending_balance = float(ending_balances.median())
    percentile_10th_ending_balance = float(ending_balances.quantile(0.10))
    percentile_90th_ending_balance = float(ending_balances.quantile(0.90))

    # Calculate average failure month (for failed paths only)
    # Generate failure month columns: if month_t == 0, then t, else None
    failure_exprs = [
        pl.when(pl.col(f"month_{t}") == 0.0)
        .then(pl.lit(t))
        .otherwise(None)
        .alias(f"fail_{t}")
        for t in range(1, m + 1)
    ]
    df_fails = df.select(failure_exprs)
    
    # First failure month is the minimum horizontal value across failure columns
    df_first_fail = df_fails.select(pl.min_horizontal(pl.all()).alias("first_fail_month"))
    failed_paths = df_first_fail.filter(pl.col("first_fail_month").is_not_null())
    
    if failed_paths.height > 0:
        average_failure_month = float(failed_paths["first_fail_month"].mean())
    else:
        average_failure_month = 0.0

    # Format monthly paths for UI rendering (transposing the first 100 paths)
    num_visualized_paths = min(n, 100)
    month_cols = [f"month_{t}" for t in range(m + 1)]
    paths_subset = df.head(num_visualized_paths).select(month_cols)

    # Transpose paths_subset to shape (M+1, num_visualized_paths)
    transposed = paths_subset.transpose(column_names=[f"path_{i}" for i in range(num_visualized_paths)])
    transposed = transposed.with_columns(pl.Series("month", list(range(m + 1))))

    # Convert to dict of lists
    monthly_paths = transposed.to_dict(as_series=False)

    return SimulationResults(
        success_probability=success_probability,
        median_ending_balance=median_ending_balance,
        percentile_10th_ending_balance=percentile_10th_ending_balance,
        percentile_90th_ending_balance=percentile_90th_ending_balance,
        average_failure_month=average_failure_month,
        monthly_paths=monthly_paths,
    )
