from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.schemas.library_schema import MovieUserState
from app.schemas.movie_schema import (
    CreditsDTO,
    DiscoverFilters,
    GenreDTO,
    MovieDetailsBundle,
    MovieDetailsDTO,
    MoviePageDTO,
    MovieSummaryDTO,
)

__all__ = [
    "CreditsDTO",
    "DiscoverFilters",
    "GenreDTO",
    "LoginRequest",
    "MovieDetailsBundle",
    "MovieDetailsDTO",
    "MoviePageDTO",
    "MovieSummaryDTO",
    "MovieUserState",
    "RegisterRequest",
]
