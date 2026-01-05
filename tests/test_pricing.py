import pytest
from decimal import Decimal
from src.cctop.utils.pricing import (
    normalize_model_name,
    get_pricing,
    calculate_cost,
)


def test_normalize_model_name():
    assert normalize_model_name("claude-sonnet-4-5-20250929") == "claude-sonnet-4-5"
    assert normalize_model_name("claude-opus-4-5-20251101") == "claude-opus-4-5"
    assert normalize_model_name("claude-3-5-sonnet-20241022") == "claude-3-5-sonnet"
    assert normalize_model_name("claude-3-opus-20240229") == "claude-3-opus"
    assert normalize_model_name("claude-3-5-haiku-20241022") == "claude-3-5-haiku"
    assert normalize_model_name("claude-3-haiku-20240307") == "claude-3-haiku"


def test_get_pricing():
    pricing = get_pricing("claude-sonnet-4-5-20250929")
    assert pricing['input'] == Decimal("0.000003")
    assert pricing['output'] == Decimal("0.000015")

    pricing_opus = get_pricing("claude-opus-4-5-20251101")
    assert pricing_opus['input'] == Decimal("0.000015")
    assert pricing_opus['output'] == Decimal("0.000075")


def test_calculate_cost():
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
