import logging
import sys

from app.utils.paths import log_dir

LOGGER_NAME = "movie_recommendation"


def setup_logging(level: int = logging.INFO) -> None:
    log_path = log_dir() / "app.log"
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logging.basicConfig(
        level=level,
        handlers=[stream, file_handler],
        force=True,
    )
    logging.getLogger(LOGGER_NAME).info("Application starting")
