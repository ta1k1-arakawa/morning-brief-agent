from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from morning_brief.config import AppConfig, ConfigError, load_config
from morning_brief.core.collector import BriefCollector, CollectedBriefData
from morning_brief.core.summarizer import BriefSummarizer, SummaryResult
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


def run(services: AppServices) -> SummaryResult:
    logger.info("Collecting morning brief data")
    data = services.collector.collect()
    _log_collection_failures(data)

    logger.info("Generating morning brief summary")
    result = services.summarizer.summarize(data)

    logger.info("Sending morning brief to Slack")
    services.slack_notifier.send_message(result.summary)

    logger.info("Morning brief completed")
    return result


def build_services(config: AppConfig) -> AppServices:
    _ = config
    raise NotImplementedError(
        "Service clients are not implemented yet. "
        "Create services/google_calendar.py, services/gmail.py, "
        "services/todoist.py, services/openai_client.py, and services/slack.py first."
    )


def main() -> int:
    configure_logging()

    try:
        config = load_config()
        services = build_services(config)
        run(services)
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 2
    except NotImplementedError as exc:
        logger.error("%s", exc)
        return 3
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


if __name__ == "__main__":
    raise SystemExit(main())
