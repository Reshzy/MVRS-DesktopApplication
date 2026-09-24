from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_property, style_button
from app.ui.theme.icons import make_icon
from app.ui.theme.spacing import LG, MD


class EmptyState(QWidget):
    retried = Signal()
    action_requested = Signal()

    def __init__(
        self,
        title: str = "Nothing to show",
        message: str = "Try a different search or filter.",
        parent: QWidget | None = None,
        *,
        action_label: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("emptyState")

        self.icon_label = QLabel()
        self.icon_label.setObjectName("emptyStateIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("emptyStateTitle")
        apply_property(self.title_label, "role", "heading")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)

        self.message_label = QLabel(message)
        self.message_label.setObjectName("emptyStateMessage")
        apply_property(self.message_label, "role", "muted")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(420)

        self.retry_button = QPushButton("Try again")
        self.retry_button.setObjectName("emptyStateRetryButton")
        apply_property(self.retry_button, "variant", "secondary")
        style_button(self.retry_button, tooltip="Try loading this again")
        self.retry_button.clicked.connect(self.retried.emit)
        self.retry_button.hide()

        self.action_button = QPushButton(action_label or "Sign in")
        self.action_button.setObjectName("emptyStateActionButton")
        apply_property(self.action_button, "variant", "primary")
        style_button(self.action_button, tooltip="Sign in to continue")
        self.action_button.clicked.connect(self.action_requested.emit)
        self.action_button.setVisible(bool(action_label))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.setSpacing(MD)
        layout.addStretch()
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.retry_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.action_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        self._set_kind("guest" if action_label else "empty")

    def set_content(
        self,
        title: str,
        message: str,
        *,
        retry: bool = False,
        action_label: str | None = None,
        kind: str | None = None,
    ) -> None:
        self.title_label.setText(title)
        self.message_label.setText(message)
        self.retry_button.setVisible(retry)
        if action_label:
            self.action_button.setText(action_label)
            self.action_button.show()
        else:
            self.action_button.hide()
        if kind is None:
            if retry:
                kind = "error"
            elif action_label:
                kind = "guest"
            else:
                kind = "empty"
        self._set_kind(kind)

    def _set_kind(self, kind: str) -> None:
        icon_name = {"error": "error", "guest": "guest", "empty": "empty"}.get(kind, "empty")
        self.icon_label.setPixmap(make_icon(icon_name, size=32).pixmap(32, 32))
        self.icon_label.setToolTip(kind.replace("_", " ").title())
