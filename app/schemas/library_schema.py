from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MovieUserState:
    on_watchlist: bool = False
    watched: bool = False
    rating: int | None = None
    liked: bool = False
    disliked: bool = False
    not_interested: bool = False
