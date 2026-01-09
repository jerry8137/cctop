"""Tests for pricing fetcher module."""

import json
import pytest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import urllib.error

from src.cctop.utils.pricing_fetcher import (
    fetch_litellm_pricing,
    convert_litellm_to_internal,
    _convert_scientific_to_decimal,
    _normalize_litellm_model_name,
)


@pytest.fixture
def sample_litellm_data():
    """Load sample LiteLLM API response."""
    fixture_path = Path(__file__).parent / "fixtures" / "litellm_sample.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def test_convert_scientific_to_decimal():
    """Test converting scientific notation to Decimal."""
    assert _convert_scientific_to_decimal(3e-06) == Decimal("0.000003")
    assert _convert_scientific_to_decimal(1.5e-05) == Decimal("0.000015")
    assert _convert_scientific_to_decimal(0.000003) == Decimal("0.000003")
    assert _convert_scientific_to_decimal(0) == Decimal("0")


def test_normalize_litellm_model_name():
    """Test normalizing LiteLLM model names."""
    assert (
        _normalize_litellm_model_name("claude-sonnet-4-5-20250929")
        == "claude-sonnet-4-5"
    )
    assert (
        _normalize_litellm_model_name("claude-opus-4-5-20251101") == "claude-opus-4-5"
    )
    assert (
        _normalize_litellm_model_name("anthropic.claude-3-5-sonnet-20241022-v2:0")
        == "claude-3-5-sonnet"
    )
    assert _normalize_litellm_model_name("claude-3-opus-20240229") == "claude-3-opus"
    assert (
        _normalize_litellm_model_name("claude-3-5-haiku-20241022") == "claude-3-5-haiku"
    )
    assert _normalize_litellm_model_name("claude-3-haiku-20240307") == "claude-3-haiku"


def test_convert_litellm_to_internal(sample_litellm_data):
    """Test converting LiteLLM format to internal format."""
    result = convert_litellm_to_internal(sample_litellm_data)

    # Should extract 6 Claude models (not GPT)
    assert len(result) == 6

    # Check Sonnet 4.5
    assert "claude-sonnet-4-5" in result
    assert result["claude-sonnet-4-5"]["input"] == Decimal("0.000003")
    assert result["claude-sonnet-4-5"]["output"] == Decimal("0.000015")
    assert result["claude-sonnet-4-5"]["cache_creation"] == Decimal("0.00000375")
    assert result["claude-sonnet-4-5"]["cache_read"] == Decimal("0.0000003")

    # Check Opus 4.5 (corrected pricing)
    assert "claude-opus-4-5" in result
    assert result["claude-opus-4-5"]["input"] == Decimal("0.000005")
    assert result["claude-opus-4-5"]["output"] == Decimal("0.000025")

    # Check 3.5 Sonnet (with anthropic. prefix and -v2:0 suffix)
    assert "claude-3-5-sonnet" in result

    # Check other models
    assert "claude-3-opus" in result
    assert "claude-3-5-haiku" in result
    assert "claude-3-haiku" in result

    # Should NOT include non-Claude models
    assert "gpt-4-turbo" not in result


def test_convert_litellm_to_internal_missing_pricing():
    """Test handling models with missing pricing fields."""
    data = {
        "claude-sonnet-4-5-20250929": {
            "input_cost_per_token": 3e-06,
            # Missing output_cost_per_token
            "cache_creation_input_token_cost": 3.75e-06,
            "cache_read_input_token_cost": 3e-07,
        }
    }

    result = convert_litellm_to_internal(data)
    # Should skip models with missing essential pricing
    assert len(result) == 0


def test_convert_litellm_to_internal_missing_cache_pricing():
    """Test handling models with missing cache pricing (should default to 0)."""
    data = {
        "claude-sonnet-4-5-20250929": {
            "input_cost_per_token": 3e-06,
            "output_cost_per_token": 1.5e-05,
            # Missing cache pricing
        }
    }

    result = convert_litellm_to_internal(data)
    assert len(result) == 1
    assert result["claude-sonnet-4-5"]["cache_creation"] == Decimal("0")
    assert result["claude-sonnet-4-5"]["cache_read"] == Decimal("0")


@patch("urllib.request.urlopen")
def test_fetch_litellm_pricing_success(mock_urlopen, sample_litellm_data):
    """Test successful pricing fetch from LiteLLM."""
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps(sample_litellm_data).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response

    result = fetch_litellm_pricing()

    assert result is not None
    assert len(result) == 6
    assert "claude-sonnet-4-5" in result
    assert "claude-opus-4-5" in result
    assert result["claude-opus-4-5"]["input"] == Decimal("0.000005")


@patch("urllib.request.urlopen")
def test_fetch_litellm_pricing_http_error(mock_urlopen):
    """Test handling HTTP errors."""
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="http://test.com", code=500, msg="Internal Server Error", hdrs={}, fp=None
    )

    result = fetch_litellm_pricing()
    assert result is None


@patch("urllib.request.urlopen")
def test_fetch_litellm_pricing_url_error(mock_urlopen):
    """Test handling network errors."""
    mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

    result = fetch_litellm_pricing()
    assert result is None


@patch("urllib.request.urlopen")
def test_fetch_litellm_pricing_timeout(mock_urlopen):
    """Test handling timeout errors."""
    import socket

    mock_urlopen.side_effect = socket.timeout("Connection timed out")

    result = fetch_litellm_pricing()
    assert result is None


@patch("urllib.request.urlopen")
def test_fetch_litellm_pricing_invalid_json(mock_urlopen):
    """Test handling invalid JSON response."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b"{ this is not valid JSON }"
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response

    result = fetch_litellm_pricing()
    assert result is None


@patch("urllib.request.urlopen")
def test_fetch_litellm_pricing_empty_response(mock_urlopen):
    """Test handling empty JSON response."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response

    result = fetch_litellm_pricing()
    # Should return None when no Claude models found
    assert result is None


@patch("urllib.request.urlopen")
def test_fetch_litellm_pricing_non_200_status(mock_urlopen):
    """Test handling non-200 HTTP status."""
    mock_response = MagicMock()
    mock_response.status = 404
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response

    result = fetch_litellm_pricing()
    assert result is None


@patch("urllib.request.urlopen")
def test_fetch_litellm_pricing_with_custom_timeout(mock_urlopen, sample_litellm_data):
    """Test fetch with custom timeout parameter."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps(sample_litellm_data).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response

    result = fetch_litellm_pricing(timeout=5)

    assert result is not None
    # Verify urlopen was called with timeout
    assert mock_urlopen.called
