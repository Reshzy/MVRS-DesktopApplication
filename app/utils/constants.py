from typing import Final

LIKE: Final[str] = "like"
DISLIKE: Final[str] = "dislike"
NOT_INTERESTED: Final[str] = "not_interested"

INTERACTION_TYPES: Final[tuple[str, ...]] = (LIKE, DISLIKE, NOT_INTERESTED)

MIN_RATING: Final[int] = 1
MAX_RATING: Final[int] = 5

LANGUAGE_NAMES: Final[dict[str, str]] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "hi": "Hindi",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
}

FAVORITE_GENRE: Final[str] = "favorite_genre"
FAVORITE_MOVIE: Final[str] = "favorite_movie"
PREFERRED_LANGUAGE: Final[str] = "preferred_language"
RELEASE_PERIOD: Final[str] = "release_period"
MINIMUM_RATING: Final[str] = "minimum_rating"
INTEREST: Final[str] = "interest"

PREFERENCE_TYPES: Final[tuple[str, ...]] = (
    FAVORITE_GENRE,
    FAVORITE_MOVIE,
    PREFERRED_LANGUAGE,
    RELEASE_PERIOD,
    MINIMUM_RATING,
    INTEREST,
)

RELEASE_PERIODS: Final[tuple[tuple[str, str], ...]] = (
    ("before-1980", "Classic (before 1980)"),
    ("1980s", "1980s"),
    ("1990s", "1990s"),
    ("2000s", "2000s"),
    ("2010s", "2010s"),
    ("2020s", "2020s"),
)

MINIMUM_RATINGS: Final[tuple[float, ...]] = (5.0, 6.0, 7.0, 8.0, 9.0)

MAX_FAVORITE_MOVIES: Final[int] = 8
MAX_INTERESTS: Final[int] = 8
MAX_INTEREST_LENGTH: Final[int] = 40
PREFERENCE_VALUE_LIMIT: Final[int] = 255

RECOMMENDATION_WEIGHTS: Final[dict[str, float]] = {
    "genre_similarity": 0.35,
    "favorite_movie_similarity": 0.25,
    "tmdb_rating_score": 0.15,
    "popularity_score": 0.10,
    "release_preference_score": 0.05,
    "interaction_score": 0.10,
}

DISLIKE_PENALTY: Final[float] = 0.35
WATCHED_PENALTY: Final[float] = 0.15
HIGH_RATING_THRESHOLD: Final[int] = 4
DEFAULT_RECOMMENDATION_LIMIT: Final[int] = 20
CONTENT_MATCH_THRESHOLD: Final[float] = 0.08
DASHBOARD_ROW_LIMIT: Final[int] = 12
DASHBOARD_RECENT_DAYS: Final[int] = 365
HIGHLY_RATED_THRESHOLD: Final[float] = 7.0
