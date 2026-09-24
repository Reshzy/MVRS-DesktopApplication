from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.schemas.movie_schema import MovieSummaryDTO


@dataclass(frozen=True)
class RatedMovieDTO:
    movie: MovieSummaryDTO
    rating: int


@dataclass(frozen=True)
class ActivityItemDTO:
    kind: str
    movie: MovieSummaryDTO
    occurred_at: datetime | None
    detail: str


@dataclass(frozen=True)
class InsightsDTO:
    watched_count: int = 0
    watchlist_count: int = 0
    average_rating: float | None = None
    favorite_genres: list[str] = field(default_factory=list)
    most_watched_genre: str | None = None
    highest_rated: list[RatedMovieDTO] = field(default_factory=list)
    recent_activity: list[ActivityItemDTO] = field(default_factory=list)
