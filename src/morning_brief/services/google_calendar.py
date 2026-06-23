from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from morning_brief.models import CalendarEvent
from morning_brief.utils.datetime_utils import calendar_time_window

GOOGLE_CALENDAR_READONLY_SCOPES = (
    "https://www.googleapis.com/auth/calendar.readonly",
)


class GoogleCalendarServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoogleCalendarService:
    client_secret_file: str
    token_file: str = "token.json"
    timezone: str = "Asia/Tokyo"
    lookahead_days: int = 2

    def get_events_for_brief(self) -> tuple[CalendarEvent, ...]:
        if self.lookahead_days < 1:
            raise GoogleCalendarServiceError("lookahead_days must be at least 1")

        try:
            credentials = self._load_credentials()
            service = build(
                "calendar",
                "v3",
                credentials=credentials,
                cache_discovery=False,
            )
            items = self._get_all_event_pages(service)
        except HttpError as exc:
            status = getattr(exc.resp, "status", "unknown")
            raise GoogleCalendarServiceError(
                f"Google Calendar API returned HTTP {status}"
            ) from exc
        except (GoogleAuthError, OSError, ValueError) as exc:
            raise GoogleCalendarServiceError(
                f"Failed to access Google Calendar: {exc}"
            ) from exc

        return tuple(self._to_calendar_event(item) for item in items)

    def _load_credentials(self) -> Credentials:
        token_path = Path(self.token_file)
        credentials: Credentials | None = None

        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(token_path),
                GOOGLE_CALENDAR_READONLY_SCOPES,
            )

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        elif not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secret_file,
                GOOGLE_CALENDAR_READONLY_SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    def _get_all_event_pages(self, service: Any) -> list[dict[str, Any]]:
        time_window = calendar_time_window(
            days=self.lookahead_days,
            timezone=self.timezone,
        )
        items: list[dict[str, Any]] = []
        page_token: str | None = None

        while True:
            response = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_window.start_iso,
                    timeMax=time_window.end_iso,
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=page_token,
                )
                .execute()
            )

            page_items = response.get("items", [])
            items.extend(item for item in page_items if isinstance(item, dict))

            page_token = response.get("nextPageToken")
            if not page_token:
                return items

    def _to_calendar_event(self, item: dict[str, Any]) -> CalendarEvent:
        start_data = item.get("start", {})
        end_data = item.get("end", {})
        is_all_day = "date" in start_data

        return CalendarEvent(
            title=str(item.get("summary") or "(タイトルなし)"),
            start=str(start_data.get("dateTime") or start_data.get("date") or ""),
            end=str(end_data.get("dateTime") or end_data.get("date") or ""),
            location=str(item.get("location") or ""),
            description=str(item.get("description") or ""),
            is_all_day=is_all_day,
        )
