"""Cron service for handling cron expressions and scheduling."""

from croniter import croniter
from datetime import datetime, timezone
import pytz
from typing import List
import structlog

logger = structlog.get_logger()

class CronService:
    """Service for handling cron expressions and calculating next run times."""

    def __init__(self):
        pass

    def get_next_run_time(self, cron_expression: str, timezone_str: str = "UTC") -> datetime:
        """Get the next run time for a cron expression."""
        try:
            # Parse timezone
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)

            # Create croniter instance
            cron = croniter(cron_expression, now)
            next_run = cron.get_next(datetime)

            # Convert to UTC for storage
            return next_run.astimezone(pytz.UTC).replace(tzinfo=None)

        except Exception as e:
            raise ValueError(f"Invalid cron expression or timezone: {str(e)}")

    def get_next_run_times(self, cron_expression: str, timezone_str: str = "UTC", count: int = 5) -> List[datetime]:
        """Get multiple next run times for a cron expression."""
        try:
            # Parse timezone
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)

            # Create croniter instance
            cron = croniter(cron_expression, now)

            next_runs = []
            for _ in range(count):
                next_run = cron.get_next(datetime)
                # Convert to UTC for consistency
                next_runs.append(next_run.astimezone(pytz.UTC).replace(tzinfo=None))

            return next_runs

        except Exception as e:
            raise ValueError(f"Invalid cron expression or timezone: {str(e)}")

    def is_valid_cron(self, cron_expression: str) -> bool:
        """Check if a cron expression is valid."""
        try:
            croniter(cron_expression)
            return True
        except:
            return False

    def get_cron_description(self, cron_expression: str) -> str:
        """Get human-readable description of cron expression."""
        # This is a simplified version - in production you'd use a library like cron-descriptor
        parts = cron_expression.split()
        if len(parts) != 5:
            return "Invalid cron expression"

        minute, hour, day, month, weekday = parts

        descriptions = []

        if minute == "0" and hour == "0":
            descriptions.append("daily at midnight")
        elif minute == "0":
            if hour == "*":
                descriptions.append("every hour")
            else:
                descriptions.append(f"at {hour}:00")

        if day != "*":
            descriptions.append(f"on day {day}")

        if month != "*":
            descriptions.append(f"in month {month}")

        if weekday != "*":
            weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            if weekday.isdigit():
                descriptions.append(f"on {weekdays[int(weekday)]}")

        return " ".join(descriptions) if descriptions else "custom schedule"
