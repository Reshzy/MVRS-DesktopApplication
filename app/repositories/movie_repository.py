from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.genre import Genre
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.schemas.movie_schema import GenreDTO, MovieSummaryDTO
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

_TEXT_LIMITS = {
    "title": 255,
    "original_title": 255,
    "poster_path": 255,
    "backdrop_path": 255,
    "original_language": 16,
}
_OPTIONAL_FIELDS = (
    "original_title",
    "overview",
    "poster_path",
    "backdrop_path",
    "release_date",
    "runtime",
    "vote_average",
    "vote_count",
    "popularity",
    "original_language",
)


class MovieRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, movie_id: int) -> Movie | None:
        return self._session.scalar(self._movie_query().where(Movie.id == movie_id))

    def get_by_tmdb_id(self, tmdb_id: int) -> Movie | None:
        return self._session.scalar(self._movie_query().where(Movie.tmdb_id == tmdb_id))

    def get_genre_by_tmdb_id(self, tmdb_genre_id: int) -> Genre | None:
        return self._session.scalar(select(Genre).where(Genre.tmdb_genre_id == tmdb_genre_id))

    def upsert(self, dto: MovieSummaryDTO) -> Movie | None:
        if dto.tmdb_id <= 0:
            logger.warning("Skipping movie cache because tmdb_id is missing")
            return None

        movie = self.get_by_tmdb_id(dto.tmdb_id)
        if movie is None:
            movie = Movie(tmdb_id=dto.tmdb_id, title=self._title_or_placeholder(dto.title))
            self._session.add(movie)
            self._session.flush()

        self._apply_fields(movie, dto)
        self._sync_genres(movie, dto)
        movie.updated_at = datetime.now(timezone.utc)
        self._session.flush()
        return movie

    def upsert_many(self, movies: list[MovieSummaryDTO]) -> list[Movie]:
        stored: list[Movie] = []
        for dto in movies:
            movie = self.upsert(dto)
            if movie is not None:
                stored.append(movie)
        return stored

    def upsert_genre(self, tmdb_genre_id: int, name: str) -> Genre | None:
        cleaned = name.strip()
        if tmdb_genre_id <= 0 or not cleaned:
            return None

        genre = self.get_genre_by_tmdb_id(tmdb_genre_id)
        if genre is None:
            genre = Genre(tmdb_genre_id=tmdb_genre_id, name=cleaned[:100])
            self._session.add(genre)
            self._session.flush()
            return genre

        if genre.name != cleaned[:100]:
            genre.name = cleaned[:100]
        return genre

    def upsert_genres(self, genres: list[GenreDTO]) -> list[Genre]:
        stored: list[Genre] = []
        seen: set[int] = set()
        for dto in genres:
            if dto.tmdb_genre_id in seen:
                continue
            seen.add(dto.tmdb_genre_id)
            genre = self.upsert_genre(dto.tmdb_genre_id, dto.name)
            if genre is not None:
                stored.append(genre)
        return stored

    def _apply_fields(self, movie: Movie, dto: MovieSummaryDTO) -> None:
        title = self._clip(dto.title, _TEXT_LIMITS["title"])
        if title:
            movie.title = title

        values = dto.model_dump()
        for field in _OPTIONAL_FIELDS:
            if field not in values:
                continue
            cleaned = self._clean_field(field, values[field])
            if cleaned is None:
                continue
            setattr(movie, field, cleaned)

    def _sync_genres(self, movie: Movie, dto: MovieSummaryDTO) -> None:
        named = self._named_genres(dto)
        if named:
            genres = [genre for genre in (self.upsert_genre(item.tmdb_genre_id, item.name) for item in named) if genre]
            self._replace_genre_links(movie, genres)
            return

        if not dto.genre_ids:
            return

        resolved: list[Genre] = []
        seen: set[int] = set()
        for genre_id in dto.genre_ids:
            if genre_id in seen or genre_id <= 0:
                continue
            seen.add(genre_id)
            genre = self.get_genre_by_tmdb_id(genre_id)
            if genre is not None:
                resolved.append(genre)
        if resolved:
            self._merge_genre_links(movie, resolved)

    def _replace_genre_links(self, movie: Movie, genres: list[Genre]) -> None:
        desired_ids = {genre.id for genre in genres}
        for link in list(movie.genre_links):
            if link.genre_id not in desired_ids:
                movie.genre_links.remove(link)
        self._merge_genre_links(movie, genres)

    def _merge_genre_links(self, movie: Movie, genres: list[Genre]) -> None:
        linked_ids = {link.genre_id for link in movie.genre_links}
        for genre in genres:
            if genre.id in linked_ids:
                continue
            movie.genre_links.append(MovieGenre(genre=genre))
            linked_ids.add(genre.id)

    def _movie_query(self):
        return select(Movie).options(selectinload(Movie.genre_links).selectinload(MovieGenre.genre))

    @staticmethod
    def _named_genres(dto: MovieSummaryDTO) -> list[GenreDTO]:
        raw = getattr(dto, "genres", None) or []
        named: list[GenreDTO] = []
        seen: set[int] = set()
        for genre in raw:
            if genre.tmdb_genre_id <= 0 or genre.tmdb_genre_id in seen or not genre.name.strip():
                continue
            seen.add(genre.tmdb_genre_id)
            named.append(genre)
        return named

    @staticmethod
    def _clean_field(field: str, value: object) -> object | None:
        if value is None:
            return None
        if field in _TEXT_LIMITS and field != "title":
            if not isinstance(value, str):
                return None
            return MovieRepository._clip(value, _TEXT_LIMITS[field])
        if field == "overview":
            if not isinstance(value, str) or not value.strip():
                return None
            return value.strip()
        if field == "runtime":
            runtime = int(value)
            return runtime if runtime > 0 else None
        if field == "vote_count":
            count = int(value)
            return count if count >= 0 else None
        if field in {"vote_average", "popularity"}:
            return float(value)
        return value

    @staticmethod
    def _clip(value: str | None, limit: int) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        return text[:limit]

    @staticmethod
    def _title_or_placeholder(title: str | None) -> str:
        return MovieRepository._clip(title, _TEXT_LIMITS["title"]) or "Untitled"
