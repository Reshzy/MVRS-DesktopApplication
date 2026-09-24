from app.models.genre import Genre
from app.models.interaction import Interaction
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.models.rating import Rating
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.watch_history import WatchHistory
from app.models.watchlist import Watchlist


def load_models() -> None:
    """Import models so SQLAlchemy metadata is fully populated."""


__all__ = [
    "Genre",
    "Interaction",
    "Movie",
    "MovieGenre",
    "Rating",
    "User",
    "UserPreference",
    "WatchHistory",
    "Watchlist",
    "load_models",
]
