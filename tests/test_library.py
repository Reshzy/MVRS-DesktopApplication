from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.interaction import Interaction
from app.models.rating import Rating
from app.models.watch_history import WatchHistory
from app.models.watchlist import Watchlist
from app.schemas.movie_schema import MovieSummaryDTO
from app.services.auth_service import AuthService
from app.services.history_service import HistoryService
from app.services.interaction_service import InteractionService
from app.services.library_base import GuestAccessError, LibraryError
from app.services.rating_service import RatingService
from app.services.watchlist_service import WatchlistService
from app.utils.constants import DISLIKE, LIKE, NOT_INTERESTED
from tests.test_movies import FULL_DETAILS

OTHER_DETAILS = FULL_DETAILS.model_copy(update={"tmdb_id": 551, "title": "Inception"})


def _user(auth_service: AuthService):
    return auth_service.register(
        name="Ada Lovelace",
        email="ada@example.com",
        password="password123",
        confirm_password="password123",
    )


def test_watchlist_add_remove_and_duplicate(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = WatchlistService(db_session)

    first = service.add(user.id, FULL_DETAILS)
    second = service.add(user.id, FULL_DETAILS)

    assert first.id == second.id
    assert service.is_saved(user.id, FULL_DETAILS.tmdb_id)
    assert db_session.scalar(select(func.count()).select_from(Watchlist)) == 1

    assert service.remove(user.id, FULL_DETAILS) is True
    assert service.is_saved(user.id, FULL_DETAILS.tmdb_id) is False
    assert service.remove(user.id, FULL_DETAILS) is False

    service.add(user.id, FULL_DETAILS)
    service.add(user.id, OTHER_DETAILS)
    titles = [entry.movie.title for entry in service.list_entries(user.id)]
    assert titles.count("Fight Club") == 1
    assert titles.count("Inception") == 1
    assert all(entry.watched is False for entry in service.list_entries(user.id))


def test_history_mark_watched_updates_existing(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = HistoryService(db_session)

    first = service.mark_watched(user.id, FULL_DETAILS)
    second = service.mark_watched(user.id, FULL_DETAILS)

    assert first.id == second.id
    assert service.has_watched(user.id, FULL_DETAILS.tmdb_id)
    assert db_session.scalar(select(func.count()).select_from(WatchHistory)) == 1

    RatingService(db_session).set_rating(user.id, FULL_DETAILS, 4)
    WatchlistService(db_session).add(user.id, FULL_DETAILS)
    entries = service.list_entries(user.id)
    assert len(entries) == 1
    assert entries[0].movie.title == "Fight Club"
    assert entries[0].movie.tmdb_id == 550
    assert entries[0].rating == 4
    assert entries[0].watched_at is not None
    assert WatchlistService(db_session).list_entries(user.id)[0].watched is True


def test_rating_upsert_and_invalid_range(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = RatingService(db_session)

    service.set_rating(user.id, FULL_DETAILS, 3)
    updated = service.set_rating(user.id, FULL_DETAILS, 5)

    assert updated.rating == 5
    assert service.get_rating(user.id, FULL_DETAILS.tmdb_id) == 5
    assert db_session.scalar(select(func.count()).select_from(Rating)) == 1

    with pytest.raises(LibraryError, match="between"):
        service.set_rating(user.id, FULL_DETAILS, 6)


def test_interactions_like_dislike_exclusive(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = InteractionService(db_session)

    assert service.set_like(user.id, FULL_DETAILS, True) is True
    assert service.has(user.id, FULL_DETAILS.tmdb_id, LIKE)
    assert service.has(user.id, FULL_DETAILS.tmdb_id, DISLIKE) is False

    assert service.set_dislike(user.id, FULL_DETAILS, True) is True
    assert service.has(user.id, FULL_DETAILS.tmdb_id, DISLIKE)
    assert service.has(user.id, FULL_DETAILS.tmdb_id, LIKE) is False

    service.set_not_interested(user.id, FULL_DETAILS, True)
    assert service.has(user.id, FULL_DETAILS.tmdb_id, NOT_INTERESTED)
    assert {item.interaction_type for item in db_session.scalars(select(Interaction))} == {
        DISLIKE,
        NOT_INTERESTED,
    }

    service.set_not_interested(user.id, FULL_DETAILS, False)
    assert service.has(user.id, FULL_DETAILS.tmdb_id, NOT_INTERESTED) is False


def test_guest_user_id_cannot_persist_library_data(db_session: Session) -> None:
    movie = FULL_DETAILS
    with pytest.raises(GuestAccessError):
        WatchlistService(db_session).add(0, movie)
    with pytest.raises(GuestAccessError):
        HistoryService(db_session).mark_watched(0, movie)
    with pytest.raises(GuestAccessError):
        RatingService(db_session).set_rating(0, movie, 4)
    with pytest.raises(GuestAccessError):
        InteractionService(db_session).set_like(0, movie, True)

    assert db_session.scalar(select(func.count()).select_from(Watchlist)) == 0
    assert db_session.scalar(select(func.count()).select_from(WatchHistory)) == 0
    assert db_session.scalar(select(func.count()).select_from(Rating)) == 0
    assert db_session.scalar(select(func.count()).select_from(Interaction)) == 0


def test_missing_tmdb_id_is_rejected(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = WatchlistService(db_session)

    with pytest.raises(LibraryError):
        service.add(user.id, MovieSummaryDTO(tmdb_id=0, title="Missing"))


def test_rating_rejects_zero_and_accepts_minimum(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = RatingService(db_session)

    with pytest.raises(LibraryError, match="between"):
        service.set_rating(user.id, FULL_DETAILS, 0)

    saved = service.set_rating(user.id, FULL_DETAILS, 1)
    assert saved.rating == 1
    assert service.get_rating(user.id, FULL_DETAILS.tmdb_id) == 1


def test_like_can_be_toggled_off(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = InteractionService(db_session)

    assert service.set_like(user.id, FULL_DETAILS, True) is True
    assert service.set_like(user.id, FULL_DETAILS, False) is False
    assert service.has(user.id, FULL_DETAILS.tmdb_id, LIKE) is False
    assert service.types_for_movie(user.id, FULL_DETAILS.tmdb_id) == set()


def test_library_data_is_isolated_per_user(db_session: Session, auth_service: AuthService) -> None:
    first = _user(auth_service)
    second = auth_service.register(
        name="Grace Hopper",
        email="grace@example.com",
        password="password123",
        confirm_password="password123",
    )
    WatchlistService(db_session).add(first.id, FULL_DETAILS)
    HistoryService(db_session).mark_watched(first.id, FULL_DETAILS)
    RatingService(db_session).set_rating(first.id, FULL_DETAILS, 5)
    InteractionService(db_session).set_like(first.id, FULL_DETAILS, True)

    assert WatchlistService(db_session).is_saved(second.id, FULL_DETAILS.tmdb_id) is False
    assert HistoryService(db_session).has_watched(second.id, FULL_DETAILS.tmdb_id) is False
    assert RatingService(db_session).get_rating(second.id, FULL_DETAILS.tmdb_id) is None
    assert InteractionService(db_session).has(second.id, FULL_DETAILS.tmdb_id, LIKE) is False
    assert WatchlistService(db_session).list_entries(second.id) == []
    assert HistoryService(db_session).list_entries(second.id) == []


def test_unknown_interaction_type_is_rejected(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    service = InteractionService(db_session)
    with pytest.raises(LibraryError, match="Unknown"):
        service._set_exclusive(user.id, FULL_DETAILS, "binge", True)
