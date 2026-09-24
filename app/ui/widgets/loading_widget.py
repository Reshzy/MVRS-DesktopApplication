from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from app.ui.theme import apply_property
from app.ui.theme.icons import make_icon
from app.ui.theme.spacing import LG, MD


class LoadingWidget(QWidget):
    def __init__(self, message: str = "Loading movies...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("loadingWidget")

        self.icon_label = QLabel()
        self.icon_label.setObjectName("loadingIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(make_icon("film", size=28).pixmap(28, 28))

        self.progress = QProgressBar()
        self.progress.setObjectName("loadingProgress")
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(220)
        self.progress.setMaximumHeight(6)

        self.label = QLabel(message)
        self.label.setObjectName("loadingLabel")
        apply_property(self.label, "role", "muted")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.setSpacing(MD)
        layout.addStretch()
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        layout.addStretch()

    def set_message(self, message: str) -> None:
        self.label.setText(message)
