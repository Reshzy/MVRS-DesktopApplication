from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.schemas.insights_schema import ActivityItemDTO, InsightsDTO, RatedMovieDTO
from app.schemas.movie_schema import MovieSummaryDTO
from app.services.user_service import UserService
from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, SM, XL
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.loading_widget import LoadingWidget
from app.ui.widgets.movie_card import format_release_year
from app.ui.workers.request_gate import RequestGate
from app.ui.workers.task_runner import TaskRunner
from app.utils.constants import MAX_RATING
from app.utils.helpers import format_user_date


@dataclass
class _InsightsResult:
    request_id: int
    insights: InsightsDTO | None = None
    error: str | None = None


class InsightsPage(QWidget):
    movie_selected = Signal(object)
    sign_in_requested = Signal()

    def __init__(
        self,
        user_service: UserService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("insightsPage")
        self._user_service = user_service
        self._runner = TaskRunner(self)
        self._requests = RequestGate()
        self._app_state: AppState | None = None

        self.title = QLabel("Insights")
        apply_property(self.title, "role", "title")

        self.subtitle = QLabel("A snapshot of what you watch, rate, and save.")
        self.subtitle.setObjectName("insightsSubtitle")
        apply_property(self.subtitle, "role", "muted")
        self.subtitle.setWordWrap(True)

        self.guest = EmptyState(
            "Sign in to see insights",
            "Watch history, ratings, and watchlist totals stay with your account.",
            self,
            action_label="Sign in",
        )
        self.guest.action_requested.connect(self.sign_in_requested.emit)

        self.loading = LoadingWidget("Loading insights...")
        self.loading.setObjectName("insightsLoading")

        self.error = EmptyState("Could not load insights", "Try again in a moment.", self)
        self.error.set_content("Could not load insights", "Try again in a moment.", retry=True)
        self.error.retried.connect(self._retry)

        self.watched_value = self._stat_value("insightsWatchedValue")
        self.watchlist_value = self._stat_value("insightsWatchlistValue")
        self.average_value = self._stat_value("insightsAverageValue")

        stats = QWidget()
        stats.setObjectName("insightsStats")
        stats_layout = QHBoxLayout(stats)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(MD)
        stats_layout.addWidget(self._stat_card("Watched", self.watched_value), 1)
        stats_layout.addWidget(self._stat_card("Watchlist", self.watchlist_value), 1)
        stats_layout.addWidget(self._stat_card("Average rating", self.average_value), 1)

        self.favorite_genres_label = QLabel()
        self.favorite_genres_label.setObjectName("insightsFavoriteGenres")
        apply_property(self.favorite_genres_label, "role", "body")
        self.favorite_genres_label.setWordWrap(True)

        self.most_watched_label = QLabel()
        self.most_watched_label.setObjectName("insightsMostWatchedGenre")
        apply_property(self.most_watched_label, "role", "body")
        self.most_watched_label.setWordWrap(True)

        taste = self._card(
            "Taste",
            "Favorite genres come from your preferences. Most-watched is based on history.",
            self._labeled("Favorite genres", self.favorite_genres_label),
            self._labeled("Most-watched genre", self.most_watched_label),
        )

        self.highest_host = QWidget()
        self.highest_host.setObjectName("insightsHighestRated")
        self.highest_layout = QVBoxLayout(self.highest_host)
        self.highest_layout.setContentsMargins(0, 0, 0, 0)
        self.highest_layout.setSpacing(SM)

        self.highest_empty = QLabel("Rate movies to see them here.")
        apply_property(self.highest_empty, "role", "caption")
        self.highest_empty.setWordWrap(True)

        highest = self._card("Highest-rated movies", "Your top scores, newest first when ratings match.", self.highest_host, self.highest_empty)

        self.activity_host = QWidget()
        self.activity_host.setObjectName("insightsRecentActivity")
        self.activity_layout = QVBoxLayout(self.activity_host)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(SM)

        self.activity_empty = QLabel("Watch or rate a movie to start a timeline.")
        apply_property(self.activity_empty, "role", "caption")
        self.activity_empty.setWordWrap(True)

        activity = self._card("Recent activity", "Watches, ratings, likes, and watchlist saves.", self.activity_host, self.activity_empty)

        self.content = QWidget()
        self.content.setObjectName("insightsContent")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(XL, XL, XL, XL)
        content_layout.setSpacing(LG)
        content_layout.addWidget(self.title)
        content_layout.addWidget(self.subtitle)
        content_layout.addWidget(stats)
        content_layout.addWidget(taste)
        content_layout.addWidget(highest)
        content_layout.addWidget(activity)
        content_layout.addStretch()

        self.scroll = QScrollArea()
        self.scroll.setObjectName("insightsScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.guest)
        layout.addWidget(self.loading)
        layout.addWidget(self.error)
        layout.addWidget(self.scroll)
        self._show(self.guest)

    def refresh(self, app_state: AppState) -> None:
        self._app_state = app_state
        user = app_state.current_user
        if user is None:
            self._show(self.guest)
            return
        if self._user_service is None:
            self.error.set_content("Insights are unavailable", "Sign in again or restart the app.", retry=False)
            self._show(self.error)
            return
        key = f"insights:{user.id}"
        if self._runner.is_inflight(key):
            self._show(self.loading)
            return
        request_id = self._requests.begin()
        self.loading.set_message("Loading insights...")
        self._show(self.loading)
        signals = self._runner.submit(self._insights_job, request_id, user.id, key=key)
        self._runner.bind(signals, self._on_result, lambda message, rid=request_id: self._on_job_error(rid, message))

    def _retry(self) -> None:
        if self._app_state is not None:
            self.refresh(self._app_state)

    def _insights_job(self, request_id: int, user_id: int) -> _InsightsResult:
        try:
            assert self._user_service is not None
            insights = self._user_service.get_insights(user_id)
        except Exception as exc:
            message = str(exc).strip() or "Could not load insights."
            return _InsightsResult(request_id, error=message)
        return _InsightsResult(request_id, insights=insights)

    def _on_job_error(self, request_id: int, message: str) -> None:
        self._on_result(_InsightsResult(request_id, error=message or "Could not load insights."))

    @Slot(object)
    def _on_result(self, payload: object) -> None:
        if not isinstance(payload, _InsightsResult) or not self._requests.is_current(payload.request_id):
            return
        if payload.error or payload.insights is None:
            self.error.set_content("Could not load insights", payload.error or "Try again in a moment.", retry=True)
            self._show(self.error)
            return
        self._render(payload.insights)
        self._show(self.scroll)

    def _render(self, insights: InsightsDTO) -> None:
        self.watched_value.setText(str(insights.watched_count))
        self.watchlist_value.setText(str(insights.watchlist_count))
        if insights.average_rating is None:
            self.average_value.setText("—")
        else:
            self.average_value.setText(f"{insights.average_rating:.1f}")
        self.favorite_genres_label.setText(
            ", ".join(insights.favorite_genres) if insights.favorite_genres else "None saved yet."
        )
        self.most_watched_label.setText(insights.most_watched_genre or "Not enough watch history yet.")
        self._render_highest(insights.highest_rated)
        self._render_activity(insights.recent_activity)

    def _render_highest(self, movies: list[RatedMovieDTO]) -> None:
        self._clear(self.highest_layout)
        self.highest_empty.setVisible(not movies)
        self.highest_host.setVisible(bool(movies))
        for index, item in enumerate(movies):
            year = format_release_year(item.movie.release_date)
            title = item.movie.title if year == "—" else f"{item.movie.title} ({year})"
            self.highest_layout.addWidget(
                self._movie_button(
                    f"insightsHighest{index}",
                    f"{title}  ·  {item.rating}/{MAX_RATING}",
                    item.movie,
                )
            )

    def _render_activity(self, items: list[ActivityItemDTO]) -> None:
        self._clear(self.activity_layout)
        self.activity_empty.setVisible(not items)
        self.activity_host.setVisible(bool(items))
        for index, item in enumerate(items):
            when = format_user_date(item.occurred_at)
            self.activity_layout.addWidget(
                self._movie_button(
                    f"insightsActivity{index}",
                    f"{item.detail}  ·  {item.movie.title}  ·  {when}",
                    item.movie,
                )
            )

    def _movie_button(self, object_name: str, text: str, movie: MovieSummaryDTO) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_property(button, "variant", "secondary")
        button.setProperty("tmdb_id", movie.tmdb_id)
        button.clicked.connect(lambda _checked=False, chosen=movie: self.movie_selected.emit(chosen))
        return button

    def _show(self, widget: QWidget) -> None:
        self.guest.setVisible(widget is self.guest)
        self.loading.setVisible(widget is self.loading)
        self.error.setVisible(widget is self.error)
        self.scroll.setVisible(widget is self.scroll)

    @staticmethod
    def _stat_value(object_name: str) -> QLabel:
        label = QLabel("0")
        label.setObjectName(object_name)
        apply_property(label, "role", "stat")
        return label

    @staticmethod
    def _stat_card(title: str, value: QLabel) -> QFrame:
        frame = QFrame()
        apply_property(frame, "role", "card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.setSpacing(SM)
        caption = QLabel(title)
        apply_property(caption, "role", "caption")
        layout.addWidget(caption)
        layout.addWidget(value)
        return frame

    @staticmethod
    def _card(title: str, hint: str, *widgets: QWidget) -> QFrame:
        frame = QFrame()
        apply_property(frame, "role", "card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.setSpacing(SM)
        heading = QLabel(title)
        apply_property(heading, "role", "heading")
        caption = QLabel(hint)
        apply_property(caption, "role", "caption")
        caption.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(caption)
        layout.addSpacing(SM)
        for widget in widgets:
            layout.addWidget(widget)
        return frame

    @staticmethod
    def _labeled(title: str, body: QLabel) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SM)
        caption = QLabel(title)
        apply_property(caption, "role", "caption")
        layout.addWidget(caption)
        layout.addWidget(body)
        return box

    @staticmethod
    def _clear(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
