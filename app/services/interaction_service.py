from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.interaction_repository import InteractionRepository
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie_schema import MovieSummaryDTO
from app.database.locks import session_guard
from app.services.library_base import LibraryError, UserMovieActionService, require_signed_in_user
from app.utils.constants import DISLIKE, INTERACTION_TYPES, LIKE, NOT_INTERESTED


class InteractionService(UserMovieActionService):
    def __init__(self, session: Session, movie_repository: MovieRepository | None = None) -> None:
        super().__init__(session, movie_repository)
        self._interactions = InteractionRepository(session)

    def set_like(self, user_id: int, movie: MovieSummaryDTO, enabled: bool = True) -> bool:
        return self._set_exclusive(user_id, movie, LIKE, enabled, exclusive_with=(DISLIKE,))

    def set_dislike(self, user_id: int, movie: MovieSummaryDTO, enabled: bool = True) -> bool:
        return self._set_exclusive(user_id, movie, DISLIKE, enabled, exclusive_with=(LIKE,))

    def set_not_interested(self, user_id: int, movie: MovieSummaryDTO, enabled: bool = True) -> bool:
        return self._set_exclusive(user_id, movie, NOT_INTERESTED, enabled)

    @session_guard
    def has(self, user_id: int, tmdb_id: int, interaction_type: str) -> bool:
        movie_id = self._movie_id_for_tmdb(tmdb_id)
        if movie_id is None:
            return False
        return self._interactions.get(user_id, movie_id, interaction_type) is not None

    @session_guard
    def types_for_movie(self, user_id: int, tmdb_id: int) -> set[str]:
        movie_id = self._movie_id_for_tmdb(tmdb_id)
        if movie_id is None:
            return set()
        return {item.interaction_type for item in self._interactions.list_for_movie(user_id, movie_id)}

    @session_guard
    def _set_exclusive(
        self,
        user_id: int,
        movie: MovieSummaryDTO,
        interaction_type: str,
        enabled: bool,
        exclusive_with: tuple[str, ...] = (),
    ) -> bool:
        if interaction_type not in INTERACTION_TYPES:
            raise LibraryError("Unknown interaction type.")
        user_id = require_signed_in_user(user_id)
        stored = self._resolve_movie(movie)
        if not enabled:
            removed = self._interactions.remove(user_id, stored.id, interaction_type)
            if removed:
                self._commit()
            return False
        if exclusive_with:
            self._interactions.remove_types(user_id, stored.id, exclusive_with)
        self._interactions.set(user_id, stored.id, interaction_type)
        self._commit()
        return True
