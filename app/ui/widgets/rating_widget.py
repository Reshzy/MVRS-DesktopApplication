from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from app.ui.theme import apply_property
from app.ui.theme.spacing import SM
from app.utils.constants import MAX_RATING, MIN_RATING


class RatingWidget(QWidget):
    ratingChanged = Signal(int)

    def __init__(
        self,
        rating: int | None = None,
        parent: QWidget | None = None,
        *,
        star_size: int = 36,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ratingWidget")
        self.setMouseTracking(True)
        self._rating = self._clamp(rating)
        self._preview: int | None = None
        self._stars: list[QPushButton] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SM)

        for value in range(MIN_RATING, MAX_RATING + 1):
            button = QPushButton("★")
            button.setObjectName(f"ratingStar{value}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.setFixedSize(star_size, star_size)
            button.setMouseTracking(True)
            apply_property(button, "role", "star")
            stars = "star" if value == 1 else "stars"
            button.setToolTip(f"Rate {value} {stars}")
            button.setAccessibleName(f"Rate {value} {stars}")
            button.clicked.connect(lambda _checked=False, rating=value: self._select(rating))
            button.installEventFilter(self)
            self._stars.append(button)
            layout.addWidget(button)

        layout.addStretch()
        self._sync()

    @property
    def stars(self) -> list[QPushButton]:
        return list(self._stars)

    def rating(self) -> int:
        return self._rating

    def set_rating(self, rating: int | None) -> None:
        self._rating = self._clamp(rating)
        self._preview = None
        self._sync()

    def _select(self, rating: int) -> None:
        self.set_rating(rating)
        self.ratingChanged.emit(self._rating)

    def eventFilter(self, watched, event: QEvent) -> bool:  # type: ignore[override]
        if watched in self._stars:
            value = self._stars.index(watched) + 1
            if event.type() == QEvent.Type.Enter:
                self._preview = value
                self._sync()
            elif event.type() == QEvent.Type.Leave:
                self._preview = None
                self._sync()
        return super().eventFilter(watched, event)

    def leaveEvent(self, event: QEvent) -> None:
        self._preview = None
        self._sync()
        super().leaveEvent(event)

    def _sync(self) -> None:
        preview = self._preview
        for index, button in enumerate(self._stars, start=1):
            apply_property(button, "filled", "true" if index <= self._rating else "false")
            apply_property(button, "preview", "true" if preview is not None and index <= preview else "false")

    @staticmethod
    def _clamp(rating: int | None) -> int:
        if rating is None:
            return 0
        value = int(rating)
        if value < MIN_RATING:
            return 0
        return min(value, MAX_RATING)
