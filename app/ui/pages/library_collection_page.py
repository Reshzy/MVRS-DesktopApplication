from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QLabel, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from app.services.library_base import LibraryError
from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, XL
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.flow_layout import FlowLayout
from app.ui.widgets.library_tile import LibraryTile
from app.ui.widgets.loading_widget import LoadingWidget
from app.ui.workers.image_worker import ImageLoader
from app.ui.workers.request_gate import RequestGate
from app.ui.workers.task_runner import TaskRunner
from app.utils.logging_config import LOGGER_NAME


@dataclass
class _LibraryResult:
    request_id: int
    entries: list[object] = field(default_factory=list)
    error: str | None = None

logger = logging.getLogger(LOGGER_NAME)


class LibraryCollectionPage(QWidget):
    movie_selected = Signal(object)
    sign_in_requested = Signal()

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
        self._runner = TaskRunner(self)
        self._requests = RequestGate()
        self._app_state: AppState | None = None
        self._guest_title = guest_title
        self._guest_message = guest_message
        self._empty_title = empty_title
        self._empty_message = empty_message
        self._pending_status: str | None = None
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

        self.loading = LoadingWidget("Loading your list...")
        self.loading.setObjectName(f"{object_name}Loading")

        self.empty = EmptyState(guest_title, guest_message, self, action_label="Sign in")
        self.empty.action_requested.connect(self.sign_in_requested.emit)
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
        self.states.addWidget(self.loading)
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

    def refresh(self, app_state: AppState, *, status: str | None = None) -> None:
        self._app_state = app_state
        if status is not None:
            self._pending_status = status
        user = app_state.current_user
        if user is None:
            self._clear_tiles()
            self.status_label.setText("")
            self._pending_status = None
            self._show_empty(self._guest_title, self._guest_message)
            return
        key = f"{self.objectName()}:{user.id}"
        if self._runner.is_inflight(key):
            self.states.setCurrentWidget(self.loading)
            return
        request_id = self._requests.begin()
        self.loading.set_message("Loading your list...")
        self.states.setCurrentWidget(self.loading)
        signals = self._runner.submit(self._load_job, request_id, user.id, key=key)
        self._runner.bind(signals, self._on_result, lambda message, rid=request_id: self._on_job_error(rid, message))

    def load_entries(self, user_id: int) -> Sequence[object]:
        raise NotImplementedError

    def create_tile(self, entry: object) -> LibraryTile:
        raise NotImplementedError

    def _retry(self) -> None:
        if self._app_state is not None:
            self.refresh(self._app_state)

    def _load_job(self, request_id: int, user_id: int) -> _LibraryResult:
        try:
            entries = list(self.load_entries(user_id))
        except Exception as exc:
            logger.exception("Failed to load library page %s", self.objectName())
            return _LibraryResult(request_id, error=self._action_error(exc, "Could not load this list."))
        return _LibraryResult(request_id, entries=entries)

    def _on_job_error(self, request_id: int, message: str) -> None:
        self._on_result(_LibraryResult(request_id, error=message or "Could not load this list."))

    @Slot(object)
    def _on_result(self, payload: object) -> None:
        if not isinstance(payload, _LibraryResult) or not self._requests.is_current(payload.request_id):
            return
        if payload.error:
            self._clear_tiles()
            self._show_error(payload.error)
            return
        if not payload.entries:
            self._clear_tiles()
            self._show_empty(self._empty_title, self._empty_message)
            return
        self._render(payload.entries)

    def _render(self, entries: Sequence[object]) -> None:
        self._clear_tiles()
        for entry in entries:
            tile = self.create_tile(entry)
            tile.movie_selected.connect(self.movie_selected.emit)
            self.flow.addWidget(tile)
            self._tiles.append(tile)
        count = len(self._tiles)
        self._apply_status(f"{count} title{'s' if count != 1 else ''}")
        self.states.setCurrentWidget(self.scroll)

    def _clear_tiles(self) -> None:
        self.flow.clear()
        self._tiles.clear()

    def _show_empty(self, title: str, message: str) -> None:
        is_guest = self._app_state is None or not self._app_state.is_authenticated
        self.empty.set_content(title, message, action_label="Sign in" if is_guest else None)
        self._apply_status("")
        self.states.setCurrentWidget(self.empty)

    def _show_error(self, message: str) -> None:
        self._pending_status = None
        self.status_label.setText("Something went wrong.")
        self.error.set_content("Could not load this list", message, retry=True)
        self.states.setCurrentWidget(self.error)

    def _apply_status(self, fallback: str) -> None:
        text = self._pending_status if self._pending_status is not None else fallback
        self._pending_status = None
        self.status_label.setText(text)

    @staticmethod
    def _action_error(exc: Exception, fallback: str) -> str:
        if isinstance(exc, LibraryError):
            return str(exc)
        message = str(exc).strip()
        return message or fallback
