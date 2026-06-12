import logging
import sys


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%H:%M:%S"

    logging.basicConfig(
        level = level, format=fmt, datefmt=datefmt, stream=sys.stdout, force=True,
    )

    for noisy in ("httpx", "httpcore", "openai", "langchain", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)