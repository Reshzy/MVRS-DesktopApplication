from __future__ import annotations

import os
import sys
from pathlib import Path

from app.config.settings import PROJECT_ROOT


def resource_root() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return PROJECT_ROOT


def assets_dir() -> Path:
    return resource_root() / "assets"


def placeholder_dir() -> Path:
    return assets_dir() / "placeholders"


def poster_placeholder_path() -> Path:
    return placeholder_dir() / "poster.png"


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
