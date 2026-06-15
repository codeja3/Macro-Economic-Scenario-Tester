"""Unit tests for the orchestration and LLM layer of MEST."""

import json
from unittest.mock import patch, MagicMock
import pytest
import requests

from mest.llm.classifier import classify_scenario
from mest.llm.orchestrator import generate_analysis_stream, decompose_query


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


def test_generate_analysis_stream_short_query() -> None:
    """Verifies that a short query (< 50 tokens) goes straight to CoT/SR generation."""
    # We mock requests.post to return a stream of chunks containing thought, reflection, and response.
    # We include prefix text before tags to test the yield of preceding buffer content.
    mock_chunks = [
        "Prefix text ", "<thought>", "Analyzing ", "parameters.", "</thought>",
        " Intermediate text ", "<reflection>", "No issues.", "</reflection>",
        " Extra text ", "<response>", "Strategy is safe.", "</response>"
    ]
    
    mock_resp = MagicMock()
    # iter_lines returns a list of byte strings
    lines = [json.dumps({"response": c, "done": False}).encode("utf-8") for c in mock_chunks]
    # Include an invalid json line to verify it is caught/ignored by raw_token_generator
    lines.insert(3, b"invalid json line string\n")
    lines.append(json.dumps({"response": "", "done": True}).encode("utf-8"))
    mock_resp.iter_lines.return_value = lines
    mock_resp.__enter__.return_value = mock_resp
    
    stats = {"success_probability": 0.95}
    
    with patch("requests.post", return_value=mock_resp) as mock_post:
        generator = generate_analysis_stream(prompt="Is 8% withdrawal safe?", stats=stats)
        results = list(generator)
        
        # Verify it called requests.post once
        mock_post.assert_called_once()
        
        # Verify the chunks are parsed into structured items
        thought_content = "".join([r["content"] for r in results if r["type"] == "thought"])
        reflection_content = "".join([r["content"] for r in results if r["type"] == "reflection"])
        response_content = "".join([r["content"] for r in results if r["type"] == "response"])
        
        assert "Analyzing parameters" in thought_content
        assert "No issues" in reflection_content
        # Response should contain the prefix text, intermediate text, extra text, and the response block
        assert "Prefix text" in response_content
        assert "Intermediate text" in response_content
        assert "Extra text" in response_content
        assert "Strategy is safe" in response_content


def test_generate_analysis_stream_long_query() -> None:
    """Verifies that a long query (> 50 tokens) is first decomposed into sub-questions."""
    # A query with > 50 words
    long_query = " ".join(["word"] * 55) + "?"
    
    # Side effect: first call returns decomposition, next two return stream
    def post_side_effect(url, json, **kwargs):
        # Check if this is a decomposition request (stream is False)
        if json.get("stream") is False:
            r = MagicMock()
            # We return a list containing an empty line, a digit dot list item, and a bullet list item
            r.json.return_value = {
                "response": "\n1. Sub-question 1?\n\n* Sub-question 2?\n"
            }
            return r
        else:
            # streaming response
            r = MagicMock()
            r.iter_lines.return_value = [
                json.dumps({"response": c, "done": False}).encode("utf-8")
                for c in ["<thought>", "think", "</thought>", "<response>", "ans", "</response>"]
            ]
            r.__enter__.return_value = r
            return r

    stats = {"success_probability": 0.8}
    
    with patch("requests.post", side_effect=post_side_effect) as mock_post:
        generator = generate_analysis_stream(prompt=long_query, stats=stats)
        results = list(generator)
        
        # Verify it called requests.post multiple times (1 for decomp, 2 for sub-questions)
        assert mock_post.call_count == 3
        
        # Verify that sub-question markers were yielded
        sub_questions = [r["content"] for r in results if r["type"] == "sub_question"]
        assert len(sub_questions) == 2
        assert "Sub-question 1?" in sub_questions[0]
        assert "Sub-question 2?" in sub_questions[1]


def test_generate_analysis_stream_fallback() -> None:
    """Verifies that if the LLM output does not contain xml tags, it defaults to response."""
    mock_chunks = ["Direct ", "answer ", "without ", "tags."]
    mock_resp = MagicMock()
    lines = [json.dumps({"response": c, "done": False}).encode("utf-8") for c in mock_chunks]
    lines.append(json.dumps({"response": "", "done": True}).encode("utf-8"))
    mock_resp.iter_lines.return_value = lines
    mock_resp.__enter__.return_value = mock_resp
    
    stats = {"success_probability": 0.9}
    
    with patch("requests.post", return_value=mock_resp):
        generator = generate_analysis_stream(prompt="Simple question", stats=stats)
        results = list(generator)
        
        # All output should be of type 'response'
        response_content = "".join([r["content"] for r in results if r["type"] == "response"])
        assert response_content == "Direct answer without tags."
        
        # No thoughts or reflections
        assert not any(r["type"] == "thought" for r in results)
        assert not any(r["type"] == "reflection" for r in results)


def test_generate_analysis_stream_connection_error() -> None:
    """Verifies that if connection to Ollama fails, it yields a graceful error response."""
    stats = {"success_probability": 0.85}
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError("Connection refused")):
        generator = generate_analysis_stream(prompt="Is my plan OK?", stats=stats)
        results = list(generator)
        
        # Verify we got a response chunk with the error message
        response_content = "".join([r["content"] for r in results if r["type"] == "response"])
        assert "Failed to connect" in response_content


def test_decompose_query_failure() -> None:
    """Verifies that if decomposition fails, it falls back to the original query."""
    with patch("requests.post", side_effect=Exception("Ollama down")):
        questions = decompose_query("Some very long prompt that exceeds fifty words " * 10)
        assert len(questions) == 1
        assert "Some very long prompt" in questions[0]


def test_decompose_query_no_numbered_list() -> None:
    """Verifies that if decomposition returns plain text instead of a list, it falls back."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "Just some plain text paragraph describing questions."}
    
    with patch("requests.post", return_value=mock_resp):
        questions = decompose_query("Some very long prompt that exceeds fifty words " * 10)
        # Should fallback to the original prompt
        assert len(questions) == 1
        assert "Some very long prompt" in questions[0]
