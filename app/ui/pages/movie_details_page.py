from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.api.image_client import DEFAULT_BACKDROP_SIZE, DEFAULT_POSTER_SIZE
from app.schemas.library_schema import MovieUserState
from app.schemas.movie_schema import CreditsDTO, MovieDetailsBundle, MovieDetailsDTO, MovieSummaryDTO
from app.services.history_service import HistoryService
from app.services.interaction_service import InteractionService
from app.services.library_base import LibraryError
from app.services.movie_service import MovieService
from app.services.rating_service import RatingService
from app.services.watchlist_service import WatchlistService
from app.state.app_state import AppState
from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, MD, SM, XL
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.flow_layout import FlowLayout
from app.ui.widgets.loading_widget import LoadingWidget
from app.ui.widgets.movie_card import MovieCard, format_rating, format_release_year
from app.ui.widgets.poster_placeholder import poster_placeholder
from app.ui.widgets.rating_widget import RatingWidget
from app.ui.workers.image_worker import ImageLoader
from app.ui.workers.signals import QUEUED
from app.ui.workers.task_runner import TaskRunner
from app.utils.constants import (
    DISLIKE,
    LANGUAGE_NAMES,
    LIKE,
    MAX_RATING,
    NOT_INTERESTED,
    SIGN_IN_STATUS_MESSAGE,
)
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

DETAILS_POSTER_WIDTH = 200
DETAILS_POSTER_HEIGHT = 300
BACKDROP_HEIGHT = 200
SIMILAR_POSTER_WIDTH = 120
SIMILAR_POSTER_HEIGHT = 180
SIGN_IN_MESSAGE = SIGN_IN_STATUS_MESSAGE


@dataclass
class _DetailsResult:
    request_id: int
    bundle: MovieDetailsBundle | None = None
    user_state: MovieUserState | None = None
    error: str | None = None


def format_runtime(runtime: int | None) -> str:
    if runtime is None or runtime <= 0:
        return "—"
    hours, minutes = divmod(runtime, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes} min"


def format_language(code: str | None) -> str:
    if not code:
        return "—"
    return LANGUAGE_NAMES.get(code.lower(), code.upper())


