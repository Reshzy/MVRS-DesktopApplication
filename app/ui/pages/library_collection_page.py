from __future__ import annotations

import logging
from collections.abc import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from app.services.library_base import LibraryError
from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, XL
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.flow_layout import FlowLayout
from app.ui.widgets.library_tile import LibraryTile
from app.ui.workers.image_worker import ImageLoader
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class LibraryCollectionPage(QWidget):
    movie_selected = Signal(object)

    def __init__(
        self,
        object_name: str,
        title: str,
        subtitle: str,
        *,
        guest_title: str,
        guest_message: str,
        empty_title: str,
        empty_message: str,
        image_loader: ImageLoader | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self._image_loader = image_loader
        self._app_state: AppState | None = None
        self._guest_title = guest_title
        self._guest_message = guest_message
        self._empty_title = empty_title
        self._empty_message = empty_message
        self._tiles: list[LibraryTile] = []

        heading = QLabel(title)
        apply_property(heading, "role", "title")

        self.subtitle = QLabel(subtitle)
        apply_property(self.subtitle, "role", "muted")
        self.subtitle.setWordWrap(True)

        self.status_label = QLabel("")
        self.status_label.setObjectName(f"{object_name}Status")
        apply_property(self.status_label, "role", "caption")
        self.status_label.setWordWrap(True)

        self.empty = EmptyState(guest_title, guest_message, self)
        self.error = EmptyState("Could not load this list", "Try again in a moment.", self)
        apply_property(self.error.title_label, "role", "heading")
        self.error.set_content("Could not load this list", "Try again in a moment.", retry=True)
        self.error.retried.connect(self._retry)

        self.grid_host = QWidget()
        self.grid_host.setObjectName(f"{object_name}Grid")
        self.flow = FlowLayout(self.grid_host, spacing=MD)

        self.scroll = QScrollArea()
        self.scroll.setObjectName(f"{object_name}Scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.grid_host)

        self.states = QStackedWidget()
        self.states.setObjectName(f"{object_name}States")
        self.states.addWidget(self.empty)
        self.states.addWidget(self.error)
        self.states.addWidget(self.scroll)
        self.states.setCurrentWidget(self.empty)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addWidget(heading)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.status_label)
        layout.addWidget(self.states, 1)

    @property
    def tiles(self) -> list[LibraryTile]:
        return list(self._tiles)

    def refresh(self, app_state: AppState) -> None:
        self._app_state = app_state
        user = app_state.current_user
        if user is None:
            self._clear_tiles()
            self.status_label.setText("")
            self._show_empty(self._guest_title, self._guest_message)
            return
        try:
            entries = self.load_entries(user.id)
        except Exception as exc:
            logger.exception("Failed to load library page %s", self.objectName())
            self._clear_tiles()
            self._show_error(self._action_error(exc, "Could not load this list."))
            return
        if not entries:
            self._clear_tiles()
            self._show_empty(self._empty_title, self._empty_message)
            return
        self._render(entries)

    def load_entries(self, user_id: int) -> Sequence[object]:
        raise NotImplementedError

    def create_tile(self, entry: object) -> LibraryTile:
        raise NotImplementedError

    def _retry(self) -> None:
        if self._app_state is not None:
            self.refresh(self._app_state)

    def _render(self, entries: Sequence[object]) -> None:
        self._clear_tiles()
        for entry in entries:
            tile = self.create_tile(entry)
            tile.movie_selected.connect(self.movie_selected.emit)
            self.flow.addWidget(tile)
            self._tiles.append(tile)
        count = len(self._tiles)
        self.status_label.setText(f"{count} title{'s' if count != 1 else ''}")
        self.states.setCurrentWidget(self.scroll)

    def _clear_tiles(self) -> None:
        self.flow.clear()
        self._tiles.clear()

    def _show_empty(self, title: str, message: str) -> None:
        self.empty.set_content(title, message)
        self.states.setCurrentWidget(self.empty)

    def _show_error(self, message: str) -> None:
        self.status_label.setText("Something went wrong.")
        self.error.set_content("Could not load this list", message, retry=True)
        self.states.setCurrentWidget(self.error)

    @staticmethod
    def _action_error(exc: Exception, fallback: str) -> str:
        if isinstance(exc, LibraryError):
            return str(exc)
        message = str(exc).strip()
        return message or fallback
