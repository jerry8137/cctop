from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class UsageMetrics:
    """Usage tracking data model for session and weekly metrics"""

    # Session metrics (since app start)
    session_total_tokens: int = 0
    session_request_count: int = 0
    session_start_time: Optional[datetime] = None

    # Weekly metrics (since last Monday 00:00 UTC)
    weekly_total_tokens: int = 0
    weekly_request_count: int = 0
    weekly_start_time: Optional[datetime] = None

    # Reset schedule
    next_reset_time: Optional[datetime] = None
    subscription_type: str = "pro"

    @property
    def time_until_reset(self) -> timedelta:
        """Calculate time remaining until next reset"""
        if self.next_reset_time is None:
            return timedelta(0)
        return self.next_reset_time - datetime.now(timezone.utc)

    @staticmethod
    def calculate_next_monday_utc() -> datetime:
        """Find next Monday 00:00 UTC

        Returns:
            datetime object representing next Monday at 00:00 UTC
        """
        now_utc = datetime.now(timezone.utc)
        days_until_monday = (7 - now_utc.weekday()) % 7
        if days_until_monday == 0:
            # Today is Monday, get next week's Monday
            days_until_monday = 7
        next_monday = now_utc + timedelta(days=days_until_monday)
        return next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
