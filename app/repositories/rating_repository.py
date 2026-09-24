from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.rating import Rating


class RatingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int, movie_id: int) -> Rating | None:
        return self._session.scalar(
            select(Rating).where(Rating.user_id == user_id, Rating.movie_id == movie_id)
        )

    def upsert(self, user_id: int, movie_id: int, rating: int) -> Rating:
        existing = self.get(user_id, movie_id)
        if existing is not None:
            existing.rating = rating
            self._session.flush()
            return existing
        item = Rating(user_id=user_id, movie_id=movie_id, rating=rating)
        self._session.add(item)
        self._session.flush()
        return item

    def list_for_user(self, user_id: int) -> list[Rating]:
        return list(
            self._session.scalars(
                select(Rating)
                .where(Rating.user_id == user_id)
                .options(selectinload(Rating.movie))
                .order_by(Rating.updated_at.desc())
            )
        )
