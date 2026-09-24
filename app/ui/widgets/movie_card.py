from __future__ import annotations

from datetime import date

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QEnterEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from app.schemas.movie_schema import MovieSummaryDTO
from app.ui.theme import apply_property
from app.ui.theme.spacing import MD, SM
from app.ui.widgets.poster_placeholder import poster_placeholder
from app.ui.workers.image_worker import ImageLoader

POSTER_WIDTH = 160
POSTER_HEIGHT = 240
POSTER_RATIO = (2, 3)


def format_release_year(value: date | None) -> str:
    return str(value.year) if value else "—"


def format_rating(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}"


class MovieCard(QFrame):
    clicked = Signal(object)

    def __init__(
        self,
        movie: MovieSummaryDTO,
        image_loader: ImageLoader | None = None,
        parent: QWidget | None = None,
        *,
        poster_width: int = POSTER_WIDTH,
        poster_height: int = POSTER_HEIGHT,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("movieCard")
        apply_property(self, "role", "card")
        apply_property(self, "hovered", "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.movie = movie
        self._image_key: str | None = None
        self._has_remote_poster = False
        self._poster_width = poster_width
        self._poster_height = poster_height

        self.poster_label = QLabel(self)
        self.poster_label.setObjectName("moviePoster")
        self.poster_label.setFixedSize(poster_width, poster_height)
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setScaledContents(False)
        self._show_placeholder()

        self.title_label = QLabel(movie.title, self)
        self.title_label.setObjectName("movieCardTitle")
        apply_property(self.title_label, "role", "body")
        self.title_label.setWordWrap(True)
        self.title_label.setToolTip(movie.title)
        line = self.title_label.fontMetrics().lineSpacing()
        self.title_label.setFixedHeight((line * 2) + 2)

        self.year_label = QLabel(format_release_year(movie.release_date), self)
        self.year_label.setObjectName("movieCardYear")
        apply_property(self.year_label, "role", "caption")

        self.rating_label = QLabel(format_rating(movie.vote_average), self)
        self.rating_label.setObjectName("movieCardRating")
        apply_property(self.rating_label, "role", "caption")

        meta = QHBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(SM)
        meta.addWidget(self.year_label)
        meta.addStretch()
        meta.addWidget(self.rating_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SM, SM, SM, MD)
        layout.setSpacing(SM)
        layout.addWidget(self.poster_label)
        layout.addWidget(self.title_label)
        layout.addLayout(meta)

        if image_loader is not None:
            image_loader.loaded.connect(self._on_image_loaded)
            image_loader.failed.connect(self._on_image_failed)
            self._image_key = image_loader.request(movie.poster_path)

    def enterEvent(self, event: QEnterEvent) -> None:
        apply_property(self, "hovered", "true")
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        apply_property(self, "hovered", "false")
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.movie)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space}:
            self.clicked.emit(self.movie)
            return
        super().keyPressEvent(event)

    def _on_image_loaded(self, key: str, pixmap: object) -> None:
        if key != self._image_key or not isinstance(pixmap, QPixmap) or pixmap.isNull():
            return
        scaled = pixmap.scaled(
            self._poster_width,
            self._poster_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._has_remote_poster = True
        self.poster_label.setPixmap(scaled)

    @property
    def has_loaded_poster(self) -> bool:
        return self._has_remote_poster

    def _on_image_failed(self, key: str) -> None:
        if key != self._image_key:
            return
        self._has_remote_poster = False
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        self.poster_label.setPixmap(poster_placeholder(self._poster_width, self._poster_height))
