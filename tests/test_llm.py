"""Unit tests for the orchestration and LLM layer of MEST."""

import pytest

from mest.llm.classifier import classify_scenario


def test_classify_scenario_stagflation() -> None:
    """Verifies return < 4% and inflation > 4% yields Stagflation."""
    assert classify_scenario(mean_return=0.03, volatility=0.12, inflation=0.05) == "Stagflation"
    # Border check: exactly 0.039 and 0.041
    assert classify_scenario(mean_return=0.039, volatility=0.10, inflation=0.041) == "Stagflation"


def test_classify_scenario_disinflationary_growth() -> None:
    """Verifies return > 10% and inflation < 2% yields Disinflationary Growth."""
    assert classify_scenario(mean_return=0.12, volatility=0.15, inflation=0.01) == "Disinflationary Growth"
    # Border check: exactly 0.101 and 0.019
    assert classify_scenario(mean_return=0.101, volatility=0.10, inflation=0.019) == "Disinflationary Growth"


def test_classify_scenario_high_volatility_stress() -> None:
    """Verifies volatility > 20% yields High Volatility Stress Scenario."""
    assert classify_scenario(mean_return=0.05, volatility=0.25, inflation=0.03) == "High Volatility Stress Scenario"
    # Border check
    assert classify_scenario(mean_return=0.08, volatility=0.21, inflation=0.035) == "High Volatility Stress Scenario"


def test_classify_scenario_severe_market_downturn() -> None:
    """Verifies return < 0% yields Severe Market Downturn."""
    assert classify_scenario(mean_return=-0.02, volatility=0.15, inflation=0.02) == "Severe Market Downturn"


def test_classify_scenario_mixed_custom() -> None:
    """Verifies default case yields Mixed Custom Scenario."""
    assert classify_scenario(mean_return=0.06, volatility=0.12, inflation=0.025) == "Mixed Custom Scenario"


def test_classify_scenario_order_priority() -> None:
    """Verifies that scenario rules are evaluated in correct order.
    
    1. return < 0.04 and inflation > 0.04 (Stagflation)
    2. return > 0.10 and inflation < 0.02 (Disinflationary Growth)
    3. volatility > 0.20 (High Volatility Stress)
    4. return < 0.0 (Severe Market Downturn)
    """
    # Case A: volatility > 0.20 AND return < 0.0.
    # Volatility takes priority over return downturn, returning High Volatility Stress.
    assert classify_scenario(mean_return=-0.05, volatility=0.25, inflation=0.02) == "High Volatility Stress Scenario"

    # Case B: return < 0.04 and inflation > 0.04 AND return < 0.0.
    # Stagflation takes priority over return downturn, returning Stagflation.
    assert classify_scenario(mean_return=-0.01, volatility=0.15, inflation=0.05) == "Stagflation"
