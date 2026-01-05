from decimal import Decimal

PRICING = {
    "claude-sonnet-4-5": {
        "input": Decimal("0.000003"),
        "output": Decimal("0.000015"),
        "cache_creation": Decimal("0.00000375"),
        "cache_read": Decimal("0.0000003"),
    },
    "claude-opus-4-5": {
        "input": Decimal("0.000015"),
        "output": Decimal("0.000075"),
        "cache_creation": Decimal("0.00001875"),
        "cache_read": Decimal("0.0000015"),
    },
    "claude-3-5-sonnet": {
        "input": Decimal("0.000003"),
        "output": Decimal("0.000015"),
        "cache_creation": Decimal("0.00000375"),
        "cache_read": Decimal("0.0000003"),
    },
    "claude-3-opus": {
        "input": Decimal("0.000015"),
        "output": Decimal("0.000075"),
        "cache_creation": Decimal("0.00001875"),
        "cache_read": Decimal("0.0000015"),
    },
    "claude-3-5-haiku": {
        "input": Decimal("0.0000008"),
        "output": Decimal("0.000004"),
        "cache_creation": Decimal("0.000001"),
        "cache_read": Decimal("0.00000008"),
    },
    "claude-3-haiku": {
        "input": Decimal("0.00000025"),
        "output": Decimal("0.00000125"),
        "cache_creation": Decimal("0.0000003"),
        "cache_read": Decimal("0.00000003"),
    },
}

DEFAULT_PRICING = {
    "input": Decimal("0.000003"),
    "output": Decimal("0.000015"),
    "cache_creation": Decimal("0.00000375"),
    "cache_read": Decimal("0.0000003"),
}


def normalize_model_name(model: str) -> str:
    model_lower = model.lower()

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
    normalized = normalize_model_name(model)
    return PRICING.get(normalized, DEFAULT_PRICING)


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> Decimal:
    pricing = get_pricing(model)

    input_cost = Decimal(input_tokens) * pricing["input"]
    output_cost = Decimal(output_tokens) * pricing["output"]
    cache_creation_cost = Decimal(cache_creation_tokens) * pricing["cache_creation"]
    cache_read_cost = Decimal(cache_read_tokens) * pricing["cache_read"]

    total = input_cost + output_cost + cache_creation_cost + cache_read_cost

    return total.quantize(Decimal("0.000001"))
