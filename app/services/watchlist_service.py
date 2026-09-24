from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.watchlist import Watchlist
from app.repositories.history_repository import HistoryRepository
from app.repositories.movie_repository import MovieRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.library_schema import WatchlistEntryDTO
from app.schemas.movie_schema import MovieSummaryDTO
from app.services.library_base import UserMovieActionService


class WatchlistService(UserMovieActionService):
    def __init__(self, session: Session, movie_repository: MovieRepository | None = None) -> None:
        super().__init__(session, movie_repository)
        self._watchlist = WatchlistRepository(session)
        self._history = HistoryRepository(session)

    def add(self, user_id: int, movie: MovieSummaryDTO) -> Watchlist:
        stored = self._resolve_movie(movie)
        item = self._watchlist.add(user_id, stored.id)
        self._commit()
        return item

    def remove(self, user_id: int, movie: MovieSummaryDTO) -> bool:
        movie_id = self._movie_id_for_tmdb(movie.tmdb_id)
        if movie_id is None:
            return False
        removed = self._watchlist.remove(user_id, movie_id)
        if removed:
            self._commit()
        return removed

    def is_saved(self, user_id: int, tmdb_id: int) -> bool:
        movie_id = self._movie_id_for_tmdb(tmdb_id)
        if movie_id is None:
            return False
        return self._watchlist.get(user_id, movie_id) is not None

    def list_for_user(self, user_id: int) -> list[Watchlist]:
        return self._watchlist.list_for_user(user_id)

    def list_entries(self, user_id: int) -> list[WatchlistEntryDTO]:
        watched_ids = {item.movie_id for item in self._history.list_for_user(user_id)}
        entries: list[WatchlistEntryDTO] = []
        for item in self._watchlist.list_for_user(user_id):
            movie = item.movie
            if movie is None:
                continue
            entries.append(
                WatchlistEntryDTO(
                    movie=MovieSummaryDTO.from_model(movie),
                    created_at=item.created_at,
                    watched=item.movie_id in watched_ids,
                )
            )
        return entries
