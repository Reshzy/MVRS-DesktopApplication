from __future__ import annotations

import httpx
import pytest

from app.api.exceptions import TMDBAPIError, TMDBConfigError, TMDBConnectionError, TMDBTimeoutError
from app.api.tmdb_client import TMDB_BASE_URL, TMDBClient
from app.config.settings import Settings
from app.schemas.movie_schema import DiscoverFilters, MovieDetailsBundle, MovieDetailsDTO, MoviePageDTO
from app.services.movie_service import MovieService

SAMPLE_MOVIE = {
    "id": 550,
    "title": "Fight Club",
    "original_title": "Fight Club",
    "overview": "An insomniac office worker...",
    "poster_path": "/pB8BM7pdSp6B6ih7QZ4DrQ3PmJK.jpg",
    "backdrop_path": "/backdrop.jpg",
    "release_date": "1999-10-15",
    "vote_average": 8.4,
    "vote_count": 26000,
    "popularity": 70.1,
    "original_language": "en",
    "genre_ids": [18],
    "runtime": 139,
    "genres": [{"id": 18, "name": "Drama"}],
}

PAGE = {"page": 1, "total_pages": 2, "total_results": 1, "results": [SAMPLE_MOVIE]}


def _service(handler) -> MovieService:
    settings = Settings(tmdb_access_token="test-token")
    http_client = httpx.Client(
        base_url=TMDB_BASE_URL,
        transport=httpx.MockTransport(handler),
        headers={"Accept": "application/json"},
    )
    return MovieService(
        TMDBClient(settings=settings, http_client=http_client),
        cache_enabled=False,
    )


def test_search_movies_returns_dtos() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/search/movie")
        assert "query=inception" in str(request.url)
        return httpx.Response(200, json=PAGE)

    page = _service(handler).search_movies("inception")
    assert isinstance(page, MoviePageDTO)
    assert page.results[0].tmdb_id == 550
    assert page.results[0].title == "Fight Club"
    assert page.results[0].release_date.year == 1999


def test_empty_search_skips_network() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("empty search should not call TMDB")

    page = _service(handler).search_movies("   ")
    assert page.results == []


def test_movie_details_and_credits() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/movie/550/credits"):
            return httpx.Response(
                200,
                json={
                    "cast": [{"name": "Brad Pitt", "character": "Tyler"}],
                    "crew": [{"name": "David Fincher", "job": "Director"}],
                },
            )
        if request.url.path.endswith("/movie/550"):
            return httpx.Response(200, json=SAMPLE_MOVIE)
        raise AssertionError(request.url.path)

    service = _service(handler)
    details = service.get_movie_details(550)
    credits = service.get_movie_credits(550)
    assert isinstance(details, MovieDetailsDTO)
    assert details.runtime == 139
    assert details.genres[0].name == "Drama"
    assert credits.director == "David Fincher"
    assert credits.cast[0].name == "Brad Pitt"

    bundle = service.get_details_bundle(550)
    assert isinstance(bundle, MovieDetailsBundle)
    assert bundle.details.runtime == 139
    assert bundle.credits.director == "David Fincher"


def test_catalog_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/movie/popular"):
            return httpx.Response(200, json=PAGE)
        if path.endswith("/trending/movie/week"):
            return httpx.Response(200, json=PAGE)
        if path.endswith("/genre/movie/list"):
            return httpx.Response(200, json={"genres": [{"id": 28, "name": "Action"}]})
        if path.endswith("/movie/550/similar"):
            return httpx.Response(200, json=PAGE)
        if path.endswith("/discover/movie"):
            assert "sort_by=vote_average.desc" in str(request.url)
            return httpx.Response(200, json=PAGE)
        raise AssertionError(path)

    service = _service(handler)
    assert service.get_popular_movies().results[0].tmdb_id == 550
    assert service.get_trending_movies().results[0].title == "Fight Club"
    assert service.get_genres()[0].name == "Action"
    assert service.get_similar_movies(550).total_pages == 2
    discovered = service.discover_movies(DiscoverFilters(sort_by="vote_average.desc"))
    assert discovered.results[0].tmdb_id == 550


def test_missing_credentials() -> None:
    client = TMDBClient(settings=Settings(tmdb_api_key="", tmdb_access_token=""))
    with pytest.raises(TMDBConfigError):
        client.get_popular_movies()


def test_timeout_is_wrapped() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("slow")

    with pytest.raises(TMDBTimeoutError):
        _service(handler).get_popular_movies()


def test_connection_error_is_wrapped() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline")

    with pytest.raises(TMDBConnectionError):
        _service(handler).get_popular_movies()


def test_api_error_and_missing_movie() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/movie/1"):
            return httpx.Response(404, json={"status_message": "not found"})
        return httpx.Response(401, json={"status_message": "invalid"})

    service = _service(handler)
    with pytest.raises(TMDBAPIError) as missing:
        service.get_movie_details(1)
    assert missing.value.status_code == 404

    with pytest.raises(TMDBAPIError) as auth:
        service.get_popular_movies()
    assert auth.value.status_code == 401
