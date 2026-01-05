from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from decimal import Decimal


class AgentStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    WAITING_FOR_USER = "waiting_for_user"
    STOPPED = "stopped"


@dataclass
class Agent:
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
        return self.agent_id[:7] if len(self.agent_id) >= 7 else self.agent_id

    @property
    def short_model(self) -> str:
        if "sonnet" in self.model.lower():
            return "S-4.5" if "4.5" in self.model or "4-5" in self.model else "S-3.5"
        elif "opus" in self.model.lower():
            return "O-4.5" if "4.5" in self.model or "4-5" in self.model else "O-3"
        elif "haiku" in self.model.lower():
            return "H-3.5"
        return self.model[:8]
