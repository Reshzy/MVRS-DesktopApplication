from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models import load_models
from app.services.auth_service import AuthService
from app.state.app_state import AppState
from app.ui.app_window import MainWindow
from app.ui.theme import apply_theme
from tests.fakes import FakeMovieService


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


@pytest.fixture()
def themed_app(qapp: QApplication) -> QApplication:
    apply_theme(qapp)
    return qapp


@pytest.fixture()
def movie_service() -> FakeMovieService:
    return FakeMovieService()


@pytest.fixture()
def main_window(
    qtbot,
    themed_app: QApplication,
    auth_service: AuthService,
    app_state: AppState,
    movie_service: FakeMovieService,
) -> MainWindow:
    window = MainWindow(
        auth_service=auth_service,
        app_state=app_state,
        confirm_logout=lambda **_kwargs: True,
        movie_service=movie_service,
    )
    qtbot.addWidget(window)
    window.show()
    return window
