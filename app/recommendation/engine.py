from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.recommendation.content_based import compute_content_scores
from app.recommendation.feature_builder import (
    CandidateMovie,
    UserRecommendationSignals,
    build_catalog,
    build_feature_frame,
)
from app.recommendation.scoring import apply_scores
from app.schemas.user_schema import RELEASE_PERIOD_LABELS
from app.utils.constants import DEFAULT_RECOMMENDATION_LIMIT, RECOMMENDATION_WEIGHTS
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class RecommendationError(Exception):
    pass


@dataclass(frozen=True)
class ScoreBreakdown:
    genre_similarity: float
    favorite_movie_similarity: float
    tmdb_rating_score: float
    popularity_score: float
    release_preference_score: float
    interaction_score: float
    penalty: float
    final_score: float


@dataclass(frozen=True)
class Recommendation:
    movie: CandidateMovie
    score: float
    reasons: tuple[str, ...]
    breakdown: ScoreBreakdown


class RecommendationEngine:
    def __init__(
        self,
        *,
        weights: Mapping[str, float] | None = None,
        penalize_watched: bool = True,
        limit: int = DEFAULT_RECOMMENDATION_LIMIT,
    ) -> None:
        self._weights = dict(weights or RECOMMENDATION_WEIGHTS)
        self._penalize_watched = penalize_watched
        self._limit = limit

    def recommend(
        self,
        signals: UserRecommendationSignals,
        candidates: Sequence[CandidateMovie],
        *,
        limit: int | None = None,
    ) -> list[Recommendation]:
        try:
            return self._rank(signals, candidates, limit=self._limit if limit is None else limit)
        except RecommendationError:
            raise
        except Exception as exc:
            logger.exception("Recommendation ranking failed")
            raise RecommendationError("Could not generate recommendations.") from exc

    def _rank(
        self,
        signals: UserRecommendationSignals,
        candidates: Sequence[CandidateMovie],
        *,
        limit: int,
    ) -> list[Recommendation]:
        visible = [movie for movie in candidates if movie.tmdb_id not in signals.not_interested]
        if not visible:
            return []

        movies_by_id = {movie.tmdb_id: movie for movie in visible}
        frame = build_feature_frame(visible)
        catalog = build_catalog(visible, signals.favorite_movies)
        content = compute_content_scores(frame, signals, catalog)
        nearest_by_id = {
            movie.tmdb_id: title
            for movie, title in zip(visible, content.nearest_favorite, strict=False)
        }
        scored = apply_scores(
            frame,
            signals,
            content,
            weights=self._weights,
            penalize_watched=self._penalize_watched,
        )
        ranked = scored.sort_values(
            by=["final_score", "tmdb_id"],
            ascending=[False, True],
            kind="mergesort",
        )

        recommendations: list[Recommendation] = []
        for row in ranked.itertuples(index=False):
            movie = movies_by_id[int(row.tmdb_id)]
            breakdown = ScoreBreakdown(
                genre_similarity=float(row.genre_similarity),
                favorite_movie_similarity=float(row.favorite_movie_similarity),
                tmdb_rating_score=float(row.tmdb_rating_score),
                popularity_score=float(row.popularity_score),
                release_preference_score=float(row.release_preference_score),
                interaction_score=float(row.interaction_score),
                penalty=float(row.penalty),
                final_score=float(row.final_score),
            )
            nearest = nearest_by_id.get(movie.tmdb_id)
            recommendations.append(
                Recommendation(
                    movie=movie,
                    score=breakdown.final_score,
                    reasons=explanation_reasons(movie, signals, breakdown, nearest),
                    breakdown=breakdown,
                )
            )
            if len(recommendations) >= limit:
                break
        return recommendations


def explanation_reasons(
    movie: CandidateMovie,
    signals: UserRecommendationSignals,
    breakdown: ScoreBreakdown,
    nearest_favorite: str | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    matched = [genre for genre in movie.genres if genre in signals.favorite_genres]
    if matched and breakdown.genre_similarity > 0:
        reasons.append(f"Matches your interest in {', '.join(matched)}")
    if nearest_favorite and breakdown.favorite_movie_similarity > 0:
        reasons.append(f"Similar to {nearest_favorite}")
    elif breakdown.favorite_movie_similarity > 0:
        reasons.append("Similar to titles you enjoy")
    if signals.release_period and breakdown.release_preference_score >= 1.0:
        label = RELEASE_PERIOD_LABELS.get(signals.release_period, signals.release_period)
        reasons.append(f"Fits your {label} preference")
    if movie.vote_average is not None and movie.vote_average >= 7.5:
        reasons.append("Highly rated")
    overview = (movie.overview or "").casefold()
    for interest in signals.interests:
        if interest.casefold() in overview:
            reasons.append(f"Touches on {interest}")
            break
    if not reasons:
        if breakdown.popularity_score > 0 or breakdown.tmdb_rating_score > 0:
            reasons.append("Popular and well reviewed")
        else:
            reasons.append("Suggested for you")
    return tuple(reasons[:3])
