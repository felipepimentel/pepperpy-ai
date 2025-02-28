"""Date utilities.

This module provides utilities for working with dates and times.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union


class DateUtils:
    """Utility functions for date manipulation."""

    DEFAULT_TIMEZONE = timezone.utc
    DEFAULT_DATE_FORMAT = "%Y-%m-%d"
    DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def now(tz: Optional[timezone] = None) -> datetime:
        """Get current datetime.

        Args:
            tz: Timezone object

        Returns:
            Current datetime
        """
        tz = tz or DateUtils.DEFAULT_TIMEZONE
        return datetime.now(tz)

    @staticmethod
    def today(tz: Optional[timezone] = None) -> datetime:
        """Get current date at midnight.

        Args:
            tz: Timezone object

        Returns:
            Current date at midnight
        """
        return DateUtils.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def parse_date(
        date_str: str, format: Optional[str] = None, tz: Optional[timezone] = None
    ) -> datetime:
        """Parse date string.

        Args:
            date_str: Date string
            format: Date format
            tz: Timezone object

        Returns:
            Parsed datetime
        """
        format = format or DateUtils.DEFAULT_DATE_FORMAT
        dt = datetime.strptime(date_str, format)
        if tz:
            dt = dt.replace(tzinfo=tz)
        return dt

    @staticmethod
    def format_date(
        dt: datetime, format: Optional[str] = None, tz: Optional[timezone] = None
    ) -> str:
        """Format datetime.

        Args:
            dt: Datetime to format
            format: Date format
            tz: Timezone object

        Returns:
            Formatted date string
        """
        format = format or DateUtils.DEFAULT_DATE_FORMAT
        if tz and dt.tzinfo != tz:
            dt = dt.astimezone(tz)
        return dt.strftime(format)

    @staticmethod
    def add_days(dt: datetime, days: int) -> datetime:
        """Add days to datetime.

        Args:
            dt: Base datetime
            days: Number of days to add

        Returns:
            New datetime
        """
        return dt + timedelta(days=days)

    @staticmethod
    def add_hours(dt: datetime, hours: int) -> datetime:
        """Add hours to datetime.

        Args:
            dt: Base datetime
            hours: Number of hours to add

        Returns:
            New datetime
        """
        return dt + timedelta(hours=hours)

    @staticmethod
    def add_minutes(dt: datetime, minutes: int) -> datetime:
        """Add minutes to datetime.

        Args:
            dt: Base datetime
            minutes: Number of minutes to add

        Returns:
            New datetime
        """
        return dt + timedelta(minutes=minutes)

    @staticmethod
    def days_between(start: datetime, end: datetime) -> int:
        """Calculate days between dates.

        Args:
            start: Start date
            end: End date

        Returns:
            Number of days
        """
        return (end - start).days

    @staticmethod
    def is_weekend(dt: datetime) -> bool:
        """Check if date is weekend.

        Args:
            dt: Date to check

        Returns:
            True if weekend
        """
        return dt.weekday() >= 5

    @staticmethod
    def is_business_day(dt: datetime) -> bool:
        """Check if date is business day.

        Args:
            dt: Date to check

        Returns:
            True if business day
        """
        return not DateUtils.is_weekend(dt)

    @staticmethod
    def get_month_start(dt: datetime) -> datetime:
        """Get first day of month.

        Args:
            dt: Reference date

        Returns:
            First day of month
        """
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def get_month_end(dt: datetime) -> datetime:
        """Get last day of month.

        Args:
            dt: Reference date

        Returns:
            Last day of month
        """
        next_month = dt.replace(day=28) + timedelta(days=4)
        return next_month.replace(day=1) - timedelta(days=1)

    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC datetime.

        Returns:
            Current UTC datetime
        """
        return datetime.now(timezone.utc)

    @staticmethod
    def from_timestamp(timestamp: Union[int, float]) -> datetime:
        """Convert timestamp to datetime.

        Args:
            timestamp: Unix timestamp

        Returns:
            Datetime object
        """
        return datetime.fromtimestamp(timestamp, timezone.utc)
