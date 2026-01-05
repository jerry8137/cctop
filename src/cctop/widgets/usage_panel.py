from textual.widgets import Static
from rich.text import Text

from ..models.metrics import SystemMetrics
from ..utils.formatting import format_tokens, format_duration


class UsagePanel(Static):
    """Display subscription usage tracking"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics = SystemMetrics()

    def update_metrics(self, metrics: SystemMetrics) -> None:
        self.metrics = metrics
        self.refresh()

    def render(self) -> Text:
        if self.metrics.usage_metrics is None:
            return Text("Usage Tracking\n\nNo data available", style="dim")

        usage = self.metrics.usage_metrics

        # Format subscription type
        sub_type = usage.subscription_type.upper()

        # Format token counts
        session_tokens = format_tokens(usage.session_total_tokens)
        weekly_tokens = format_tokens(usage.weekly_total_tokens)

        # Format countdown
        reset_countdown = format_duration(usage.time_until_reset)

        lines = [
            Text("Usage Tracking", style="bold underline"),
            Text(""),
            Text(f"Subscription: {sub_type}", style="bold cyan"),
            Text(""),
            Text("Session:", style="yellow"),
            Text(f"  Tokens:   {session_tokens}", style="cyan"),
            Text(f"  Requests: {usage.session_request_count}", style="cyan"),
            Text(""),
            Text("This Week:", style="yellow"),
            Text(f"  Tokens:   {weekly_tokens}", style="green"),
            Text(f"  Requests: {usage.weekly_request_count}", style="green"),
            Text(""),
            Text(f"Resets in: {reset_countdown}", style="bold magenta"),
        ]

        return Text("\n").join(lines)
