"""Main Textual application for CCTOP."""

from pathlib import Path
import argparse
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Horizontal
from textual.binding import Binding

from .parsers.aggregator import DataAggregator
from .widgets.metrics_panel import MetricsPanel
from .widgets.agent_table import AgentTable
from .widgets.cost_panel import CostPanel
from .widgets.system_panel import SystemPanel
from .widgets.usage_panel import UsagePanel
from .widgets.notification import NotificationBar
from .widgets.agent_detail import AgentDetail
from .watchers.file_watcher import LogFileWatcher
from .models.agent import AgentStatus


class CCTopApp(App):
    """CCTOP - HTOP-like TUI monitor for Claude Code agents."""

    CSS_PATH = "app.css"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("s", "toggle_sort", "Sort", priority=True),
        Binding("f", "toggle_filter", "Filter", priority=True),
        Binding("c", "toggle_cost_panel", "Toggle Costs", priority=True),
        Binding("enter", "show_detail", "Details", priority=True),
        Binding("?", "show_help", "Help", priority=True),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, claude_home: Path = None, refresh_interval: float = 1.0):
        """Initialize CCTOP application.

        Args:
            claude_home: Path to Claude home directory (default: ~/.claude)
            refresh_interval: Refresh interval in seconds (default: 1.0)
        """
        super().__init__()
        self.aggregator = DataAggregator(claude_home)
        self.watcher = None
        self.last_refresh_time = 0
        self.refresh_interval = refresh_interval
        self.sort_by = "last_activity"
        self.filter_status = None
        self.cost_panel_visible = True
        self._claude_home = claude_home or Path.home() / ".claude"
        self._disable_watcher = False

    def compose(self) -> ComposeResult:
        """Compose the application UI.

        Returns:
            ComposeResult: Widget composition
        """
        yield Header(show_clock=True)
        yield MetricsPanel(id="metrics")
        yield AgentTable(id="agents")
        yield NotificationBar(id="notification")
        with Horizontal(id="panels"):
            yield CostPanel(id="cost")
            yield SystemPanel(id="system")
            yield UsagePanel(id="usage")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted. Sets up watchers and starts refresh."""
        self.title = "CCTOP - Claude Code Monitor"
        self.sub_title = "Press '?' for help"

        if not self._disable_watcher:
            self.watcher = LogFileWatcher(self._claude_home, self.on_log_file_changed)
            self.watcher.start()

        self.set_interval(self.refresh_interval, self.periodic_refresh)

        self.refresh_data()

    def on_unmount(self) -> None:
        """Called when app is unmounted. Stops file watcher."""
        if self.watcher:
            self.watcher.stop()

    def on_log_file_changed(self, file_path: Path) -> None:
        """Called when a log file is modified or created.

        Args:
            file_path: Path to the changed log file
        """
        import time
        current_time = time.time()

        if current_time - self.last_refresh_time < 0.1:
            return

        self.last_refresh_time = current_time
        self.call_from_thread(self.refresh_data)

    def periodic_refresh(self) -> None:
        """Periodic refresh when file watching is disabled."""
        if self._disable_watcher:
            self.refresh_data()

    def refresh_data(self) -> None:
        """Scan logs, calculate metrics, and update all widgets."""
        metrics = self.aggregator.scan_all_logs()
        agents = self.aggregator.get_all_agents_sorted(self.sort_by)

        # Calculate usage metrics
        usage_metrics = self.aggregator.calculate_usage_metrics(
            self.aggregator.start_time
        )
        metrics.usage_metrics = usage_metrics

        # Apply filter if set
        if self.filter_status:
            agents = [a for a in agents if a.status == self.filter_status]

        waiting_agents = self.aggregator.get_waiting_agents()

        metrics_panel = self.query_one("#metrics", MetricsPanel)
        metrics_panel.update_metrics(metrics)

        agent_table = self.query_one("#agents", AgentTable)
        agent_table.update_agents(agents)

        cost_panel = self.query_one("#cost", CostPanel)
        cost_panel.update_metrics(metrics)

        system_panel = self.query_one("#system", SystemPanel)
        system_panel.update_metrics(metrics)

        usage_panel = self.query_one("#usage", UsagePanel)
        usage_panel.update_metrics(metrics)

        notification_bar = self.query_one("#notification", NotificationBar)
        notification_bar.update_waiting_agents(waiting_agents)

    def action_refresh(self) -> None:
        """Action: Manually refresh all data."""
        self.refresh_data()
        self.notify("Refreshed data")

    def action_toggle_sort(self) -> None:
        """Action: Cycle through sort options."""
        sort_options = ["last_activity", "cost", "tokens", "agent_id"]
        current_index = sort_options.index(self.sort_by)
        next_index = (current_index + 1) % len(sort_options)
        self.sort_by = sort_options[next_index]

        sort_names = {
            "last_activity": "Last Activity",
            "cost": "Cost",
            "tokens": "Tokens",
            "agent_id": "Agent ID"
        }
        self.notify(f"Sorting by: {sort_names[self.sort_by]}")
        self.refresh_data()

    def action_toggle_filter(self) -> None:
        """Action: Cycle through filter options."""
        filter_options = [None, AgentStatus.ACTIVE, AgentStatus.IDLE, AgentStatus.WAITING_FOR_USER, AgentStatus.STOPPED]
        current_index = filter_options.index(self.filter_status)
        next_index = (current_index + 1) % len(filter_options)
        self.filter_status = filter_options[next_index]

        if self.filter_status:
            self.notify(f"Filter: {self.filter_status.value.upper()}")
        else:
            self.notify("Filter: ALL")
        self.refresh_data()

    def action_toggle_cost_panel(self) -> None:
        """Action: Toggle visibility of bottom panels."""
        panels = self.query_one("#panels")
        self.cost_panel_visible = not self.cost_panel_visible
        panels.display = self.cost_panel_visible
        self.notify(f"Cost panel: {'visible' if self.cost_panel_visible else 'hidden'}")

    def action_show_detail(self) -> None:
        """Action: Show detailed view for selected agent."""
        agent_table = self.query_one("#agents", AgentTable)
        if agent_table.cursor_row < len(agent_table.rows):
            row_key = agent_table.get_row_at(agent_table.cursor_row)[0]
            if row_key in self.aggregator.agents:
                agent = self.aggregator.agents[row_key]
                self.push_screen(AgentDetail(agent))

    def action_show_help(self) -> None:
        """Action: Display help screen with keyboard shortcuts."""
        help_text = """
