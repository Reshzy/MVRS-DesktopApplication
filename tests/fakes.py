from __future__ import annotations

import time
from datetime import date, timedelta

from app.api.exceptions import TMDBConnectionError
from app.schemas.movie_schema import (
    CastMemberDTO,
    CreditsDTO,
    DiscoverFilters,
    GenreDTO,
    MovieDetailsBundle,
    MovieDetailsDTO,
    MoviePageDTO,
    MovieSummaryDTO,
)


def sample_movie(index: int = 1, title: str | None = None, **updates: object) -> MovieSummaryDTO:
    payload = {
        "tmdb_id": 1000 + index,
        "title": title or f"Sample Movie {index}",
        "overview": f"Overview for movie {index}.",
        "release_date": date(2000 + index, 5, 1),
        "vote_average": 7.0 + index / 10,
        "poster_path": None,
        "genre_ids": [],
    }
    payload.update(updates)
    return MovieSummaryDTO(**payload)


class FakeMovieService:
    def __init__(self) -> None:
        self.search_calls: list[tuple[str, int]] = []
        self.discover_calls: list[DiscoverFilters] = []
        self.details_calls: list[int] = []
        self.credits_calls: list[int] = []
        self.similar_calls: list[int] = []
        self.popular_calls: list[int] = []
        self.trending_calls = 0
        self.genre_calls = 0
        self.delay = 0.0
        self.query_delays: dict[str, float] = {}
        self.echo_query = False
        self.fail = False
        self.fail_methods: set[str] = set()
        self.empty = False
        self.total_pages = 2
        self.genres = [
            GenreDTO(tmdb_genre_id=18, name="Drama"),
            GenreDTO(tmdb_genre_id=28, name="Action"),
        ]
        self.movies = [
            sample_movie(1, "Fight Club", genre_ids=[18], popularity=70.0, original_language="en"),
            sample_movie(2, "Inception", genre_ids=[28], popularity=90.0, original_language="en"),
        ]

    def close(self) -> None:
        return None

    def get_genres(self) -> list[GenreDTO]:
        self._maybe_delay()
        self.genre_calls += 1
        self._maybe_fail("get_genres")
        return list(self.genres)

    def search_movies(self, query: str, page: int = 1) -> MoviePageDTO:
        self._maybe_delay(self.query_delays.get(query, self.delay))
        self.search_calls.append((query, page))
        self._maybe_fail("search_movies")
        if not query.strip():
            return MoviePageDTO()
        page_data = self._page(page)
        if self.echo_query and page_data.results:
            first = page_data.results[0].model_copy(update={"title": query.strip()})
            page_data = MoviePageDTO(
                page=page_data.page,
                total_pages=page_data.total_pages,
                total_results=page_data.total_results,
                results=[first, *page_data.results[1:]],
            )
        return page_data

    def get_movie_details(self, movie_id: int) -> MovieDetailsDTO:
        self._maybe_delay()
        self.details_calls.append(movie_id)
        self._maybe_fail("get_movie_details")
        movie = next((item for item in self.movies if item.tmdb_id == movie_id), self.movies[0])
        payload = movie.model_dump()
        payload["runtime"] = 139
        payload["original_language"] = movie.original_language or "en"
        payload["genres"] = [GenreDTO(tmdb_genre_id=18, name="Drama")]
        return MovieDetailsDTO(**payload)

    def get_movie_credits(self, movie_id: int) -> CreditsDTO:
        self._maybe_delay()
        self.credits_calls.append(movie_id)
        self._maybe_fail("get_movie_credits")
        return CreditsDTO(
            cast=[
                CastMemberDTO(name="Brad Pitt", character="Tyler Durden"),
                CastMemberDTO(name="Edward Norton", character="The Narrator"),
            ],
            director="David Fincher",
        )

    def get_popular_movies(self, page: int = 1) -> MoviePageDTO:
        self._maybe_delay()
        self.popular_calls.append(page)
        self._maybe_fail("get_popular_movies")
        return self._page(page)

    def get_trending_movies(self) -> MoviePageDTO:
        self._maybe_delay()
        self.trending_calls += 1
        self._maybe_fail("get_trending_movies")
        return self._page(1)

    def get_similar_movies(self, movie_id: int) -> MoviePageDTO:
        self._maybe_delay()
        self.similar_calls.append(movie_id)
        self._maybe_fail("get_similar_movies")
        others = [item for item in self.movies if item.tmdb_id != movie_id]
        return MoviePageDTO(page=1, total_pages=1, total_results=len(others), results=others)

    def get_details_bundle(self, movie_id: int) -> MovieDetailsBundle:
        details = self.get_movie_details(movie_id)
        try:
            credits = self.get_movie_credits(movie_id)
        except Exception:
            credits = CreditsDTO()
        try:
            similar = self.get_similar_movies(movie_id).results
        except Exception:
            similar = []
        return MovieDetailsBundle(details=details, credits=credits, similar=similar)

    def discover_movies(self, filters: DiscoverFilters | dict | None = None) -> MoviePageDTO:
        self._maybe_delay()
        payload = filters if isinstance(filters, DiscoverFilters) else DiscoverFilters.model_validate(filters or {})
        self.discover_calls.append(payload)
        self._maybe_fail("discover_movies")
        return self._page(payload.page)

    def get_recent_movies(self, page: int = 1) -> MoviePageDTO:
        self._maybe_delay()
        self._maybe_fail("get_recent_movies")
        today = date.today()
        start = today - timedelta(days=365)
        payload = DiscoverFilters(
            page=page,
            sort_by="primary_release_date.desc",
            primary_release_date_gte=start.isoformat(),
            primary_release_date_lte=today.isoformat(),
        )
        self.discover_calls.append(payload)
        return self._page(page)

    def get_highly_rated_movies(self, page: int = 1) -> MoviePageDTO:
        self._maybe_delay()
        self._maybe_fail("get_highly_rated_movies")
        payload = DiscoverFilters(page=page, sort_by="vote_average.desc", vote_average_gte=7.0)
        self.discover_calls.append(payload)
        return self._page(page)

    def _page(self, page: int) -> MoviePageDTO:
        if self.empty:
            return MoviePageDTO(page=page, total_pages=1, total_results=0, results=[])
        return MoviePageDTO(
            page=page,
            total_pages=self.total_pages,
            total_results=len(self.movies) * self.total_pages,
            results=list(self.movies),
        )

    def _maybe_delay(self, delay: float | None = None) -> None:
        wait = self.delay if delay is None else delay
        if wait:
            time.sleep(wait)

    def _maybe_fail(self, method: str = "") -> None:
        if self.fail or method in self.fail_methods:
            raise TMDBConnectionError("Could not reach the movie service. Check your internet connection.")
