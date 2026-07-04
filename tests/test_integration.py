"""Integration tests for MEST.

This module tests the end-to-end integration between the data loader,
simulation core, deterministic classifier, and local LLM orchestrator.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import polars as pl
import pytest

from mest.core.data_loader import load_historical_data
from mest.core.simulator import SimulationConfig, run_simulation
from mest.llm.classifier import classify_scenario
from mest.llm.orchestrator import generate_analysis_stream


def test_integration_data_engine_and_classifier() -> None:
    """Verifies that the data loader feeds into the simulation core and classifier correctly."""
    # 1. Load real historical data
    csv_path = Path("data") / "historical_regimes.csv"
    assert csv_path.exists(), "Historical data CSV must exist for integration test."
    
    historical_df = load_historical_data(csv_path)
    assert isinstance(historical_df, pl.DataFrame)
    assert historical_df.height > 1000

    # 2. Configure and run a historical bootstrap simulation
    config = SimulationConfig(
        starting_principal=1_000_000.0,
        bridge_duration_months=60,
        bridge_monthly_withdrawal=8000.0,
        post_bridge_monthly_withdrawal=4000.0,
        simulation_duration_months=360,
        simulation_mode="historical_bootstrap",
        mean_return_annual=0.0,
        volatility_annual=0.0,
        inflation_annual=0.0,
        num_paths=1000,
        seed=101
    )
    
    results = run_simulation(config, historical_df=historical_df)
    assert 0.0 <= results.success_probability <= 1.0
    assert results.median_ending_balance >= 0.0
    assert results.percentile_10th_ending_balance >= 0.0
    assert results.percentile_90th_ending_balance >= results.median_ending_balance

    # 3. Classify a corresponding stochastic config to verify classifier parameters
    regime = classify_scenario(mean_return=0.07, volatility=0.12, inflation=0.03)
    assert regime == "Mixed Custom Scenario"


def test_integration_full_analyst_pipeline() -> None:
    """Verifies that simulation metrics pass into the orchestrator narrative stream seamlessly."""
    # Create realistic simulation results
    mock_stats = {
        "starting_principal": 1_000_000.0,
        "bridge_duration_months": 60,
        "bridge_monthly_withdrawal": 8000.0,
        "post_bridge_monthly_withdrawal": 4000.0,
        "simulation_duration_months": 360,
        "simulation_mode": "stochastic",
        "success_probability": 0.88,
        "median_ending_balance": 1500000.0,
        "percentile_10th_ending_balance": 0.0,
        "percentile_90th_ending_balance": 4200000.0,
        "average_failure_month": 240.0,
        "regime_classification": "Mixed Custom Scenario"
    }

    # Mock Ollama streaming response
    mock_chunks = [
        "Prefix text ", "<thought>", "Analyzing metrics.", "</thought>",
        " <reflection>", "Correct.", "</reflection>",
        " <response>", "Decumulation is viable.", "</response>"
    ]
    mock_resp = MagicMock()
    lines = [json.dumps({"response": c, "done": False}).encode("utf-8") for c in mock_chunks]
    lines.append(json.dumps({"response": "", "done": True}).encode("utf-8"))
    mock_resp.iter_lines.return_value = lines
    mock_resp.__enter__.return_value = mock_resp

    with patch("requests.post", return_value=mock_resp) as mock_post:
        # Run short query that triggers the stream_cot_sr pipeline directly
        generator = generate_analysis_stream(
            prompt="Is my decumulation bridge safe?",
            stats=mock_stats
        )
        chunks = list(generator)
        
        # Verify call parameters
        mock_post.assert_called_once()
        call_json = mock_post.call_args[1]["json"]
        assert "stream" in call_json
        assert call_json["stream"] is True
        assert "Analyzing metrics" in "".join([c["content"] for c in chunks if c["type"] == "thought"])
        assert "Decumulation is viable" in "".join([c["content"] for c in chunks if c["type"] == "response"])
