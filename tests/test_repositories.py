from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.interaction import Interaction
from app.models.movie import Movie
from app.models.rating import Rating
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.watch_history import WatchHistory
from app.models.watchlist import Watchlist
from app.repositories.history_repository import HistoryRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.movie_repository import MovieRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.rating_repository import RatingRepository
from app.repositories.user_repository import UserRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.services.auth_service import AuthService
from app.utils.constants import DISLIKE, FAVORITE_GENRE, LIKE, THEME_LIGHT, THEME_PREFERENCE
from tests.test_movies import FULL_DETAILS

OTHER_DETAILS = FULL_DETAILS.model_copy(update={"tmdb_id": 551, "title": "Inception"})


def _user(auth_service: AuthService):
    return auth_service.register(
        name="Ada Lovelace",
        email="ada@example.com",
        password="password123",
        confirm_password="password123",
    )


def _second_user(auth_service: AuthService):
    return auth_service.register(
        name="Grace Hopper",
        email="grace@example.com",
        password="password123",
        confirm_password="password123",
    )


def _movie(db_session: Session, dto=FULL_DETAILS) -> Movie:
    stored = MovieRepository(db_session).upsert(dto)
    assert stored is not None
    return stored


def test_user_repository_create_read_update(db_session: Session) -> None:
    repository = UserRepository(db_session)

    created = repository.create(name="Ada Lovelace", email="ada@example.com", password_hash="hashed")
    by_id = repository.get_by_id(created.id)
    by_email = repository.get_by_email("ada@example.com")

    assert created.id is not None
    assert by_id is created
    assert by_email is created
    assert repository.get_by_email("missing@example.com") is None

    repository.update_name(created, "Ada")
    repository.set_onboarding_completed(created, True)

    assert created.name == "Ada"
    assert created.onboarding_completed is True
    assert db_session.get(User, created.id) is created


def test_watchlist_repository_add_remove_and_duplicate(
    db_session: Session, auth_service: AuthService
) -> None:
    user = _user(auth_service)
    movie = _movie(db_session)
    other = _movie(db_session, OTHER_DETAILS)
    repository = WatchlistRepository(db_session)

    first = repository.add(user.id, movie.id)
    second = repository.add(user.id, movie.id)
    repository.add(user.id, other.id)

    assert first.id == second.id
    assert repository.get(user.id, movie.id) is first
    assert db_session.scalar(select(func.count()).select_from(Watchlist)) == 2
    assert {item.movie_id for item in repository.list_for_user(user.id)} == {movie.id, other.id}

    assert repository.remove(user.id, movie.id) is True
    assert repository.get(user.id, movie.id) is None
    assert repository.remove(user.id, movie.id) is False
    assert {item.movie_id for item in repository.list_for_user(user.id)} == {other.id}


def test_history_repository_updates_existing_watch(
    db_session: Session, auth_service: AuthService
) -> None:
    user = _user(auth_service)
    movie = _movie(db_session)
    other = _movie(db_session, OTHER_DETAILS)
    repository = HistoryRepository(db_session)

    first = repository.mark_watched(user.id, movie.id)
    first_watched_at = first.watched_at
    second = repository.mark_watched(user.id, movie.id)
    repository.mark_watched(user.id, other.id)

    assert first.id == second.id
    assert first_watched_at.tzinfo is not None
    assert second.watched_at.tzinfo is not None
    assert second.watched_at >= first_watched_at
    assert db_session.scalar(select(func.count()).select_from(WatchHistory)) == 2
    assert {item.movie_id for item in repository.list_for_user(user.id)} == {movie.id, other.id}


def test_rating_repository_upserts_without_duplicates(
    db_session: Session, auth_service: AuthService
) -> None:
    user = _user(auth_service)
    movie = _movie(db_session)
    repository = RatingRepository(db_session)

    created = repository.upsert(user.id, movie.id, 3)
    updated = repository.upsert(user.id, movie.id, 5)

    assert created.id == updated.id
    assert updated.rating == 5
    assert repository.get(user.id, movie.id).rating == 5
    assert db_session.scalar(select(func.count()).select_from(Rating)) == 1
    assert repository.list_for_user(user.id)[0].movie_id == movie.id


def test_preference_repository_replaces_rows_and_skips_duplicates(
    db_session: Session, auth_service: AuthService
) -> None:
    user = _user(auth_service)
    repository = PreferenceRepository(db_session)
    repository.upsert_value(user.id, THEME_PREFERENCE, THEME_LIGHT)

    created = repository.replace_for_user(
        user.id,
        [
            (FAVORITE_GENRE, "18|Drama", 1.0),
            (FAVORITE_GENRE, "18|Drama", 1.0),
            (FAVORITE_GENRE, "28|Action", 1.0),
        ],
    )
    values = [item.preference_value for item in repository.list_for_user(user.id)]

    assert [item.preference_value for item in created] == ["18|Drama", "28|Action"]
    assert values.count("18|Drama") == 1
    assert "28|Action" in values
    assert repository.get_value(user.id, THEME_PREFERENCE) == THEME_LIGHT
    assert db_session.scalar(
        select(func.count()).select_from(UserPreference).where(UserPreference.user_id == user.id)
    ) == 3


def test_interaction_repository_set_remove_and_duplicate(
    db_session: Session, auth_service: AuthService
) -> None:
    user = _user(auth_service)
    movie = _movie(db_session)
    repository = InteractionRepository(db_session)

    first = repository.set(user.id, movie.id, LIKE)
    second = repository.set(user.id, movie.id, LIKE)
    repository.set(user.id, movie.id, DISLIKE)

    assert first.id == second.id
    assert repository.get(user.id, movie.id, LIKE) is first
    assert {item.interaction_type for item in repository.list_for_movie(user.id, movie.id)} == {
        LIKE,
        DISLIKE,
    }

    repository.remove_types(user.id, movie.id, (LIKE,))
    assert repository.get(user.id, movie.id, LIKE) is None
    assert repository.remove(user.id, movie.id, LIKE) is False
    assert {item.interaction_type for item in repository.list_for_user(user.id)} == {DISLIKE}
    assert db_session.scalar(select(func.count()).select_from(Interaction)) == 1


def test_library_repositories_keep_users_isolated(
    db_session: Session, auth_service: AuthService
) -> None:
    first_user = _user(auth_service)
    second_user = _second_user(auth_service)
    movie = _movie(db_session)
    watchlist = WatchlistRepository(db_session)
    history = HistoryRepository(db_session)
    ratings = RatingRepository(db_session)

    watchlist.add(first_user.id, movie.id)
    history.mark_watched(first_user.id, movie.id)
    ratings.upsert(first_user.id, movie.id, 4)

    assert watchlist.get(second_user.id, movie.id) is None
    assert history.get(second_user.id, movie.id) is None
    assert ratings.get(second_user.id, movie.id) is None
    assert watchlist.list_for_user(second_user.id) == []
    assert history.list_for_user(second_user.id) == []
    assert ratings.list_for_user(second_user.id) == []
