from __future__ import annotations

import time
from datetime import date

from app.api.exceptions import TMDBConnectionError
from app.schemas.movie_schema import DiscoverFilters, GenreDTO, MoviePageDTO, MovieSummaryDTO


def sample_movie(index: int = 1, title: str | None = None) -> MovieSummaryDTO:
    return MovieSummaryDTO(
        tmdb_id=1000 + index,
        title=title or f"Sample Movie {index}",
        overview=f"Overview for movie {index}.",
        release_date=date(2000 + index, 5, 1),
        vote_average=7.0 + index / 10,
        poster_path=None,
    )


class FakeMovieService:
    def __init__(self) -> None:
        self.search_calls: list[tuple[str, int]] = []
        self.discover_calls: list[DiscoverFilters] = []
        self.genre_calls = 0
        self.delay = 0.0
        self.fail = False
        self.empty = False
        self.total_pages = 2
        self.genres = [
            GenreDTO(tmdb_genre_id=18, name="Drama"),
            GenreDTO(tmdb_genre_id=28, name="Action"),
        ]
        self.movies = [sample_movie(1, "Fight Club"), sample_movie(2, "Inception")]

    def close(self) -> None:
        return None

    def get_genres(self) -> list[GenreDTO]:
        self._maybe_delay()
        self.genre_calls += 1
        self._maybe_fail()
        return list(self.genres)

    def search_movies(self, query: str, page: int = 1) -> MoviePageDTO:
        self._maybe_delay()
        self.search_calls.append((query, page))
        self._maybe_fail()
        if not query.strip():
            return MoviePageDTO()
        return self._page(page)

    def discover_movies(self, filters: DiscoverFilters | dict | None = None) -> MoviePageDTO:
        self._maybe_delay()
        payload = filters if isinstance(filters, DiscoverFilters) else DiscoverFilters.model_validate(filters or {})
        self.discover_calls.append(payload)
        self._maybe_fail()
        return self._page(payload.page)

    def _page(self, page: int) -> MoviePageDTO:
        if self.empty:
            return MoviePageDTO(page=page, total_pages=1, total_results=0, results=[])
        return MoviePageDTO(
            page=page,
            total_pages=self.total_pages,
            total_results=len(self.movies) * self.total_pages,
            results=list(self.movies),
        )

    def _maybe_delay(self) -> None:
        if self.delay:
            time.sleep(self.delay)

    def _maybe_fail(self) -> None:
        if self.fail:
            raise TMDBConnectionError("Could not reach the movie service. Check your internet connection.")
