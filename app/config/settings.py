import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseModel):
    app_name: str = "Movie Recommendation System"
    tmdb_api_key: str = ""
    tmdb_access_token: str = ""
    database_url: str = "sqlite:///movie_recommendation.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Movie Recommendation System"),
        tmdb_api_key=os.getenv("TMDB_API_KEY", ""),
        tmdb_access_token=os.getenv("TMDB_ACCESS_TOKEN", ""),
        database_url=os.getenv("DATABASE_URL", "sqlite:///movie_recommendation.db"),
    )
