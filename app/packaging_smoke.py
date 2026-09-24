from __future__ import annotations

import logging

from app.config.settings import get_settings
from app.database.init_db import init_database
from app.database.session import SessionLocal
from app.recommendation.engine import RecommendationEngine
from app.recommendation.feature_builder import CandidateMovie, UserRecommendationSignals
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.watchlist_service import WatchlistService
from app.state.app_state import AppState
from app.utils.logging_config import LOGGER_NAME
from app.utils.paths import app_data_dir, default_sqlite_path, theme_qss_path

logger = logging.getLogger(LOGGER_NAME)

SMOKE_EMAIL = "packaging-smoke@example.com"
SMOKE_PASSWORD = "password123"


def run_smoke_test() -> int:
    init_database()
    settings = get_settings()
    if not theme_qss_path().exists():
        raise RuntimeError(f"Bundled theme is missing: {theme_qss_path()}")
    if not default_sqlite_path().exists():
        raise RuntimeError(f"SQLite database was not created at {default_sqlite_path()}")

    session = SessionLocal()
    try:
        state = AppState()
        auth = AuthService(session, state)
        if UserRepository(session).get_by_email(SMOKE_EMAIL) is None:
            user = auth.register(
                name="Packaging Smoke",
                email=SMOKE_EMAIL,
                password=SMOKE_PASSWORD,
                confirm_password=SMOKE_PASSWORD,
            )
        else:
            user = auth.login(email=SMOKE_EMAIL, password=SMOKE_PASSWORD)
        if user.id is None:
            raise RuntimeError("Auth smoke test did not persist a user.")

        movie = CandidateMovie(
            tmdb_id=550,
            title="Fight Club",
            overview="An insomniac office worker.",
            genres=("Drama",),
            vote_average=8.4,
            popularity=70.0,
            original_language="en",
            release_year=1999,
        )
        from app.schemas.movie_schema import GenreDTO, MovieDetailsDTO

        details = MovieDetailsDTO(
            tmdb_id=550,
            title="Fight Club",
            overview="An insomniac office worker.",
            genres=[GenreDTO(tmdb_genre_id=18, name="Drama")],
            vote_average=8.4,
            original_language="en",
        )
        WatchlistService(session).add(user.id, details)
        if not WatchlistService(session).is_saved(user.id, 550):
            raise RuntimeError("Watchlist persistence failed.")

        ranked = RecommendationEngine().recommend(
            UserRecommendationSignals(favorite_genres=("Drama",)),
            [movie],
        )
        if not ranked:
            raise RuntimeError("Recommendation engine returned no results.")

        if settings.tmdb_access_token or settings.tmdb_api_key:
            from app.api.image_client import ImageClient
            from app.services.movie_service import MovieService

            service = MovieService(session=session)
            page = service.search_movies("Inception")
            if not page.results:
                raise RuntimeError("TMDB search returned no results.")
            logger.info("TMDB smoke search returned %s", page.results[0].title)
            poster = page.results[0].poster_path
            if poster:
                client = ImageClient()
                try:
                    data = client.fetch(poster)
                    if not data:
                        raise RuntimeError("Image download was empty.")
                    logger.info("Image smoke downloaded %s bytes", len(data))
                finally:
                    client.close()
        else:
            logger.info("TMDB credentials are not configured; skipped live API smoke checks.")
    finally:
        session.close()

    marker = app_data_dir() / "smoke_ok.txt"
    marker.write_text("SMOKE_OK\n", encoding="utf-8")
    logger.info("SMOKE_OK data_dir=%s db=%s", app_data_dir(), default_sqlite_path())
    print("SMOKE_OK")
    return 0
