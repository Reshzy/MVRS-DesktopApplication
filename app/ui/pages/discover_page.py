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

from app.schemas.movie_schema import DiscoverFilters, GenreDTO, MoviePageDTO
from app.services.movie_service import MovieService
from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, XL
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.filter_panel import FilterPanel
from app.ui.widgets.flow_layout import FlowLayout
from app.ui.widgets.loading_widget import LoadingWidget
from app.ui.widgets.movie_card import MovieCard
from app.ui.widgets.search_bar import SearchBar
from app.ui.workers.image_worker import ImageLoader
from app.ui.workers.task_runner import TaskRunner


@dataclass
class _CatalogResult:
    request_id: int
    page: MoviePageDTO | None = None
    error: str | None = None


class DiscoverPage(QWidget):
    movie_selected = Signal(object)

    def __init__(
        self,
        movie_service: MovieService,
        image_loader: ImageLoader | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("discoverPage")
        self._movie_service = movie_service
        self._image_loader = image_loader or ImageLoader(self)
        self._runner = TaskRunner(self)
        self._request_id = 0
        self._mode = "discover"
        self._query = ""
        self._page_number = 1
        self._total_pages = 1
        self._has_loaded = False
        self._genres_requested = False
        self._cards: list[MovieCard] = []

        title = QLabel("Discover")
        apply_property(title, "role", "title")

        subtitle = QLabel("Search by title or browse with filters.")
        apply_property(subtitle, "role", "muted")
        subtitle.setWordWrap(True)

        self.search_bar = SearchBar(self)
        self.search_bar.search_requested.connect(self._on_search)
        self.search_bar.input.textChanged.connect(lambda _text: self.search_hint.hide())
        self.search_hint = QLabel("")
        self.search_hint.setObjectName("discoverSearchHint")
        apply_property(self.search_hint, "role", "error")
        self.search_hint.hide()

        self.filters = FilterPanel(self)
        self.filters.applied.connect(self._on_apply_filters)

        self.status_label = QLabel("Browse popular titles or start a search.")
        self.status_label.setObjectName("discoverStatusLabel")
        apply_property(self.status_label, "role", "caption")

        self.loading = LoadingWidget("Loading movies...")
        self.empty = EmptyState("No movies found", "Try another title or clear a filter.")
        self.error = EmptyState("Could not load movies", "Check your connection and try again.", self)
        apply_property(self.error.title_label, "role", "heading")
        self.error.set_content(
            "Could not load movies",
            "Check your connection and try again.",
            retry=True,
        )
        self.error.retried.connect(self._retry)

        self.grid_host = QWidget()
        self.grid_host.setObjectName("discoverGrid")
        self.flow = FlowLayout(self.grid_host, spacing=MD)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("discoverScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.grid_host)

        self.states = QStackedWidget()
        self.states.setObjectName("discoverStates")
        self.states.addWidget(self.loading)
        self.states.addWidget(self.empty)
        self.states.addWidget(self.error)
        self.states.addWidget(self.scroll)

        self.prev_button = QPushButton("Previous")
        self.prev_button.setObjectName("discoverPrevButton")
        apply_property(self.prev_button, "variant", "secondary")
        self.prev_button.clicked.connect(lambda: self._change_page(-1))

        self.next_button = QPushButton("Next")
        self.next_button.setObjectName("discoverNextButton")
        apply_property(self.next_button, "variant", "secondary")
        self.next_button.clicked.connect(lambda: self._change_page(1))

        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setObjectName("discoverPageLabel")
        apply_property(self.page_label, "role", "caption")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pager = QHBoxLayout()
        pager.setContentsMargins(0, 0, 0, 0)
        pager.setSpacing(MD)
        pager.addWidget(self.prev_button)
        pager.addStretch()
        pager.addWidget(self.page_label)
        pager.addStretch()
        pager.addWidget(self.next_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.search_hint)
        layout.addWidget(self.filters)
        layout.addWidget(self.status_label)
        layout.addWidget(self.states, 1)
        layout.addLayout(pager)
        self._update_pager()
        self.states.setCurrentWidget(self.loading)

    @property
    def cards(self) -> list[MovieCard]:
        return list(self._cards)

    def refresh(self, app_state: AppState) -> None:
        self._request_genres()
        pending = app_state.active_filters.pop("query", None)
        if isinstance(pending, str) and pending.strip():
            self.search_bar.set_text(pending.strip())
            self._on_search(pending.strip())
            return
        if not self._has_loaded:
            self._request_catalog("discover", "", self.filters.to_filters(1))

    def _on_search(self, query: str) -> None:
        if not query.strip():
            self.search_hint.setText("Enter a movie title to search.")
            self.search_hint.show()
            return
        self.search_hint.hide()
        self._request_catalog("search", query.strip(), self.filters.to_filters(1))

    def _on_apply_filters(self) -> None:
        self.search_hint.hide()
        self._request_catalog("discover", "", self.filters.to_filters(1))

    def _change_page(self, delta: int) -> None:
        next_page = self._page_number + delta
        if next_page < 1 or next_page > self._total_pages:
            return
        filters = self.filters.to_filters(next_page)
        self._request_catalog(self._mode, self._query, filters)

    def _retry(self) -> None:
        filters = self.filters.to_filters(self._page_number)
        self._request_catalog(self._mode, self._query, filters)

    def _request_catalog(self, mode: str, query: str, filters: DiscoverFilters) -> None:
        self._request_id += 1
        self._mode = mode
        self._query = query
        self._page_number = filters.page
        self._show_loading()
        signals = self._runner.submit(self._catalog_job, self._request_id, mode, query, filters)
        signals.result.connect(self._on_catalog_result)

    def _catalog_job(
        self,
        request_id: int,
        mode: str,
        query: str,
        filters: DiscoverFilters,
    ) -> _CatalogResult:
        try:
            if mode == "search":
                page = self._movie_service.search_movies(query, page=filters.page)
            else:
                page = self._movie_service.discover_movies(filters)
        except Exception as exc:
            message = str(exc).strip() or "Could not load movies."
            return _CatalogResult(request_id, error=message)
        return _CatalogResult(request_id, page=page)

    @Slot(object)
    def _on_catalog_result(self, payload: object) -> None:
        if not isinstance(payload, _CatalogResult) or payload.request_id != self._request_id:
            return
        self._has_loaded = True
        if payload.error:
            self._show_error(payload.error)
            return
        page = payload.page or MoviePageDTO()
        self._render_page(page)

    def _render_page(self, page: MoviePageDTO) -> None:
        self._page_number = max(1, page.page)
        self._total_pages = max(1, page.total_pages)
        self._update_pager()
        self.flow.clear()
        self._cards.clear()

        if not page.results:
            self.status_label.setText("No movies matched this request.")
            self.empty.set_content("No movies found", "Try another title or clear a filter.")
            self.states.setCurrentWidget(self.empty)
            return

        for movie in page.results:
            card = MovieCard(movie, image_loader=self._image_loader, parent=self.grid_host)
            card.clicked.connect(self.movie_selected.emit)
            self.flow.addWidget(card)
            self._cards.append(card)

        kind = "Search results" if self._mode == "search" else "Browse results"
        self.status_label.setText(f"{kind} · {page.total_results} titles")
        self.states.setCurrentWidget(self.scroll)

    def _request_genres(self) -> None:
        if self._genres_requested:
            return
        self._genres_requested = True
        signals = self._runner.submit(self._genres_job)
        signals.result.connect(self._on_genres)

    def _genres_job(self) -> list[GenreDTO]:
        try:
            return self._movie_service.get_genres()
        except Exception:
            return []

    @Slot(object)
    def _on_genres(self, payload: object) -> None:
        if not isinstance(payload, list):
            return
        genres = [item for item in payload if isinstance(item, GenreDTO)]
        if genres:
            self.filters.set_genres(genres)

    def _show_loading(self) -> None:
        self.status_label.setText("Loading movies...")
        self.loading.set_message("Loading movies...")
        self.states.setCurrentWidget(self.loading)

    def _show_error(self, message: str) -> None:
        self.status_label.setText("Something went wrong.")
        self.error.set_content("Could not load movies", message, retry=True)
        self.states.setCurrentWidget(self.error)
        self._update_pager()

    def _update_pager(self) -> None:
        self.page_label.setText(f"Page {self._page_number} of {self._total_pages}")
        self.prev_button.setEnabled(self._page_number > 1)
        self.next_button.setEnabled(self._page_number < self._total_pages)
