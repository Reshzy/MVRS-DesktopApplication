from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", None))


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def executable_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return project_root()


def resource_root() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return project_root()


def assets_dir() -> Path:
    return resource_root() / "assets"


def icons_dir() -> Path:
    return assets_dir() / "icons"


def images_dir() -> Path:
    return assets_dir() / "images"


def placeholder_dir() -> Path:
    return assets_dir() / "placeholders"


def poster_placeholder_path() -> Path:
    return placeholder_dir() / "poster.png"


def app_icon_path() -> Path:
    for name in ("app.ico", "app.png"):
        candidate = icons_dir() / name
        if candidate.exists():
            return candidate
    return icons_dir() / "app.ico"


def theme_qss_path() -> Path:
    bundled = resource_root() / "app" / "ui" / "theme" / "theme.qss"
    if bundled.exists():
        return bundled
    return project_root() / "app" / "ui" / "theme" / "theme.qss"


def app_data_dir() -> Path:
    override = os.getenv("MVRS_DATA_DIR")
    if override:
        path = Path(override)
    elif os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home())
        path = root / "MovieRecommendationSystem"
    else:
        path = Path.home() / ".movie_recommendation"
    path.mkdir(parents=True, exist_ok=True)
    return path


def image_cache_dir() -> Path:
    path = app_data_dir() / "image_cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_sqlite_path() -> Path:
    return app_data_dir() / "movie_recommendation.db"


def env_file_candidates() -> list[Path]:
    if is_frozen():
        return [executable_dir() / ".env", app_data_dir() / ".env"]
    return [project_root() / ".env", app_data_dir() / ".env"]
