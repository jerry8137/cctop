from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Optional


@dataclass
class SystemMetrics:
    """Aggregated metrics for all agents in the system.

    Attributes:
        total_agents: Total number of agents
        active_agents: Number of active agents
        idle_agents: Number of idle agents
        waiting_for_user: Number of agents waiting for user input
        stopped_agents: Number of stopped agents
        total_sessions: Total number of unique sessions
        total_input_tokens: Total input tokens across all agents
        total_output_tokens: Total output tokens across all agents
        total_cache_creation_tokens: Total cache creation tokens
        total_cache_read_tokens: Total cache read tokens
        total_cost: Total cost in USD across all agents
        uptime: Application uptime duration
        usage_metrics: Optional usage tracking metrics
    """

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
        """Initialize usage_metrics if not provided."""
        if self.usage_metrics is None:
            from .usage_metrics import UsageMetrics

            self.usage_metrics = UsageMetrics()

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens across all categories.

        Returns:
            int: Sum of all token types
        """
        return (
            self.total_input_tokens
            + self.total_output_tokens
            + self.total_cache_creation_tokens
            + self.total_cache_read_tokens
        )
