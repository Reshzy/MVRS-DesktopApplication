from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.watchlist import Watchlist


class WatchlistRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int, movie_id: int) -> Watchlist | None:
        return self._session.scalar(
            select(Watchlist).where(Watchlist.user_id == user_id, Watchlist.movie_id == movie_id)
        )

    def add(self, user_id: int, movie_id: int) -> Watchlist:
        existing = self.get(user_id, movie_id)
        if existing is not None:
            return existing
        item = Watchlist(user_id=user_id, movie_id=movie_id)
        self._session.add(item)
        self._session.flush()
        return item

    def remove(self, user_id: int, movie_id: int) -> bool:
        item = self.get(user_id, movie_id)
        if item is None:
            return False
        self._session.delete(item)
        self._session.flush()
        return True

    def list_for_user(self, user_id: int) -> list[Watchlist]:
        return list(
            self._session.scalars(
                select(Watchlist).where(Watchlist.user_id == user_id).order_by(Watchlist.created_at.desc())
            )
        )
