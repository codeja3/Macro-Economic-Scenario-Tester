"""Deterministic scenario classification for economic regimes.

This module provides rules to categorize macroeconomic configurations (return,
volatility, inflation) into recognized economic regimes.
"""


def classify_scenario(mean_return: float, volatility: float, inflation: float) -> str:
    """Classifies user parameters into a standard economic regime name.

    Args:
        mean_return: The annual mean return of the portfolio (as a decimal fraction).
        volatility: The annual volatility of the portfolio (as a decimal fraction).
        inflation: The annual inflation rate (as a decimal fraction).

    Returns:
        A string representing the name of the classified scenario.
    """
    # 1. Stagflation (low return, high inflation)
    if mean_return < 0.04 and inflation > 0.04:
        return "Stagflation"
    
    # 2. Disinflationary Growth (high return, low inflation)
    elif mean_return > 0.10 and inflation < 0.02:
        return "Disinflationary Growth"
    
    # 3. High Volatility Stress (excessive volatility)
    elif volatility > 0.20:
        return "High Volatility Stress Scenario"
    
    # 4. Severe Market Downturn (negative returns)
    elif mean_return < 0.0:
        return "Severe Market Downturn"
    
    # 5. Default mixed case
    else:
        return "Mixed Custom Scenario"
