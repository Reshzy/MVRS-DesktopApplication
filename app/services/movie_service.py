from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.api.tmdb_client import TMDBClient
from app.database.session import session_scope
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie_schema import (
    CreditsDTO,
    DiscoverFilters,
    GenreDTO,
    MovieDetailsBundle,
    MovieDetailsDTO,
    MoviePageDTO,
    MovieSummaryDTO,
)
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class MovieService:
    def __init__(
        self,
        client: TMDBClient | None = None,
        session: Session | None = None,
        repository: MovieRepository | None = None,
        *,
        cache_enabled: bool = True,
    ) -> None:
        self._client = client or TMDBClient()
        self._session = session
        self._repository = repository if repository is not None else (
            MovieRepository(session) if session is not None else None
        )
        self._cache_enabled = cache_enabled

    def close(self) -> None:
        self._client.close()

    def search_movies(self, query: str, page: int = 1) -> MoviePageDTO:
        if not query.strip():
            return MoviePageDTO()
        result = MoviePageDTO.from_tmdb(self._client.search_movies(query.strip(), page=page))
        self._cache_page(result)
        return result

    def get_movie_details(self, movie_id: int) -> MovieDetailsDTO:
        details = MovieDetailsDTO.from_tmdb(self._client.get_movie_details(movie_id))
        self._cache_movie(details)
        return details

    def get_popular_movies(self, page: int = 1) -> MoviePageDTO:
        result = MoviePageDTO.from_tmdb(self._client.get_popular_movies(page=page))
        self._cache_page(result)
        return result

    def get_trending_movies(self) -> MoviePageDTO:
        result = MoviePageDTO.from_tmdb(self._client.get_trending_movies())
        self._cache_page(result)
        return result

    def get_genres(self) -> list[GenreDTO]:
        payload = self._client.get_genres()
        genres = [GenreDTO.from_tmdb(item) for item in payload.get("genres") or []]
        self._cache_genres(genres)
        return genres

    def get_movie_credits(self, movie_id: int) -> CreditsDTO:
        return CreditsDTO.from_tmdb(self._client.get_movie_credits(movie_id))

    def get_similar_movies(self, movie_id: int) -> MoviePageDTO:
        result = MoviePageDTO.from_tmdb(self._client.get_similar_movies(movie_id))
        self._cache_page(result)
        return result

    def get_details_bundle(self, movie_id: int) -> MovieDetailsBundle:
        details = self.get_movie_details(movie_id)
        credits = CreditsDTO()
        similar: list[MovieSummaryDTO] = []
        try:
            credits = self.get_movie_credits(movie_id)
        except Exception:
            logger.exception("Failed to load credits for tmdb_id=%s", movie_id)
        try:
            similar = self.get_similar_movies(movie_id).results
        except Exception:
            logger.exception("Failed to load similar movies for tmdb_id=%s", movie_id)
        return MovieDetailsBundle(details=details, credits=credits, similar=similar)

    def discover_movies(self, filters: DiscoverFilters | dict | None = None) -> MoviePageDTO:
        result = MoviePageDTO.from_tmdb(self._client.discover_movies(filters))
        self._cache_page(result)
        return result

    def _cache_page(self, page: MoviePageDTO) -> None:
        self._cache_movies(page.results)

    def _cache_movie(self, movie: MovieSummaryDTO) -> None:
        self._cache_movies([movie])

    def _cache_movies(self, movies: list[MovieSummaryDTO]) -> None:
        if not movies:
            return
        self._with_repository(lambda repository: repository.upsert_many(movies))

    def _cache_genres(self, genres: list[GenreDTO]) -> None:
        if not genres:
            return
        self._with_repository(lambda repository: repository.upsert_genres(genres))

    def _with_repository(self, action: Callable[[MovieRepository], None]) -> None:
        if not self._cache_enabled:
            return
        try:
            if self._repository is not None:
                action(self._repository)
                if self._session is not None:
                    self._session.commit()
                return
            with session_scope() as session:
                action(MovieRepository(session))
        except Exception:
            logger.exception("Failed to cache movie metadata")
            if self._session is not None:
                self._session.rollback()
            raise
