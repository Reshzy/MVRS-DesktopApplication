from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.user_schema import GenrePreference, UserPreferences
from app.services.auth_service import AuthService
from app.services.history_service import HistoryService
from app.services.interaction_service import InteractionService
from app.services.rating_service import RatingService
from app.services.user_service import UserService
from app.services.watchlist_service import WatchlistService
from tests.test_movies import FULL_DETAILS

ACTION_DETAILS = FULL_DETAILS.model_copy(
    update={
        "tmdb_id": 551,
        "title": "Inception",
        "genres": [FULL_DETAILS.genres[0].model_copy(update={"tmdb_genre_id": 28, "name": "Action"})],
    }
)
SECOND_DRAMA = FULL_DETAILS.model_copy(update={"tmdb_id": 552, "title": "The Godfather"})


def _user(auth_service: AuthService):
    return auth_service.register(
        name="Ada Lovelace",
        email="ada@example.com",
        password="password123",
        confirm_password="password123",
    )


def test_insights_aggregates_library_and_taste(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    users = UserService(db_session)
    history = HistoryService(db_session)
    watchlist = WatchlistService(db_session)
    ratings = RatingService(db_session)
    interactions = InteractionService(db_session)

    users.save_preferences(
        user.id,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=18, name="Drama")]),
    )
    history.mark_watched(user.id, FULL_DETAILS)
    history.mark_watched(user.id, SECOND_DRAMA)
    history.mark_watched(user.id, ACTION_DETAILS)
    watchlist.add(user.id, FULL_DETAILS)
    watchlist.add(user.id, ACTION_DETAILS)
    ratings.set_rating(user.id, FULL_DETAILS, 5)
    ratings.set_rating(user.id, ACTION_DETAILS, 3)
    interactions.set_like(user.id, FULL_DETAILS, True)

    insights = users.get_insights(user.id)

    assert insights.watched_count == 3
    assert insights.watchlist_count == 2
    assert insights.average_rating == 4.0
    assert insights.favorite_genres == ["Drama"]
    assert insights.most_watched_genre == "Drama"
    assert [item.movie.title for item in insights.highest_rated] == ["Fight Club", "Inception"]
    assert insights.highest_rated[0].rating == 5
    kinds = {item.kind for item in insights.recent_activity}
    titles = {item.movie.title for item in insights.recent_activity}
    assert "watched" in kinds
    assert "rated" in kinds
    assert "watchlist" in kinds
    assert "like" in kinds
    assert "Fight Club" in titles


def test_insights_empty_for_new_user(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    insights = UserService(db_session).get_insights(user.id)

    assert insights.watched_count == 0
    assert insights.watchlist_count == 0
    assert insights.average_rating is None
    assert insights.favorite_genres == []
    assert insights.most_watched_genre is None
    assert insights.highest_rated == []
    assert insights.recent_activity == []
