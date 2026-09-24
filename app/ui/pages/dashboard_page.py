from __future__ import annotations

import logging
from dataclasses import dataclass, field

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.schemas.movie_schema import MovieSummaryDTO
from app.services.history_service import HistoryService
from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService
from app.state.app_state import AppState
from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, MD, XL
from app.ui.widgets.dashboard_row import DashboardRow
from app.ui.widgets.movie_card import MovieCard
from app.ui.widgets.search_bar import SearchBar
from app.ui.workers.image_worker import ImageLoader
from app.ui.workers.signals import QUEUED
from app.ui.workers.task_runner import TaskRunner
from app.utils.constants import DASHBOARD_ROW_LIMIT
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

SECTIONS: tuple[tuple[str, str], ...] = (
    ("recommended", "Recommended For You"),
    ("trending", "Trending"),
    ("popular", "Popular"),
    ("recent", "Recently Released"),
    ("continue", "Continue Exploring"),
)
@dataclass
class _SectionResult:
    section: str
    request_id: int
    movies: list[MovieSummaryDTO] = field(default_factory=list)
    error: str | None = None


class DashboardPage(QWidget):
    movie_selected = Signal(object)
    search_requested = Signal(str)
    profile_requested = Signal()
    view_all_requested = Signal(str)
    sign_in_requested = Signal()

    def __init__(
        self,
        movie_service: MovieService,
        image_loader: ImageLoader | None = None,
        recommendation_service: RecommendationService | None = None,
        history_service: HistoryService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardPage")
        self._movie_service = movie_service
        self._recommendation_service = recommendation_service
        self._history_service = history_service
        self._image_loader = image_loader or ImageLoader(self)
        self._runner = TaskRunner(self)
        self._app_state: AppState | None = None
        self._user_id: int | None = None
        self._request_ids: dict[str, int] = {section: 0 for section, _title in SECTIONS}
        self._loaded_sections: set[str] = set()

        self.greeting = QLabel("Welcome")
        self.greeting.setObjectName("dashboardGreeting")
        apply_property(self.greeting, "role", "title")

        self.profile_button = QPushButton("Profile")
        self.profile_button.setObjectName("dashboardProfileButton")
        apply_property(self.profile_button, "variant", "secondary")
        style_button(self.profile_button, tooltip="Open profile", icon="profile")
        self.profile_button.clicked.connect(self.profile_requested.emit)

        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(MD)
        heading.addWidget(self.greeting, 1)
        heading.addWidget(self.profile_button)

        self.subtitle = QLabel("Find something to watch.")
        self.subtitle.setObjectName("dashboardSubtitle")
        apply_property(self.subtitle, "role", "muted")
        self.subtitle.setWordWrap(True)

        self.search_bar = SearchBar(self)
        self.search_bar.setObjectName("dashboardSearchBar")
        self.search_bar.input.setPlaceholderText("Search movies")
        self.search_bar.search_requested.connect(self._on_search)

        self.search_hint = QLabel("")
        self.search_hint.setObjectName("dashboardSearchHint")
        apply_property(self.search_hint, "role", "error")
        self.search_hint.hide()

        self._rows: dict[str, DashboardRow] = {}
        rows_host = QWidget()
        rows_host.setObjectName("dashboardRows")
        rows_layout = QVBoxLayout(rows_host)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(LG)
        for section_id, title in SECTIONS:
            row = DashboardRow(section_id, title, rows_host)
            row.movie_selected.connect(self.movie_selected.emit)
            row.view_all_requested.connect(lambda sid=section_id: self.view_all_requested.emit(sid))
            row.retry_requested.connect(lambda sid=section_id: self._load_section(sid))
            row.sign_in_requested.connect(self.sign_in_requested.emit)
            rows_layout.addWidget(row)
            self._rows[section_id] = row
        rows_layout.addStretch()

        self.scroll = QScrollArea()
        self.scroll.setObjectName("dashboardScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(rows_host)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addLayout(heading)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.search_hint)
        layout.addWidget(self.scroll, 1)

    def row(self, section_id: str) -> DashboardRow:
        return self._rows[section_id]

    @property
    def cards(self) -> list[MovieCard]:
        items: list[MovieCard] = []
        for row in self._rows.values():
            items.extend(row.cards)
        return items

    def refresh(self, app_state: AppState, *, force: bool = False) -> None:
        self._app_state = app_state
        user = app_state.current_user
        user_id = user.id if user is not None else None
        identity_changed = user_id != self._user_id
        if identity_changed:
            self._loaded_sections.clear()
        self._user_id = user_id
        self._update_header(app_state)

        for section_id in ("trending", "popular", "recent"):
            if force or section_id not in self._loaded_sections:
                self._load_section(section_id)

        if user_id is None:
            self._show_guest_recommended()
        elif force or identity_changed or "recommended" not in self._loaded_sections:
            self._load_section("recommended")

        if user_id is not None or force or "continue" not in self._loaded_sections:
            self._load_section("continue")

    def _update_header(self, app_state: AppState) -> None:
        user = app_state.current_user
        if user is None:
            self.greeting.setText("Welcome")
            self.subtitle.setText("Browse trending and popular titles, or sign in for personal picks.")
            return
        self.greeting.setText(f"Hello, {user.name}")
        self.subtitle.setText("Personalized rows plus what's trending right now.")

    def _on_search(self, query: str) -> None:
        if not query.strip():
            self.search_hint.setText("Enter a movie title to search.")
            self.search_hint.show()
            return
        self.search_hint.hide()
        self.search_requested.emit(query.strip())

    def _show_guest_recommended(self) -> None:
        self._request_ids["recommended"] += 1
        self._loaded_sections.add("recommended")
        self._rows["recommended"].show_empty(
            "Sign in for personalized picks",
            "Recommendations use your ratings, likes, watch history, and preferences.",
            action_label="Sign in",
        )

    def _load_section(self, section_id: str) -> None:
        self._request_ids[section_id] += 1
        request_id = self._request_ids[section_id]
        self._rows[section_id].show_loading()
        if section_id == "recommended":
            if self._user_id is None:
                self._show_guest_recommended()
                return
            if self._recommendation_service is None:
                self._rows[section_id].show_error("Recommendations are unavailable right now.")
                return
            signals = self._runner.submit(self._recommended_job, request_id, self._user_id)
        elif section_id == "continue":
            signals = self._runner.submit(self._continue_job, request_id, self._user_id)
        else:
            signals = self._runner.submit(self._catalog_job, section_id, request_id)
        if signals is not None:
            signals.result.connect(self._on_section_result, QUEUED)
            signals.error.connect(
                lambda message, sid=section_id, rid=request_id: self._on_section_result(
                    _SectionResult(sid, rid, error=message or "Could not load movies.")
                ),
                QUEUED,
            )

    def _catalog_job(self, section_id: str, request_id: int) -> _SectionResult:
        try:
            if section_id == "trending":
                page = self._movie_service.get_trending_movies()
            elif section_id == "popular":
                page = self._movie_service.get_popular_movies()
            elif section_id == "recent":
                page = self._movie_service.get_recent_movies()
            else:
                return _SectionResult(section_id, request_id, error="Unknown dashboard section.")
        except Exception as exc:
            logger.exception("Failed to load dashboard section %s", section_id)
            message = str(exc).strip() or "Could not load movies."
            return _SectionResult(section_id, request_id, error=message)
        return _SectionResult(section_id, request_id, movies=list(page.results)[:DASHBOARD_ROW_LIMIT])

    def _recommended_job(self, request_id: int, user_id: int) -> _SectionResult:
        if self._recommendation_service is None:
            return _SectionResult("recommended", request_id, error="Recommendations are unavailable right now.")
        try:
            items = self._recommendation_service.recommend_for_user(user_id, limit=DASHBOARD_ROW_LIMIT)
        except Exception as exc:
            logger.exception("Failed to load dashboard recommendations")
            message = str(exc).strip() or "Could not load recommendations."
            return _SectionResult("recommended", request_id, error=message)
        return _SectionResult("recommended", request_id, movies=[item.movie for item in items])

    def _continue_job(self, request_id: int, user_id: int | None) -> _SectionResult:
        seed_tmdb_id: int | None = None
        if self._history_service is not None and user_id is not None:
            try:
                entries = self._history_service.list_entries(user_id)
            except Exception:
                logger.exception("Failed to read watch history for dashboard continue row")
                entries = []
            if entries:
                seed_tmdb_id = int(entries[0].movie.tmdb_id)
        try:
            if seed_tmdb_id:
                page = self._movie_service.get_similar_movies(seed_tmdb_id)
            else:
                page = self._movie_service.get_highly_rated_movies()
        except Exception as exc:
            logger.exception("Failed to load dashboard continue row")
            message = str(exc).strip() or "Could not load movies."
            return _SectionResult("continue", request_id, error=message)
        return _SectionResult("continue", request_id, movies=list(page.results)[:DASHBOARD_ROW_LIMIT])

    @Slot(object)
    def _on_section_result(self, payload: object) -> None:
        if not isinstance(payload, _SectionResult):
            return
        if payload.request_id != self._request_ids.get(payload.section):
            return
        row = self._rows[payload.section]
        if payload.error:
            self._loaded_sections.discard(payload.section)
            row.show_error(payload.error)
            return
        movies = payload.movies
        if movies:
            self._loaded_sections.add(payload.section)
            row.show_movies(movies, self._image_loader)
            return
        self._loaded_sections.add(payload.section)
        if payload.section == "recommended":
            row.show_empty("No recommendations yet", "Rate a few titles or update your preferences.")
            return
        row.show_empty("Nothing here yet", "Browse Discover for more titles.")
