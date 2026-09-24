from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.recommendation.content_based import cosine_to_user_vector
from app.recommendation.engine import RecommendationEngine
from app.recommendation.feature_builder import (
    CandidateMovie,
    UserRecommendationSignals,
    build_feature_frame,
    movie_feature_text,
)
from app.recommendation.scoring import year_in_release_period
from app.schemas.movie_schema import GenreDTO, MovieDetailsDTO
from app.schemas.user_schema import GenrePreference, MoviePreference, UserPreferences
from app.utils.constants import DISLIKE_PENALTY, RECOMMENDATION_WEIGHTS, WATCHED_PENALTY


def _movie(**kwargs: object) -> CandidateMovie:
    values = {
        "overview": "",
        "genres": (),
        "popularity": 50.0,
        "vote_average": 7.0,
        "original_language": "en",
    }
    values.update(kwargs)
    return CandidateMovie(**values)  # type: ignore[arg-type]


CATALOG = (
    _movie(
        tmdb_id=1,
        title="Die Hard",
        overview="A cop fights terrorists in a skyscraper.",
        genres=("Action", "Thriller"),
        vote_average=8.0,
        popularity=80.0,
        release_year=1988,
    ),
    _movie(
        tmdb_id=2,
        title="The Hours",
        overview="Three women connected by a novel.",
        genres=("Drama",),
        vote_average=7.5,
        popularity=40.0,
        release_year=2002,
    ),
    _movie(
        tmdb_id=3,
        title="Superbad",
        overview="High school friends chase a party.",
        genres=("Comedy",),
        vote_average=7.2,
        popularity=55.0,
        release_year=2007,
    ),
    _movie(
        tmdb_id=4,
        title="John Wick",
        overview="An assassin fights a criminal underground.",
        genres=("Action", "Thriller"),
        vote_average=7.8,
        popularity=90.0,
        release_year=2014,
    ),
    _movie(
        tmdb_id=5,
        title="Inception",
        overview="A thief enters dreams to plant an idea.",
        genres=("Science Fiction", "Action", "Thriller"),
        vote_average=8.4,
        popularity=95.0,
        release_year=2010,
    ),
    _movie(
        tmdb_id=6,
        title="Amelie",
        overview="A shy waitress changes lives in Paris.",
        genres=("Comedy", "Romance"),
        vote_average=8.0,
        popularity=45.0,
        original_language="fr",
        release_year=2001,
    ),
)


def _titles(results: list) -> list[str]:
    return [item.movie.title for item in results]


def test_weights_sum_to_one() -> None:
    assert sum(RECOMMENDATION_WEIGHTS.values()) == pytest.approx(1.0)


def test_feature_text_includes_genres_overview_and_language() -> None:
    text = movie_feature_text(CATALOG[0])
    assert "Action" in text
    assert "terrorists" in text
    assert "lang_en" in text

    frame = build_feature_frame(CATALOG)
    assert list(frame["tmdb_id"]) == [movie.tmdb_id for movie in CATALOG]
    assert frame.loc[0, "genre_text"] == "Action Thriller"


def test_genre_relevance_ranks_matching_movies_higher() -> None:
    results = RecommendationEngine().recommend(
        UserRecommendationSignals(favorite_genres=("Action",)),
        CATALOG,
    )
    titles = _titles(results)
    assert titles[0] in {"Die Hard", "John Wick", "Inception"}
    assert titles.index("Die Hard") < titles.index("The Hours")
    assert titles.index("John Wick") < titles.index("Superbad")
    assert titles.index("Inception") < titles.index("Amelie")


def test_cold_start_uses_onboarding_genres() -> None:
    results = RecommendationEngine().recommend(
        UserRecommendationSignals(favorite_genres=("Drama",)),
        CATALOG,
    )
    assert results[0].movie.title == "The Hours"
    assert any("Drama" in reason for reason in results[0].reasons)


def test_cold_start_without_signals_falls_back_to_quality() -> None:
    results = RecommendationEngine().recommend(UserRecommendationSignals(), CATALOG)
    assert results[0].movie.title == "Inception"
    assert results[0].reasons


def test_not_interested_movies_are_excluded() -> None:
    results = RecommendationEngine().recommend(
        UserRecommendationSignals(favorite_genres=("Action",), not_interested=frozenset({4, 5})),
        CATALOG,
    )
    assert {item.movie.tmdb_id for item in results}.isdisjoint({4, 5})
    assert {item.movie.tmdb_id for item in results}


def test_dislike_penalty_lowers_rank() -> None:
    first = _movie(
        tmdb_id=10,
        title="Alpha Strike",
        overview="Action spies explode downtown.",
        genres=("Action",),
        vote_average=8.5,
        popularity=80.0,
    )
    second = _movie(
        tmdb_id=11,
        title="Bravo Strike",
        overview="Action spies explode downtown.",
        genres=("Action",),
        vote_average=8.5,
        popularity=80.0,
    )
    results = RecommendationEngine().recommend(
        UserRecommendationSignals(favorite_genres=("Action",), dislikes=frozenset({10})),
        [first, second],
    )
    assert _titles(results) == ["Bravo Strike", "Alpha Strike"]
    assert results[1].breakdown.penalty == pytest.approx(DISLIKE_PENALTY)
    assert results[1].score < results[0].score


