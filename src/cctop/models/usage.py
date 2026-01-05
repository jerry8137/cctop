from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    timestamp: datetime
    model: str
    request_id: str = ""

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens +
            self.output_tokens +
            self.cache_creation_tokens +
            self.cache_read_tokens
        )

    def calculate_cost(self) -> Decimal:
        from ..utils.pricing import calculate_cost
        return calculate_cost(
            model=self.model,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cache_creation_tokens=self.cache_creation_tokens,
            cache_read_tokens=self.cache_read_tokens,
        )
