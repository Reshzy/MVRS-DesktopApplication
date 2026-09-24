from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database.locks import session_lock
from app.models.movie import Movie
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie_schema import MovieSummaryDTO
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class LibraryError(Exception):
    pass


class GuestAccessError(LibraryError):
    """Raised when a guest tries to persist account-owned data."""


def require_signed_in_user(user_id: int | None) -> int:
    if user_id is None or user_id <= 0:
        raise GuestAccessError("Sign in to save this action.")
    return user_id


class UserMovieActionService:
    def __init__(self, session: Session, movie_repository: MovieRepository | None = None) -> None:
        self._session = session
        self._movies = movie_repository or MovieRepository(session)

    def _resolve_movie(self, movie: MovieSummaryDTO) -> Movie:
        with session_lock():
            stored = self._movies.upsert(movie)
        if stored is None:
            raise LibraryError("This movie cannot be saved.")
        return stored

    def _movie_id_for_tmdb(self, tmdb_id: int) -> int | None:
        with session_lock():
            stored = self._movies.get_by_tmdb_id(tmdb_id)
        return stored.id if stored is not None else None

    def _commit(self) -> None:
        try:
            with session_lock():
                self._session.commit()
        except Exception:
            with session_lock():
                self._session.rollback()
            logger.exception("Failed to save library change")
            raise