def test_watched_movies_are_deprioritized() -> None:
    first = _movie(
        tmdb_id=10,
        title="Alpha Strike",
        overview="Action spies explode downtown.",
        genres=("Action",),
        vote_average=8.0,
        popularity=50.0,
    )
    second = _movie(
        tmdb_id=11,
        title="Bravo Strike",
        overview="Action spies explode downtown.",
        genres=("Action",),
        vote_average=8.0,
        popularity=50.0,
    )
    results = RecommendationEngine(penalize_watched=True).recommend(
        UserRecommendationSignals(favorite_genres=("Action",), watch_history=frozenset({10})),
        [first, second],
    )
    assert results[0].movie.tmdb_id == 11
    assert results[1].breakdown.penalty == pytest.approx(WATCHED_PENALTY)


def test_favorite_movie_similarity_pulls_related_titles() -> None:
    results = RecommendationEngine().recommend(
        UserRecommendationSignals(favorite_movies=(CATALOG[4],)),
        CATALOG,
    )
    titles = _titles(results)
    assert titles.index("John Wick") < titles.index("The Hours")
    assert titles.index("Die Hard") < titles.index("Amelie")


def test_likes_and_high_ratings_shape_the_user_vector() -> None:
    liked = RecommendationEngine().recommend(
        UserRecommendationSignals(likes=frozenset({5}), ratings={5: 5}),
        CATALOG,
    )
    cold = RecommendationEngine().recommend(UserRecommendationSignals(), CATALOG)
    liked_action = [item.movie.title for item in liked if "Action" in item.movie.genres]
    cold_action = [item.movie.title for item in cold if "Action" in item.movie.genres]
    assert liked_action[0] in {"Die Hard", "John Wick", "Inception"}
    assert liked[0].movie.title == cold[0].movie.title or liked_action != cold_action


def test_release_period_boosts_matching_years() -> None:
    classic = _movie(
        tmdb_id=20,
        title="Classic Action",
        overview="Action shootout.",
        genres=("Action",),
        release_year=1975,
        vote_average=7.0,
        popularity=50.0,
    )
    modern = _movie(
        tmdb_id=21,
        title="Modern Action",
        overview="Action shootout.",
        genres=("Action",),
        release_year=2015,
        vote_average=7.0,
        popularity=50.0,
    )
    results = RecommendationEngine().recommend(
        UserRecommendationSignals(favorite_genres=("Action",), release_period="before-1980"),
        [classic, modern],
    )
    assert results[0].movie.tmdb_id == 20
    assert any("Classic" in reason for reason in results[0].reasons)
    assert year_in_release_period(2014, "2010s")
    assert not year_in_release_period(2009, "2010s")


def test_ranking_is_deterministic() -> None:
    signals = UserRecommendationSignals(
        favorite_genres=("Action",),
        favorite_movies=(CATALOG[4],),
        ratings={5: 5},
        likes=frozenset({5}),
        watch_history=frozenset({1}),
    )
    engine = RecommendationEngine()
    first = [(item.movie.tmdb_id, pytest.approx(item.score)) for item in engine.recommend(signals, CATALOG)]
    second = [(item.movie.tmdb_id, pytest.approx(item.score)) for item in engine.recommend(signals, CATALOG)]
    assert first == second


def test_explanations_are_human_readable() -> None:
    results = RecommendationEngine().recommend(
        UserRecommendationSignals(favorite_genres=("Action",), favorite_movies=(CATALOG[4],)),
        CATALOG,
        limit=3,
    )
    for item in results:
        assert item.reasons
        assert all("cosine" not in reason.lower() for reason in item.reasons)
        assert item.breakdown.final_score == pytest.approx(item.score)


def test_empty_and_fully_excluded_catalogs() -> None:
    engine = RecommendationEngine()
    assert engine.recommend(UserRecommendationSignals(), []) == []
    assert (
        engine.recommend(
            UserRecommendationSignals(not_interested=frozenset(movie.tmdb_id for movie in CATALOG)),
            CATALOG,
        )
        == []
    )


def test_candidate_from_dto_and_signals_from_preferences() -> None:
    details = MovieDetailsDTO(
        tmdb_id=550,
        title="Fight Club",
        overview="An insomniac office worker.",
        genres=[GenreDTO(tmdb_genre_id=18, name="Drama")],
        genre_ids=[18],
        vote_average=8.4,
        original_language="en",
    )
    movie = CandidateMovie.from_dto(details)
    assert movie.genres == ("Drama",)
    assert movie.genre_ids == (18,)

    signals = UserRecommendationSignals.from_preferences(
        UserPreferences(
            favorite_genres=[GenrePreference(tmdb_genre_id=28, name="Action")],
            favorite_movies=[MoviePreference(tmdb_id=5, title="Inception")],
            preferred_language="en",
            release_period="2010s",
            minimum_rating=7.0,
            interests=["dreams"],
        ),
        likes=[5],
        favorite_movie_details=(CATALOG[4],),
    )
    assert signals.favorite_genres == ("Action",)
    assert signals.favorite_movies[0].overview.startswith("A thief")
    assert signals.likes == frozenset({5})


def test_tfidf_user_vector_is_deterministic() -> None:
    documents = ["action thriller heist", "quiet drama novel", "action thriller heist"]
    first = cosine_to_user_vector(documents, "action thriller")
    second = cosine_to_user_vector(documents, "action thriller")
    assert first.tolist() == second.tolist()
    assert first[0] == pytest.approx(first[2])
    assert first[0] > first[1]


def test_recommendation_package_has_no_qt_imports() -> None:
    root = Path(__file__).resolve().parents[1] / "app" / "recommendation"
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("PySide")
                    assert not alias.name.startswith("PyQt")
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("PySide")
                assert not node.module.startswith("PyQt")
