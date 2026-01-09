"""Tests for pricing cache management."""

import json
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.cctop.utils.pricing_cache import (
    get_cache_path,
    is_cache_valid,
    load_from_cache,
    save_to_cache,
    CACHE_TTL_HOURS,
)


@pytest.fixture
def sample_pricing_data():
    """Sample pricing data for testing."""
    return {
        "claude-sonnet-4-5": {
            "input": Decimal("0.000003"),
            "output": Decimal("0.000015"),
            "cache_creation": Decimal("0.00000375"),
            "cache_read": Decimal("0.0000003"),
        },
        "claude-opus-4-5": {
            "input": Decimal("0.000005"),
            "output": Decimal("0.000025"),
            "cache_creation": Decimal("0.00000625"),
            "cache_read": Decimal("0.0000005"),
        },
    }


@pytest.fixture
def mock_cache_path(tmp_path, monkeypatch):
    """Mock cache path to use temporary directory."""
    cache_file = tmp_path / "pricing.json"

    def mock_get_cache_path():
        return cache_file

    monkeypatch.setattr("src.cctop.utils.pricing_cache.get_cache_path", mock_get_cache_path)
    return cache_file


def test_get_cache_path():
    """Test that cache path is in user cache directory."""
    cache_path = get_cache_path()
    assert cache_path.name == "pricing.json"
    assert "cctop" in str(cache_path)


def test_save_to_cache(mock_cache_path, sample_pricing_data):
    """Test saving pricing data to cache."""
    result = save_to_cache(sample_pricing_data)

    assert result is True
    assert mock_cache_path.exists()

    # Verify JSON structure
    with open(mock_cache_path, 'r') as f:
        data = json.load(f)

    assert data["version"] == "1.0"
    assert "fetched_at" in data
    assert data["ttl_hours"] == CACHE_TTL_HOURS
    assert "pricing" in data
    assert "claude-sonnet-4-5" in data["pricing"]
    assert data["pricing"]["claude-sonnet-4-5"]["input"] == "0.000003"
    assert data["pricing"]["claude-opus-4-5"]["output"] == "0.000025"


def test_load_from_cache_valid(mock_cache_path, sample_pricing_data):
    """Test loading valid cache data."""
    # First save data
    save_to_cache(sample_pricing_data)

    # Then load it
    loaded_data = load_from_cache()

    assert loaded_data is not None
    assert len(loaded_data) == 2
    assert "claude-sonnet-4-5" in loaded_data
    assert loaded_data["claude-sonnet-4-5"]["input"] == Decimal("0.000003")
    assert loaded_data["claude-opus-4-5"]["output"] == Decimal("0.000025")


def test_load_from_cache_missing(mock_cache_path):
    """Test loading when cache file doesn't exist."""
    result = load_from_cache()
    assert result is None


def test_load_from_cache_expired(mock_cache_path, sample_pricing_data):
    """Test loading expired cache."""
    # Create cache with old timestamp
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS + 1))

    cache_data = {
        "version": "1.0",
        "fetched_at": old_timestamp.isoformat().replace('+00:00', 'Z'),
        "ttl_hours": CACHE_TTL_HOURS,
        "pricing": {
            "claude-sonnet-4-5": {
                "input": "0.000003",
                "output": "0.000015",
                "cache_creation": "0.00000375",
                "cache_read": "0.0000003"
            }
        }
    }

    with open(mock_cache_path, 'w') as f:
        json.dump(cache_data, f)

    result = load_from_cache()
    assert result is None


def test_load_from_cache_corrupted(mock_cache_path):
    """Test loading corrupted JSON file."""
    mock_cache_path.write_text("{ this is not valid JSON }")

    result = load_from_cache()
    assert result is None


def test_load_from_cache_invalid_structure(mock_cache_path):
    """Test loading cache with missing required fields."""
    # Missing "pricing" field
    cache_data = {
        "version": "1.0",
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

    with open(mock_cache_path, 'w') as f:
        json.dump(cache_data, f)

    result = load_from_cache()
    assert result is None


def test_load_from_cache_invalid_pricing_data(mock_cache_path):
    """Test loading cache with invalid pricing values."""
    cache_data = {
        "version": "1.0",
        "fetched_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "ttl_hours": CACHE_TTL_HOURS,
        "pricing": {
            "claude-sonnet-4-5": {
                "input": "not_a_number",
                "output": "0.000015",
                "cache_creation": "0.00000375",
                "cache_read": "0.0000003"
            }
        }
    }

    with open(mock_cache_path, 'w') as f:
        json.dump(cache_data, f)

    result = load_from_cache()
    # Should return None because no valid models
    assert result is None


def test_is_cache_valid_fresh(mock_cache_path, sample_pricing_data):
    """Test cache validity check for fresh cache."""
    save_to_cache(sample_pricing_data)
    assert is_cache_valid() is True


def test_is_cache_valid_missing(mock_cache_path):
    """Test cache validity check when file missing."""
    assert is_cache_valid() is False


def test_is_cache_valid_expired(mock_cache_path):
    """Test cache validity check for expired cache."""
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS + 1))

    cache_data = {
        "version": "1.0",
        "fetched_at": old_timestamp.isoformat().replace('+00:00', 'Z'),
        "ttl_hours": CACHE_TTL_HOURS,
        "pricing": {}
    }

    with open(mock_cache_path, 'w') as f:
        json.dump(cache_data, f)

    assert is_cache_valid() is False


def test_cache_directory_creation(tmp_path, monkeypatch, sample_pricing_data):
    """Test that cache directory is created if it doesn't exist."""
    cache_dir = tmp_path / "nested" / "cache" / "dir"
    cache_file = cache_dir / "pricing.json"

    def mock_get_cache_path():
        return cache_file

    monkeypatch.setattr("src.cctop.utils.pricing_cache.get_cache_path", mock_get_cache_path)

    assert not cache_dir.exists()

    result = save_to_cache(sample_pricing_data)

    assert result is True
    assert cache_dir.exists()
    assert cache_file.exists()


def test_save_to_cache_atomic_write(mock_cache_path, sample_pricing_data):
    """Test that save uses atomic write pattern (.tmp then rename)."""
    result = save_to_cache(sample_pricing_data)

    assert result is True
    assert mock_cache_path.exists()

    # Temp file should not exist after successful write
    temp_file = mock_cache_path.with_suffix('.tmp')
    assert not temp_file.exists()


def test_round_trip(mock_cache_path, sample_pricing_data):
    """Test save and load round trip preserves data."""
    # Save
    save_result = save_to_cache(sample_pricing_data)
    assert save_result is True

    # Load
    loaded_data = load_from_cache()
    assert loaded_data is not None

    # Verify all data matches
    for model in sample_pricing_data:
        assert model in loaded_data
        for rate_type in ["input", "output", "cache_creation", "cache_read"]:
            assert loaded_data[model][rate_type] == sample_pricing_data[model][rate_type]
