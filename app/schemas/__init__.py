from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.schemas.user_schema import (
    GenrePreference,
    MoviePreference,
    ProfileUpdateRequest,
    UserPreferences,
)
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
    "GenrePreference",
    "LoginRequest",
    "MovieDetailsBundle",
    "MovieDetailsDTO",
    "MoviePageDTO",
    "MoviePreference",
    "MovieSummaryDTO",
    "HistoryEntryDTO",
    "MovieUserState",
    "ProfileUpdateRequest",
    "RegisterRequest",
    "UserPreferences",
    "WatchlistEntryDTO",
]
