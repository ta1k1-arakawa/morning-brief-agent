from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Protocol

from morning_brief.config import AppConfig, ConfigError, load_config
from morning_brief.core.collector import BriefCollector, CollectedBriefData
from morning_brief.core.summarizer import BriefSummarizer, SummaryResult
from morning_brief.services.gmail import GmailService
from morning_brief.services.google_calendar import GoogleCalendarService
from morning_brief.services.openai_client import OpenAIClient
from morning_brief.services.slack import SlackWebhookNotifier
from morning_brief.services.todoist import TodoistService
from morning_brief.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


class SlackNotifier(Protocol):
    def send_message(self, text: str) -> None:
        """Send a message to Slack."""


@dataclass(frozen=True)
class AppServices:
    collector: BriefCollector
    summarizer: BriefSummarizer
    slack_notifier: SlackNotifier


def run(
    services: AppServices,
    *,
    show_emails: bool = False,
) -> SummaryResult:
    logger.info("Collecting morning brief data")
    data = services.collector.collect()
    _log_collection_failures(data)

    if show_emails:
        _print_collected_emails(data)

    logger.info("Generating morning brief summary")
    result = services.summarizer.summarize(data)

    logger.info("Sending morning brief to Slack")
    services.slack_notifier.send_message(result.summary)

    logger.info("Morning brief completed")
    return result


def build_services(config: AppConfig) -> AppServices:
    calendar_service = GoogleCalendarService(
        client_secret_file=config.google_client_secret_file,
        token_file=config.google_calendar_token_file,
        timezone=config.timezone,
        lookahead_days=config.calendar_lookahead_days,
    )
    gmail_service = GmailService(
        client_secret_file=config.google_client_secret_file,
        token_file=config.gmail_token_file,
        timezone=config.timezone,
        max_results=config.gmail_max_results,
    )
    todoist_service = TodoistService(
        api_token=config.todoist_api_token,
        timezone=config.timezone,
        timeout_seconds=config.request_timeout_seconds,
    )
    openai_client = OpenAIClient(
        api_key=config.openai_api_key,
        model=config.openai_model,
        timeout_seconds=config.request_timeout_seconds,
    )
    slack_notifier = SlackWebhookNotifier(
        webhook_url=config.slack_webhook_url,
        timeout_seconds=config.request_timeout_seconds,
    )

    collector = BriefCollector(
        calendar_service=calendar_service,
        gmail_service=gmail_service,
        todoist_service=todoist_service,
    )
    summarizer = BriefSummarizer(openai_client=openai_client)

    return AppServices(
        collector=collector,
        summarizer=summarizer,
        slack_notifier=slack_notifier,
    )


def main() -> int:
    args = _parse_args()
    configure_logging()

    try:
        config = load_config()
        services = build_services(config)
        run(services, show_emails=args.show_emails)
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 2
    except Exception:
        logger.exception("Morning brief failed")
        return 1

    return 0


def _log_collection_failures(data: CollectedBriefData) -> None:
    for failure in data.failures:
        logger.warning(
            "Failed to collect %s data: %s",
            failure.source,
            failure.message,
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a morning brief")
    parser.add_argument(
        "--show-emails",
        action="store_true",
        help="show every fetched email summary in the terminal",
    )
    return parser.parse_args()


def _print_collected_emails(data: CollectedBriefData) -> None:
    print(f"\n取得したメール: {len(data.emails)}件")

    if not data.emails:
        print("対象メールはありません。")
        return

    for index, email in enumerate(data.emails, start=1):
        read_status = "未読" if email.is_unread else "既読"
        print(f"\n[{index}] {email.subject}")
        print(f"送信者: {email.sender}")
        print(f"受信日時: {email.received_at}")
        print(f"状態: {read_status}")
        print(f"スニペット: {email.snippet or '(なし)'}")


if __name__ == "__main__":
    raise SystemExit(main())
