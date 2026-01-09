"""Notification bar widget for displaying alerts."""

from textual.widgets import Static
from rich.text import Text
from typing import List

from ..models.agent import Agent


class NotificationBar(Static):
    """Display notifications for agents waiting for user input."""

    def __init__(self, **kwargs):
        """Initialize notification bar.

        Args:
            **kwargs: Additional widget parameters
        """
        super().__init__(**kwargs)
        self.waiting_agents: List[Agent] = []

    def update_waiting_agents(self, agents: List[Agent]) -> None:
        """Update list of waiting agents and refresh display.

        Args:
            agents: List of agents waiting for user input
        """
        self.waiting_agents = agents
        self.refresh()

    def render(self) -> Text:
        """Render notification message.

        Returns:
            Text: Formatted notification text (empty if no waiting agents)
        """
        if not self.waiting_agents:
            return Text("")

        if len(self.waiting_agents) == 1:
            agent = self.waiting_agents[0]
            return Text(
                f"⚠ Agent '{agent.slug}' is waiting for user input!",
                style="bold yellow on dark_red",
            )
        else:
            count = len(self.waiting_agents)
            names = ", ".join([a.slug[:15] for a in self.waiting_agents[:3]])
            if count > 3:
                names += f", +{count - 3} more"
            return Text(
                f"⚠ {count} agents waiting for input: {names}",
                style="bold yellow on dark_red",
            )
