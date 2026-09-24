from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.locks import session_lock
from app.models.movie import Movie
from app.models.user import User
from app.repositories.history_repository import HistoryRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.rating_repository import RatingRepository
from app.repositories.user_repository import UserRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.insights_schema import ActivityItemDTO, InsightsDTO, RatedMovieDTO
from app.schemas.movie_schema import MovieSummaryDTO
from app.schemas.user_schema import ProfileUpdateRequest, UserPreferences
from app.utils.constants import (
    DEFAULT_THEME,
    DISLIKE,
    INSIGHTS_RECENT_LIMIT,
    INSIGHTS_TOP_MOVIES,
    LIKE,
    MAX_RATING,
    THEME_PREFERENCE,
    THEMES,
)
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

_ACTIVITY_LABELS = {
    "watched": "Watched",
    "rated": "Rated",
    "watchlist": "Added to watchlist",
    LIKE: "Liked",
    DISLIKE: "Disliked",
}


class UserServiceError(Exception):
    pass


class UserService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._preferences = PreferenceRepository(session)
        self._history = HistoryRepository(session)
        self._watchlist = WatchlistRepository(session)
        self._ratings = RatingRepository(session)
        self._interactions = InteractionRepository(session)

    def get_profile(self, user_id: int) -> User:
        with session_lock():
            user = self._users.get_by_id(user_id)
        if user is None:
            raise UserServiceError("Account not found.")
        return user

    def update_profile(self, user_id: int, name: str) -> User:
        try:
            payload = ProfileUpdateRequest(name=name)
        except ValidationError as exc:
            message = next((str(error.get("msg", "")).removeprefix("Value error, ") for error in exc.errors()), "")
            raise UserServiceError(message or "Name is required.") from exc
        with session_lock():
            user = self._users.get_by_id(user_id)
            if user is None:
                raise UserServiceError("Account not found.")
            try:
                self._users.update_name(user, payload.name)
                self._session.commit()
                self._session.refresh(user)
            except UserServiceError:
                raise
            except Exception as exc:
                self._session.rollback()
                logger.exception("Failed to update profile for user_id=%s", user_id)
                raise UserServiceError("Could not update profile.") from exc
        return user

    def get_theme(self, user_id: int) -> str:
        try:
            with session_lock():
                stored = self._preferences.get_value(user_id, THEME_PREFERENCE)
        except Exception as exc:
            with session_lock():
                self._session.rollback()
            logger.exception("Failed to load theme for user_id=%s", user_id)
            raise UserServiceError("Could not load theme preference.") from exc
        if stored in THEMES:
            return stored
        return DEFAULT_THEME

    def save_theme(self, user_id: int, theme: str) -> str:
        if theme not in THEMES:
            raise UserServiceError("Choose a supported theme.")
        with session_lock():
            user = self._users.get_by_id(user_id)
            if user is None:
                raise UserServiceError("Account not found.")
            try:
                self._preferences.upsert_value(user_id, THEME_PREFERENCE, theme)
                self._session.commit()
            except Exception as exc:
                self._session.rollback()
                logger.exception("Failed to save theme for user_id=%s", user_id)
                raise UserServiceError("Could not save theme preference.") from exc
        return theme

    def get_preferences(self, user_id: int) -> UserPreferences:
        try:
            with session_lock():
                rows = self._preferences.list_for_user(user_id)
        except Exception as exc:
            with session_lock():
                self._session.rollback()
            logger.exception("Failed to load preferences for user_id=%s", user_id)
            raise UserServiceError("Could not load preferences.") from exc
        return UserPreferences.from_rows(rows)

    def save_preferences(self, user_id: int, preferences: UserPreferences) -> User:
        with session_lock():
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

    def get_insights(self, user_id: int) -> InsightsDTO:
        try:
            with session_lock():
                history = self._history.list_for_user(user_id)
                watchlist = self._watchlist.list_for_user(user_id)
                ratings = self._ratings.list_for_user(user_id)
                interactions = self._interactions.list_for_user(user_id)
                preferences = UserPreferences.from_rows(self._preferences.list_for_user(user_id))
        except Exception as exc:
            with session_lock():
                self._session.rollback()
            logger.exception("Failed to load insights for user_id=%s", user_id)
            raise UserServiceError("Could not load insights.") from exc

        scores = [item.rating for item in ratings]
        average = sum(scores) / len(scores) if scores else None
        return InsightsDTO(
            watched_count=len(history),
            watchlist_count=len(watchlist),
            average_rating=average,
            favorite_genres=[genre.name for genre in preferences.favorite_genres],
            most_watched_genre=self._most_watched_genre(history),
            highest_rated=self._highest_rated(ratings),
            recent_activity=self._recent_activity(history, watchlist, ratings, interactions),
        )

    @staticmethod
    def _most_watched_genre(history: list) -> str | None:
        counts: Counter[str] = Counter()
        for item in history:
            movie = getattr(item, "movie", None)
            if movie is None:
                continue
            for link in getattr(movie, "genre_links", None) or []:
                genre = getattr(link, "genre", None)
                name = str(getattr(genre, "name", "") or "").strip()
                if name:
                    counts[name] += 1
        if not counts:
            return None
        return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].casefold()))[0][0]

    @staticmethod
    def _highest_rated(ratings: list) -> list[RatedMovieDTO]:
        ranked: list[tuple[int, datetime, RatedMovieDTO]] = []
        for item in ratings:
            movie = UserService._movie_summary(getattr(item, "movie", None))
            if movie is None:
                continue
            ranked.append(
                (
                    item.rating,
                    UserService._timestamp(getattr(item, "updated_at", None)),
                    RatedMovieDTO(movie, item.rating),
                )
            )
        ranked.sort(key=lambda row: (-row[0], -row[1].timestamp(), row[2].movie.title.casefold()))
        return [row[2] for row in ranked[:INSIGHTS_TOP_MOVIES]]

    @staticmethod
    def _recent_activity(history: list, watchlist: list, ratings: list, interactions: list) -> list[ActivityItemDTO]:
        items: list[ActivityItemDTO] = []
        for entry in history:
            movie = UserService._movie_summary(getattr(entry, "movie", None))
            if movie is None:
                continue
            items.append(
                ActivityItemDTO("watched", movie, getattr(entry, "watched_at", None), _ACTIVITY_LABELS["watched"])
            )
        for entry in watchlist:
            movie = UserService._movie_summary(getattr(entry, "movie", None))
            if movie is None:
                continue
            items.append(
                ActivityItemDTO("watchlist", movie, getattr(entry, "created_at", None), _ACTIVITY_LABELS["watchlist"])
            )
        for entry in ratings:
            movie = UserService._movie_summary(getattr(entry, "movie", None))
            if movie is None:
                continue
            items.append(
                ActivityItemDTO(
                    "rated",
                    movie,
                    getattr(entry, "updated_at", None),
                    f"{_ACTIVITY_LABELS['rated']} {entry.rating}/{MAX_RATING}",
                )
            )
        for entry in interactions:
            kind = str(getattr(entry, "interaction_type", "") or "")
            if kind not in {LIKE, DISLIKE}:
                continue
            movie = UserService._movie_summary(getattr(entry, "movie", None))
            if movie is None:
                continue
            items.append(
                ActivityItemDTO(kind, movie, getattr(entry, "updated_at", None), _ACTIVITY_LABELS[kind])
            )
        items.sort(
            key=lambda item: (
                -UserService._timestamp(item.occurred_at).timestamp(),
                item.kind,
                item.movie.title.casefold(),
            )
        )
        return items[:INSIGHTS_RECENT_LIMIT]

    @staticmethod
    def _movie_summary(movie: Movie | None) -> MovieSummaryDTO | None:
        if movie is None or not getattr(movie, "tmdb_id", 0):
            return None
        return MovieSummaryDTO.from_model(movie)

    @staticmethod
    def _timestamp(value: datetime | None) -> datetime:
        if value is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
