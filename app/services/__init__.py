from app.services.auth_service import (
    AuthError,
    AuthService,
    DuplicateEmailError,
    InvalidCredentialsError,
)
from app.services.history_service import HistoryService
from app.services.interaction_service import InteractionService
from app.services.library_base import LibraryError
from app.services.movie_service import MovieService
from app.services.rating_service import RatingService
from app.services.recommendation_service import RecommendationService, RecommendationServiceError
from app.services.user_service import UserService, UserServiceError
from app.services.watchlist_service import WatchlistService

__all__ = [
    "AuthError",
    "AuthService",
    "DuplicateEmailError",
    "HistoryService",
    "InteractionService",
    "InvalidCredentialsError",
    "LibraryError",
    "MovieService",
    "RatingService",
    "RecommendationService",
    "RecommendationServiceError",
    "UserService",
    "UserServiceError",
    "WatchlistService",
]
