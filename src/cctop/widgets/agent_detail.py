"""Agent detail modal screen widget."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.containers import Container, Vertical
from rich.text import Text

from ..models.agent import Agent
from ..utils.formatting import (
    format_tokens,
    format_cost,
    format_time_ago,
    format_duration,
)


class AgentDetail(ModalScreen):
    """Modal screen showing detailed information about an agent."""

    CSS = """
    AgentDetail {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #content {
        height: auto;
        margin-bottom: 1;
    }

    #close-btn {
        width: 100%;
        margin-top: 1;
    }
    """

    def __init__(self, agent: Agent):
        """Initialize agent detail screen.

        Args:
            agent: Agent to display details for
        """
        super().__init__()
        self.agent = agent

    def compose(self) -> ComposeResult:
        """Compose the modal dialog.

        Returns:
            ComposeResult: Widget composition
        """
        with Container(id="dialog"):
            yield Static(f"Agent Details: {self.agent.slug}", id="title")
            yield Static(self._format_details(), id="content")
            yield Button("Close (ESC)", variant="primary", id="close-btn")

    def _format_details(self) -> Text:
        """Format agent details as rich text.

        Returns:
            Text: Formatted agent details
        """
        a = self.agent

        lines = [
            Text(f"Agent ID:        {a.agent_id}", style="cyan"),
            Text(f"Slug:            {a.slug}", style="cyan"),
            Text(f"Session ID:      {a.session_id}", style="cyan"),
            Text(f"Status:          {a.status.value.upper()}", style="bold yellow"),
            Text(""),
            Text(f"Model:           {a.model}", style="green"),
            Text(f"Project Path:    {a.project_path}", style="blue"),
            Text(f"Working Dir:     {a.current_cwd}", style="blue"),
            Text(""),
            Text("Token Usage:", style="bold underline"),
            Text(
                f"  Input:         {format_tokens(a.total_input_tokens)}", style="cyan"
            ),
            Text(
                f"  Output:        {format_tokens(a.total_output_tokens)}",
                style="green",
            ),
            Text(
                f"  Cache Create:  {format_tokens(a.total_cache_creation_tokens)}",
                style="yellow",
            ),
            Text(
                f"  Cache Read:    {format_tokens(a.total_cache_read_tokens)}",
                style="blue",
            ),
            Text(f"  Messages:      {a.message_count}", style="white"),
            Text(""),
            Text(f"Cost:            {format_cost(a.total_cost)}", style="bold magenta"),
            Text(""),
            Text(
                f"Created:         {a.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                style="dim",
            ),
            Text(f"Last Activity:   {format_time_ago(a.last_activity)}", style="dim"),
        ]

        return Text("\n").join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle close button press.

        Args:
            event: Button pressed event
        """
        self.dismiss()

    def on_key(self, event) -> None:
        """Handle keyboard input.

        Args:
            event: Key event
        """
        if event.key == "escape":
            self.dismiss()
