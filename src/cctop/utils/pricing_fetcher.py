"""Fetch pricing data from LiteLLM API."""

import json
import logging
import urllib.request
import urllib.error
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)

LITELLM_PRICING_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
TIMEOUT_SECONDS = 10


def _convert_scientific_to_decimal(value: float) -> Decimal:
    """Convert scientific notation float to Decimal.

    Args:
        value: Float value (may be in scientific notation like 3e-06)

    Returns:
        Decimal: Precise decimal representation
    """
    # Convert to string first to maintain precision
    return Decimal(str(value))


def _normalize_litellm_model_name(model_name: str) -> str:
    """Normalize LiteLLM model names to internal format.

    Args:
        model_name: LiteLLM model identifier (e.g., "anthropic.claude-3-5-sonnet-20241022-v1:0")

    Returns:
        str: Normalized model name for internal use
    """
    model_lower = model_name.lower()

    # Strip provider prefixes
    model_lower = model_lower.replace("anthropic.", "").replace("bedrock/", "")

    # Strip version suffixes
    if "-v" in model_lower:
        model_lower = model_lower.split("-v")[0]

    # Match to Claude model families
    if "opus-4" in model_lower or ("opus" in model_lower and "4.5" in model_lower):
        return "claude-opus-4-5"
    elif "sonnet-4" in model_lower or (
        "sonnet" in model_lower and "4.5" in model_lower
    ):
        return "claude-sonnet-4-5"
    elif "3-5-sonnet" in model_lower or "3.5-sonnet" in model_lower:
        return "claude-3-5-sonnet"
    elif "3-opus" in model_lower or (
        "opus" in model_lower and "3" in model_lower and "4" not in model_lower
    ):
        return "claude-3-opus"
    elif (
        "3-5-haiku" in model_lower
        or "3.5-haiku" in model_lower
        or "haiku-4" in model_lower
    ):
        return "claude-3-5-haiku"
    elif "3-haiku" in model_lower or (
        "haiku" in model_lower and "3" in model_lower and "4" not in model_lower
    ):
        return "claude-3-haiku"

    return model_lower


def convert_litellm_to_internal(litellm_data: dict) -> dict:
    """Convert LiteLLM pricing format to internal format.

    Args:
        litellm_data: Raw LiteLLM API response with pricing data

    Returns:
        dict: Pricing data in internal format:
            {
                "claude-sonnet-4-5": {
                    "input": Decimal("0.000003"),
                    "output": Decimal("0.000015"),
                    "cache_creation": Decimal("0.00000375"),
                    "cache_read": Decimal("0.0000003")
                },
                ...
            }
    """
    internal_pricing = {}

    for model_name, model_data in litellm_data.items():
        # Only process Claude/Anthropic models
        if not any(
            keyword in model_name.lower() for keyword in ["claude", "anthropic"]
        ):
            continue

        try:
            # Extract pricing fields (LiteLLM uses different field names)
            input_cost = model_data.get("input_cost_per_token")
            output_cost = model_data.get("output_cost_per_token")
            cache_creation_cost = model_data.get("cache_creation_input_token_cost")
            cache_read_cost = model_data.get("cache_read_input_token_cost")

            # Skip if missing essential pricing
            if input_cost is None or output_cost is None:
                logger.debug(f"Skipping {model_name}: missing input/output pricing")
                continue

            # Normalize model name
            normalized_name = _normalize_litellm_model_name(model_name)

            # Convert to Decimal (handle scientific notation)
            pricing_entry = {
                "input": _convert_scientific_to_decimal(input_cost),
                "output": _convert_scientific_to_decimal(output_cost),
                "cache_creation": _convert_scientific_to_decimal(
                    cache_creation_cost or 0.0
                ),
                "cache_read": _convert_scientific_to_decimal(cache_read_cost or 0.0),
            }

            # Use the most specific/recent version if multiple exist
            # (e.g., prefer claude-sonnet-4-5-20250929 over older versions)
            if normalized_name not in internal_pricing:
                internal_pricing[normalized_name] = pricing_entry
                logger.debug(f"Added pricing for {normalized_name} from {model_name}")
            else:
                # If we already have this model, keep existing (assumes first is most recent)
                logger.debug(
                    f"Skipping duplicate {normalized_name} (already have pricing)"
                )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Invalid pricing data for {model_name}: {e}")
            continue

    return internal_pricing


def fetch_litellm_pricing(timeout: int = TIMEOUT_SECONDS) -> Optional[dict]:
    """Fetch pricing data from LiteLLM API.

    Args:
        timeout: HTTP request timeout in seconds (default: 10)

    Returns:
        dict: Pricing data in internal format, or None if fetch fails
    """
    try:
        logger.debug(f"Fetching pricing from {LITELLM_PRICING_URL}")

        # Create request with timeout
        req = urllib.request.Request(
            LITELLM_PRICING_URL, headers={"User-Agent": "cctop/0.2.0"}
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                logger.warning(f"LiteLLM API returned status {response.status}")
                return None

            # Read and parse JSON
            data = json.loads(response.read().decode("utf-8"))

            # Convert to internal format
            internal_pricing = convert_litellm_to_internal(data)

            if not internal_pricing:
                logger.warning("No Claude models found in LiteLLM data")
                return None

            logger.info(
                f"Fetched pricing for {len(internal_pricing)} Claude models from LiteLLM"
            )
            return internal_pricing

    except urllib.error.HTTPError as e:
        logger.warning(f"HTTP error fetching pricing: {e.code} {e.reason}")
        return None

    except urllib.error.URLError as e:
        logger.warning(f"Network error fetching pricing: {e.reason}")
        return None

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from LiteLLM: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error fetching pricing: {e}")
        return None
