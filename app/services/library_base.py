from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.movie import Movie
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie_schema import MovieSummaryDTO
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class LibraryError(Exception):
    pass


class UserMovieActionService:
    def __init__(self, session: Session, movie_repository: MovieRepository | None = None) -> None:
        self._session = session
        self._movies = movie_repository or MovieRepository(session)

    def _resolve_movie(self, movie: MovieSummaryDTO) -> Movie:
        stored = self._movies.upsert(movie)
        if stored is None:
            raise LibraryError("This movie cannot be saved.")
        return stored

    def _movie_id_for_tmdb(self, tmdb_id: int) -> int | None:
        stored = self._movies.get_by_tmdb_id(tmdb_id)
        return stored.id if stored is not None else None

    def _commit(self) -> None:
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            logger.exception("Failed to save library change")
            raise
