import json
import logging
import logging.config
import os
import sys
from contextvars import ContextVar


correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="system")


class CorrelationIDFilter(logging.Filter):
    """
    Injects correlation_id into every log record so you never get a
        # a log line without it, even outside of a request context.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = correlation_id_var.get()
        return True


class DevFormatter(logging.Formatter):
    """
    A developer-friendly formatter that displays extra data clearly.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Start with the standard format
        log_line = super().format(record)

        # Check for any extra data and append it
        extra_data = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__
            and k not in ("message", "asctime", "levelname", "name", "correlation_id")
        }

        if extra_data:
            # Pretty print the extra data
            import json

            extra_str = json.dumps(extra_data, indent=2, default=str)
            log_line += f"\n--- extra data ---\n{extra_str}\n------------------"

        return log_line


class JSONFormatter(logging.Formatter):
    """Simple typed JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "system"),
            "dd.trace_id": getattr(record, "dd.trace_id", None),
            "dd.span_id": getattr(record, "dd.span_id", None),
            "dd.env": getattr(record, "dd.env", None),
            "dd.service": getattr(record, "dd.service", None),
            "dd.version": getattr(record, "dd.version", None),
        }

        extra_data = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__
            and k
            not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "asctime",
                "correlation_id",
            }
        }

        if extra_data:
            log_record["extra"] = extra_data

        return json.dumps(log_record, default=str)


def build_logging_config(log_level: str, use_json: bool) -> dict[str, object]:
    """
    Builds the logging config dict dynamically.
    use_json=True  → structured JSON  (production / staging)
    use_json=False → readable text    (local development)
    """
    formatter = (
        {
            "()": JSONFormatter,
            "fmt": "%(message)s %(levelname)s %(name)s",
        }
        if use_json
        else {
            "()": DevFormatter,
            "format": "%(asctime)s [%(levelname)s] %(name)s [%(correlation_id)s]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    )

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": CorrelationIDFilter,
            }
        },
        "formatters": {
            "default": formatter,
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
                "filters": ["correlation_id"],
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "WARNING",  # Suppress per-request access logs — your
                "propagate": False,  # CorrelationIDMiddleware handles those
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": os.getenv("SQLALCHEMY_LOG_LEVEL", "WARNING"),
                "propagate": False,
            },
        },
    }


def setup_logging() -> None:
    env = os.getenv("APP_ENV", "development")
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    use_json = env in ("production", "staging")

    logging.config.dictConfig(build_logging_config(level, use_json))

    # Bootstrap ddtrace log injection.
    # This monkey-patches the logging system to automatically add
    # dd.trace_id / dd.span_id to every LogRecord when a trace is active.
    if use_json:
        try:
            from ddtrace import patch

            patch(logging=True)
            logging.getLogger(__name__).info(
                "ddtrace log injection enabled",
                extra={"env": env},
            )
        except ImportError:
            logging.getLogger(__name__).warning(
                "ddtrace not installed — Datadog trace correlation disabled"
            )
