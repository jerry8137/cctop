from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Optional


@dataclass
class SystemMetrics:
    total_agents: int = 0
    active_agents: int = 0
    idle_agents: int = 0
    waiting_for_user: int = 0
    stopped_agents: int = 0
    total_sessions: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_creation_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cost: Decimal = Decimal("0.00")
    uptime: timedelta = timedelta(seconds=0)
    usage_metrics: Optional["UsageMetrics"] = None

    def __post_init__(self):
        if self.usage_metrics is None:
            from .usage_metrics import UsageMetrics
            self.usage_metrics = UsageMetrics()

    @property
    def total_tokens(self) -> int:
        return (
            self.total_input_tokens +
            self.total_output_tokens +
            self.total_cache_creation_tokens +
            self.total_cache_read_tokens
        )
