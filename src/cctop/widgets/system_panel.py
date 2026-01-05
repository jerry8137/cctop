"""System resources panel widget."""

from textual.widgets import Static
from rich.text import Text
import psutil
from datetime import timedelta

from ..models.metrics import SystemMetrics
from ..utils.formatting import format_duration


class SystemPanel(Static):
    """Display system resource usage."""

    def __init__(self, **kwargs):
        """Initialize system panel.

        Args:
            **kwargs: Additional widget parameters
        """
        super().__init__(**kwargs)
        self.metrics = SystemMetrics()

    def update_metrics(self, metrics: SystemMetrics) -> None:
        """Update metrics and refresh display.

        Args:
            metrics: Updated system metrics
        """
        self.metrics = metrics
        self.refresh()

    def render(self) -> Text:
        """Render system resource information.

        Returns:
            Text: Formatted system resources
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024 ** 3)
        except Exception:
            cpu_percent = 0
            memory_percent = 0
            memory_used_gb = 0

        cpu_bar = self._make_bar(cpu_percent)
        mem_bar = self._make_bar(memory_percent)

        uptime = format_duration(self.metrics.uptime)

        lines = [
            Text("System Resources", style="bold underline"),
            Text(""),
            Text(f"CPU:    {cpu_bar} {cpu_percent:.1f}%", style="cyan"),
            Text(f"Memory: {mem_bar} {memory_percent:.1f}% ({memory_used_gb:.1f}GB)", style="green"),
            Text(""),
            Text(f"Uptime: {uptime}", style="blue"),
        ]

        return Text("\n").join(lines)

    def _make_bar(self, percent: float, width: int = 10) -> str:
        """Create a text-based progress bar.

        Args:
            percent: Percentage value (0-100)
            width: Width of bar in characters (default: 10)

        Returns:
            str: Text bar representation
        """
        filled = int(percent / 10)
        filled = min(filled, width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
