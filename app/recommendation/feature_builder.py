from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.schemas.movie_schema import MovieSummaryDTO
from app.schemas.user_schema import UserPreferences
from app.utils.constants import HIGH_RATING_THRESHOLD


@dataclass(frozen=True)
class CandidateMovie:
    tmdb_id: int
    title: str
    overview: str = ""
    genres: tuple[str, ...] = ()
    genre_ids: tuple[int, ...] = ()
    release_year: int | None = None
    vote_average: float | None = None
    popularity: float | None = None
    original_language: str | None = None

    @classmethod
    def from_dto(
        cls,
        movie: MovieSummaryDTO,
        *,
        genre_lookup: Mapping[int, str] | None = None,
    ) -> CandidateMovie:
        names: list[str] = []
        ids = [int(genre_id) for genre_id in movie.genre_ids]
        extra_genres = getattr(movie, "genres", None) or []
        if extra_genres:
            names = [str(genre.name) for genre in extra_genres if getattr(genre, "name", None)]
            extra_ids = [
                int(genre.tmdb_genre_id)
                for genre in extra_genres
                if getattr(genre, "tmdb_genre_id", None)
            ]
            if extra_ids:
                ids = extra_ids
        elif genre_lookup:
            names = [genre_lookup[genre_id] for genre_id in ids if genre_id in genre_lookup]

        release = movie.release_date
        return cls(
            tmdb_id=int(movie.tmdb_id),
            title=str(movie.title),
            overview=str(movie.overview or ""),
            genres=tuple(names),
            genre_ids=tuple(ids),
            release_year=release.year if release is not None else None,
            vote_average=movie.vote_average,
            popularity=movie.popularity,
            original_language=movie.original_language,
        )


@dataclass(frozen=True)
class UserRecommendationSignals:
    favorite_genres: tuple[str, ...] = ()
    favorite_genre_ids: tuple[int, ...] = ()
    favorite_movies: tuple[CandidateMovie, ...] = ()
    ratings: Mapping[int, int] = field(default_factory=dict)
    likes: frozenset[int] = field(default_factory=frozenset)
    dislikes: frozenset[int] = field(default_factory=frozenset)
    watch_history: frozenset[int] = field(default_factory=frozenset)
    not_interested: frozenset[int] = field(default_factory=frozenset)
    preferred_language: str | None = None
    release_period: str | None = None
    minimum_rating: float | None = None
    interests: tuple[str, ...] = ()

    @classmethod
    def from_preferences(
        cls,
        preferences: UserPreferences,
        *,
        ratings: Mapping[int, int] | None = None,
        likes: Iterable[int] = (),
        dislikes: Iterable[int] = (),
        watch_history: Iterable[int] = (),
        not_interested: Iterable[int] = (),
        favorite_movie_details: Sequence[CandidateMovie] = (),
    ) -> UserRecommendationSignals:
        details = {movie.tmdb_id: movie for movie in favorite_movie_details}
        favorites = tuple(
            details.get(movie.tmdb_id, CandidateMovie(tmdb_id=movie.tmdb_id, title=movie.title))
            for movie in preferences.favorite_movies
        )
        return cls(
            favorite_genres=tuple(genre.name for genre in preferences.favorite_genres),
            favorite_genre_ids=tuple(genre.tmdb_genre_id for genre in preferences.favorite_genres),
            favorite_movies=favorites,
            ratings=dict(ratings or {}),
            likes=frozenset(likes),
            dislikes=frozenset(dislikes),
            watch_history=frozenset(watch_history),
            not_interested=frozenset(not_interested),
            preferred_language=preferences.preferred_language,
            release_period=preferences.release_period,
            minimum_rating=preferences.minimum_rating,
            interests=tuple(preferences.interests),
        )


FEATURE_COLUMNS: tuple[str, ...] = (
    "tmdb_id",
    "title",
    "feature_text",
    "genre_text",
    "release_year",
    "vote_average",
    "popularity",
    "original_language",
)


def _clean_text(*parts: Any) -> str:
    chunks: list[str] = []
    for part in parts:
        if part is None:
            continue
        text = " ".join(str(part).split())
        if text:
            chunks.append(text)
    return " ".join(chunks)


def movie_feature_text(movie: CandidateMovie) -> str:
    genre_terms = " ".join(movie.genres)
    language = f"lang_{movie.original_language}" if movie.original_language else ""
    return _clean_text(
        genre_terms,
        genre_terms,
        movie.title,
        movie.overview,
        language,
    )


def genre_feature_text(movie: CandidateMovie) -> str:
    return _clean_text(*movie.genres)


def build_catalog(*groups: Sequence[CandidateMovie]) -> dict[int, CandidateMovie]:
    catalog: dict[int, CandidateMovie] = {}
    for group in groups:
        for movie in group:
            existing = catalog.get(movie.tmdb_id)
            if existing is None or _is_richer(movie, existing):
                catalog[movie.tmdb_id] = movie
    return catalog


def _is_richer(new: CandidateMovie, old: CandidateMovie) -> bool:
    return (len(new.overview), len(new.genres)) > (len(old.overview), len(old.genres))


def _positive_signal_movies(
    signals: UserRecommendationSignals,
    catalog: Mapping[int, CandidateMovie],
) -> list[CandidateMovie]:
    movies: list[CandidateMovie] = []
    seen: set[int] = set()

    def add(movie: CandidateMovie | None) -> None:
        if movie is None or movie.tmdb_id in seen:
            return
        if movie.tmdb_id in signals.dislikes or movie.tmdb_id in signals.not_interested:
            return
        seen.add(movie.tmdb_id)
        movies.append(movie)

    for movie in signals.favorite_movies:
        add(catalog.get(movie.tmdb_id, movie))

    for tmdb_id in signals.likes:
        add(catalog.get(tmdb_id))

    for tmdb_id, rating in signals.ratings.items():
        if rating >= HIGH_RATING_THRESHOLD:
            add(catalog.get(tmdb_id))

    return movies


def user_genre_text(
    signals: UserRecommendationSignals,
    catalog: Mapping[int, CandidateMovie],
) -> str:
    names = list(signals.favorite_genres)
    for movie in _positive_signal_movies(signals, catalog):
        names.extend(movie.genres)
    return _clean_text(*names)


def user_profile_text(
    signals: UserRecommendationSignals,
    catalog: Mapping[int, CandidateMovie],
) -> str:
    parts: list[str] = []
    parts.extend(signals.favorite_genres)
    parts.extend(signals.favorite_genres)
    parts.extend(signals.interests)
    if signals.preferred_language:
        parts.append(f"lang_{signals.preferred_language}")

    for movie in signals.favorite_movies:
        text = movie_feature_text(catalog.get(movie.tmdb_id, movie))
        parts.append(text)
        parts.append(text)

    for movie in _positive_signal_movies(signals, catalog):
        if movie.tmdb_id in {item.tmdb_id for item in signals.favorite_movies}:
            continue
        parts.append(movie_feature_text(movie))

    return _clean_text(*parts)


def build_feature_frame(movies: Sequence[CandidateMovie]) -> pd.DataFrame:
    if not movies:
        return pd.DataFrame(columns=list(FEATURE_COLUMNS))
    records = [
        {
            "tmdb_id": movie.tmdb_id,
            "title": movie.title,
            "feature_text": movie_feature_text(movie),
            "genre_text": genre_feature_text(movie),
            "release_year": movie.release_year,
            "vote_average": movie.vote_average,
            "popularity": movie.popularity,
            "original_language": movie.original_language,
        }
        for movie in movies
    ]
    return pd.DataFrame.from_records(records)
