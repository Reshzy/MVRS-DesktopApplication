from __future__ import annotations

import logging
from typing import Any

import httpx

from app.api.exceptions import (
    TMDBAPIError,
    TMDBConfigError,
    TMDBConnectionError,
    TMDBTimeoutError,
)
from app.config.settings import Settings, get_settings
from app.schemas.movie_schema import DiscoverFilters
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
DEFAULT_TIMEOUT_SECONDS = 10.0


class TMDBClient:
    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.Client | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._settings = settings or get_settings()
        self._owns_client = http_client is None
        headers = {"Accept": "application/json"}
        if self._settings.tmdb_access_token:
            headers["Authorization"] = f"Bearer {self._settings.tmdb_access_token}"
        self._http = http_client or httpx.Client(
            base_url=TMDB_BASE_URL,
            timeout=timeout,
            headers=headers,
        )

    def search_movies(self, query: str, page: int = 1) -> dict[str, Any]:
        return self._get("/search/movie", params={"query": query, "page": page})

    def get_movie_details(self, movie_id: int) -> dict[str, Any]:
        return self._get(f"/movie/{movie_id}")

    def get_popular_movies(self, page: int = 1) -> dict[str, Any]:
        return self._get("/movie/popular", params={"page": page})

    def get_trending_movies(self, window: str = "week") -> dict[str, Any]:
        return self._get(f"/trending/movie/{window}")

    def get_genres(self) -> dict[str, Any]:
        return self._get("/genre/movie/list")

    def get_movie_credits(self, movie_id: int) -> dict[str, Any]:
        return self._get(f"/movie/{movie_id}/credits")

    def get_similar_movies(self, movie_id: int) -> dict[str, Any]:
        return self._get(f"/movie/{movie_id}/similar")

    def discover_movies(self, filters: DiscoverFilters | dict[str, Any] | None = None) -> dict[str, Any]:
        payload = filters if isinstance(filters, DiscoverFilters) else DiscoverFilters.model_validate(filters or {})
        return self._get("/discover/movie", params=payload.to_params())

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_configured()
        query = dict(params or {})
        if not self._settings.tmdb_access_token and self._settings.tmdb_api_key:
            query["api_key"] = self._settings.tmdb_api_key

        try:
            response = self._http.get(path, params=query)
        except httpx.TimeoutException as exc:
            logger.warning("TMDB request timed out path=%s", path)
            raise TMDBTimeoutError("The movie service took too long to respond.") from exc
        except httpx.ConnectError as exc:
            logger.warning("TMDB connection failed path=%s", path)
            raise TMDBConnectionError("Could not reach the movie service. Check your internet connection.") from exc
        except httpx.HTTPError as exc:
            logger.warning("TMDB request failed path=%s error=%s", path, exc.__class__.__name__)
            raise TMDBConnectionError("The movie service is unavailable right now.") from exc

        if response.status_code == 404:
            logger.info("TMDB resource missing path=%s status=%s", path, response.status_code)
            raise TMDBAPIError("That movie could not be found.", status_code=404)
        if response.status_code in {401, 403}:
            logger.warning("TMDB authentication failed status=%s path=%s", response.status_code, path)
            raise TMDBAPIError("Movie service authentication failed. Check your TMDB credentials.", status_code=response.status_code)
        if response.status_code >= 400:
            logger.warning("TMDB API error status=%s path=%s", response.status_code, path)
            raise TMDBAPIError("The movie service returned an error.", status_code=response.status_code)

        payload = response.json()
        if not isinstance(payload, dict):
            raise TMDBAPIError("The movie service returned an unexpected response.")
        return payload

    def _ensure_configured(self) -> None:
        if self._settings.tmdb_access_token or self._settings.tmdb_api_key:
            return
        raise TMDBConfigError("TMDB credentials are not configured.")
