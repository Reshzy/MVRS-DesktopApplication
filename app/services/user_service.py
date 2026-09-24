from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserPreferences
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class UserServiceError(Exception):
    pass


class UserService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._preferences = PreferenceRepository(session)

    def get_preferences(self, user_id: int) -> UserPreferences:
        try:
            rows = self._preferences.list_for_user(user_id)
        except Exception as exc:
            self._session.rollback()
            logger.exception("Failed to load preferences for user_id=%s", user_id)
            raise UserServiceError("Could not load preferences.") from exc
        return UserPreferences.from_rows(rows)

    def save_preferences(self, user_id: int, preferences: UserPreferences) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UserServiceError("Account not found.")
        try:
            self._preferences.replace_for_user(user_id, preferences.to_rows())
            self._users.set_onboarding_completed(user, True)
            self._session.commit()
            self._session.refresh(user)
        except Exception as exc:
            self._session.rollback()
            logger.exception("Failed to save preferences for user_id=%s", user_id)
            raise UserServiceError("Could not save preferences.") from exc
        return user
