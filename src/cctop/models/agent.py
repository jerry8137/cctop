from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from decimal import Decimal


class AgentStatus(str, Enum):
    """Enumeration of possible agent statuses.

    Attributes:
        ACTIVE: Agent is currently active (activity within last 30 seconds)
        IDLE: Agent is idle (activity within last hour)
        WAITING_FOR_USER: Agent is waiting for user input
        STOPPED: Agent is stopped (no activity for over 1 hour)
    """
    ACTIVE = "active"
    IDLE = "idle"
    WAITING_FOR_USER = "waiting_for_user"
    STOPPED = "stopped"


@dataclass
class Agent:
    """Data model representing a Claude Code agent.

    Attributes:
        agent_id: Unique identifier for the agent
        slug: Human-readable agent name/slug
        session_id: Session identifier
        status: Current agent status (active, idle, waiting, stopped)
        project_path: Path to the project directory
        current_cwd: Current working directory of the agent
        created_at: Timestamp when the agent was created
        last_activity: Timestamp of the last agent activity
        total_input_tokens: Total input tokens consumed
        total_output_tokens: Total output tokens generated
        total_cache_creation_tokens: Total cache creation tokens
        total_cache_read_tokens: Total cache read tokens
        message_count: Number of messages exchanged
        model: Claude model identifier (e.g., claude-sonnet-4-5)
        is_sidechain: Whether this is a sidechain agent
    """
    agent_id: str
    slug: str
    session_id: str
    status: AgentStatus
    project_path: str
    current_cwd: str
    created_at: datetime
    last_activity: datetime
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_creation_tokens: int = 0
    total_cache_read_tokens: int = 0
    message_count: int = 0
    model: str = ""
    is_sidechain: bool = False

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost for this agent based on token usage.

        Returns:
            Decimal: Total cost in USD
        """
        from ..utils.pricing import calculate_cost
        return calculate_cost(
            model=self.model,
            input_tokens=self.total_input_tokens,
            output_tokens=self.total_output_tokens,
            cache_creation_tokens=self.total_cache_creation_tokens,
            cache_read_tokens=self.total_cache_read_tokens,
        )

    @property
    def short_id(self) -> str:
        """Get shortened agent ID (first 7 characters).

        Returns:
            str: Shortened agent ID
        """
        return self.agent_id[:7] if len(self.agent_id) >= 7 else self.agent_id

    @property
    def short_model(self) -> str:
        """Get abbreviated model name for display.

        Returns:
            str: Abbreviated model name (e.g., 'S-4.5' for Sonnet 4.5)
        """
        if "sonnet" in self.model.lower():
            return "S-4.5" if "4.5" in self.model or "4-5" in self.model else "S-3.5"
        elif "opus" in self.model.lower():
            return "O-4.5" if "4.5" in self.model or "4-5" in self.model else "O-3"
        elif "haiku" in self.model.lower():
            return "H-3.5"
        return self.model[:8]
