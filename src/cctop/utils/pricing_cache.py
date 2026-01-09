"""Cache management for dynamic pricing data."""

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

try:
    from platformdirs import user_cache_dir
except ImportError:
    # Fallback if platformdirs not available
    def user_cache_dir(app_name: str, app_author: str = None) -> str:
        """Simple fallback for cache directory."""
        return str(Path.home() / ".cache" / app_name)


logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 24


def get_cache_path() -> Path:
    """Get the path to the pricing cache file.

    Returns:
        Path: Path to pricing cache JSON file (~/.cache/cctop/pricing.json)
    """
    cache_dir = Path(user_cache_dir("cctop", "anthropic"))
    return cache_dir / "pricing.json"


def is_cache_valid() -> bool:
    """Check if cache exists and is not expired.

    Returns:
        bool: True if cache exists and is within TTL, False otherwise
    """
    cache_path = get_cache_path()

    if not cache_path.exists():
        return False

    try:
        with open(cache_path, "r") as f:
            data = json.load(f)

        fetched_at_str = data.get("fetched_at")
        if not fetched_at_str:
            return False

        fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
        ttl_hours = data.get("ttl_hours", CACHE_TTL_HOURS)
        expiry_time = fetched_at + timedelta(hours=ttl_hours)

        return datetime.now(timezone.utc) < expiry_time

    except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
        logger.debug(f"Cache validation failed: {e}")
        return False


def load_from_cache() -> Optional[dict]:
    """Load pricing data from cache if valid.

    Returns:
        dict: Pricing data with structure:
            {
                "claude-sonnet-4-5": {
                    "input": Decimal("0.000003"),
                    "output": Decimal("0.000015"),
                    "cache_creation": Decimal("0.00000375"),
                    "cache_read": Decimal("0.0000003")
                },
                ...
            }
        None if cache is expired, missing, or corrupted
    """
    cache_path = get_cache_path()

    if not cache_path.exists():
        logger.debug(f"Cache file not found: {cache_path}")
        return None

    try:
        with open(cache_path, "r") as f:
            data = json.load(f)

        # Verify cache structure
        if "version" not in data or "fetched_at" not in data or "pricing" not in data:
            logger.warning("Cache file has invalid structure")
            return None

        # Check TTL
        fetched_at_str = data["fetched_at"]
        fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
        ttl_hours = data.get("ttl_hours", CACHE_TTL_HOURS)
        expiry_time = fetched_at + timedelta(hours=ttl_hours)

        if datetime.now(timezone.utc) >= expiry_time:
            logger.info(f"Cache expired (fetched {fetched_at}, TTL {ttl_hours}h)")
            return None

        # Convert JSON strings to Decimal
        pricing_data = {}
        for model, rates in data["pricing"].items():
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

        if not pricing_data:
            logger.warning("No valid pricing data found in cache")
            return None

        logger.info(
            f"Loaded {len(pricing_data)} models from cache (fetched {fetched_at})"
        )
        return pricing_data

    except json.JSONDecodeError as e:
        logger.error(f"Cache file is corrupted (JSON parse error): {e}")
        return None
    except (OSError, IOError) as e:
        logger.error(f"Failed to read cache file: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading cache: {e}")
        return None


def save_to_cache(pricing_data: dict) -> bool:
    """Save pricing data to cache with timestamp.

    Args:
        pricing_data: Pricing dictionary with Decimal values

    Returns:
        bool: True if saved successfully, False otherwise
    """
    cache_path = get_cache_path()

    try:
        # Create cache directory if it doesn't exist
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Decimal to strings for JSON serialization
        pricing_json = {}
        for model, rates in pricing_data.items():
            pricing_json[model] = {
                "input": str(rates["input"]),
                "output": str(rates["output"]),
                "cache_creation": str(rates["cache_creation"]),
                "cache_read": str(rates["cache_read"]),
            }

        # Create cache structure
        cache_data = {
            "version": "1.0",
            "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "ttl_hours": CACHE_TTL_HOURS,
            "pricing": pricing_json,
        }

        # Atomic write: write to temp file then rename
        temp_path = cache_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        # Atomic rename
        temp_path.replace(cache_path)

        logger.info(f"Saved {len(pricing_data)} models to cache: {cache_path}")
        return True

    except (OSError, IOError) as e:
        logger.error(f"Failed to write cache file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving cache: {e}")
        return False
