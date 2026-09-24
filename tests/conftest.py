from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models import load_models
from app.services.auth_service import AuthService
from app.state.app_state import AppState


@pytest.fixture()
def db_session(tmp_path: Path) -> Iterator[Session]:
    load_models()
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}", future=True)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def app_state() -> AppState:
    return AppState()


@pytest.fixture()
def auth_service(db_session: Session, app_state: AppState) -> AuthService:
    return AuthService(db_session, app_state)
