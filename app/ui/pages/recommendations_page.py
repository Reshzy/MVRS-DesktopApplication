from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.schemas.recommendation_schema import RecommendedMovie
from app.services.recommendation_service import RecommendationService
from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, SM, XL
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.flow_layout import FlowLayout
from app.ui.widgets.loading_widget import LoadingWidget
from app.ui.widgets.movie_card import POSTER_WIDTH, MovieCard
from app.ui.workers.image_worker import ImageLoader
from app.ui.workers.task_runner import TaskRunner


@dataclass
class _RecommendationResult:
    request_id: int
    items: list[RecommendedMovie] | None = None
    error: str | None = None


class RecommendationTile(QWidget):
    clicked = Signal(object)

    def __init__(
        self,
        item: RecommendedMovie,
        image_loader: ImageLoader | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("recommendationTile")
        self.item = item
        self.movie = item.movie

        self.card = MovieCard(item.movie, image_loader=image_loader, parent=self)
        self.card.clicked.connect(self.clicked.emit)

        self.reason_label = QLabel(item.reason, self)
        self.reason_label.setObjectName("recommendationReason")
        apply_property(self.reason_label, "role", "caption")
        self.reason_label.setWordWrap(True)
        self.reason_label.setFixedWidth(POSTER_WIDTH)
        self.reason_label.setToolTip(item.reason)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SM)
        layout.addWidget(self.card)
        layout.addWidget(self.reason_label)
        layout.addStretch()


class RecommendationsPage(QWidget):
    movie_selected = Signal(object)

    def __init__(
        self,
        recommendation_service: RecommendationService | None = None,
        image_loader: ImageLoader | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("recommendationsPage")
        self._service = recommendation_service
        self._image_loader = image_loader or ImageLoader(self)
        self._runner = TaskRunner(self)
        self._app_state: AppState | None = None
        self._request_id = 0
        self._profile_key: tuple | None = None
        self._has_loaded = False
        self._tiles: list[RecommendationTile] = []

        title = QLabel("Recommended For You")
        apply_property(title, "role", "title")

        subtitle = QLabel("Picks based on your genres, ratings, and viewing history.")
        apply_property(subtitle, "role", "muted")
        subtitle.setWordWrap(True)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("recommendationsRefreshButton")
        apply_property(self.refresh_button, "variant", "secondary")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)

        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(MD)
        heading.addWidget(title, 1)
        heading.addWidget(self.refresh_button)

        self.status_label = QLabel("Sign in to get personalized recommendations.")
        self.status_label.setObjectName("recommendationsStatusLabel")
        apply_property(self.status_label, "role", "caption")

        self.loading = LoadingWidget("Finding movies for you...")
        self.empty = EmptyState("No recommendations yet", "Rate a few titles or update your preferences.")
        self.guest = EmptyState(
            "Sign in for personalized picks",
            "Recommendations use your ratings, likes, watch history, and preferences.",
        )
        self.error = EmptyState("Could not load recommendations", "Check your connection and try again.", self)
        self.error.set_content(
            "Could not load recommendations",
            "Check your connection and try again.",
            retry=True,
        )
        self.error.retried.connect(lambda: self.refresh(self._app_state, force=True) if self._app_state else None)

        self.grid_host = QWidget()
        self.grid_host.setObjectName("recommendationsGrid")
        self.flow = FlowLayout(self.grid_host, spacing=MD)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("recommendationsScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.grid_host)

        self.states = QStackedWidget()
        self.states.setObjectName("recommendationsStates")
        self.states.addWidget(self.loading)
        self.states.addWidget(self.empty)
        self.states.addWidget(self.guest)
        self.states.addWidget(self.error)
        self.states.addWidget(self.scroll)
        self.states.setCurrentWidget(self.guest)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addLayout(heading)
        layout.addWidget(subtitle)
        layout.addWidget(self.status_label)
        layout.addWidget(self.states, 1)

    @property
    def cards(self) -> list[MovieCard]:
        return [tile.card for tile in self._tiles]

    @property
    def tiles(self) -> list[RecommendationTile]:
        return list(self._tiles)

    def refresh(self, app_state: AppState, *, force: bool = False) -> None:
        self._app_state = app_state
        user = app_state.current_user
        if user is None:
            self._has_loaded = False
            self._profile_key = None
            self._show_guest()
            return
        if self._service is None:
            self._show_error("Recommendations are unavailable right now.")
            return
        try:
            key = self._service.profile_key(user.id)
        except Exception:
            key = None
        if (
            not force
            and self._has_loaded
            and key is not None
            and key == self._profile_key
            and self.states.currentWidget() is self.scroll
        ):
            return
        self._load(user.id, key)

    def _on_refresh_clicked(self) -> None:
        if self._app_state is None:
            return
        self.refresh(self._app_state, force=True)

    def _load(self, user_id: int, profile_key: tuple | None) -> None:
        self._request_id += 1
        self._profile_key = profile_key
        self._show_loading()
        signals = self._runner.submit(self._generate_job, self._request_id, user_id)
        signals.result.connect(self._on_result)

    def _generate_job(self, request_id: int, user_id: int) -> _RecommendationResult:
        if self._service is None:
            return _RecommendationResult(request_id, error="Recommendations are unavailable right now.")
        try:
            items = self._service.recommend_for_user(user_id)
        except Exception as exc:
            message = str(exc).strip() or "Could not generate recommendations."
            return _RecommendationResult(request_id, error=message)
        return _RecommendationResult(request_id, items=items)

    @Slot(object)
    def _on_result(self, payload: object) -> None:
        if not isinstance(payload, _RecommendationResult) or payload.request_id != self._request_id:
            return
        self._has_loaded = True
        self.refresh_button.setEnabled(True)
        if payload.error:
            self._show_error(payload.error)
            return
        self._render(payload.items or [])

    def _render(self, items: list[RecommendedMovie]) -> None:
        self.flow.clear()
        self._tiles.clear()
        if not items:
            self.status_label.setText("No personalized picks yet.")
            self.empty.set_content(
                "No recommendations yet",
                "Rate a few titles, like a movie, or update your preferences.",
            )
            self.states.setCurrentWidget(self.empty)
            return
        for item in items:
            tile = RecommendationTile(item, image_loader=self._image_loader, parent=self.grid_host)
            tile.clicked.connect(self.movie_selected.emit)
            self.flow.addWidget(tile)
            self._tiles.append(tile)
        self.status_label.setText(f"{len(items)} picks based on your taste.")
        self.states.setCurrentWidget(self.scroll)

    def _show_loading(self) -> None:
        self.refresh_button.setEnabled(False)
        self.status_label.setText("Finding movies for you...")
        self.loading.set_message("Finding movies for you...")
        self.states.setCurrentWidget(self.loading)

    def _show_guest(self) -> None:
        self.refresh_button.setEnabled(True)
        self.flow.clear()
        self._tiles.clear()
        self.status_label.setText("Sign in to get personalized recommendations.")
        self.states.setCurrentWidget(self.guest)

    def _show_error(self, message: str) -> None:
        self.refresh_button.setEnabled(True)
        self.status_label.setText("Something went wrong.")
        self.error.set_content("Could not load recommendations", message, retry=True)
        self.states.setCurrentWidget(self.error)
