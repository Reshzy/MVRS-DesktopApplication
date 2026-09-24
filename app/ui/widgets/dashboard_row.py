from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.schemas.movie_schema import MovieSummaryDTO
from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, MD, SM
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.loading_widget import LoadingWidget
from app.ui.widgets.movie_card import POSTER_HEIGHT, MovieCard
from app.ui.workers.image_worker import ImageLoader

ROW_BODY_HEIGHT = POSTER_HEIGHT + 100


class DashboardRow(QWidget):
    movie_selected = Signal(object)
    view_all_requested = Signal()
    retry_requested = Signal()
    sign_in_requested = Signal()

    def __init__(
        self,
        section_id: str,
        title: str,
        parent: QWidget | None = None,
        *,
        view_all_label: str = "View all",
    ) -> None:
        super().__init__(parent)
        self.section_id = section_id
        self.setObjectName(f"dashboardRow_{section_id}")
        apply_property(self, "role", "dashboard-row")

        self.heading = QLabel(title, self)
        self.heading.setObjectName(f"dashboardRowHeading_{section_id}")
        apply_property(self.heading, "role", "heading")

        self.view_all_button = QPushButton(view_all_label, self)
        self.view_all_button.setObjectName(f"dashboardViewAll_{section_id}")
        apply_property(self.view_all_button, "variant", "link")
        style_button(self.view_all_button, tooltip=f"Open the full {title.lower()} list")
        self.view_all_button.clicked.connect(self.view_all_requested.emit)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(MD)
        header.addWidget(self.heading, 1)
        header.addWidget(self.view_all_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.loading = LoadingWidget("Loading movies...")
        self.loading.setObjectName(f"dashboardRowLoading_{section_id}")
        self.empty = EmptyState("Nothing here yet", "Browse Discover for more titles.")
        self.empty.setObjectName(f"dashboardRowEmpty_{section_id}")
        self.empty.action_requested.connect(self.sign_in_requested.emit)
        self.error = EmptyState("Could not load this row", "Check your connection and try again.")
        self.error.setObjectName(f"dashboardRowError_{section_id}")
        self.error.set_content("Could not load this row", "Check your connection and try again.", retry=True)
        self.error.retried.connect(self.retry_requested.emit)

        self.row_host = QWidget()
        self.row_host.setObjectName(f"dashboardRowHost_{section_id}")
        self.row_layout = QHBoxLayout(self.row_host)
        self.row_layout.setContentsMargins(0, 0, SM, 0)
        self.row_layout.setSpacing(MD)
        self.row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.scroll = QScrollArea()
        self.scroll.setObjectName(f"dashboardRowScroll_{section_id}")
        self.scroll.setWidgetResizable(False)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setFixedHeight(ROW_BODY_HEIGHT)
        self.scroll.setWidget(self.row_host)

        self.states = QStackedWidget(self)
        self.states.setObjectName(f"dashboardRowStates_{section_id}")
        self.states.setMinimumHeight(ROW_BODY_HEIGHT)
        self.states.addWidget(self.loading)
        self.states.addWidget(self.empty)
        self.states.addWidget(self.error)
        self.states.addWidget(self.scroll)
        self.states.setCurrentWidget(self.loading)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, LG)
        layout.setSpacing(SM)
        layout.addLayout(header)
        layout.addWidget(self.states)

        self._cards: list[MovieCard] = []

    @property
    def cards(self) -> list[MovieCard]:
        return list(self._cards)

    def show_loading(self, message: str = "Loading movies...") -> None:
        self.loading.set_message(message)
        self.view_all_button.setEnabled(False)
        self.states.setCurrentWidget(self.loading)

    def show_error(self, message: str) -> None:
        self.view_all_button.setEnabled(True)
        self.error.set_content("Could not load this row", message, retry=True)
        self.states.setCurrentWidget(self.error)

    def show_empty(
        self,
        title: str,
        message: str,
        *,
        retry: bool = False,
        action_label: str | None = None,
    ) -> None:
        self.view_all_button.setEnabled(True)
        self.empty.set_content(title, message, retry=retry, action_label=action_label)
        self.states.setCurrentWidget(self.empty)

    def show_movies(self, movies: list[MovieSummaryDTO], image_loader: ImageLoader | None) -> None:
        self._clear_cards()
        self.view_all_button.setEnabled(True)
        if not movies:
            self.show_empty("Nothing here yet", "Browse Discover for more titles.")
            return
        for movie in movies:
            card = MovieCard(movie, image_loader=image_loader, parent=self.row_host)
            card.clicked.connect(self.movie_selected.emit)
            self.row_layout.addWidget(card)
            self._cards.append(card)
        self.row_host.adjustSize()
        self.states.setCurrentWidget(self.scroll)

    def _clear_cards(self) -> None:
        while self.row_layout.count():
            item = self.row_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._cards.clear()
