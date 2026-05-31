from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    start: str
    end: str
    location: str = ""
    description: str = ""
    is_all_day: bool = False


@dataclass(frozen=True)
class EmailItem:
    sender: str
    subject: str
    received_at: str
    snippet: str = ""
    is_unread: bool = True


@dataclass(frozen=True)
class TodoistTask:
    content: str
    due: str = ""
    priority: int = 1
    project: str = ""
    is_overdue: bool = False


@dataclass(frozen=True)
class DailyBriefing:
    calendar_events: tuple[CalendarEvent, ...] = field(default_factory=tuple)
    emails: tuple[EmailItem, ...] = field(default_factory=tuple)
    tasks: tuple[TodoistTask, ...] = field(default_factory=tuple)
    summary: str = ""
