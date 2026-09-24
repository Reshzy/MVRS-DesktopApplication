from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.schemas.movie_schema import MovieSummaryDTO
from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, XL
from app.ui.widgets.movie_card import format_rating, format_release_year


class MovieDetailsPage(QWidget):
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("movieDetailsPage")

        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("movieDetailsBackButton")
        apply_property(self.back_button, "variant", "secondary")
        self.back_button.clicked.connect(self.back_requested.emit)

        self.title_label = QLabel("Movie details")
        self.title_label.setObjectName("movieDetailsTitle")
        apply_property(self.title_label, "role", "title")
        self.title_label.setWordWrap(True)

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("movieDetailsMeta")
        apply_property(self.meta_label, "role", "muted")

        self.overview_label = QLabel("Select a movie from Discover to see details.")
        self.overview_label.setObjectName("movieDetailsOverview")
        apply_property(self.overview_label, "role", "body")
        self.overview_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.title_label)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.overview_label)
        layout.addStretch()

    def refresh(self, app_state: AppState) -> None:
        movie = app_state.selected_movie
        if not isinstance(movie, MovieSummaryDTO):
            self.title_label.setText("Movie details")
            self.meta_label.setText("")
            self.overview_label.setText("Select a movie from Discover to see details.")
            return

        self.title_label.setText(movie.title)
        self.meta_label.setText(
            f"{format_release_year(movie.release_date)}  ·  {format_rating(movie.vote_average)}"
        )
        self.overview_label.setText(movie.overview or "Full details arrive in the next phase.")