class MovieDetailsPage(QWidget):
    back_requested = Signal()
    sign_in_requested = Signal()

    def __init__(
        self,
        movie_service: MovieService | None = None,
        image_loader: ImageLoader | None = None,
        watchlist_service: WatchlistService | None = None,
        history_service: HistoryService | None = None,
        rating_service: RatingService | None = None,
        interaction_service: InteractionService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("movieDetailsPage")

        self._movie_service = movie_service
        self._image_loader = image_loader or ImageLoader(self)
        self._watchlist_service = watchlist_service
        self._history_service = history_service
        self._rating_service = rating_service
        self._interaction_service = interaction_service
        self._runner = TaskRunner(self)
        self._app_state: AppState | None = None
        self._request_id = 0
        self._detail_stack: list[MovieSummaryDTO] = []
        self._current_summary: MovieSummaryDTO | None = None
        self._current_details: MovieDetailsDTO | None = None
        self._user_state = MovieUserState()
        self._poster_key: str | None = None
        self._backdrop_key: str | None = None
        self._similar_cards: list[MovieCard] = []

        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("movieDetailsBackButton")
        apply_property(self.back_button, "variant", "secondary")
        style_button(self.back_button, tooltip="Go back (Esc)", icon="back")
        self.back_button.clicked.connect(self._on_back)
        self._escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._escape.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._escape.activated.connect(self.go_back)

        self.title_label = QLabel("Movie details")
        self.title_label.setObjectName("movieDetailsTitle")
        apply_property(self.title_label, "role", "title")
        self.title_label.setWordWrap(True)

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("movieDetailsMeta")
        apply_property(self.meta_label, "role", "muted")
        self.meta_label.setWordWrap(True)

        self.loading = LoadingWidget("Loading movie details...")
        self.empty = EmptyState("No movie selected", "Choose a title from Discover to see details.")
        self.error = EmptyState("Could not load details", "Check your connection and try again.", self)
        apply_property(self.error.title_label, "role", "heading")
        self.error.set_content("Could not load details", "Check your connection and try again.", retry=True)
        self.error.retried.connect(self._retry)

        self.content = self._build_content()
        self.states = QStackedWidget()
        self.states.setObjectName("movieDetailsStates")
        self.states.addWidget(self.loading)
        self.states.addWidget(self.empty)
        self.states.addWidget(self.error)
        self.states.addWidget(self.content)
        self.states.setCurrentWidget(self.empty)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.title_label)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.states, 1)

        self._image_loader.loaded.connect(self._on_image_loaded)
        self._image_loader.failed.connect(self._on_image_failed)

    def _build_content(self) -> QWidget:
        self.backdrop_label = QLabel()
        self.backdrop_label.setObjectName("movieDetailsBackdrop")
        self.backdrop_label.setFixedHeight(BACKDROP_HEIGHT)
        self.backdrop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.backdrop_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.backdrop_label.hide()

        self.poster_label = QLabel()
        self.poster_label.setObjectName("movieDetailsPoster")
        self.poster_label.setFixedSize(DETAILS_POSTER_WIDTH, DETAILS_POSTER_HEIGHT)
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setPixmap(poster_placeholder(DETAILS_POSTER_WIDTH, DETAILS_POSTER_HEIGHT))

        self.genre_label = QLabel("")
        self.genre_label.setObjectName("movieDetailsGenres")
        apply_property(self.genre_label, "role", "caption")
        self.genre_label.setWordWrap(True)

        self.overview_label = QLabel("")
        self.overview_label.setObjectName("movieDetailsOverview")
        apply_property(self.overview_label, "role", "body")
        self.overview_label.setWordWrap(True)

        self.director_label = QLabel("")
        self.director_label.setObjectName("movieDetailsDirector")
        apply_property(self.director_label, "role", "body")
        self.director_label.setWordWrap(True)

        self.cast_label = QLabel("")
        self.cast_label.setObjectName("movieDetailsCast")
        apply_property(self.cast_label, "role", "muted")
        self.cast_label.setWordWrap(True)

        self.watchlist_button = QPushButton("Add to Watchlist")
        self.watchlist_button.setObjectName("movieDetailsWatchlistButton")
        apply_property(self.watchlist_button, "variant", "primary")
        style_button(self.watchlist_button, tooltip="Save this title to your watchlist", icon="watchlist")
        self.watchlist_button.clicked.connect(self._toggle_watchlist)

        self.watched_button = QPushButton("Mark Watched")
        self.watched_button.setObjectName("movieDetailsWatchedButton")
        apply_property(self.watched_button, "variant", "secondary")
        style_button(self.watched_button, tooltip="Mark this title as watched", icon="history")
        self.watched_button.clicked.connect(self._mark_watched)

        self.like_button = QPushButton("Like")
        self.like_button.setObjectName("movieDetailsLikeButton")
        apply_property(self.like_button, "variant", "secondary")
        style_button(self.like_button, tooltip="Like this title")
        self.like_button.clicked.connect(lambda: self._toggle_interaction("like"))

        self.dislike_button = QPushButton("Dislike")
        self.dislike_button.setObjectName("movieDetailsDislikeButton")
        apply_property(self.dislike_button, "variant", "secondary")
        style_button(self.dislike_button, tooltip="Dislike this title")
        self.dislike_button.clicked.connect(lambda: self._toggle_interaction("dislike"))

        self.not_interested_button = QPushButton("Not Interested")
        self.not_interested_button.setObjectName("movieDetailsNotInterestedButton")
        apply_property(self.not_interested_button, "variant", "muted")
        style_button(self.not_interested_button, tooltip="Hide this title from recommendations")
        self.not_interested_button.clicked.connect(lambda: self._toggle_interaction("not_interested"))

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(SM)
        for button in (
            self.watchlist_button,
            self.watched_button,
            self.like_button,
            self.dislike_button,
            self.not_interested_button,
        ):
            actions.addWidget(button)
        actions.addStretch()

        rate_label = QLabel("Rate movie")
        rate_label.setObjectName("movieDetailsRateLabel")
        apply_property(rate_label, "role", "caption")

        self.rating_widget = RatingWidget(parent=self)
        self.rating_widget.setObjectName("movieDetailsRating")
        self.rating_widget.ratingChanged.connect(self._rate)
        self.star_buttons = self.rating_widget.stars

        stars = QHBoxLayout()
        stars.setContentsMargins(0, 0, 0, 0)
        stars.setSpacing(SM)
        stars.addWidget(rate_label)
        stars.addWidget(self.rating_widget)
        stars.addStretch()

        self.status_label = QLabel("")
        self.status_label.setObjectName("movieDetailsStatus")
        apply_property(self.status_label, "role", "caption")
        self.status_label.setWordWrap(True)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(MD)
        info.addWidget(self.genre_label)
        info.addWidget(self.overview_label)
        info.addWidget(self.director_label)
        info.addWidget(self.cast_label)
        info.addLayout(actions)
        info.addLayout(stars)
        info.addWidget(self.status_label)
        info.addStretch()

        hero = QHBoxLayout()
        hero.setContentsMargins(0, 0, 0, 0)
        hero.setSpacing(XL)
        hero.addWidget(self.poster_label, alignment=Qt.AlignmentFlag.AlignTop)
        hero.addLayout(info, 1)

        self.similar_heading = QLabel("Similar movies")
        self.similar_heading.setObjectName("movieDetailsSimilarHeading")
        apply_property(self.similar_heading, "role", "heading")

        self.similar_host = QWidget()
        self.similar_host.setObjectName("movieDetailsSimilarGrid")
        self.similar_flow = FlowLayout(self.similar_host, spacing=MD)

        self.similar_scroll = QScrollArea()
        self.similar_scroll.setObjectName("movieDetailsSimilarScroll")
        self.similar_scroll.setWidgetResizable(True)
        self.similar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.similar_scroll.setWidget(self.similar_host)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, SM, 0)
        inner_layout.setSpacing(LG)
        inner_layout.addWidget(self.backdrop_label)
        inner_layout.addLayout(hero)
        inner_layout.addWidget(self.similar_heading)
        inner_layout.addWidget(self.similar_scroll)
        inner_layout.addStretch()

        scroll = QScrollArea()
        scroll.setObjectName("movieDetailsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        return scroll

    @property
    def similar_cards(self) -> list[MovieCard]:
        return list(self._similar_cards)

    def refresh(self, app_state: AppState) -> None:
        self._app_state = app_state
        self._detail_stack.clear()
        movie = app_state.selected_movie
        if not isinstance(movie, MovieSummaryDTO):
            self._current_summary = None
            self._current_details = None
            self.title_label.setText("Movie details")
            self.meta_label.setText("")
            self.states.setCurrentWidget(self.empty)
            return
        self._begin_load(movie)

    def go_back(self) -> None:
        self._on_back()

    def _on_back(self) -> None:
        if self._detail_stack:
            previous = self._detail_stack.pop()
            if self._app_state is not None:
                self._app_state.selected_movie = previous
            self._begin_load(previous)
            return
        self.back_requested.emit()

    def _retry(self) -> None:
        if self._current_summary is not None:
            self._begin_load(self._current_summary)

    def _begin_load(self, movie: MovieSummaryDTO) -> None:
        self._current_summary = movie
        self._current_details = None
        self._user_state = MovieUserState()
        self.title_label.setText(movie.title)
        self.meta_label.setText(self._summary_meta(movie))
        self.status_label.setText("")
        self._show_loading()
        if self._movie_service is None:
            self._show_error("Movie details are unavailable.")
            return
        self._request_id += 1
        request_id = self._request_id
        signals = self._runner.submit(
            self._details_job,
            request_id,
            movie.tmdb_id,
            self._current_user_id(),
            key=f"details:{movie.tmdb_id}:{request_id}",
        )
        if signals is not None:
            signals.result.connect(self._on_details_result, QUEUED)
            signals.error.connect(
                lambda message, rid=request_id: self._on_details_result(
                    _DetailsResult(rid, error=message or "Could not load movie details.")
                ),
                QUEUED,
            )

    def _details_job(self, request_id: int, tmdb_id: int, user_id: int | None) -> _DetailsResult:
        try:
            assert self._movie_service is not None
            bundle = self._movie_service.get_details_bundle(tmdb_id)
        except Exception as exc:
            message = str(exc).strip() or "Could not load movie details."
            return _DetailsResult(request_id, error=message)
        return _DetailsResult(
            request_id,
            bundle=bundle,
            user_state=self._compute_user_state(user_id, bundle.details),
        )

    @Slot(object)
    def _on_details_result(self, payload: object) -> None:
        if not isinstance(payload, _DetailsResult) or payload.request_id != self._request_id:
            return
        if payload.error or payload.bundle is None:
            self._show_error(payload.error or "Could not load movie details.")
            return
        try:
            self._user_state = payload.user_state or MovieUserState()
            self._render_bundle(payload.bundle)
        except Exception as exc:
            logger.exception("Failed to render movie details")
            self._show_error(str(exc).strip() or "Could not display movie details.")

    def _render_bundle(self, bundle: MovieDetailsBundle) -> None:
        details = bundle.details
        self._current_details = details
        self._current_summary = details
        if self._app_state is not None:
            self._app_state.selected_movie = details
        self.title_label.setText(details.title)
        self.meta_label.setText(self._details_meta(details))
        self.genre_label.setText(self._genre_text(details))
        self.overview_label.setText(details.overview or "No overview available.")
        self.director_label.setText(self._director_text(bundle.credits))
        self.cast_label.setText(self._cast_text(bundle.credits))
        self._load_images(details)
        self._render_similar(details.tmdb_id, bundle.similar)
        self._apply_user_state()
        self.states.setCurrentWidget(self.content)

    def _load_images(self, details: MovieDetailsDTO) -> None:
        self.poster_label.setPixmap(poster_placeholder(DETAILS_POSTER_WIDTH, DETAILS_POSTER_HEIGHT))
        self._poster_key = self._image_loader.request(details.poster_path, DEFAULT_POSTER_SIZE)
        if details.backdrop_path:
            self.backdrop_label.show()
            self.backdrop_label.setPixmap(poster_placeholder(self.backdrop_label.width() or 640, BACKDROP_HEIGHT))
            self._backdrop_key = self._image_loader.request(details.backdrop_path, DEFAULT_BACKDROP_SIZE)
        else:
            self.backdrop_label.hide()
            self._backdrop_key = None

    def _render_similar(self, current_id: int, movies: list[MovieSummaryDTO]) -> None:
        self.similar_flow.clear()
        self._similar_cards.clear()
        unique: list[MovieSummaryDTO] = []
        seen: set[int] = set()
        for movie in movies:
            if movie.tmdb_id in {current_id, *seen} or movie.tmdb_id <= 0:
                continue
            seen.add(movie.tmdb_id)
            unique.append(movie)
        if not unique:
            self.similar_heading.hide()
            self.similar_scroll.hide()
            return
        self.similar_heading.show()
        self.similar_scroll.show()
        for movie in unique:
            card = MovieCard(
                movie,
                image_loader=self._image_loader,
                parent=self.similar_host,
                poster_width=SIMILAR_POSTER_WIDTH,
                poster_height=SIMILAR_POSTER_HEIGHT,
            )
            card.clicked.connect(self._open_similar)
            self.similar_flow.addWidget(card)
            self._similar_cards.append(card)

    def _open_similar(self, movie: object) -> None:
        if not isinstance(movie, MovieSummaryDTO):
            return
        if self._current_summary is not None:
            self._detail_stack.append(self._current_summary)
        if self._app_state is not None:
            self._app_state.selected_movie = movie
        self._begin_load(movie)

    def _current_user_id(self) -> int | None:
        user = self._app_state.current_user if self._app_state is not None else None
        return user.id if user is not None else None

    def _current_movie(self) -> MovieSummaryDTO | None:
        return self._current_details or self._current_summary

    def _refresh_user_state(self) -> None:
        movie = self._current_movie()
        self._user_state = self._compute_user_state(self._current_user_id(), movie)

    def _compute_user_state(self, user_id: int | None, movie: MovieSummaryDTO | None) -> MovieUserState:
        if movie is None or user_id is None:
            return MovieUserState()
        types: set[str] = set()
        if self._interaction_service is not None:
            types = self._interaction_service.types_for_movie(user_id, movie.tmdb_id)
        return MovieUserState(
            on_watchlist=bool(self._watchlist_service and self._watchlist_service.is_saved(user_id, movie.tmdb_id)),
            watched=bool(self._history_service and self._history_service.has_watched(user_id, movie.tmdb_id)),
            rating=self._rating_service.get_rating(user_id, movie.tmdb_id) if self._rating_service else None,
            liked=LIKE in types,
            disliked=DISLIKE in types,
            not_interested=NOT_INTERESTED in types,
        )

    def _apply_user_state(self) -> None:
        signed_in = self._current_user_id() is not None
        state = self._user_state
        self.watchlist_button.setText("Remove from Watchlist" if state.on_watchlist else "Add to Watchlist")
        apply_property(self.watchlist_button, "variant", "secondary" if state.on_watchlist else "primary")
        self.watchlist_button.setToolTip(
            "Remove this title from your watchlist" if state.on_watchlist else "Save this title to your watchlist"
        )
        self.watched_button.setText("Watched" if state.watched else "Mark Watched")
        apply_property(self.watched_button, "selected", "true" if state.watched else "false")
        self.watched_button.setToolTip("Already marked as watched" if state.watched else "Mark this title as watched")
        apply_property(self.like_button, "selected", "true" if state.liked else "false")
        self.like_button.setToolTip("Remove like" if state.liked else "Like this title")
        apply_property(self.dislike_button, "selected", "true" if state.disliked else "false")
        self.dislike_button.setToolTip("Remove dislike" if state.disliked else "Dislike this title")
        apply_property(self.not_interested_button, "selected", "true" if state.not_interested else "false")
        self.not_interested_button.setToolTip(
            "Allow this title in recommendations" if state.not_interested else "Hide this title from recommendations"
        )
        self.rating_widget.set_rating(state.rating)
        if not signed_in:
            self.status_label.setText(SIGN_IN_MESSAGE)

    def _require_user(self) -> int | None:
        user_id = self._current_user_id()
        if user_id is None:
            self.status_label.setText(SIGN_IN_MESSAGE)
            self.sign_in_requested.emit()
            return None
        return user_id

    def _toggle_watchlist(self) -> None:
        user_id = self._require_user()
        movie = self._current_movie()
        if user_id is None or movie is None or self._watchlist_service is None:
            return
        try:
            if self._user_state.on_watchlist:
                self._watchlist_service.remove(user_id, movie)
                self.status_label.setText("Removed from your watchlist.")
            else:
                self._watchlist_service.add(user_id, movie)
                self.status_label.setText("Added to your watchlist.")
        except Exception as exc:
            logger.exception("Watchlist update failed")
            self.status_label.setText(self._action_error(exc, "Could not update watchlist."))
            return
        self._refresh_user_state()
        self._apply_user_state()

    def _mark_watched(self) -> None:
        user_id = self._require_user()
        movie = self._current_movie()
        if user_id is None or movie is None or self._history_service is None:
            return
        try:
            self._history_service.mark_watched(user_id, movie)
            self.status_label.setText("Marked as watched.")
        except Exception as exc:
            logger.exception("History update failed")
            self.status_label.setText(self._action_error(exc, "Could not mark this movie as watched."))
            return
        self._refresh_user_state()
        self._apply_user_state()

    def _rate(self, rating: int) -> None:
        user_id = self._require_user()
        movie = self._current_movie()
        if user_id is None or movie is None or self._rating_service is None:
            self.rating_widget.set_rating(self._user_state.rating)
            return
        try:
            self._rating_service.set_rating(user_id, movie, rating)
            self.status_label.setText(f"Rated {rating} of {MAX_RATING}.")
        except Exception as exc:
            logger.exception("Rating update failed")
            self.rating_widget.set_rating(self._user_state.rating)
            self.status_label.setText(self._action_error(exc, "Could not save your rating."))
            return
        self._refresh_user_state()
        self._apply_user_state()

    def _toggle_interaction(self, kind: str) -> None:
        user_id = self._require_user()
        movie = self._current_movie()
        if user_id is None or movie is None or self._interaction_service is None:
            return
        enabled = {
            "like": not self._user_state.liked,
            "dislike": not self._user_state.disliked,
            "not_interested": not self._user_state.not_interested,
        }[kind]
        try:
            if kind == "like":
                self._interaction_service.set_like(user_id, movie, enabled)
                self.status_label.setText("Removed like." if not enabled else "Marked as liked.")
            elif kind == "dislike":
                self._interaction_service.set_dislike(user_id, movie, enabled)
                self.status_label.setText("Removed dislike." if not enabled else "Marked as disliked.")
            else:
                self._interaction_service.set_not_interested(user_id, movie, enabled)
                self.status_label.setText(
                    "Removed not interested." if not enabled else "Marked as not interested."
                )
        except Exception as exc:
            logger.exception("Interaction update failed")
            self.status_label.setText(self._action_error(exc, "Could not save that action."))
            return
        self._refresh_user_state()
        self._apply_user_state()

    def _show_loading(self) -> None:
        self.loading.set_message("Loading movie details...")
        self.states.setCurrentWidget(self.loading)

    def _show_error(self, message: str) -> None:
        self.error.set_content("Could not load details", message, retry=True)
        self.states.setCurrentWidget(self.error)

    @Slot(str, object)
    def _on_image_loaded(self, key: str, pixmap: object) -> None:
        if not isinstance(pixmap, QPixmap) or pixmap.isNull():
            return
        if key == self._poster_key:
            self.poster_label.setPixmap(
                pixmap.scaled(
                    DETAILS_POSTER_WIDTH,
                    DETAILS_POSTER_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        if key == self._backdrop_key:
            width = max(self.backdrop_label.width(), 640)
            self.backdrop_label.setPixmap(
                pixmap.scaled(
                    width,
                    BACKDROP_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    @Slot(str)
    def _on_image_failed(self, key: str) -> None:
        if key == self._poster_key:
            self.poster_label.setPixmap(poster_placeholder(DETAILS_POSTER_WIDTH, DETAILS_POSTER_HEIGHT))
        if key == self._backdrop_key:
            self.backdrop_label.hide()

    @staticmethod
    def _summary_meta(movie: MovieSummaryDTO) -> str:
        return f"{format_release_year(movie.release_date)}  ·  TMDB {format_rating(movie.vote_average)}"

    @staticmethod
    def _details_meta(details: MovieDetailsDTO) -> str:
        return "  ·  ".join(
            [
                format_release_year(details.release_date),
                format_runtime(details.runtime),
                format_language(details.original_language),
                f"TMDB {format_rating(details.vote_average)}",
            ]
        )

    @staticmethod
    def _genre_text(details: MovieDetailsDTO) -> str:
        names = [genre.name for genre in details.genres if genre.name]
        return "  ·  ".join(names) if names else "Genres unavailable"

    @staticmethod
    def _director_text(credits: CreditsDTO) -> str:
        return f"Director: {credits.director}" if credits.director else "Director: —"

    @staticmethod
    def _cast_text(credits: CreditsDTO) -> str:
        names = [member.name for member in credits.cast if member.name][:8]
        return f"Cast: {', '.join(names)}" if names else "Cast: —"

    @staticmethod
    def _action_error(exc: Exception, fallback: str) -> str:
        if isinstance(exc, LibraryError):
            return str(exc)
        message = str(exc).strip()
        return message or fallback
