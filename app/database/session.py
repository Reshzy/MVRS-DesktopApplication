from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings
from app.utils.paths import app_data_dir


def _resolve_database_url(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url

    raw_path = database_url.removeprefix(prefix)
    path = Path(raw_path)
    if path.is_absolute() or (len(raw_path) > 1 and raw_path[1] == ":"):
        resolved = path
    else:
        resolved = app_data_dir() / path
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return f"{prefix}{resolved.resolve().as_posix()}"


def create_db_engine() -> Engine:
    settings = get_settings()
    database_url = _resolve_database_url(settings.database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, echo=False, connect_args=connect_args)


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
