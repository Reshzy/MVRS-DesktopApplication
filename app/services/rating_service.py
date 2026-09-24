from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.rating import Rating
from app.repositories.movie_repository import MovieRepository
from app.repositories.rating_repository import RatingRepository
from app.schemas.movie_schema import MovieSummaryDTO
from app.services.library_base import LibraryError, UserMovieActionService
from app.utils.constants import MAX_RATING, MIN_RATING


class RatingService(UserMovieActionService):
    def __init__(self, session: Session, movie_repository: MovieRepository | None = None) -> None:
        super().__init__(session, movie_repository)
        self._ratings = RatingRepository(session)

    def set_rating(self, user_id: int, movie: MovieSummaryDTO, rating: int) -> Rating:
        if rating < MIN_RATING or rating > MAX_RATING:
            raise LibraryError(f"Rating must be between {MIN_RATING} and {MAX_RATING}.")
        stored = self._resolve_movie(movie)
        item = self._ratings.upsert(user_id, stored.id, rating)
        self._commit()
        return item

    def get_rating(self, user_id: int, tmdb_id: int) -> int | None:
        movie_id = self._movie_id_for_tmdb(tmdb_id)
        if movie_id is None:
            return None
        item = self._ratings.get(user_id, movie_id)
        return item.rating if item is not None else None

    def list_for_user(self, user_id: int) -> list[Rating]:
        return self._ratings.list_for_user(user_id)
