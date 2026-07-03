from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from morning_brief.models import TodoistTask
from morning_brief.utils.datetime_utils import today_in_timezone

TODOIST_API_BASE_URL = "https://api.todoist.com/api/v1"
BRIEF_FILTER = "#インボックス & (today | overdue | p1 | p2)"


class TodoistServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class TodoistService:
    api_token: str
    timezone: str = "Asia/Tokyo"
    timeout_seconds: int = 30

    def get_tasks_for_brief(self) -> tuple[TodoistTask, ...]:
        today = today_in_timezone(self.timezone)
        project_names = self._get_project_names()
        task_items = self._get_all_pages("/tasks", {"filter": BRIEF_FILTER})

        tasks = tuple(
            self._to_task(item, project_names, today) for item in task_items
        )

        return tuple(
            sorted(
                tasks,
                key=lambda task: (
                    not task.is_overdue,
                    -task.priority,
                    task.due or "9999-12-31",
                    task.content.casefold(),
                ),
            )
        )

    def _get_project_names(self) -> dict[str, str]:
        projects = self._get_all_pages("/projects")
        return {
            str(project["id"]): str(project.get("name", ""))
            for project in projects
            if "id" in project
        }

    def _get_all_pages(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        query = dict(params or {})

        while True:
            response = self._request(path, query)
            page_items = response.get("results", [])

            if not isinstance(page_items, list):
                raise TodoistServiceError("Todoist API returned invalid results")

            items.extend(item for item in page_items if isinstance(item, dict))

            next_cursor = response.get("next_cursor")
            if not next_cursor:
                return items

            query["cursor"] = str(next_cursor)

    def _request(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        query_string = urlencode(params)
        url = f"{TODOIST_API_BASE_URL}{path}"

        if query_string:
            url = f"{url}?{query_string}"

        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise TodoistServiceError(
                f"Todoist API returned HTTP {exc.code}"
            ) from exc
        except URLError as exc:
            raise TodoistServiceError(f"Failed to call Todoist API: {exc}") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise TodoistServiceError("Todoist API returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise TodoistServiceError("Todoist API returned an invalid response")

        return payload

    def _to_task(
        self,
        item: dict[str, Any],
        project_names: dict[str, str],
        today: date,
    ) -> TodoistTask:
        due = item.get("due")
        due_data = due if isinstance(due, dict) else {}
        due_value = str(due_data.get("datetime") or due_data.get("date") or "")
        due_date = str(due_data.get("date") or "")[:10]
        project_id = str(item.get("project_id", ""))

        return TodoistTask(
            content=str(item.get("content", "")).strip(),
            due=due_value,
            priority=self._get_priority(item.get("priority")),
            project=project_names.get(project_id, ""),
            is_overdue=bool(due_date and due_date < today.isoformat()),
        )

    def _get_priority(self, value: Any) -> int:
        try:
            priority = int(value)
        except (TypeError, ValueError):
            return 1

        return priority if 1 <= priority <= 4 else 1
