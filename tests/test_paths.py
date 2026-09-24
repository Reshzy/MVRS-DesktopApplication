from __future__ import annotations

from pathlib import Path

from app.database.session import _resolve_database_url
from app.ui.theme import THEME_PATH, load_stylesheet
from app.utils.paths import (
    app_data_dir,
    assets_dir,
    default_sqlite_path,
    env_file_candidates,
    icons_dir,
    image_cache_dir,
    placeholder_dir,
    poster_placeholder_path,
    project_root,
    resource_root,
    theme_qss_path,
)


def test_resource_helpers_point_at_project_assets() -> None:
    assert resource_root() == project_root()
    assert assets_dir() == project_root() / "assets"
    assert placeholder_dir() == project_root() / "assets" / "placeholders"
    assert icons_dir() == project_root() / "assets" / "icons"
    assert theme_qss_path().exists()
    assert theme_qss_path() == THEME_PATH
    assert poster_placeholder_path().exists()
    load_stylesheet()


def test_app_data_uses_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MVRS_DATA_DIR", str(tmp_path / "data"))

    data_dir = app_data_dir()
    cache_dir = image_cache_dir()

    assert data_dir == tmp_path / "data"
    assert data_dir.is_dir()
    assert cache_dir == data_dir / "image_cache"
    assert cache_dir.is_dir()
    assert default_sqlite_path() == data_dir / "movie_recommendation.db"


def test_relative_sqlite_url_resolves_to_app_data(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MVRS_DATA_DIR", str(tmp_path / "data"))

    resolved = _resolve_database_url("sqlite:///movie_recommendation.db")
    expected = (tmp_path / "data" / "movie_recommendation.db").resolve()
    assert resolved == f"sqlite:///{expected.as_posix()}"
    assert expected.parent.is_dir()


def test_absolute_sqlite_url_is_preserved(tmp_path: Path) -> None:
    target = (tmp_path / "custom.db").resolve()
    resolved = _resolve_database_url(f"sqlite:///{target.as_posix()}")
    assert resolved == f"sqlite:///{target.as_posix()}"


def test_env_candidates_include_project_root() -> None:
    candidates = env_file_candidates()
    assert project_root() / ".env" in candidates
