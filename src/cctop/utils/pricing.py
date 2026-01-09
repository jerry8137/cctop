"""Pricing utilities for calculating Claude API costs."""

import json
import logging
from decimal import Decimal
from pathlib import Path

from . import pricing_cache
from . import pricing_fetcher

logger = logging.getLogger(__name__)

# Module-level state for pricing initialization
_PRICING_INITIALIZED = False
_PRICING_SOURCE = "unknown"  # "fetched", "cached", "bundled"

# Dynamic pricing data (populated by initialize_pricing())
PRICING = {}

# Default pricing (used as last resort fallback)
DEFAULT_PRICING = {
    "input": Decimal("0.000003"),
    "output": Decimal("0.000015"),
    "cache_creation": Decimal("0.00000375"),
    "cache_read": Decimal("0.0000003"),
}


def _convert_json_to_pricing(pricing_json: dict) -> dict:
    """Convert JSON pricing data (strings) to internal format (Decimals).

    Args:
        pricing_json: Pricing data with string values

    Returns:
        dict: Pricing data with Decimal values
    """
    pricing_data = {}
    for model, rates in pricing_json.items():
        try:
            pricing_data[model] = {
                "input": Decimal(rates["input"]),
                "output": Decimal(rates["output"]),
                "cache_creation": Decimal(rates["cache_creation"]),
                "cache_read": Decimal(rates["cache_read"]),
            }
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid pricing data for model {model}: {e}")
            continue
    return pricing_data


def _load_bundled_pricing() -> dict:
    """Load bundled pricing from package data.

    Returns:
        dict: Bundled pricing data with Decimal values
    """
    try:
        bundled_file = Path(__file__).parent / "bundled_pricing.json"
        with open(bundled_file, 'r') as f:
            data = json.load(f)
            return _convert_json_to_pricing(data['pricing'])
    except (OSError, IOError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to load bundled pricing: {e}")
        return {}


def initialize_pricing(offline_mode: bool = False) -> str:
    """Initialize pricing data from fetch/cache/bundled sources.

    This function implements a three-tier fallback strategy:
    1. Fetch from LiteLLM API (unless offline_mode=True)
    2. Load from local cache (~/.cache/cctop/pricing.json)
    3. Load from bundled pricing file

    Args:
        offline_mode: If True, skip network fetch and use cache/bundled only

    Returns:
        str: Pricing source used ("fetched", "cached", "bundled")
    """
    global PRICING, _PRICING_INITIALIZED, _PRICING_SOURCE

    if _PRICING_INITIALIZED:
        logger.debug(f"Pricing already initialized (source: {_PRICING_SOURCE})")
        return _PRICING_SOURCE

    # Step 1: Try fetch from LiteLLM (unless offline)
    if not offline_mode:
        logger.debug("Attempting to fetch pricing from LiteLLM...")
        fetched = pricing_fetcher.fetch_litellm_pricing()
        if fetched:
            PRICING.update(fetched)
            pricing_cache.save_to_cache(fetched)
            _PRICING_SOURCE = "fetched"
            _PRICING_INITIALIZED = True
            logger.info(f"Initialized pricing with {len(PRICING)} models from LiteLLM")
            return _PRICING_SOURCE

    # Step 2: Try load from cache
    logger.debug("Attempting to load pricing from cache...")
    cached = pricing_cache.load_from_cache()
    if cached:
        PRICING.update(cached)
        _PRICING_SOURCE = "cached"
        _PRICING_INITIALIZED = True
        logger.info(f"Initialized pricing with {len(PRICING)} models from cache")
        return _PRICING_SOURCE

    # Step 3: Load from bundled pricing
    logger.debug("Loading pricing from bundled file...")
    bundled = _load_bundled_pricing()
    if bundled:
        PRICING.update(bundled)
    else:
        logger.warning("Failed to load bundled pricing, PRICING dict may be incomplete")

    _PRICING_SOURCE = "bundled"
    _PRICING_INITIALIZED = True
    logger.info(f"Initialized pricing with {len(PRICING)} models from bundled file")
    return _PRICING_SOURCE


def normalize_model_name(model: str) -> str:
    """Normalize model names to standard pricing keys.

    Args:
        model: Raw model identifier from API

    Returns:
        str: Normalized model name for pricing lookup
    """
    model_lower = model.lower()

    # Strip provider prefixes (e.g., "anthropic.", "bedrock/")
    model_lower = model_lower.replace("anthropic.", "").replace("bedrock/", "")

    # Strip version suffixes (e.g., "-v1:0", "-v2:0")
    if "-v" in model_lower:
        model_lower = model_lower.split("-v")[0]

    # Match to Claude model families
    if "opus-4" in model_lower or "opus-4-5" in model_lower:
        return "claude-opus-4-5"
    elif "sonnet-4" in model_lower or "sonnet-4-5" in model_lower:
        return "claude-sonnet-4-5"
    elif "3-5-sonnet" in model_lower or "3.5-sonnet" in model_lower:
        return "claude-3-5-sonnet"
    elif "3-opus" in model_lower or "3.0-opus" in model_lower:
        return "claude-3-opus"
    elif "3-5-haiku" in model_lower or "3.5-haiku" in model_lower:
        return "claude-3-5-haiku"
    elif "3-haiku" in model_lower or "3.0-haiku" in model_lower:
        return "claude-3-haiku"

    return model


def get_pricing(model: str) -> dict:
    """Get pricing information for a specific model.

    Args:
        model: Model identifier

    Returns:
        dict: Pricing dictionary with rates for input, output, cache_creation, cache_read
    """
    normalized = normalize_model_name(model)
    return PRICING.get(normalized, DEFAULT_PRICING)


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> Decimal:
    """Calculate total cost based on token usage.

    Args:
        model: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cache_creation_tokens: Number of cache creation tokens (default: 0)
        cache_read_tokens: Number of cache read tokens (default: 0)

    Returns:
        Decimal: Total cost in USD
    """
    pricing = get_pricing(model)

    input_cost = Decimal(input_tokens) * pricing["input"]
    output_cost = Decimal(output_tokens) * pricing["output"]
    cache_creation_cost = Decimal(cache_creation_tokens) * pricing["cache_creation"]
    cache_read_cost = Decimal(cache_read_tokens) * pricing["cache_read"]

    total = input_cost + output_cost + cache_creation_cost + cache_read_cost

    return total.quantize(Decimal("0.000001"))
