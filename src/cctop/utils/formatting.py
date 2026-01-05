from datetime import datetime, timedelta
from decimal import Decimal


def format_tokens(tokens: int) -> str:
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    elif tokens >= 1_000:
        return f"{tokens / 1_000:.1f}K"
    else:
        return str(tokens)


def format_cost(cost: Decimal) -> str:
    return f"${cost:.4f}"


def format_time_ago(dt: datetime) -> str:
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
