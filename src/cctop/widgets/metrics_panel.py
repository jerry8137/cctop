from textual.app import ComposeResult
from textual.widgets import Static
from rich.text import Text

from ..models.metrics import SystemMetrics
from ..utils.formatting import format_tokens, format_cost


class MetricsPanel(Static):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics = SystemMetrics()

    def update_metrics(self, metrics: SystemMetrics) -> None:
        self.metrics = metrics
        self.refresh()

    def render(self) -> Text:
        m = self.metrics

        parts = [
            f"[bold cyan]Agents:[/] {m.total_agents}",
            f"[bold green]Active:[/] {m.active_agents}",
            f"[bold yellow]Waiting:[/] {m.waiting_for_user}",
            f"[bold blue]Idle:[/] {m.idle_agents}",
            f"[bold white]Tokens:[/] {format_tokens(m.total_tokens)}",
            f"[bold magenta]Cost:[/] {format_cost(m.total_cost)}",
        ]

        text = Text(" │ ".join(parts))
        return text
