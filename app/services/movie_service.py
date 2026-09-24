from __future__ import annotations

from app.api.tmdb_client import TMDBClient
from app.schemas.movie_schema import (
    CreditsDTO,
    DiscoverFilters,
    GenreDTO,
    MovieDetailsDTO,
    MoviePageDTO,
)


class MovieService:
    def __init__(self, client: TMDBClient | None = None) -> None:
        self._client = client or TMDBClient()

    def search_movies(self, query: str, page: int = 1) -> MoviePageDTO:
        if not query.strip():
            return MoviePageDTO()
        return MoviePageDTO.from_tmdb(self._client.search_movies(query.strip(), page=page))

    def get_movie_details(self, movie_id: int) -> MovieDetailsDTO:
        return MovieDetailsDTO.from_tmdb(self._client.get_movie_details(movie_id))

    def get_popular_movies(self, page: int = 1) -> MoviePageDTO:
        return MoviePageDTO.from_tmdb(self._client.get_popular_movies(page=page))

    def get_trending_movies(self) -> MoviePageDTO:
        return MoviePageDTO.from_tmdb(self._client.get_trending_movies())

    def get_genres(self) -> list[GenreDTO]:
        payload = self._client.get_genres()
        return [GenreDTO.from_tmdb(item) for item in payload.get("genres") or []]

    def get_movie_credits(self, movie_id: int) -> CreditsDTO:
        return CreditsDTO.from_tmdb(self._client.get_movie_credits(movie_id))

    def get_similar_movies(self, movie_id: int) -> MoviePageDTO:
        return MoviePageDTO.from_tmdb(self._client.get_similar_movies(movie_id))

    def discover_movies(self, filters: DiscoverFilters | dict | None = None) -> MoviePageDTO:
        return MoviePageDTO.from_tmdb(self._client.discover_movies(filters))
