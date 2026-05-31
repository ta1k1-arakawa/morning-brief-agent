from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable

from morning_brief.core.collector import CollectedBriefData, SourceFailure

if TYPE_CHECKING:
    from morning_brief.models import CalendarEvent, EmailItem, TodoistTask


@dataclass(frozen=True)
class PromptBuilder:
    language: str = "ja"

    def build(self, data: CollectedBriefData) -> str:
        sections = [
            self._build_role_section(),
            self._build_output_rules_section(),
            self._build_calendar_section(data.calendar_events),
            self._build_email_section(data.emails),
            self._build_task_section(data.tasks),
        ]

        if data.failures:
            sections.append(self._build_failures_section(data.failures))

        return "\n\n".join(section for section in sections if section.strip())

    def _build_role_section(self) -> str:
        return (
            "あなたは個人の予定・メール・タスクを整理する朝の秘書です。\n"
            "以下の情報をもとに、今日の優先順位が一目で分かる行動サマリーを作ってください。"
        )

    def _build_output_rules_section(self) -> str:
        language_rule = (
            "- 日本語で簡潔に書く"
            if self.language == "ja"
            else f"- {self.language}で簡潔に書く"
        )

        return "\n".join(
            [
                "出力ルール:",
                language_rule,
                "- 重要なものから順に並べる",
                "- 個人情報を必要以上に詳しく書かない",
                "- メール本文を推測で補わない",
                "- 予定・メール・タスクに根拠がないことは断定しない",
                "- 次の見出しを使う: 今日絶対にやること / できればやること / 返信・確認が必要そうなメール / 今日の予定 / 注意点 / 今日やらなくてもよいもの",
            ]
        )

    def _build_calendar_section(self, events: Iterable[CalendarEvent]) -> str:
        lines = ["予定:"]
        event_lines = [self._format_event(event) for event in events]
        lines.extend(event_lines or ["- 予定はありません"])
        return "\n".join(lines)

    def _build_email_section(self, emails: Iterable[EmailItem]) -> str:
        lines = ["メール:"]
        email_lines = [self._format_email(email) for email in emails]
        lines.extend(email_lines or ["- 対象メールはありません"])
        return "\n".join(lines)

    def _build_task_section(self, tasks: Iterable[TodoistTask]) -> str:
        lines = ["タスク:"]
        task_lines = [self._format_task(task) for task in tasks]
        lines.extend(task_lines or ["- 対象タスクはありません"])
        return "\n".join(lines)

    def _build_failures_section(self, failures: Iterable[SourceFailure]) -> str:
        lines = ["取得に失敗した情報:"]
        lines.extend(f"- {failure.source}: {failure.message}" for failure in failures)
        return "\n".join(lines)

    def _format_event(self, event: CalendarEvent) -> str:
        title = _read_value(event, "title", "summary", default="無題の予定")
        start = _read_value(event, "start", "start_time", default="開始時刻不明")
        end = _read_value(event, "end", "end_time", default="終了時刻不明")
        location = _read_value(event, "location", default="場所なし")

        return f"- {start} - {end}: {title} ({location})"

    def _format_email(self, email: EmailItem) -> str:
        sender = _read_value(email, "sender", "from_", "from", default="送信者不明")
        subject = _read_value(email, "subject", default="件名なし")
        received_at = _read_value(email, "received_at", "date", default="受信日時不明")
        snippet = _read_value(email, "snippet", default="本文要約なし")

        return f"- {received_at} / {sender} / {subject}: {snippet}"

    def _format_task(self, task: TodoistTask) -> str:
        content = _read_value(task, "content", "title", default="無題のタスク")
        due = _read_value(task, "due", "due_date", default="期限なし")
        priority = _read_value(task, "priority", default="優先度不明")

        return f"- {content} / 期限: {due} / 優先度: {priority}"


def build_brief_prompt(data: CollectedBriefData) -> str:
    return PromptBuilder().build(data)


def _read_value(item: Any, *names: str, default: str) -> str:
    for name in names:
        if isinstance(item, dict):
            value = item.get(name)
        else:
            value = getattr(item, name, None)

        if value not in (None, ""):
            return str(value)

    return default
