"""Formatting utilities for displaying metrics in the TUI."""

from datetime import datetime, timedelta
from decimal import Decimal


def format_tokens(tokens: int) -> str:
    """Format token count with K/M suffixes.

    Args:
        tokens: Number of tokens

    Returns:
        str: Formatted token string (e.g., '1.5K', '2.3M')
    """
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    elif tokens >= 1_000:
        return f"{tokens / 1_000:.1f}K"
    else:
        return str(tokens)


def format_cost(cost: Decimal) -> str:
    """Format cost as USD currency.

    Args:
        cost: Cost in USD as Decimal

    Returns:
        str: Formatted cost string (e.g., '$0.1234')
    """
    return f"${cost:.4f}"


def format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time string.

    Args:
        dt: Datetime to format

    Returns:
        str: Relative time string (e.g., '5s ago', '10m ago', '2h ago', '3d ago')
    """
    now = datetime.now()
    if dt.tzinfo is not None:
        from dateutil import tz

        now = now.replace(tzinfo=tz.tzlocal())

    delta = now - dt

    if delta < timedelta(seconds=60):
        return f"{int(delta.total_seconds())}s ago"
    elif delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() / 60)}m ago"
    elif delta < timedelta(days=1):
        return f"{int(delta.total_seconds() / 3600)}h ago"
    else:
        return f"{int(delta.days)}d ago"


def format_duration(td: timedelta) -> str:
    """Format timedelta as human-readable duration.

    Args:
        td: Timedelta to format

    Returns:
        str: Formatted duration (e.g., '5d 3h', '2h 15m', '45m 30s', '12s')
    """
    total_seconds = int(td.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
