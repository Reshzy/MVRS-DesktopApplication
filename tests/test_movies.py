from __future__ import annotations

from datetime import date

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.tmdb_client import TMDB_BASE_URL, TMDBClient
from app.config.settings import Settings
from app.models.movie import Movie
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie_schema import GenreDTO, MovieDetailsDTO, MovieSummaryDTO
from app.services.movie_service import MovieService

FULL_DETAILS = MovieDetailsDTO(
    tmdb_id=550,
    title="Fight Club",
    original_title="Fight Club",
    overview="An insomniac office worker.",
    poster_path="/poster.jpg",
    backdrop_path="/backdrop.jpg",
    release_date=date(1999, 10, 15),
    runtime=139,
    vote_average=8.4,
    vote_count=26000,
    popularity=70.1,
    original_language="en",
    genres=[GenreDTO(tmdb_genre_id=18, name="Drama")],
)

SEARCH_HIT = MovieSummaryDTO(
    tmdb_id=550,
    title="Fight Club",
    original_title="Fight Club",
    overview="An insomniac office worker.",
    poster_path="/poster.jpg",
    backdrop_path="/backdrop.jpg",
    release_date=date(1999, 10, 15),
    vote_average=8.4,
    vote_count=26000,
    popularity=70.1,
    original_language="en",
    genre_ids=[18],
)


def _genre_names(movie: Movie) -> set[str]:
    return {link.genre.name for link in movie.genre_links}


def test_upsert_stores_metadata_and_genres(db_session: Session) -> None:
    repository = MovieRepository(db_session)

    stored = repository.upsert(FULL_DETAILS)

    assert stored is not None
    assert stored.tmdb_id == 550
    assert stored.title == "Fight Club"
    assert stored.original_title == "Fight Club"
    assert stored.overview == "An insomniac office worker."
    assert stored.poster_path == "/poster.jpg"
    assert stored.backdrop_path == "/backdrop.jpg"
    assert stored.release_date == date(1999, 10, 15)
    assert stored.runtime == 139
    assert stored.vote_average == 8.4
    assert stored.vote_count == 26000
    assert stored.popularity == 70.1
    assert stored.original_language == "en"
    assert _genre_names(stored) == {"Drama"}


def test_upsert_prevents_duplicate_movies(db_session: Session) -> None:
    repository = MovieRepository(db_session)
    repository.upsert(FULL_DETAILS)
    updated = SEARCH_HIT.model_copy(update={"title": "Fight Club (1999)", "vote_average": 8.8})

    repository.upsert(updated)

    assert db_session.scalar(select(func.count()).select_from(Movie)) == 1
    stored = repository.get_by_tmdb_id(550)
    assert stored is not None
    assert stored.title == "Fight Club (1999)"
    assert stored.vote_average == 8.8


def test_incomplete_payload_does_not_wipe_cached_fields(db_session: Session) -> None:
    repository = MovieRepository(db_session)
    repository.upsert(FULL_DETAILS)
    sparse = MovieSummaryDTO(tmdb_id=550, title="Fight Club", genre_ids=[])

    repository.upsert(sparse)

    stored = repository.get_by_tmdb_id(550)
    assert stored is not None
    assert stored.overview == "An insomniac office worker."
    assert stored.poster_path == "/poster.jpg"
    assert stored.backdrop_path == "/backdrop.jpg"
    assert stored.runtime == 139
    assert stored.release_date == date(1999, 10, 15)
    assert _genre_names(stored) == {"Drama"}


def test_fresh_metadata_replaces_stale_values(db_session: Session) -> None:
    repository = MovieRepository(db_session)
    repository.upsert(FULL_DETAILS)
    refreshed = FULL_DETAILS.model_copy(
        update={
            "title": "Fight Club",
            "overview": "Updated overview.",
            "vote_average": 8.9,
            "popularity": 90.0,
            "runtime": 140,
            "genres": [
                GenreDTO(tmdb_genre_id=18, name="Drama"),
                GenreDTO(tmdb_genre_id=53, name="Thriller"),
            ],
        }
    )

    repository.upsert(refreshed)

    stored = repository.get_by_tmdb_id(550)
    assert stored is not None
    assert stored.overview == "Updated overview."
    assert stored.vote_average == 8.9
    assert stored.popularity == 90.0
    assert stored.runtime == 140
    assert _genre_names(stored) == {"Drama", "Thriller"}


