import logging

from app.database.base import Base
from app.database.session import engine
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def init_database() -> None:
    from app.models import load_models

    load_models()
    logger.info("Initializing database url=%s", engine.url)
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")
