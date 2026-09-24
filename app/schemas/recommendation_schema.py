from __future__ import annotations

from dataclasses import dataclass

from app.schemas.movie_schema import MovieSummaryDTO


@dataclass(frozen=True)
class RecommendedMovie:
    movie: MovieSummaryDTO
    reason: str
    reasons: tuple[str, ...] = ()
