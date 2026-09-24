from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interaction import Interaction


class InteractionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int, movie_id: int, interaction_type: str) -> Interaction | None:
        return self._session.scalar(
            select(Interaction).where(
                Interaction.user_id == user_id,
                Interaction.movie_id == movie_id,
                Interaction.interaction_type == interaction_type,
            )
        )

    def list_for_movie(self, user_id: int, movie_id: int) -> list[Interaction]:
        return list(
            self._session.scalars(
                select(Interaction).where(
                    Interaction.user_id == user_id,
                    Interaction.movie_id == movie_id,
                )
            )
        )

    def set(self, user_id: int, movie_id: int, interaction_type: str) -> Interaction:
        existing = self.get(user_id, movie_id, interaction_type)
        if existing is not None:
            return existing
        item = Interaction(user_id=user_id, movie_id=movie_id, interaction_type=interaction_type)
        self._session.add(item)
        self._session.flush()
        return item

    def remove(self, user_id: int, movie_id: int, interaction_type: str) -> bool:
        existing = self.get(user_id, movie_id, interaction_type)
        if existing is None:
            return False
        self._session.delete(existing)
        self._session.flush()
        return True

    def remove_types(self, user_id: int, movie_id: int, interaction_types: tuple[str, ...] | list[str]) -> None:
        for interaction_type in interaction_types:
            self.remove(user_id, movie_id, interaction_type)
