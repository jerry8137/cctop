"""Cost breakdown panel widget."""

from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container
from rich.text import Text
from decimal import Decimal

from ..models.metrics import SystemMetrics
from ..utils.formatting import format_cost
from ..utils.pricing import calculate_cost


class CostPanel(Static):
    """Display detailed cost breakdown."""

    def __init__(self, **kwargs):
        """Initialize cost panel.

        Args:
            **kwargs: Additional widget parameters
        """
        super().__init__(**kwargs)
        self.metrics = SystemMetrics()

    def update_metrics(self, metrics: SystemMetrics) -> None:
        """Update cost metrics and refresh display.

        Args:
            metrics: Updated system metrics
        """
        self.metrics = metrics
        self.refresh()

    def render(self) -> Text:
        """Render cost breakdown.

        Returns:
            Text: Formatted cost breakdown
        """
        m = self.metrics

        input_cost = calculate_cost(
            model="claude-sonnet-4-5",
            input_tokens=m.total_input_tokens,
            output_tokens=0,
        )

        output_cost = calculate_cost(
            model="claude-sonnet-4-5",
            input_tokens=0,
            output_tokens=m.total_output_tokens,
        )

        cache_creation_cost = calculate_cost(
            model="claude-sonnet-4-5",
            input_tokens=0,
            output_tokens=0,
            cache_creation_tokens=m.total_cache_creation_tokens,
        )

        cache_read_cost = calculate_cost(
            model="claude-sonnet-4-5",
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=m.total_cache_read_tokens,
        )

        lines = [
            Text("Cost Breakdown", style="bold underline"),
            Text(""),
            Text(f"Input:       {format_cost(input_cost)}", style="cyan"),
            Text(f"Output:      {format_cost(output_cost)}", style="green"),
            Text(f"Cache Create:{format_cost(cache_creation_cost)}", style="yellow"),
            Text(f"Cache Read:  {format_cost(cache_read_cost)}", style="blue"),
            Text("─" * 20),
            Text(f"Total:       {format_cost(m.total_cost)}", style="bold magenta"),
        ]

        return Text("\n").join(lines)
