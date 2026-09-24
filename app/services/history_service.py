from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.watch_history import WatchHistory
from app.repositories.history_repository import HistoryRepository
from app.repositories.movie_repository import MovieRepository
from app.repositories.rating_repository import RatingRepository
from app.schemas.library_schema import HistoryEntryDTO
from app.schemas.movie_schema import MovieSummaryDTO
from app.database.locks import session_guard
from app.services.library_base import UserMovieActionService, require_signed_in_user


class HistoryService(UserMovieActionService):
    def __init__(self, session: Session, movie_repository: MovieRepository | None = None) -> None:
        super().__init__(session, movie_repository)
        self._history = HistoryRepository(session)
        self._ratings = RatingRepository(session)

    @session_guard
    def mark_watched(self, user_id: int, movie: MovieSummaryDTO) -> WatchHistory:
        user_id = require_signed_in_user(user_id)
        stored = self._resolve_movie(movie)
        item = self._history.mark_watched(user_id, stored.id)
        self._commit()
        return item

    @session_guard
    def has_watched(self, user_id: int, tmdb_id: int) -> bool:
        movie_id = self._movie_id_for_tmdb(tmdb_id)
        if movie_id is None:
            return False
        return self._history.get(user_id, movie_id) is not None

    @session_guard
    def list_for_user(self, user_id: int) -> list[WatchHistory]:
        return self._history.list_for_user(user_id)

    @session_guard
    def list_entries(self, user_id: int) -> list[HistoryEntryDTO]:
        ratings = {item.movie_id: item.rating for item in self._ratings.list_for_user(user_id)}
        entries: list[HistoryEntryDTO] = []
        for item in self._history.list_for_user(user_id):
            movie = item.movie
            if movie is None:
                continue
            entries.append(
                HistoryEntryDTO(
                    movie=MovieSummaryDTO.from_model(movie),
                    watched_at=item.watched_at,
                    rating=ratings.get(item.movie_id),
                )
            )
        return entries