[bold]CCTOP - Keyboard Shortcuts[/bold]

[cyan]q[/] or [cyan]Ctrl+C[/]  - Quit
[cyan]r[/]              - Refresh data manually
[cyan]s[/]              - Cycle sort (Activity → Cost → Tokens → ID)
[cyan]f[/]              - Cycle filter (All → Active → Idle → Waiting → Stopped)
[cyan]c[/]              - Toggle cost/system panels
[cyan]Enter[/]          - Show agent details
[cyan]?[/]              - Show this help

[yellow]Navigation:[/]
- Use arrow keys to navigate agent list
- Press Enter on an agent to view details
        """
        self.notify(help_text.strip(), timeout=10)

    def action_quit(self) -> None:
        """Action: Quit the application."""
        self.exit()


def main():
    """Main entry point for CCTOP application."""
    parser = argparse.ArgumentParser(
        description="CCTOP - HTOP-like TUI monitor for Claude Code agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cctop                              # Run with default settings
  cctop --refresh 0.5                # Refresh every 500ms
  cctop --log-dir /custom/path       # Use custom Claude log directory
  cctop --no-watch                   # Disable file watching

Keyboard shortcuts:
  q, Ctrl+C  - Quit
  r          - Refresh manually
  s          - Cycle sort order
  f          - Cycle filter
  c          - Toggle cost/system panels
  Enter      - Show agent details
  ?          - Show help
        """
    )

    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path.home() / ".claude",
        help="Path to Claude Code log directory (default: ~/.claude)"
    )

    parser.add_argument(
        "--refresh",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Refresh interval in seconds (default: 1.0)"
    )

    parser.add_argument(
        "--no-watch",
        action="store_true",
        help="Disable file watching (use polling only)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="cctop 0.1.0"
    )

    args = parser.parse_args()

    app = CCTopApp(
        claude_home=args.log_dir,
        refresh_interval=args.refresh
    )

    # Disable file watcher if requested
    if args.no_watch:
        app._disable_watcher = True

    app.run()


if __name__ == "__main__":
    main()
