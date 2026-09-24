from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from app.recommendation.content_based import ContentScores
from app.recommendation.feature_builder import UserRecommendationSignals
from app.utils.constants import (
    DISLIKE_PENALTY,
    MAX_RATING,
    RECOMMENDATION_WEIGHTS,
    WATCHED_PENALTY,
)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def release_period_bounds(period: str | None) -> tuple[str | None, str | None] | None:
    if not period:
        return None
    if period == "before-1980":
        return (None, "1979-12-31")
    decade = period[:-1] if period.endswith("s") else ""
    if decade.isdigit():
        start = int(decade)
        return (f"{start}-01-01", f"{start + 9}-12-31")
    return None


def year_in_release_period(year: int | None, period: str | None) -> bool:
    if year is None or not period:
        return False
    if period == "before-1980":
        return year < 1980
    decade = period[:-1] if period.endswith("s") else ""
    if decade.isdigit():
        start = int(decade)
        return start <= year <= start + 9
    return False


def tmdb_rating_score(vote_average: float | None, minimum_rating: float | None = None) -> float:
    if vote_average is None:
        return 0.0
    score = clamp01(float(vote_average) / 10.0)
    if minimum_rating is not None and float(vote_average) < float(minimum_rating):
        return score * 0.4
    return score


def popularity_scores(values: Sequence[float | None]) -> np.ndarray:
    raw = np.array([0.0 if value is None else max(float(value), 0.0) for value in values], dtype=float)
    if raw.size == 0:
        return raw
    peak = float(raw.max())
    if peak <= 0:
        return np.zeros_like(raw)
    return np.log1p(raw) / np.log1p(peak)


def release_preference_score(year: int | None, period: str | None) -> float:
    if not period:
        return 0.5
    return 1.0 if year_in_release_period(year, period) else 0.0


def interaction_score(tmdb_id: int, signals: UserRecommendationSignals) -> float:
    score = 0.0
    if tmdb_id in signals.likes:
        score += 0.6
    rating = signals.ratings.get(tmdb_id)
    if rating is not None:
        score += 0.4 * (int(rating) / MAX_RATING)
    return clamp01(score)


def penalty_amount(
    tmdb_id: int,
    signals: UserRecommendationSignals,
    *,
    penalize_watched: bool,
) -> float:
    penalty = 0.0
    if tmdb_id in signals.dislikes:
        penalty += DISLIKE_PENALTY
    if penalize_watched and tmdb_id in signals.watch_history:
        penalty += WATCHED_PENALTY
    return penalty


def weighted_base_score(components: Mapping[str, float], weights: Mapping[str, float]) -> float:
    return float(sum(float(components[key]) * float(weight) for key, weight in weights.items()))


def _optional_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def apply_scores(
    frame: pd.DataFrame,
    signals: UserRecommendationSignals,
    content: ContentScores,
    *,
    weights: Mapping[str, float] | None = None,
    penalize_watched: bool = True,
) -> pd.DataFrame:
    score_weights = dict(weights or RECOMMENDATION_WEIGHTS)
    scored = frame.copy()
    pop_scores = popularity_scores(scored["popularity"].tolist())

    genre_scores: list[float] = []
    content_scores: list[float] = []
    rating_scores: list[float] = []
    popularity_column: list[float] = []
    release_scores: list[float] = []
    interaction_scores: list[float] = []
    penalties: list[float] = []
    finals: list[float] = []

    for position, row in enumerate(scored.itertuples(index=False)):
        tmdb_id = int(row.tmdb_id)
        components = {
            "genre_similarity": float(content.genre_similarity[position]) if position < len(content.genre_similarity) else 0.0,
            "favorite_movie_similarity": (
                float(content.favorite_movie_similarity[position])
                if position < len(content.favorite_movie_similarity)
                else 0.0
            ),
            "tmdb_rating_score": tmdb_rating_score(
                _optional_float(row.vote_average),
                signals.minimum_rating,
            ),
            "popularity_score": float(pop_scores[position]) if position < len(pop_scores) else 0.0,
            "release_preference_score": release_preference_score(
                _optional_int(row.release_year),
                signals.release_period,
            ),
            "interaction_score": interaction_score(tmdb_id, signals),
        }
        penalty = penalty_amount(tmdb_id, signals, penalize_watched=penalize_watched)
        final = weighted_base_score(components, score_weights) - penalty

        genre_scores.append(components["genre_similarity"])
        content_scores.append(components["favorite_movie_similarity"])
        rating_scores.append(components["tmdb_rating_score"])
        popularity_column.append(components["popularity_score"])
        release_scores.append(components["release_preference_score"])
        interaction_scores.append(components["interaction_score"])
        penalties.append(penalty)
        finals.append(final)

    scored["genre_similarity"] = genre_scores
    scored["favorite_movie_similarity"] = content_scores
    scored["tmdb_rating_score"] = rating_scores
    scored["popularity_score"] = popularity_column
    scored["release_preference_score"] = release_scores
    scored["interaction_score"] = interaction_scores
    scored["penalty"] = penalties
    scored["final_score"] = finals
    return scored
