import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog + stdlib logging once at startup.

    json_logs=True emits one JSON object per line (prod / log aggregation).
    json_logs=False emits colorized console output (local dev).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # route stdlib logging (uvicorn, etc.) through the same level
    logging.basicConfig(level=level, handlers=[logging.StreamHandler(sys.stdout)])


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
