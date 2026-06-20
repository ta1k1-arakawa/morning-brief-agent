from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from morning_brief.models import EmailItem
from morning_brief.utils.datetime_utils import format_datetime


GOOGLE_READONLY_SCOPES = (
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
)
BRIEF_QUERY = "is:unread OR is:important"


class GmailServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class GmailService:
    client_secret_file: str
    token_file: str = "token.json"
    timezone: str = "Asia/Tokyo"
    max_results: int = 10

    def get_emails_for_brief(self) -> tuple[EmailItem, ...]:
        if self.max_results < 1:
            raise GmailServiceError("max_results must be at least 1")

        try:
            credentials = self._load_credentials()
            service = build(
                "gmail",
                "v1",
                credentials=credentials,
                cache_discovery=False,
            )
            message_ids = self._get_message_ids(service)
            messages = tuple(
                self._get_message(service, message_id)
                for message_id in message_ids
            )
            return tuple(self._to_email_item(message) for message in messages)
        except HttpError as exc:
            status = getattr(exc.resp, "status", "unknown")
            raise GmailServiceError(f"Gmail API returned HTTP {status}") from exc
        except (GoogleAuthError, OSError, ValueError) as exc:
            raise GmailServiceError(f"Failed to access Gmail: {exc}") from exc

    def _load_credentials(self) -> Credentials:
        token_path = Path(self.token_file)
        credentials: Credentials | None = None

        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(token_path),
                GOOGLE_READONLY_SCOPES,
            )

        has_required_scopes = bool(
            credentials and credentials.has_scopes(GOOGLE_READONLY_SCOPES)
        )

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
            and has_required_scopes
        ):
            credentials.refresh(Request())

        if not credentials or not credentials.valid or not has_required_scopes:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secret_file,
                GOOGLE_READONLY_SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    def _get_message_ids(self, service: Any) -> list[str]:
        message_ids: list[str] = []
        page_token: str | None = None

        while len(message_ids) < self.max_results:
            remaining = self.max_results - len(message_ids)
            response = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    q=BRIEF_QUERY,
                    maxResults=min(remaining, 500),
                    pageToken=page_token,
                    fields="messages/id,nextPageToken",
                )
                .execute()
            )

            for message in response.get("messages", []):
                message_id = message.get("id")
                if message_id:
                    message_ids.append(str(message_id))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return message_ids[: self.max_results]

    def _get_message(self, service: Any, message_id: str) -> dict[str, Any]:
        return (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
                fields="id,labelIds,internalDate,snippet,payload/headers",
            )
            .execute()
        )

    def _to_email_item(self, message: dict[str, Any]) -> EmailItem:
        payload = message.get("payload", {})
        headers = self._get_headers(payload.get("headers", []))
        label_ids = message.get("labelIds", [])

        return EmailItem(
            sender=headers.get("from", "(送信者不明)"),
            subject=headers.get("subject", "(件名なし)"),
            received_at=self._get_received_at(message, headers),
            snippet=str(message.get("snippet") or "").strip(),
            is_unread="UNREAD" in label_ids,
        )

    def _get_headers(self, raw_headers: Any) -> dict[str, str]:
        if not isinstance(raw_headers, list):
            return {}

        return {
            str(header.get("name", "")).lower(): str(header.get("value", ""))
            for header in raw_headers
            if isinstance(header, dict) and header.get("name")
        }

    def _get_received_at(
        self,
        message: dict[str, Any],
        headers: dict[str, str],
    ) -> str:
        internal_date = message.get("internalDate")

        if internal_date:
            received = datetime.fromtimestamp(
                int(internal_date) / 1000,
                tz=timezone.utc,
            )
            return format_datetime(received, self.timezone)

        return headers.get("date", "")
