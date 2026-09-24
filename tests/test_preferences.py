from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user_preference import UserPreference
from app.schemas.user_schema import GenrePreference, MoviePreference, UserPreferences
from app.services.auth_service import AuthService
from app.services.user_service import UserService, UserServiceError
from app.utils.constants import DEFAULT_THEME, FAVORITE_GENRE, FAVORITE_MOVIE, INTEREST, THEME_LIGHT


def _user(auth_service: AuthService):
    return auth_service.register(
        name="Ada Lovelace",
        email="ada@example.com",
        password="password123",
        confirm_password="password123",
    )


def _sample_preferences() -> UserPreferences:
    return UserPreferences(
        favorite_genres=[
            GenrePreference(tmdb_genre_id=18, name="Drama"),
            GenrePreference(tmdb_genre_id=28, name="Action"),
        ],
        favorite_movies=[MoviePreference(tmdb_id=550, title="Fight Club")],
        preferred_language="en",
        release_period="2010s",
        minimum_rating=7,
        interests=["noir", " Noir ", "mind-bending"],
    )


def test_save_preferences_marks_onboarding_complete(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = UserService(db_session)

    saved = service.save_preferences(user.id, _sample_preferences())
    loaded = service.get_preferences(user.id)

    assert saved.onboarding_completed is True
    assert [genre.name for genre in loaded.favorite_genres] == ["Drama", "Action"]
    assert loaded.favorite_movies[0].tmdb_id == 550
    assert loaded.favorite_movies[0].title == "Fight Club"
    assert loaded.preferred_language == "en"
    assert loaded.release_period == "2010s"
    assert loaded.minimum_rating == 7.0
    assert loaded.interests == ["noir", "mind-bending"]
    assert "Drama" in loaded.summary()
    assert db_session.scalar(select(func.count()).select_from(UserPreference)) == 8


def test_save_preferences_replaces_previous_values(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = UserService(db_session)
    service.save_preferences(user.id, _sample_preferences())

    service.save_preferences(
        user.id,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=35, name="Comedy")]),
    )
    loaded = service.get_preferences(user.id)

    assert [genre.name for genre in loaded.favorite_genres] == ["Comedy"]
    assert loaded.favorite_movies == []
    assert loaded.preferred_language is None
    assert loaded.interests == []
    assert user.onboarding_completed is True
    values = db_session.scalars(select(UserPreference.preference_value)).all()
    types = set(db_session.scalars(select(UserPreference.preference_type)))
    assert values == ["35|Comedy"]
    assert types == {FAVORITE_GENRE}
    assert FAVORITE_MOVIE not in types


def test_empty_preferences_still_complete_onboarding(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = UserService(db_session)

    service.save_preferences(user.id, UserPreferences())

    assert user.onboarding_completed is True
    assert service.get_preferences(user.id).summary().startswith("No preferences yet")
    assert db_session.scalar(select(func.count()).select_from(UserPreference)) == 0


def test_save_preferences_requires_a_user(db_session: Session) -> None:
    service = UserService(db_session)
    with pytest.raises(UserServiceError):
        service.save_preferences(999, UserPreferences())


def test_preferences_ignore_unknown_and_invalid_rows() -> None:
    class Row:
        def __init__(self, preference_type: str, preference_value: str) -> None:
            self.preference_type = preference_type
            self.preference_value = preference_value

    loaded = UserPreferences.from_rows(
        [
            Row(FAVORITE_GENRE, "18|Drama"),
            Row(FAVORITE_GENRE, "not-a-genre"),
            Row(FAVORITE_MOVIE, "550|Fight Club"),
            Row("unknown", "value"),
            Row("minimum_rating", "nope"),
            Row(INTEREST, "  noir "),
        ]
    )

    assert [genre.tmdb_genre_id for genre in loaded.favorite_genres] == [18]
    assert loaded.favorite_movies[0].title == "Fight Club"
    assert loaded.minimum_rating is None
    assert loaded.interests == ["noir"]


def test_update_profile_changes_name(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = UserService(db_session)

    updated = service.update_profile(user.id, "  Ada  ")

    assert updated.name == "Ada"
    assert service.get_profile(user.id).name == "Ada"


def test_update_profile_rejects_blank_name(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = UserService(db_session)
    with pytest.raises(UserServiceError, match="Name"):
        service.update_profile(user.id, "   ")


def test_theme_preference_persists_and_survives_preference_replace(
    db_session: Session, auth_service: AuthService
) -> None:
    user = _user(auth_service)
    service = UserService(db_session)

    assert service.get_theme(user.id) == DEFAULT_THEME
    assert service.save_theme(user.id, THEME_LIGHT) == THEME_LIGHT
    service.save_preferences(user.id, _sample_preferences())

    assert service.get_theme(user.id) == THEME_LIGHT
    assert [genre.name for genre in service.get_preferences(user.id).favorite_genres] == ["Drama", "Action"]


def test_save_theme_rejects_unknown_value(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = UserService(db_session)
    with pytest.raises(UserServiceError, match="theme"):
        service.save_theme(user.id, "neon")


def test_preferences_reject_unsupported_choices() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(preferred_language="zz")
    with pytest.raises(ValidationError):
        UserPreferences(release_period="ancient")
    with pytest.raises(ValidationError):
        UserPreferences(minimum_rating=4)
    with pytest.raises(ValidationError):
        UserPreferences(
            favorite_movies=[MoviePreference(tmdb_id=index, title=f"Movie {index}") for index in range(1, 10)]
        )
