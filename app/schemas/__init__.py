from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.schemas.user_schema import (
    GenrePreference,
    MoviePreference,
    ProfileUpdateRequest,
    UserPreferences,
)
from app.schemas.insights_schema import ActivityItemDTO, InsightsDTO, RatedMovieDTO
from app.schemas.library_schema import HistoryEntryDTO, MovieUserState, WatchlistEntryDTO
from app.schemas.recommendation_schema import RecommendedMovie
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
    "ActivityItemDTO",
    "CreditsDTO",
    "DiscoverFilters",
    "GenreDTO",
    "GenrePreference",
    "InsightsDTO",
    "LoginRequest",
    "MovieDetailsBundle",
    "MovieDetailsDTO",
    "MoviePageDTO",
    "MoviePreference",
    "MovieSummaryDTO",
    "HistoryEntryDTO",
    "MovieUserState",
    "ProfileUpdateRequest",
    "RatedMovieDTO",
    "RecommendedMovie",
    "RegisterRequest",
    "UserPreferences",
    "WatchlistEntryDTO",
]
