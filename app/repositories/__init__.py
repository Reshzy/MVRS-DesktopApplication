from app.repositories.history_repository import HistoryRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.movie_repository import MovieRepository
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.rating_repository import RatingRepository
from app.repositories.user_repository import UserRepository
from app.repositories.watchlist_repository import WatchlistRepository

__all__ = [
    "HistoryRepository",
    "InteractionRepository",
    "MovieRepository",
    "PreferenceRepository",
    "RatingRepository",
    "UserRepository",
    "WatchlistRepository",
]
