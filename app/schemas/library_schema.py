from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.schemas.movie_schema import MovieSummaryDTO


@dataclass(frozen=True)
class MovieUserState:
    on_watchlist: bool = False
    watched: bool = False
    rating: int | None = None
    liked: bool = False
    disliked: bool = False
    not_interested: bool = False


@dataclass(frozen=True)
class WatchlistEntryDTO:
    movie: MovieSummaryDTO
    created_at: datetime | None = None
    watched: bool = False


@dataclass(frozen=True)
class HistoryEntryDTO:
    movie: MovieSummaryDTO
    watched_at: datetime | None = None
    rating: int | None = None
