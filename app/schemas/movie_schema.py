from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pydantic import BaseModel, Field


def parse_tmdb_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class GenreDTO(BaseModel):
    tmdb_genre_id: int
    name: str

    @classmethod
    def from_tmdb(cls, payload: dict) -> GenreDTO:
        return cls(tmdb_genre_id=int(payload.get("id") or 0), name=str(payload.get("name") or ""))


class MovieSummaryDTO(BaseModel):
    tmdb_id: int
    title: str
    original_title: str | None = None
    overview: str | None = None
    poster_path: str | None = None
    backdrop_path: str | None = None
    release_date: date | None = None
    vote_average: float | None = None
    vote_count: int | None = None
    popularity: float | None = None
    original_language: str | None = None
    genre_ids: list[int] = Field(default_factory=list)

    @classmethod
    def from_tmdb(cls, payload: dict) -> MovieSummaryDTO:
        return cls(
            tmdb_id=int(payload.get("id") or 0),
            title=str(payload.get("title") or payload.get("name") or "Untitled"),
            original_title=payload.get("original_title"),
            overview=payload.get("overview") or None,
            poster_path=payload.get("poster_path") or None,
            backdrop_path=payload.get("backdrop_path") or None,
            release_date=parse_tmdb_date(payload.get("release_date")),
            vote_average=payload.get("vote_average"),
            vote_count=payload.get("vote_count"),
            popularity=payload.get("popularity"),
            original_language=payload.get("original_language"),
            genre_ids=[int(item) for item in payload.get("genre_ids") or []],
        )


class MovieDetailsDTO(MovieSummaryDTO):
    runtime: int | None = None
    genres: list[GenreDTO] = Field(default_factory=list)

    @classmethod
    def from_tmdb(cls, payload: dict) -> MovieDetailsDTO:
        summary = MovieSummaryDTO.from_tmdb(payload)
        return cls(
            **summary.model_dump(),
            runtime=payload.get("runtime"),
            genres=[GenreDTO.from_tmdb(item) for item in payload.get("genres") or []],
        )


class CastMemberDTO(BaseModel):
    name: str
    character: str | None = None


class CreditsDTO(BaseModel):
    cast: list[CastMemberDTO] = Field(default_factory=list)
    director: str | None = None

    @classmethod
    def from_tmdb(cls, payload: dict) -> CreditsDTO:
        cast = [
            CastMemberDTO(name=str(item.get("name") or ""), character=item.get("character"))
            for item in payload.get("cast") or []
            if item.get("name")
        ]
        director = next(
            (
                str(item.get("name"))
                for item in payload.get("crew") or []
                if item.get("job") == "Director" and item.get("name")
            ),
            None,
        )
        return cls(cast=cast[:12], director=director)


@dataclass
class MovieDetailsBundle:
    details: MovieDetailsDTO
    credits: CreditsDTO = field(default_factory=CreditsDTO)
    similar: list[MovieSummaryDTO] = field(default_factory=list)


class MoviePageDTO(BaseModel):
    page: int = 1
    total_pages: int = 1
    total_results: int = 0
    results: list[MovieSummaryDTO] = Field(default_factory=list)

    @classmethod
    def from_tmdb(cls, payload: dict) -> MoviePageDTO:
        results = [MovieSummaryDTO.from_tmdb(item) for item in payload.get("results") or []]
        return cls(
            page=int(payload.get("page") or 1),
            total_pages=int(payload.get("total_pages") or 1),
            total_results=int(payload.get("total_results") or len(results)),
            results=results,
        )


class DiscoverFilters(BaseModel):
    page: int = 1
    with_genres: str | None = None
    primary_release_year: int | None = None
    vote_average_gte: float | None = None
    with_original_language: str | None = None
    sort_by: str = "popularity.desc"

    def to_params(self) -> dict[str, str | int | float]:
        params: dict[str, str | int | float] = {"page": self.page, "sort_by": self.sort_by}
        if self.with_genres:
            params["with_genres"] = self.with_genres
        if self.primary_release_year is not None:
            params["primary_release_year"] = self.primary_release_year
        if self.vote_average_gte is not None:
            params["vote_average.gte"] = self.vote_average_gte
        if self.with_original_language:
            params["with_original_language"] = self.with_original_language
        return params
