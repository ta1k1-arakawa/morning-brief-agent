from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SlackNotificationError(RuntimeError):
    pass


@dataclass(frozen=True)
class SlackWebhookNotifier:
    webhook_url: str
    timeout_seconds: int = 30

    def send_message(self, text: str) -> None:
        message = text.strip()

        if not message:
            raise SlackNotificationError("Slack message must not be empty")

        payload = json.dumps({"text": message}).encode("utf-8")
        request = Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status = response.status
        except HTTPError as exc:
            raise SlackNotificationError(
                f"Slack webhook returned HTTP {exc.code}"
            ) from exc
        except URLError as exc:
            raise SlackNotificationError(
                f"Failed to call Slack webhook: {exc}"
            ) from exc

        if status >= 400:
            raise SlackNotificationError(f"Slack webhook returned HTTP {status}")
