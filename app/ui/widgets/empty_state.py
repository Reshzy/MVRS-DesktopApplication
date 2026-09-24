from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD


class EmptyState(QWidget):
    retried = Signal()

    def __init__(
        self,
        title: str = "Nothing to show",
        message: str = "Try a different search or filter.",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("emptyState")

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

        self.retry_button = QPushButton("Try again")
        self.retry_button.setObjectName("emptyStateRetryButton")
        apply_property(self.retry_button, "variant", "secondary")
        self.retry_button.clicked.connect(self.retried.emit)
        self.retry_button.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.setSpacing(MD)
        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)
        layout.addWidget(self.retry_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def set_content(self, title: str, message: str, *, retry: bool = False) -> None:
        self.title_label.setText(title)
        self.message_label.setText(message)
        self.retry_button.setVisible(retry)