def test_genre_ids_link_known_genres_without_removing_existing(db_session: Session) -> None:
    repository = MovieRepository(db_session)
    repository.upsert_genres(
        [
            GenreDTO(tmdb_genre_id=18, name="Drama"),
            GenreDTO(tmdb_genre_id=28, name="Action"),
        ]
    )
    repository.upsert(FULL_DETAILS)

    repository.upsert(SEARCH_HIT.model_copy(update={"genre_ids": [18, 28]}))

    stored = repository.get_by_tmdb_id(550)
    assert stored is not None
    assert _genre_names(stored) == {"Drama", "Action"}
    assert db_session.scalar(select(func.count()).select_from(Movie)) == 1


def test_details_genres_replace_previous_links(db_session: Session) -> None:
    repository = MovieRepository(db_session)
    repository.upsert(FULL_DETAILS)
    replacement = FULL_DETAILS.model_copy(
        update={"genres": [GenreDTO(tmdb_genre_id=28, name="Action")]}
    )

    repository.upsert(replacement)

    stored = repository.get_by_tmdb_id(550)
    assert stored is not None
    assert _genre_names(stored) == {"Action"}


def test_skips_movie_without_tmdb_id_and_blank_genre(db_session: Session) -> None:
    repository = MovieRepository(db_session)

    assert repository.upsert(MovieSummaryDTO(tmdb_id=0, title="Missing")) is None
    assert repository.upsert_genre(0, "Nope") is None
    assert repository.upsert_genre(18, "  ") is None
    assert db_session.scalar(select(func.count()).select_from(Movie)) == 0


def test_movie_service_caches_api_results_and_updates_stale_rows(db_session: Session) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/genre/movie/list"):
            return httpx.Response(200, json={"genres": [{"id": 18, "name": "Drama"}]})
        if path.endswith("/search/movie"):
            return httpx.Response(
                200,
                json={
                    "page": 1,
                    "total_pages": 1,
                    "total_results": 1,
                    "results": [
                        {
                            "id": 550,
                            "title": "Fight Club",
                            "overview": "Search overview",
                            "poster_path": "/poster.jpg",
                            "release_date": "1999-10-15",
                            "vote_average": 8.4,
                            "genre_ids": [18],
                        }
                    ],
                },
            )
        if path.endswith("/movie/550"):
            return httpx.Response(
                200,
                json={
                    "id": 550,
                    "title": "Fight Club",
                    "original_title": "Fight Club",
                    "overview": "Detail overview",
                    "poster_path": "/poster.jpg",
                    "backdrop_path": "/backdrop.jpg",
                    "release_date": "1999-10-15",
                    "runtime": 139,
                    "vote_average": 8.8,
                    "vote_count": 26000,
                    "popularity": 70.1,
                    "original_language": "en",
                    "genres": [{"id": 18, "name": "Drama"}],
                },
            )
        raise AssertionError(path)

    settings = Settings(tmdb_access_token="test-token")
    http_client = httpx.Client(base_url=TMDB_BASE_URL, transport=httpx.MockTransport(handler))
    service = MovieService(
        TMDBClient(settings=settings, http_client=http_client),
        session=db_session,
    )

    service.get_genres()
    page = service.search_movies("fight club")
    cached = MovieRepository(db_session).get_by_tmdb_id(550)
    assert page.results[0].title == "Fight Club"
    assert cached is not None
    assert cached.runtime is None
    assert cached.overview == "Search overview"
    assert _genre_names(cached) == {"Drama"}

    details = service.get_movie_details(550)
    refreshed = MovieRepository(db_session).get_by_tmdb_id(550)
    assert details.runtime == 139
    assert refreshed is not None
    assert refreshed.id == cached.id
    assert refreshed.runtime == 139
    assert refreshed.overview == "Detail overview"
    assert refreshed.backdrop_path == "/backdrop.jpg"
    assert refreshed.vote_average == 8.8
    assert _genre_names(refreshed) == {"Drama"}
    assert db_session.scalar(select(func.count()).select_from(Movie)) == 1
