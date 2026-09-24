from __future__ import annotations

from datetime import date

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QPushButton, QWidget

from app.schemas.movie_schema import DiscoverFilters, GenreDTO
from app.ui.theme import apply_property
from app.ui.theme.spacing import MD
from app.ui.widgets.flow_layout import FlowLayout

SORT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Popularity", "popularity.desc"),
    ("Rating", "vote_average.desc"),
    ("Release date", "primary_release_date.desc"),
)

RATING_OPTIONS: tuple[tuple[str, float | None], ...] = (
    ("Any rating", None),
    ("5+", 5.0),
    ("6+", 6.0),
    ("7+", 7.0),
    ("8+", 8.0),
    ("9+", 9.0),
)

LANGUAGE_OPTIONS: tuple[tuple[str, str | None], ...] = (
    ("Any language", None),
    ("English", "en"),
    ("Spanish", "es"),
    ("French", "fr"),
    ("German", "de"),
    ("Japanese", "ja"),
    ("Korean", "ko"),
    ("Chinese", "zh"),
    ("Hindi", "hi"),
    ("Italian", "it"),
    ("Portuguese", "pt"),
)


class FilterPanel(QWidget):
    applied = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("filterPanel")

        self.genre_combo = QComboBox()
        self.genre_combo.setObjectName("discoverGenreFilter")
        self.genre_combo.addItem("Any genre", None)

        self.rating_combo = QComboBox()
        self.rating_combo.setObjectName("discoverRatingFilter")
        for label, value in RATING_OPTIONS:
            self.rating_combo.addItem(label, value)

        self.year_combo = QComboBox()
        self.year_combo.setObjectName("discoverYearFilter")
        self.year_combo.addItem("Any year", None)
        current_year = date.today().year
        for year in range(current_year, 1969, -1):
            self.year_combo.addItem(str(year), year)

        self.language_combo = QComboBox()
        self.language_combo.setObjectName("discoverLanguageFilter")
        for label, value in LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, value)

        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("discoverSortFilter")
        for label, value in SORT_OPTIONS:
            self.sort_combo.addItem(label, value)

        self.apply_button = QPushButton("Apply filters")
        self.apply_button.setObjectName("discoverApplyButton")
        apply_property(self.apply_button, "variant", "secondary")
        self.apply_button.clicked.connect(self.applied.emit)

        for combo in (
            self.genre_combo,
            self.rating_combo,
            self.year_combo,
            self.language_combo,
            self.sort_combo,
        ):
            combo.setMinimumWidth(140)

        layout = FlowLayout(self, spacing=MD)
        layout.addWidget(self.genre_combo)
        layout.addWidget(self.rating_combo)
        layout.addWidget(self.year_combo)
        layout.addWidget(self.language_combo)
        layout.addWidget(self.sort_combo)
        layout.addWidget(self.apply_button)
        self.setMinimumHeight(layout.heightForWidth(720))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        layout = self.layout()
        if isinstance(layout, FlowLayout):
            self.setMinimumHeight(layout.heightForWidth(max(self.width(), 1)))
        super().resizeEvent(event)

    def set_genres(self, genres: list[GenreDTO]) -> None:
        current = self.genre_combo.currentData()
        self.genre_combo.blockSignals(True)
        self.genre_combo.clear()
        self.genre_combo.addItem("Any genre", None)
        for genre in genres:
            if genre.tmdb_genre_id <= 0 or not genre.name.strip():
                continue
            self.genre_combo.addItem(genre.name, genre.tmdb_genre_id)
        index = self.genre_combo.findData(current)
        self.genre_combo.setCurrentIndex(max(index, 0))
        self.genre_combo.blockSignals(False)

    def to_filters(self, page: int = 1) -> DiscoverFilters:
        genre_id = self.genre_combo.currentData()
        return DiscoverFilters(
            page=page,
            with_genres=str(genre_id) if genre_id else None,
            primary_release_year=self.year_combo.currentData(),
            vote_average_gte=self.rating_combo.currentData(),
            with_original_language=self.language_combo.currentData(),
            sort_by=self.sort_combo.currentData() or "popularity.desc",
        )
