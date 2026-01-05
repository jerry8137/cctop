from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class TokenUsage:
    """Data model for token usage from a single API request.

    Attributes:
        input_tokens: Number of input tokens consumed
        output_tokens: Number of output tokens generated
        cache_creation_tokens: Number of cache creation tokens
        cache_read_tokens: Number of cache read tokens
        timestamp: When this usage occurred
        model: Claude model identifier
        request_id: Optional request identifier
    """
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    timestamp: datetime
    model: str
    request_id: str = ""

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens across all categories.

        Returns:
            int: Sum of all token types
        """
        return (
            self.input_tokens +
            self.output_tokens +
            self.cache_creation_tokens +
            self.cache_read_tokens
        )

    def calculate_cost(self) -> Decimal:
        """Calculate the cost for this token usage.

        Returns:
            Decimal: Cost in USD
        """
        from ..utils.pricing import calculate_cost
        return calculate_cost(
            model=self.model,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cache_creation_tokens=self.cache_creation_tokens,
            cache_read_tokens=self.cache_read_tokens,
        )
