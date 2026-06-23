from __future__ import annotations

import logging
import sys

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: str = "INFO",
    *,
    force: bool = False,
) -> None:
    logging.basicConfig(
        level=_parse_log_level(level),
        format=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
        stream=sys.stdout,
        force=force,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _parse_log_level(level: str) -> int:
    normalized = level.strip().upper()

    if not normalized:
        return logging.INFO

    parsed = logging.getLevelName(normalized)

    if isinstance(parsed, int):
        return parsed

    raise ValueError(f"Unknown log level: {level}")
