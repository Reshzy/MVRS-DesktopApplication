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
