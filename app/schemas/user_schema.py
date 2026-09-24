from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.utils.constants import (
    FAVORITE_GENRE,
    FAVORITE_MOVIE,
    INTEREST,
    LANGUAGE_NAMES,
    MAX_FAVORITE_MOVIES,
    MAX_INTEREST_LENGTH,
    MAX_INTERESTS,
    MINIMUM_RATING,
    MINIMUM_RATINGS,
    PREFERENCE_VALUE_LIMIT,
    PREFERRED_LANGUAGE,
    RELEASE_PERIOD,
    RELEASE_PERIODS,
)

RELEASE_PERIOD_LABELS: dict[str, str] = dict(RELEASE_PERIODS)


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Name is required")
        return name


class GenrePreference(BaseModel):
    tmdb_genre_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        name = " ".join(value.replace("|", " ").split())
        if not name:
            raise ValueError("Genre name is required")
        return name


class MoviePreference(BaseModel):
    tmdb_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=180)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        title = " ".join(value.replace("|", " ").split())
        if not title:
            raise ValueError("Movie title is required")
        return title


class UserPreferences(BaseModel):
    favorite_genres: list[GenrePreference] = Field(default_factory=list)
    favorite_movies: list[MoviePreference] = Field(default_factory=list, max_length=MAX_FAVORITE_MOVIES)
    preferred_language: str | None = None
    release_period: str | None = None
    minimum_rating: float | None = None
    interests: list[str] = Field(default_factory=list, max_length=MAX_INTERESTS)

    @field_validator("favorite_genres")
    @classmethod
    def unique_genres(cls, value: list[GenrePreference]) -> list[GenrePreference]:
        seen: set[int] = set()
        unique: list[GenrePreference] = []
        for genre in value:
            if genre.tmdb_genre_id in seen:
                continue
            seen.add(genre.tmdb_genre_id)
            unique.append(genre)
        return unique

    @field_validator("favorite_movies")
    @classmethod
    def unique_movies(cls, value: list[MoviePreference]) -> list[MoviePreference]:
        seen: set[int] = set()
        unique: list[MoviePreference] = []
        for movie in value:
            if movie.tmdb_id in seen:
                continue
            seen.add(movie.tmdb_id)
            unique.append(movie)
        return unique

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, value: str | None) -> str | None:
        if value is None or not str(value).strip():
            return None
        code = str(value).strip().lower()
        if code not in LANGUAGE_NAMES:
            raise ValueError("Choose a supported language.")
        return code

    @field_validator("release_period")
    @classmethod
    def validate_period(cls, value: str | None) -> str | None:
        if value is None or not str(value).strip():
            return None
        period = str(value).strip()
        if period not in RELEASE_PERIOD_LABELS:
            raise ValueError("Choose a release period.")
        return period

    @field_validator("minimum_rating")
    @classmethod
    def validate_minimum_rating(cls, value: float | None) -> float | None:
        if value is None:
            return None
        rating = float(value)
        if rating not in MINIMUM_RATINGS:
            raise ValueError("Choose a minimum rating.")
        return rating

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            text = " ".join(str(item).split())
            if not text:
                continue
            if len(text) > MAX_INTEREST_LENGTH:
                raise ValueError(f"Interests must be {MAX_INTEREST_LENGTH} characters or fewer.")
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
        if len(cleaned) > MAX_INTERESTS:
            raise ValueError(f"Save up to {MAX_INTERESTS} interests.")
        return cleaned

    def to_rows(self) -> list[tuple[str, str, float]]:
        rows: list[tuple[str, str, float]] = []
        for genre in self.favorite_genres:
            rows.append((FAVORITE_GENRE, encode_id_label(genre.tmdb_genre_id, genre.name), 1.0))
        for movie in self.favorite_movies:
            rows.append((FAVORITE_MOVIE, encode_id_label(movie.tmdb_id, movie.title), 1.0))
        if self.preferred_language:
            rows.append((PREFERRED_LANGUAGE, self.preferred_language, 1.0))
        if self.release_period:
            rows.append((RELEASE_PERIOD, self.release_period, 1.0))
        if self.minimum_rating is not None:
            rows.append((MINIMUM_RATING, f"{self.minimum_rating:.0f}", 1.0))
        for interest in self.interests:
            rows.append((INTEREST, interest, 1.0))
        return rows

    def summary(self) -> str:
        parts: list[str] = []
        if self.favorite_genres:
            parts.append(", ".join(genre.name for genre in self.favorite_genres))
        if self.favorite_movies:
            parts.append(", ".join(movie.title for movie in self.favorite_movies))
        if self.preferred_language:
            parts.append(LANGUAGE_NAMES.get(self.preferred_language, self.preferred_language))
        if self.release_period:
            parts.append(RELEASE_PERIOD_LABELS.get(self.release_period, self.release_period))
        if self.minimum_rating is not None:
            parts.append(f"{self.minimum_rating:.0f}+")
        if self.interests:
            parts.append(", ".join(self.interests))
        if not parts:
            return "No preferences yet. You can add them any time."
        return " · ".join(parts)

    @classmethod
    def from_rows(cls, rows: Sequence[Any]) -> UserPreferences:
        genres: list[dict[str, Any]] = []
        movies: list[dict[str, Any]] = []
        language: str | None = None
        period: str | None = None
        rating: float | None = None
        interests: list[str] = []
        seen_genres: set[int] = set()
        seen_movies: set[int] = set()
        seen_interests: set[str] = set()

        for row in rows:
            pref_type = getattr(row, "preference_type", None)
            raw = str(getattr(row, "preference_value", "") or "")
            if pref_type == FAVORITE_GENRE:
                parsed = decode_id_label(raw)
                if parsed is None or parsed[0] in seen_genres:
                    continue
                seen_genres.add(parsed[0])
                genres.append({"tmdb_genre_id": parsed[0], "name": parsed[1][:80]})
            elif pref_type == FAVORITE_MOVIE:
                parsed = decode_id_label(raw)
                if parsed is None or parsed[0] in seen_movies or len(movies) >= MAX_FAVORITE_MOVIES:
                    continue
                seen_movies.add(parsed[0])
                movies.append({"tmdb_id": parsed[0], "title": parsed[1][:180]})
            elif pref_type == PREFERRED_LANGUAGE and language is None:
                code = raw.strip().lower()
                if code in LANGUAGE_NAMES:
                    language = code
            elif pref_type == RELEASE_PERIOD and period is None:
                if raw.strip() in RELEASE_PERIOD_LABELS:
                    period = raw.strip()
            elif pref_type == MINIMUM_RATING and rating is None:
                try:
                    number = float(raw)
                except ValueError:
                    continue
                if number in MINIMUM_RATINGS:
                    rating = number
            elif pref_type == INTEREST and len(interests) < MAX_INTERESTS:
                text = " ".join(raw.split())[:MAX_INTEREST_LENGTH]
                key = text.casefold()
                if text and key not in seen_interests:
                    seen_interests.add(key)
                    interests.append(text)

        return cls(
            favorite_genres=genres,
            favorite_movies=movies,
            preferred_language=language,
            release_period=period,
            minimum_rating=rating,
            interests=interests,
        )


def encode_id_label(item_id: int, label: str) -> str:
    clean = " ".join(label.replace("|", " ").split())
    return f"{item_id}|{clean}"[:PREFERENCE_VALUE_LIMIT]


def decode_id_label(value: str) -> tuple[int, str] | None:
    item_id, separator, label = value.partition("|")
    if not separator or not item_id.isdigit():
        return None
    name = " ".join(label.split())
    number = int(item_id)
    if number <= 0 or not name:
        return None
    return number, name
