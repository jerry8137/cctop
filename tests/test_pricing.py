import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from src.cctop.utils.pricing import (
    normalize_model_name,
    get_pricing,
    calculate_cost,
    initialize_pricing,
    PRICING,
    _PRICING_INITIALIZED,
)


def test_normalize_model_name():
    assert normalize_model_name("claude-sonnet-4-5-20250929") == "claude-sonnet-4-5"
    assert normalize_model_name("claude-opus-4-5-20251101") == "claude-opus-4-5"
    assert normalize_model_name("claude-3-5-sonnet-20241022") == "claude-3-5-sonnet"
    assert normalize_model_name("claude-3-opus-20240229") == "claude-3-opus"
    assert normalize_model_name("claude-3-5-haiku-20241022") == "claude-3-5-haiku"
    assert normalize_model_name("claude-3-haiku-20240307") == "claude-3-haiku"


def test_normalize_model_name_with_prefixes():
    """Test normalization with provider prefixes and version suffixes."""
    assert normalize_model_name("anthropic.claude-3-5-sonnet-20241022-v2:0") == "claude-3-5-sonnet"
    assert normalize_model_name("bedrock/claude-opus-4-5-20251101") == "claude-opus-4-5"
    assert normalize_model_name("claude-sonnet-4-5-20250929-v1:0") == "claude-sonnet-4-5"


def test_get_pricing():
    # Initialize pricing first (uses bundled file)
    initialize_pricing(offline_mode=True)

    pricing = get_pricing("claude-sonnet-4-5-20250929")
    assert pricing['input'] == Decimal("0.000003")
    assert pricing['output'] == Decimal("0.000015")

    # Fixed: Opus 4.5 pricing should be $5/$25, not $15/$75
    pricing_opus = get_pricing("claude-opus-4-5-20251101")
    assert pricing_opus['input'] == Decimal("0.000005")
    assert pricing_opus['output'] == Decimal("0.000025")


def test_calculate_cost():
    # Initialize pricing first
    initialize_pricing(offline_mode=True)

    cost = calculate_cost(
        model="claude-sonnet-4-5-20250929",
        input_tokens=100,
        output_tokens=50,
        cache_creation_tokens=10,
        cache_read_tokens=5,
    )

    expected = (
        Decimal(100) * Decimal("0.000003") +
        Decimal(50) * Decimal("0.000015") +
        Decimal(10) * Decimal("0.00000375") +
        Decimal(5) * Decimal("0.0000003")
    )

    assert cost == expected.quantize(Decimal("0.000001"))


def test_calculate_cost_no_cache():
    # Initialize pricing first
    initialize_pricing(offline_mode=True)

    cost = calculate_cost(
        model="claude-sonnet-4-5-20250929",
        input_tokens=1000,
        output_tokens=500,
    )

    expected = (
        Decimal(1000) * Decimal("0.000003") +
        Decimal(500) * Decimal("0.000015")
    )

    assert cost == expected.quantize(Decimal("0.000001"))


def test_opus_pricing_fixed():
    """Test that Opus 4.5 pricing is corrected to $5/$25 (not $15/$75)."""
    # Initialize with bundled pricing
    initialize_pricing(offline_mode=True)

    pricing_opus = get_pricing("claude-opus-4-5")
    assert pricing_opus['input'] == Decimal("0.000005")
    assert pricing_opus['output'] == Decimal("0.000025")
    assert pricing_opus['cache_creation'] == Decimal("0.00000625")
    assert pricing_opus['cache_read'] == Decimal("0.0000005")


def test_initialize_pricing_offline_mode():
    """Test that offline mode uses bundled pricing."""
    # Reset module state
    import src.cctop.utils.pricing as pricing_module
    pricing_module._PRICING_INITIALIZED = False
    pricing_module.PRICING = {}

    source = initialize_pricing(offline_mode=True)

    assert source == "bundled"
    assert len(PRICING) > 0
    assert "claude-sonnet-4-5" in PRICING
    assert "claude-opus-4-5" in PRICING


@patch('src.cctop.utils.pricing.pricing_fetcher.fetch_litellm_pricing')
@patch('src.cctop.utils.pricing.pricing_cache.save_to_cache')
def test_initialize_pricing_fetch_success(mock_save, mock_fetch):
    """Test successful fetch from LiteLLM."""
    # Reset module state
    import src.cctop.utils.pricing as pricing_module
    pricing_module._PRICING_INITIALIZED = False
    pricing_module.PRICING = {}

    # Mock successful fetch
    mock_fetch.return_value = {
        "claude-sonnet-4-5": {
            "input": Decimal("0.000003"),
            "output": Decimal("0.000015"),
            "cache_creation": Decimal("0.00000375"),
            "cache_read": Decimal("0.0000003"),
        }
    }

    source = initialize_pricing(offline_mode=False)

    assert source == "fetched"
    assert mock_fetch.called
    assert mock_save.called
    assert "claude-sonnet-4-5" in PRICING


@patch('src.cctop.utils.pricing.pricing_fetcher.fetch_litellm_pricing')
@patch('src.cctop.utils.pricing.pricing_cache.load_from_cache')
def test_initialize_pricing_fallback_to_cache(mock_load_cache, mock_fetch):
    """Test fallback to cache when fetch fails."""
    # Reset module state
    import src.cctop.utils.pricing as pricing_module
    pricing_module._PRICING_INITIALIZED = False
    pricing_module.PRICING = {}

    # Mock fetch failure
    mock_fetch.return_value = None

    # Mock successful cache load
    mock_load_cache.return_value = {
        "claude-opus-4-5": {
            "input": Decimal("0.000005"),
            "output": Decimal("0.000025"),
            "cache_creation": Decimal("0.00000625"),
            "cache_read": Decimal("0.0000005"),
        }
    }

    source = initialize_pricing(offline_mode=False)

    assert source == "cached"
    assert mock_fetch.called
    assert mock_load_cache.called
    assert "claude-opus-4-5" in PRICING


def test_initialize_pricing_idempotent():
    """Test that initialize_pricing() can be called multiple times safely."""
    # Initialize once
    source1 = initialize_pricing(offline_mode=True)

    # Call again - should return same source without re-initializing
    source2 = initialize_pricing(offline_mode=True)

    # Both calls should return the same source
    assert source1 == source2
    # Should be one of the valid sources
    assert source2 in ["fetched", "cached", "bundled"]
