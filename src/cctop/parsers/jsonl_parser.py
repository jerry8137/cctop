"""Parser for Claude Code JSONL log files."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dateutil import parser as date_parser

from ..models.usage import TokenUsage


class JSONLParser:
    """Parser for extracting agent data from JSONL log files."""

    @staticmethod
    def parse_log_file(file_path: Path) -> List[Dict[str, Any]]:
        """Parse a JSONL log file and return all entries.

        Args:
            file_path: Path to the JSONL log file

        Returns:
            List[Dict[str, Any]]: List of parsed log entries
        """
        if not file_path.exists():
            return []

        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except (IOError, OSError):
            return []

        return entries

    @staticmethod
    def extract_usage_data(log_entry: Dict[str, Any]) -> Optional[TokenUsage]:
        """Extract token usage data from a log entry.

        Args:
            log_entry: Single JSONL log entry

        Returns:
            Optional[TokenUsage]: TokenUsage object if usage data found, None otherwise
        """
        try:
            message = log_entry.get('message', {})
            usage = message.get('usage', {})

            if not usage:
                return None

            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cache_creation_tokens = usage.get('cache_creation_input_tokens', 0)
            cache_read_tokens = usage.get('cache_read_input_tokens', 0)

            timestamp_str = log_entry.get('timestamp', '')
            if timestamp_str:
                timestamp = date_parser.isoparse(timestamp_str)
            else:
                timestamp = datetime.now()

            model = message.get('model', '')
            request_id = log_entry.get('requestId', '')

            return TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_creation_tokens=cache_creation_tokens,
                cache_read_tokens=cache_read_tokens,
                timestamp=timestamp,
                model=model,
                request_id=request_id,
            )
        except (KeyError, ValueError, TypeError):
            return None

    @staticmethod
    def get_agent_info_from_log(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract agent metadata and aggregate token usage from log entries.

        Args:
            entries: List of JSONL log entries for an agent

        Returns:
            Dict[str, Any]: Dictionary containing agent metadata and aggregated usage
        """
        if not entries:
            return {}

        first_entry = entries[0]
        last_entry = entries[-1]

        agent_id = first_entry.get('agentId', '')
        slug = first_entry.get('slug', '')
        session_id = first_entry.get('sessionId', '')
        project_path = first_entry.get('cwd', '')

        created_at_str = first_entry.get('timestamp', '')
        if created_at_str:
            created_at = date_parser.isoparse(created_at_str)
        else:
            created_at = datetime.now()

        last_activity_str = last_entry.get('timestamp', '')
        if last_activity_str:
            last_activity = date_parser.isoparse(last_activity_str)
        else:
            last_activity = created_at

        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_creation_tokens = 0
        total_cache_read_tokens = 0
        message_count = 0
        model = ""

        for entry in entries:
            usage_data = JSONLParser.extract_usage_data(entry)
            if usage_data:
                total_input_tokens += usage_data.input_tokens
                total_output_tokens += usage_data.output_tokens
                total_cache_creation_tokens += usage_data.cache_creation_tokens
                total_cache_read_tokens += usage_data.cache_read_tokens
                if usage_data.model:
                    model = usage_data.model

            if entry.get('type') in ['user', 'assistant']:
                message_count += 1

        return {
            'agent_id': agent_id,
            'slug': slug,
            'session_id': session_id,
            'project_path': project_path,
            'created_at': created_at,
            'last_activity': last_activity,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_cache_creation_tokens': total_cache_creation_tokens,
            'total_cache_read_tokens': total_cache_read_tokens,
            'message_count': message_count,
            'model': model,
        }

    @staticmethod
    def is_waiting_for_user(entries: List[Dict[str, Any]]) -> bool:
        """Determine if agent is waiting for user input based on last message.

        Args:
            entries: List of JSONL log entries for an agent

        Returns:
            bool: True if agent is waiting for user input, False otherwise
        """
        if not entries:
            return False

        last_entry = entries[-1]

        if last_entry.get('type') == 'assistant':
            message = last_entry.get('message', {})
            stop_reason = message.get('stop_reason', '')
            if stop_reason == 'end_turn':
                return True

        return False
