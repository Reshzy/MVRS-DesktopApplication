from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.watch_history import WatchHistory


class HistoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int, movie_id: int) -> WatchHistory | None:
        return self._session.scalar(
            select(WatchHistory)
            .where(WatchHistory.user_id == user_id, WatchHistory.movie_id == movie_id)
            .order_by(WatchHistory.watched_at.desc())
        )

    def mark_watched(self, user_id: int, movie_id: int) -> WatchHistory:
        existing = self.get(user_id, movie_id)
        if existing is not None:
            existing.watched_at = datetime.now(timezone.utc)
            self._session.flush()
            return existing
        item = WatchHistory(user_id=user_id, movie_id=movie_id)
        self._session.add(item)
        self._session.flush()
        return item

    def list_for_user(self, user_id: int) -> list[WatchHistory]:
        return list(
            self._session.scalars(
                select(WatchHistory)
                .where(WatchHistory.user_id == user_id)
                .order_by(WatchHistory.watched_at.desc())
            )
        )
