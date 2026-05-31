from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Tokyo"


@dataclass(frozen=True)
class DateTimeRange:
    start: datetime
    end: datetime

    @property
    def start_iso(self) -> str:
        return self.start.isoformat()

    @property
    def end_iso(self) -> str:
        return self.end.isoformat()


def get_timezone(timezone: str = DEFAULT_TIMEZONE) -> ZoneInfo:
    return ZoneInfo(timezone)


def now_in_timezone(timezone: str = DEFAULT_TIMEZONE) -> datetime:
    return datetime.now(get_timezone(timezone))


def today_in_timezone(timezone: str = DEFAULT_TIMEZONE) -> date:
    return now_in_timezone(timezone).date()


def tomorrow_in_timezone(timezone: str = DEFAULT_TIMEZONE) -> date:
    return today_in_timezone(timezone) + timedelta(days=1)


def day_range(
    target_date: date | None = None,
    timezone: str = DEFAULT_TIMEZONE,
) -> DateTimeRange:
    tz = get_timezone(timezone)
    current_date = today_in_timezone(timezone) if target_date is None else target_date
    start = datetime.combine(current_date, time.min, tzinfo=tz)
    end = start + timedelta(days=1)

    return DateTimeRange(start=start, end=end)


def calendar_time_window(
    days: int,
    timezone: str = DEFAULT_TIMEZONE,
) -> DateTimeRange:
    if days < 1:
        raise ValueError("days must be at least 1")

    start = day_range(timezone=timezone).start
    end = start + timedelta(days=days)

    return DateTimeRange(start=start, end=end)


def format_date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def format_datetime(
    value: datetime,
    timezone: str = DEFAULT_TIMEZONE,
) -> str:
    tz = get_timezone(timezone)

    if value.tzinfo is None:
        localized = value.replace(tzinfo=tz)
    else:
        localized = value.astimezone(tz)

    return localized.strftime("%Y-%m-%d %H:%M")
