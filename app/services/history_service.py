from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.watch_history import WatchHistory
from app.repositories.history_repository import HistoryRepository
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie_schema import MovieSummaryDTO
from app.services.library_base import UserMovieActionService


class HistoryService(UserMovieActionService):
    def __init__(self, session: Session, movie_repository: MovieRepository | None = None) -> None:
        super().__init__(session, movie_repository)
        self._history = HistoryRepository(session)

    def mark_watched(self, user_id: int, movie: MovieSummaryDTO) -> WatchHistory:
        stored = self._resolve_movie(movie)
        item = self._history.mark_watched(user_id, stored.id)
        self._commit()
        return item

    def has_watched(self, user_id: int, tmdb_id: int) -> bool:
        movie_id = self._movie_id_for_tmdb(tmdb_id)
        if movie_id is None:
            return False
        return self._history.get(user_id, movie_id) is not None

    def list_for_user(self, user_id: int) -> list[WatchHistory]:
        return self._history.list_for_user(user_id)
