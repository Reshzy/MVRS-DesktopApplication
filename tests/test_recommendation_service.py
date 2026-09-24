from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.schemas.movie_schema import DiscoverFilters
from app.schemas.user_schema import GenrePreference, UserPreferences
from app.services.auth_service import AuthService
from app.services.history_service import HistoryService
from app.services.interaction_service import InteractionService
from app.services.rating_service import RatingService
from app.services.recommendation_service import RecommendationService, RecommendationServiceError
from app.services.user_service import UserService
from app.recommendation.scoring import release_period_bounds
from tests.fakes import FakeMovieService


def _user(auth_service: AuthService):
    return auth_service.register(
        name="Ada Lovelace",
        email="ada@example.com",
        password="password123",
        confirm_password="password123",
    )


def _service(db_session: Session, movie_service: FakeMovieService | None = None) -> tuple[RecommendationService, FakeMovieService]:
    fake = movie_service or FakeMovieService()
    return RecommendationService(db_session, fake), fake


def test_cold_start_uses_favorite_genre(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    UserService(db_session).save_preferences(
        user.id,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=28, name="Action")]),
    )
    service, fake = _service(db_session)

    results = service.recommend_for_user(user.id)

    assert [item.movie.title for item in results][0] == "Inception"
    assert results[0].reason
    assert all("cosine" not in item.reason.lower() for item in results)
    assert fake.popular_calls
    assert fake.trending_calls
    assert fake.discover_calls
    assert fake.discover_calls[0].with_genres == "28"


def test_not_interested_is_excluded(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    UserService(db_session).save_preferences(
        user.id,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=28, name="Action")]),
    )
    service, fake = _service(db_session)
    InteractionService(db_session).set_not_interested(user.id, fake.movies[1])

    results = service.recommend_for_user(user.id)

    assert [item.movie.tmdb_id for item in results] == [1001]


def test_likes_and_ratings_change_ranking(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    UserService(db_session).save_preferences(user.id, UserPreferences())
    service, fake = _service(db_session)

    first = service.recommend_for_user(user.id)
    assert first[0].movie.title == "Inception"

    InteractionService(db_session).set_like(user.id, fake.movies[0])
    RatingService(db_session).set_rating(user.id, fake.movies[0], 5)
    second = service.recommend_for_user(user.id)

    assert second[0].movie.title == "Fight Club"
    before = service.profile_key(user.id)
    HistoryService(db_session).mark_watched(user.id, fake.movies[0])
    assert service.profile_key(user.id) != before


def test_preference_edits_change_recommendations(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    users = UserService(db_session)
    users.save_preferences(
        user.id,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=18, name="Drama")]),
    )
    service, _fake = _service(db_session)
    drama_first = service.recommend_for_user(user.id)[0].movie.title
    assert drama_first == "Fight Club"

    users.save_preferences(
        user.id,
        UserPreferences(
            favorite_genres=[GenrePreference(tmdb_genre_id=28, name="Action")],
            preferred_language="en",
            release_period="2010s",
            minimum_rating=7.0,
        ),
    )
    action_results = service.recommend_for_user(user.id)
    assert action_results[0].movie.title == "Inception"
    filters = service._movie_service.discover_calls[-1]
    assert filters.with_genres == "28"
    assert filters.with_original_language == "en"
    assert filters.vote_average_gte == 7.0
    assert filters.primary_release_date_gte == "2010-01-01"
    assert filters.primary_release_date_lte == "2019-12-31"


def test_all_candidate_sources_fail(db_session: Session, auth_service: AuthService) -> None:
    user = _user(auth_service)
    UserService(db_session).save_preferences(user.id, UserPreferences())
    fake = FakeMovieService()
    fake.fail = True
    service = RecommendationService(db_session, fake)

    with pytest.raises(RecommendationServiceError, match="connection"):
        service.recommend_for_user(user.id)


def test_guest_user_id_cannot_request_recommendations(db_session: Session) -> None:
    service, _fake = _service(db_session)
    with pytest.raises(RecommendationServiceError, match="Sign in"):
        service.recommend_for_user(0)


def test_discover_filters_include_release_window() -> None:
    filters = DiscoverFilters(
        with_genres="28",
        primary_release_date_gte="2010-01-01",
        primary_release_date_lte="2019-12-31",
    )
    params = filters.to_params()
    assert params["primary_release_date.gte"] == "2010-01-01"
    assert params["primary_release_date.lte"] == "2019-12-31"
    assert release_period_bounds("before-1980") == (None, "1979-12-31")
    assert release_period_bounds("2020s") == ("2020-01-01", "2029-12-31")
