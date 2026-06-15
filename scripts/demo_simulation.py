"""Demo script to run and understand the MEST decumulation simulator.

This script executes both stochastic and historical bootstrap simulations
using a mock retired portfolio spending plan, printing key statistics
and execution runtimes.
"""

from pathlib import Path
import time
from mest.core.data_loader import load_historical_data
from mest.core.simulator import SimulationConfig, run_simulation


def main() -> None:
    """Main demo execution function."""
    print("==================================================")
    print("   MEST Decumulation Simulator Demonstration      ")
    print("==================================================\n")

    # 1. Load historical data
    csv_path = Path("data") / "historical_regimes.csv"
    print(f"Loading historical economic data from {csv_path}...")
    start_time = time.perf_counter()
    hist_df = load_historical_data(csv_path)
    load_time = time.perf_counter() - start_time
    print(f"Loaded {len(hist_df)} historical months in {load_time:.4f} seconds.\n")

    # Define a realistic retirement scenario:
    # - Start with $1,000,000.
    # - Spend $8,000/month for 5 years (early retirement bridge period).
    # - Spend $4,000/month after the bridge (Social Security/pensions kick in).
    # - Test over 30 years (360 months).
    starting_principal = 1_000_000.0
    bridge_duration = 60
    bridge_spend = 8_000.0
    post_bridge_spend = 4_000.0
    duration_months = 360
    num_paths = 10_000

    print("--- Portfolio Strategy Configuration ---")
    print(f"Starting Principal:     ${starting_principal:,.2f}")
    print(f"Simulation Horizon:     {duration_months} months ({duration_months // 12} years)")
    print(f"Bridge Period Spend:    ${bridge_spend:,.2f}/month for first {bridge_duration} months")
    print(f"Post-Bridge Spend:      ${post_bridge_spend:,.2f}/month")
    print(f"Number of Paths:        {num_paths:,}\n")

    # 2. Run Stochastic (Monte Carlo) Simulation
    stochastic_config = SimulationConfig(
        starting_principal=starting_principal,
        bridge_duration_months=bridge_duration,
        bridge_monthly_withdrawal=bridge_spend,
        post_bridge_monthly_withdrawal=post_bridge_spend,
        simulation_duration_months=duration_months,
        simulation_mode="stochastic",
        mean_return_annual=0.07,  # 7% annual average
        volatility_annual=0.15,   # 15% annual volatility (standard stock volatility)
        inflation_annual=0.03,    # 3% annual inflation
        num_paths=num_paths,
        seed=101
    )

    print("Running STOCHASTIC (Monte Carlo) Simulation...")
    start_time = time.perf_counter()
    stoch_res = run_simulation(stochastic_config)
    stoch_time = time.perf_counter() - start_time
    print(f"Completed in {stoch_time:.4f} seconds.")
    print(f"  Success Probability (Did not hit $0): {stoch_res.success_probability * 100:.2f}%")
    print(f"  Median Ending Balance (50th percentile):  ${stoch_res.median_ending_balance:,.2f}")
    print(f"  Worst-Case Ending Balance (10th percentile): ${stoch_res.percentile_10th_ending_balance:,.2f}")
    print(f"  Best-Case Ending Balance (90th percentile):  ${stoch_res.percentile_90th_ending_balance:,.2f}")
    if stoch_res.success_probability < 1.0:
        print(f"  Average Month of Failure (for failed paths): Month {stoch_res.average_failure_month:.1f}")
    print()

    # 3. Run Historical Bootstrap Simulation
    bootstrap_config = SimulationConfig(
        starting_principal=starting_principal,
        bridge_duration_months=bridge_duration,
        bridge_monthly_withdrawal=bridge_spend,
        post_bridge_monthly_withdrawal=post_bridge_spend,
        simulation_duration_months=duration_months,
        simulation_mode="historical_bootstrap",
        mean_return_annual=0.0,  # Unused in bootstrap
        volatility_annual=0.0,   # Unused in bootstrap
        inflation_annual=0.0,    # Unused in bootstrap
        num_paths=num_paths,
        seed=101
    )

    print("Running HISTORICAL BOOTSTRAP Simulation (60/40 Equity/Bond Mix)...")
    start_time = time.perf_counter()
    boot_res = run_simulation(bootstrap_config, historical_df=hist_df)
    boot_time = time.perf_counter() - start_time
    print(f"Completed in {boot_time:.4f} seconds.")
    print(f"  Success Probability (Did not hit $0): {boot_res.success_probability * 100:.2f}%")
    print(f"  Median Ending Balance (50th percentile):  ${boot_res.median_ending_balance:,.2f}")
    print(f"  Worst-Case Ending Balance (10th percentile): ${boot_res.percentile_10th_ending_balance:,.2f}")
    print(f"  Best-Case Ending Balance (90th percentile):  ${boot_res.percentile_90th_ending_balance:,.2f}")
    if boot_res.success_probability < 1.0:
        print(f"  Average Month of Failure (for failed paths): Month {boot_res.average_failure_month:.1f}")
    print("\n==================================================")


if __name__ == "__main__":
    main()
