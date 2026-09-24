from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.schemas.movie_schema import MovieSummaryDTO
from app.ui.theme import apply_property
from app.ui.theme.spacing import SM
from app.ui.widgets.movie_card import POSTER_WIDTH, MovieCard
from app.ui.workers.image_worker import ImageLoader


class LibraryTile(QWidget):
    movie_selected = Signal(object)
    remove_requested = Signal(object)
    watched_requested = Signal(object)

    def __init__(
        self,
        movie: MovieSummaryDTO,
        *,
        meta_text: str = "",
        show_remove: bool = False,
        show_watched: bool = False,
        watched: bool = False,
        image_loader: ImageLoader | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("libraryTile")
        self.movie = movie

        self.card = MovieCard(movie, image_loader=image_loader, parent=self)
        self.card.clicked.connect(self.movie_selected.emit)

        self.meta_label = QLabel(meta_text)
        self.meta_label.setObjectName("libraryTileMeta")
        apply_property(self.meta_label, "role", "caption")
        self.meta_label.setWordWrap(True)
        self.meta_label.setVisible(bool(meta_text))

        self.remove_button = QPushButton("Remove")
        self.remove_button.setObjectName("libraryTileRemoveButton")
        apply_property(self.remove_button, "variant", "danger")
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self.movie))
        self.remove_button.setVisible(show_remove)

        self.watched_button = QPushButton("Watched" if watched else "Mark Watched")
        self.watched_button.setObjectName("libraryTileWatchedButton")
        apply_property(self.watched_button, "variant", "secondary")
        apply_property(self.watched_button, "selected", "true" if watched else "false")
        self.watched_button.clicked.connect(lambda: self.watched_requested.emit(self.movie))
        self.watched_button.setVisible(show_watched)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(SM)
        actions.addWidget(self.remove_button)
        actions.addWidget(self.watched_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SM)
        layout.addWidget(self.card)
        layout.addWidget(self.meta_label)
        layout.addLayout(actions)

        self.setFixedWidth(self.card.sizeHint().width() or (POSTER_WIDTH + SM * 2))
