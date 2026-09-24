from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.ui.theme import apply_property
from app.ui.theme.spacing import LG


class LoadingWidget(QWidget):
    def __init__(self, message: str = "Loading movies...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("loadingWidget")

        self.label = QLabel(message)
        self.label.setObjectName("loadingLabel")
        apply_property(self.label, "role", "muted")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.addStretch()
        layout.addWidget(self.label)
        layout.addStretch()

    def set_message(self, message: str) -> None:
        self.label.setText(message)
