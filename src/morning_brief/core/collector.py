from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Protocol, Sequence, TypeVar

if TYPE_CHECKING:
    from morning_brief.models import CalendarEvent, EmailItem, TodoistTask


T = TypeVar("T")


class CalendarService(Protocol):
    def get_events_for_brief(self) -> Sequence[CalendarEvent]:
        """Return calendar events that should be considered for the brief."""


class GmailService(Protocol):
    def get_emails_for_brief(self) -> Sequence[EmailItem]:
        """Return email summaries that should be considered for the brief."""


class TodoistService(Protocol):
    def get_tasks_for_brief(self) -> Sequence[TodoistTask]:
        """Return Todoist tasks that should be considered for the brief."""


@dataclass(frozen=True)
class SourceFailure:
    source: str
    message: str


class CollectionFailedError(RuntimeError):
    pass


@dataclass(frozen=True)
class CollectedBriefData:
    calendar_events: tuple[CalendarEvent, ...] = field(default_factory=tuple)
    emails: tuple[EmailItem, ...] = field(default_factory=tuple)
    tasks: tuple[TodoistTask, ...] = field(default_factory=tuple)
    failures: tuple[SourceFailure, ...] = field(default_factory=tuple)

    @property
    def has_failures(self) -> bool:
        return bool(self.failures)


@dataclass(frozen=True)
class BriefCollector:
    calendar_service: CalendarService
    gmail_service: GmailService
    todoist_service: TodoistService
    strict: bool = False

    def collect(self) -> CollectedBriefData:
        failures: list[SourceFailure] = []

        calendar_events = self._collect_source(
            "calendar",
            self.calendar_service.get_events_for_brief,
            failures,
        )
        emails = self._collect_source(
            "gmail",
            self.gmail_service.get_emails_for_brief,
            failures,
        )
        tasks = self._collect_source(
            "todoist",
            self.todoist_service.get_tasks_for_brief,
            failures,
        )

        return CollectedBriefData(
            calendar_events=calendar_events,
            emails=emails,
            tasks=tasks,
            failures=tuple(failures),
        )

    def _collect_source(
        self,
        source: str,
        loader: Callable[[], Sequence[T]],
        failures: list[SourceFailure],
    ) -> tuple[T, ...]:
        try:
            return tuple(loader())
        except Exception as exc:
            if self.strict:
                raise CollectionFailedError(
                    f"Failed to collect data from {source}: {exc}"
                ) from exc

            failures.append(SourceFailure(source=source, message=str(exc)))
            return ()
