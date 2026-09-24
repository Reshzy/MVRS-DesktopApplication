from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_preference import UserPreference
from app.utils.constants import PREFERENCE_TYPES


class PreferenceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_user(self, user_id: int) -> list[UserPreference]:
        return list(
            self._session.scalars(
                select(UserPreference)
                .where(UserPreference.user_id == user_id)
                .order_by(UserPreference.id)
            )
        )

    def replace_for_user(self, user_id: int, rows: list[tuple[str, str, float]]) -> list[UserPreference]:
        existing = self._session.scalars(
            select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.preference_type.in_(PREFERENCE_TYPES),
            )
        )
        for item in existing:
            self._session.delete(item)
        self._session.flush()

        created: list[UserPreference] = []
        seen: set[tuple[str, str]] = set()
        for preference_type, preference_value, weight in rows:
            key = (preference_type, preference_value)
            if key in seen:
                continue
            seen.add(key)
            item = UserPreference(
                user_id=user_id,
                preference_type=preference_type,
                preference_value=preference_value[:255],
                weight=weight,
            )
            self._session.add(item)
            created.append(item)
        self._session.flush()
        return created
