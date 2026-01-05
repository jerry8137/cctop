"""Agent data table widget for displaying agent list."""

from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.coordinate import Coordinate
from rich.text import Text
from typing import List

from ..models.agent import Agent, AgentStatus
from ..utils.formatting import format_tokens, format_cost, format_time_ago


class AgentTable(DataTable):
    """Display agents in a sortable data table."""

    def __init__(self, **kwargs):
        """Initialize agent table.

        Args:
            **kwargs: Additional widget parameters
        """
        super().__init__(**kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
        self._setup_columns()

    def _setup_columns(self) -> None:
        """Setup table columns with headers and widths."""
        self.add_column("ID", key="id", width=8)
        self.add_column("Name", key="name", width=20)
        self.add_column("Status", key="status", width=10)
        self.add_column("Model", key="model", width=8)
        self.add_column("Input", key="input", width=8)
        self.add_column("Output", key="output", width=8)
        self.add_column("Cost", key="cost", width=10)
        self.add_column("Last Active", key="last_active", width=12)

    def update_agents(self, agents: List[Agent]) -> None:
        """Update table with agent data.

        Args:
            agents: List of agents to display
        """
        self.clear()

        for agent in agents:
            status_text = self._format_status(agent.status)

            self.add_row(
                agent.short_id,
                agent.slug[:20],
                status_text,
                agent.short_model,
                format_tokens(agent.total_input_tokens),
                format_tokens(agent.total_output_tokens),
                format_cost(agent.total_cost),
                format_time_ago(agent.last_activity),
                key=agent.agent_id,
            )

    def _format_status(self, status: AgentStatus) -> Text:
        """Format agent status with color coding.

        Args:
            status: Agent status enum

        Returns:
            Text: Colored status text
        """
        if status == AgentStatus.ACTIVE:
            return Text("ACTIVE", style="bold green")
        elif status == AgentStatus.WAITING_FOR_USER:
            return Text("WAITING", style="bold yellow")
        elif status == AgentStatus.IDLE:
            return Text("IDLE", style="blue")
        elif status == AgentStatus.STOPPED:
            return Text("STOPPED", style="dim")
        else:
            return Text(status.value.upper(), style="white")
