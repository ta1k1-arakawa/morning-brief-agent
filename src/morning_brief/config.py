from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_ENV_FILE = ".env"
DEFAULT_TIMEZONE = "Asia/Tokyo"
DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_GMAIL_MAX_RESULTS = 10
DEFAULT_CALENDAR_LOOKAHEAD_DAYS = 2
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_GOOGLE_CALENDAR_TOKEN_FILE = "calendar_token.json"
DEFAULT_GMAIL_TOKEN_FILE = "gmail_token.json"


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str
    slack_webhook_url: str
    todoist_api_token: str
    google_client_secret_file: str
    google_calendar_token_file: str = DEFAULT_GOOGLE_CALENDAR_TOKEN_FILE
    gmail_token_file: str = DEFAULT_GMAIL_TOKEN_FILE
    timezone: str = DEFAULT_TIMEZONE
    openai_model: str = DEFAULT_OPENAI_MODEL
    gmail_max_results: int = DEFAULT_GMAIL_MAX_RESULTS
    calendar_lookahead_days: int = DEFAULT_CALENDAR_LOOKAHEAD_DAYS
    request_timeout_seconds: int = DEFAULT_REQUEST_TIMEOUT_SECONDS

    @property
    def missing_required_env_vars(self) -> tuple[str, ...]:
        missing: list[str] = []

        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.slack_webhook_url:
            missing.append("SLACK_WEBHOOK_URL")
        if not self.todoist_api_token:
            missing.append("TODOIST_API_TOKEN")
        if not self.google_client_secret_file:
            missing.append("GOOGLE_CLIENT_SECRET_FILE")

        return tuple(missing)

    def validate(self) -> None:
        missing = self.missing_required_env_vars

        if missing:
            names = ", ".join(missing)
            raise ConfigError(f"Missing required environment variables: {names}")


def load_config(
    env: Mapping[str, str] | None = None,
    env_file: str | os.PathLike[str] | None = DEFAULT_ENV_FILE,
    *,
    validate: bool = True,
) -> AppConfig:
    file_env = _load_env_file(env_file) if env_file is not None else {}
    runtime_env = os.environ if env is None else env
    source = {**file_env, **runtime_env}

    config = AppConfig(
        openai_api_key=_get_string(source, "OPENAI_API_KEY"),
        slack_webhook_url=_get_string(source, "SLACK_WEBHOOK_URL"),
        todoist_api_token=_get_string(source, "TODOIST_API_TOKEN"),
        google_client_secret_file=_get_string(source, "GOOGLE_CLIENT_SECRET_FILE"),
        google_calendar_token_file=_get_string(
            source,
            "GOOGLE_CALENDAR_TOKEN_FILE",
            DEFAULT_GOOGLE_CALENDAR_TOKEN_FILE,
        ),
        gmail_token_file=_get_string(
            source,
            "GMAIL_TOKEN_FILE",
            DEFAULT_GMAIL_TOKEN_FILE,
        ),
        timezone=_get_string(source, "APP_TIMEZONE", DEFAULT_TIMEZONE),
        openai_model=_get_string(source, "OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        gmail_max_results=_get_int(
            source,
            "GMAIL_MAX_RESULTS",
            DEFAULT_GMAIL_MAX_RESULTS,
            min_value=1,
        ),
        calendar_lookahead_days=_get_int(
            source,
            "CALENDAR_LOOKAHEAD_DAYS",
            DEFAULT_CALENDAR_LOOKAHEAD_DAYS,
            min_value=1,
        ),
        request_timeout_seconds=_get_int(
            source,
            "REQUEST_TIMEOUT_SECONDS",
            DEFAULT_REQUEST_TIMEOUT_SECONDS,
            min_value=1,
        ),
    )

    if validate:
        config.validate()

    return config


def _get_string(env: Mapping[str, str], name: str, default: str = "") -> str:
    value = env.get(name, default)
    return value.strip()


def _load_env_file(env_file: str | os.PathLike[str]) -> dict[str, str]:
    path = Path(env_file)

    if not path.exists():
        return {}

    values: dict[str, str] = {}

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line.removeprefix("export ").strip()

        if "=" not in line:
            raise ConfigError(f"{path}:{line_number} must use KEY=VALUE format")

        name, value = line.split("=", 1)
        name = name.strip()

        if not name:
            raise ConfigError(f"{path}:{line_number} has an empty variable name")

        values[name] = _strip_quotes(value.strip())

    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    return value


def _get_int(
    env: Mapping[str, str],
    name: str,
    default: int,
    *,
    min_value: int,
) -> int:
    value = _get_string(env, name)

    if not value:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc

    if parsed < min_value:
        raise ConfigError(f"{name} must be at least {min_value}")

    return parsed
