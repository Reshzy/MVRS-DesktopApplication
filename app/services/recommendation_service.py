from __future__ import annotations

import logging
import re
from collections.abc import Callable, Sequence
from datetime import date

from sqlalchemy.orm import Session

from app.database.locks import session_lock
from app.recommendation.engine import Recommendation, RecommendationEngine, RecommendationError
from app.recommendation.feature_builder import CandidateMovie, UserRecommendationSignals
from app.recommendation.scoring import release_period_bounds
from app.repositories.history_repository import HistoryRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.movie_repository import MovieRepository
from app.repositories.rating_repository import RatingRepository
from app.schemas.movie_schema import DiscoverFilters, GenreDTO, MovieSummaryDTO
from app.schemas.recommendation_schema import RecommendedMovie
from app.schemas.user_schema import UserPreferences
from app.services.movie_service import MovieService
from app.services.user_service import UserService
from app.utils.constants import (
    DEFAULT_RECOMMENDATION_LIMIT,
    DISLIKE,
    HIGH_RATING_THRESHOLD,
    LIKE,
    NOT_INTERESTED,
)
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

_NUMERIC_REASON = re.compile(r"^[-+]?\d*\.?\d+$")


class RecommendationServiceError(Exception):
    pass


class RecommendationService:
    def __init__(
        self,
        session: Session,
        movie_service: MovieService,
        *,
        engine: RecommendationEngine | None = None,
        user_service: UserService | None = None,
    ) -> None:
        self._session = session
        self._movie_service = movie_service
        self._engine = engine or RecommendationEngine()
        self._users = user_service or UserService(session)
        self._ratings = RatingRepository(session)
        self._interactions = InteractionRepository(session)
        self._history = HistoryRepository(session)
        self._movies = MovieRepository(session)

    def profile_key(self, user_id: int) -> tuple:
        signals = self.build_signals(user_id, enrich_favorites=False)
        return (
            signals.favorite_genres,
            signals.favorite_genre_ids,
            tuple(movie.tmdb_id for movie in signals.favorite_movies),
            tuple(sorted(signals.ratings.items())),
            tuple(sorted(signals.likes)),
            tuple(sorted(signals.dislikes)),
            tuple(sorted(signals.watch_history)),
            tuple(sorted(signals.not_interested)),
            signals.preferred_language,
            signals.release_period,
            signals.minimum_rating,
            signals.interests,
        )

    def build_signals(
        self,
        user_id: int,
        *,
        enrich_favorites: bool = False,
        genre_lookup: dict[int, str] | None = None,
    ) -> UserRecommendationSignals:
        preferences = self._users.get_preferences(user_id)
        with session_lock():
            ratings: dict[int, int] = {}
            for item in self._ratings.list_for_user(user_id):
                movie = item.movie
                if movie is None:
                    continue
                ratings[int(movie.tmdb_id)] = int(item.rating)

            likes: set[int] = set()
            dislikes: set[int] = set()
            not_interested: set[int] = set()
            for item in self._interactions.list_for_user(user_id):
                movie = item.movie
                if movie is None:
                    continue
                tmdb_id = int(movie.tmdb_id)
                if item.interaction_type == LIKE:
                    likes.add(tmdb_id)
                elif item.interaction_type == DISLIKE:
                    dislikes.add(tmdb_id)
                elif item.interaction_type == NOT_INTERESTED:
                    not_interested.add(tmdb_id)

            history = {
                int(item.movie.tmdb_id)
                for item in self._history.list_for_user(user_id)
                if item.movie is not None
            }
        favorite_details: Sequence[CandidateMovie] = ()
        if enrich_favorites:
            favorite_details = self._favorite_details(preferences, genre_lookup=genre_lookup)
        return UserRecommendationSignals.from_preferences(
            preferences,
            ratings=ratings,
            likes=likes,
            dislikes=dislikes,
            watch_history=history,
            not_interested=not_interested,
            favorite_movie_details=favorite_details,
        )

    def recommend_for_user(self, user_id: int, *, limit: int = DEFAULT_RECOMMENDATION_LIMIT) -> list[RecommendedMovie]:
        if user_id <= 0:
            raise RecommendationServiceError("Sign in to get personalized recommendations.")
        try:
            genre_lookup = self._genre_lookup()
            signals = self.build_signals(user_id, enrich_favorites=True, genre_lookup=genre_lookup)
            summaries = self._collect_candidates(signals)
            candidates = [
                CandidateMovie.from_dto(movie, genre_lookup=genre_lookup) for movie in summaries
            ]
            by_id = {movie.tmdb_id: movie for movie in summaries}
            ranked = self._engine.recommend(signals, candidates, limit=limit)
            return [self._to_recommended(item, by_id) for item in ranked]
        except RecommendationServiceError:
            raise
        except RecommendationError as exc:
            raise RecommendationServiceError(str(exc)) from exc
        except Exception as exc:
            logger.exception("Failed to generate recommendations for user_id=%s", user_id)
            raise RecommendationServiceError("Could not generate recommendations.") from exc

    def _favorite_details(
        self,
        preferences: UserPreferences,
        *,
        genre_lookup: dict[int, str] | None = None,
    ) -> tuple[CandidateMovie, ...]:
        if not preferences.favorite_movies:
            return ()
        lookup = genre_lookup if genre_lookup is not None else self._genre_lookup()
        details: list[CandidateMovie] = []
        for movie in preferences.favorite_movies:
            summary = self._lookup_movie(movie.tmdb_id)
            if summary is not None:
                details.append(CandidateMovie.from_dto(summary, genre_lookup=lookup))
            else:
                details.append(CandidateMovie(tmdb_id=movie.tmdb_id, title=movie.title))
        return tuple(details)

    def _lookup_movie(self, tmdb_id: int) -> MovieSummaryDTO | None:
        with session_lock():
            stored = self._movies.get_by_tmdb_id(tmdb_id)
            if stored is not None:
                return MovieSummaryDTO.from_model(stored)
        try:
            return self._movie_service.get_movie_details(tmdb_id)
        except Exception:
            logger.exception("Failed to enrich favorite movie tmdb_id=%s", tmdb_id)
            return None

    def _genre_lookup(self) -> dict[int, str]:
        try:
            genres = self._movie_service.get_genres()
        except Exception:
            logger.exception("Failed to load genres for recommendations")
            return {}
        return {int(genre.tmdb_genre_id): genre.name for genre in genres if isinstance(genre, GenreDTO)}

    def _collect_candidates(self, signals: UserRecommendationSignals) -> list[MovieSummaryDTO]:
        merged: dict[int, MovieSummaryDTO] = {}
        attempts = 0
        failures = 0

        def add(label: str, fetch: Callable[[], Sequence[MovieSummaryDTO] | object]) -> None:
            nonlocal attempts, failures
            attempts += 1
            try:
                payload = fetch()
                movies = payload.results if hasattr(payload, "results") else payload
                for movie in movies or []:
                    if not isinstance(movie, MovieSummaryDTO) or movie.tmdb_id <= 0:
                        continue
                    merged.setdefault(movie.tmdb_id, movie)
            except Exception:
                failures += 1
                logger.exception("Failed to load %s recommendation candidates", label)

        add("popular", lambda: self._movie_service.get_popular_movies(page=1))
        add("trending", lambda: self._movie_service.get_trending_movies())
        filters = self._preference_filters(signals)
        if filters is not None:
            add("discover", lambda: self._movie_service.discover_movies(filters))
        for movie in signals.favorite_movies[:3]:
            add(
                f"similar:{movie.tmdb_id}",
                lambda tmdb_id=movie.tmdb_id: self._movie_service.get_similar_movies(tmdb_id),
            )
        seeds = [tmdb_id for tmdb_id, rating in signals.ratings.items() if rating >= HIGH_RATING_THRESHOLD]
        seeds.extend(signals.likes)
        for tmdb_id in list(dict.fromkeys(seeds))[:3]:
            add(
                f"similar:{tmdb_id}",
                lambda movie_id=tmdb_id: self._movie_service.get_similar_movies(movie_id),
            )

        if not merged and attempts and failures == attempts:
            raise RecommendationServiceError(
                "Could not load recommendations. Check your connection and try again."
            )
        return list(merged.values())

    def _preference_filters(self, signals: UserRecommendationSignals) -> DiscoverFilters | None:
        kwargs: dict[str, object] = {}
        if signals.favorite_genre_ids:
            kwargs["with_genres"] = ",".join(str(genre_id) for genre_id in signals.favorite_genre_ids)
        if signals.preferred_language:
            kwargs["with_original_language"] = signals.preferred_language
        if signals.minimum_rating is not None:
            kwargs["vote_average_gte"] = signals.minimum_rating
        bounds = release_period_bounds(signals.release_period)
        if bounds is not None:
            start, end = bounds
            if start:
                kwargs["primary_release_date_gte"] = start
            if end:
                kwargs["primary_release_date_lte"] = end
        if not kwargs:
            return None
        if signals.favorite_genre_ids or signals.minimum_rating is not None:
            kwargs["sort_by"] = "vote_average.desc"
        return DiscoverFilters(**kwargs)

    def _to_recommended(
        self,
        item: Recommendation,
        by_id: dict[int, MovieSummaryDTO],
    ) -> RecommendedMovie:
        reasons = public_reasons(item.reasons)
        return RecommendedMovie(
            movie=by_id.get(item.movie.tmdb_id) or _summary_from_candidate(item.movie),
            reason=reasons[0],
            reasons=reasons,
        )


def public_reasons(reasons: Sequence[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for reason in reasons:
        text = " ".join(str(reason).split())
        if not text or not _is_public_reason(text):
            continue
        cleaned.append(text)
    if not cleaned:
        return ("Suggested for you",)
    return tuple(cleaned)


def _is_public_reason(text: str) -> bool:
    lowered = text.lower()
    if "cosine" in lowered or "similarity score" in lowered:
        return False
    return _NUMERIC_REASON.fullmatch(text) is None


def _summary_from_candidate(movie: CandidateMovie) -> MovieSummaryDTO:
    release = date(movie.release_year, 1, 1) if movie.release_year else None
    return MovieSummaryDTO(
        tmdb_id=movie.tmdb_id,
        title=movie.title,
        overview=movie.overview or None,
        release_date=release,
        vote_average=movie.vote_average,
        popularity=movie.popularity,
        original_language=movie.original_language,
        genre_ids=list(movie.genre_ids),
    )
