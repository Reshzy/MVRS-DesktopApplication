from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.schemas.user_schema import ProfileUpdateRequest
from app.schemas.library_schema import HistoryEntryDTO, MovieUserState, WatchlistEntryDTO
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
    "HistoryEntryDTO",
    "MovieUserState",
    "ProfileUpdateRequest",
    "RegisterRequest",
    "WatchlistEntryDTO",
]
