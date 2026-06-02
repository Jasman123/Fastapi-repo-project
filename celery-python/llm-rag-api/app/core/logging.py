import logging
import structlog
import os

def setup_logging(level: str = "INFO") -> None:
    is_dev = os.getenv("APP_ENV", "development") == "development"
    renderer = (
        structlog.dev.ConsoleRenderer(colors=True)
        if is_dev
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    logging.basicConfig(
        level = getattr(logging, level.upper()),
        format="%(message)s",
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chroma").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str = __name__):
    return structlog.get_logger(name)