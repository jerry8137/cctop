"""Data aggregator for scanning and aggregating Claude Code agent logs."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List
from decimal import Decimal

from ..models.agent import Agent, AgentStatus
from ..models.metrics import SystemMetrics
from .jsonl_parser import JSONLParser


class DataAggregator:
    """Aggregates data from Claude Code agent log files."""

    def __init__(self, claude_home: Path = None):
        """Initialize the data aggregator.

        Args:
            claude_home: Path to Claude home directory (default: ~/.claude)
        """
        if claude_home is None:
            claude_home = Path.home() / ".claude"
        self.claude_home = claude_home
        self.agents: Dict[str, Agent] = {}
        self.sessions: Dict[str, str] = {}
        self.parser = JSONLParser()
        self.start_time = datetime.now()

    def scan_all_logs(self) -> SystemMetrics:
        """Scan all agent log files and return aggregated metrics.

        Returns:
            SystemMetrics: Aggregated system metrics for all agents
        """
        self.agents.clear()
        self.sessions.clear()

        projects_dir = self.claude_home / "projects"
        if not projects_dir.exists():
            return self._empty_metrics()

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            self._scan_project_logs(project_dir)

        return self._calculate_metrics()

    def _scan_project_logs(self, project_dir: Path):
        """Scan all agent log files in a project directory.

        Args:
            project_dir: Path to project directory
        """
        for log_file in project_dir.glob("agent-*.jsonl"):
            agent = self._parse_agent_log(log_file)
            if agent:
                self.agents[agent.agent_id] = agent
                self.sessions[agent.session_id] = agent.session_id

    def _parse_agent_log(self, log_file: Path) -> Agent | None:
        """Parse a single agent log file and create an Agent object.

        Args:
            log_file: Path to agent log file

        Returns:
            Agent | None: Agent object if parsing successful, None otherwise
        """
        entries = self.parser.parse_log_file(log_file)
        if not entries:
            return None

        agent_info = self.parser.get_agent_info_from_log(entries)
        if not agent_info.get('agent_id'):
            return None

        status = self._determine_agent_status(
            entries,
            agent_info['last_activity'],
            agent_info.get('agent_id', ''),
            agent_info.get('session_id', '')
        )

        current_cwd = agent_info.get('project_path', '')
        if entries:
            for entry in reversed(entries):
                if entry.get('cwd'):
                    current_cwd = entry['cwd']
                    break

        return Agent(
            agent_id=agent_info['agent_id'],
            slug=agent_info['slug'] or agent_info['agent_id'][:7],
            session_id=agent_info['session_id'],
            status=status,
            project_path=str(log_file.parent),
            current_cwd=current_cwd,
            created_at=agent_info['created_at'],
            last_activity=agent_info['last_activity'],
            total_input_tokens=agent_info['total_input_tokens'],
            total_output_tokens=agent_info['total_output_tokens'],
            total_cache_creation_tokens=agent_info['total_cache_creation_tokens'],
            total_cache_read_tokens=agent_info['total_cache_read_tokens'],
            message_count=agent_info['message_count'],
            model=agent_info['model'],
        )

    def _determine_agent_status(self, entries: List[Dict], last_activity: datetime, agent_id: str = "", session_id: str = "") -> AgentStatus:
        """Determine agent status based on activity and message history.

        Args:
            entries: List of log entries for the agent
            last_activity: Timestamp of last activity
            agent_id: Agent identifier
            session_id: Session identifier

        Returns:
            AgentStatus: Determined status for the agent
        """
        from dateutil import tz

        now = datetime.now()
        if last_activity.tzinfo is not None:
            now = now.replace(tzinfo=tz.tzlocal())

        time_since_activity = now - last_activity

        if self._check_waiting_for_user(entries, agent_id, session_id):
            return AgentStatus.WAITING_FOR_USER

        if time_since_activity < timedelta(seconds=30):
            return AgentStatus.ACTIVE

        if time_since_activity < timedelta(hours=1):
            return AgentStatus.IDLE

        return AgentStatus.STOPPED

    def _check_waiting_for_user(self, entries: List[Dict], agent_id: str, session_id: str) -> bool:
        """Enhanced check for agents waiting for user input.

        Args:
            entries: List of log entries for the agent
            agent_id: Agent identifier
            session_id: Session identifier

        Returns:
            bool: True if agent is waiting for user input, False otherwise
        """

        # Check 1: Parse last message in log
        if self.parser.is_waiting_for_user(entries):
            return True

        # Check 2: Look for todo files
        if session_id:
            todo_patterns = [
                self.claude_home / f"todos/{session_id}.json",
                self.claude_home / f"todos/{session_id}-agent-{agent_id}.json",
            ]

            for todo_file in todo_patterns:
                if todo_file.exists():
                    try:
                        import json
                        todos = json.loads(todo_file.read_text())
                        # Empty todo list might indicate waiting
                        if isinstance(todos, list) and len(todos) == 0:
                            # But only if there's recent activity
                            if entries:
                                last_timestamp = entries[-1].get('timestamp', '')
                                if last_timestamp:
                                    from dateutil import parser as date_parser, tz
                                    last_time = date_parser.isoparse(last_timestamp)
                                    now = datetime.now()
                                    if last_time.tzinfo:
                                        now = now.replace(tzinfo=tz.tzlocal())
                                    if (now - last_time) < timedelta(minutes=5):
                                        return True
                    except (json.JSONDecodeError, IOError):
                        pass

        return False

    def _calculate_metrics(self) -> SystemMetrics:
        """Calculate aggregated system metrics from all agents.

        Returns:
            SystemMetrics: Aggregated metrics
        """
        metrics = SystemMetrics()

        metrics.total_agents = len(self.agents)
        metrics.total_sessions = len(self.sessions)

        for agent in self.agents.values():
            metrics.total_input_tokens += agent.total_input_tokens
            metrics.total_output_tokens += agent.total_output_tokens
            metrics.total_cache_creation_tokens += agent.total_cache_creation_tokens
            metrics.total_cache_read_tokens += agent.total_cache_read_tokens
            metrics.total_cost += agent.total_cost

            if agent.status == AgentStatus.ACTIVE:
                metrics.active_agents += 1
            elif agent.status == AgentStatus.IDLE:
                metrics.idle_agents += 1
            elif agent.status == AgentStatus.WAITING_FOR_USER:
                metrics.waiting_for_user += 1
            elif agent.status == AgentStatus.STOPPED:
                metrics.stopped_agents += 1

        metrics.uptime = datetime.now() - self.start_time

        return metrics

    def _empty_metrics(self) -> SystemMetrics:
        """Return empty system metrics.

        Returns:
            SystemMetrics: Empty metrics object
        """
        return SystemMetrics()

    def get_active_agents(self) -> List[Agent]:
        """Get list of all active agents.

        Returns:
            List[Agent]: List of active agents
        """
        return [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.ACTIVE
        ]

    def get_waiting_agents(self) -> List[Agent]:
        """Get list of all agents waiting for user input.

        Returns:
            List[Agent]: List of waiting agents
        """
        return [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.WAITING_FOR_USER
        ]

    def get_all_agents_sorted(self, sort_by: str = "last_activity") -> List[Agent]:
        """Get sorted list of all agents.

        Args:
            sort_by: Sort criterion ('last_activity', 'cost', 'tokens', 'agent_id')

        Returns:
            List[Agent]: Sorted list of agents
        """
        agents = list(self.agents.values())

        if sort_by == "last_activity":
            agents.sort(key=lambda a: a.last_activity, reverse=True)
        elif sort_by == "cost":
            agents.sort(key=lambda a: a.total_cost, reverse=True)
        elif sort_by == "tokens":
            agents.sort(key=lambda a: a.total_input_tokens + a.total_output_tokens, reverse=True)
        elif sort_by == "agent_id":
            agents.sort(key=lambda a: a.agent_id)

        return agents

    def calculate_total_cost(self) -> Decimal:
        """Calculate total cost across all agents.

        Returns:
            Decimal: Total cost in USD
        """
        total = Decimal("0.00")
        for agent in self.agents.values():
            total += agent.total_cost
        return total

    def load_subscription_type(self) -> str:
        """Parse ~/.claude/.credentials.json for subscriptionType

        Returns:
            str: Subscription type ("pro" or "max"), defaults to "pro"
        """
        creds_file = self.claude_home / ".credentials.json"
        if creds_file.exists():
            try:
                data = json.loads(creds_file.read_text())
                return data.get("claudeAiOauth", {}).get("subscriptionType", "pro")
            except (json.JSONDecodeError, IOError):
                pass
        return "pro"

    def calculate_usage_metrics(self, session_start: datetime):
        """Calculate session and weekly usage from JSONL logs

        Args:
            session_start: Timestamp when the app started (session boundary)

        Returns:
            UsageMetrics object with calculated session and weekly usage
        """
        from ..models.usage_metrics import UsageMetrics

        metrics = UsageMetrics()

        # Calculate boundaries
        now_utc = datetime.now(timezone.utc)
        days_since_monday = now_utc.weekday()
        weekly_start = now_utc - timedelta(days=days_since_monday)
        weekly_start = weekly_start.replace(hour=0, minute=0, second=0, microsecond=0)

        metrics.session_start_time = session_start
        metrics.weekly_start_time = weekly_start
        metrics.next_reset_time = UsageMetrics.calculate_next_monday_utc()

        # Scan all JSONL files
        projects_dir = self.claude_home / "projects"
        if projects_dir.exists():
            for project_dir in projects_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                for log_file in project_dir.glob("agent-*.jsonl"):
                    entries = self.parser.parse_log_file(log_file)
                    for entry in entries:
                        usage_data = self.parser.extract_usage_data(entry)
                        if not usage_data:
                            continue

                        # Normalize timestamp to UTC
                        entry_time = usage_data.timestamp
                        if entry_time.tzinfo is None:
                            entry_time = entry_time.replace(tzinfo=timezone.utc)
                        else:
                            entry_time = entry_time.astimezone(timezone.utc)

                        total_tokens = usage_data.total_tokens

                        # Session tracking
                        session_start_utc = session_start.replace(tzinfo=timezone.utc) if session_start.tzinfo is None else session_start.astimezone(timezone.utc)
                        if entry_time >= session_start_utc:
                            metrics.session_total_tokens += total_tokens
                            metrics.session_request_count += 1

                        # Weekly tracking
                        if entry_time >= weekly_start:
                            metrics.weekly_total_tokens += total_tokens
                            metrics.weekly_request_count += 1

        metrics.subscription_type = self.load_subscription_type()
        return metrics
