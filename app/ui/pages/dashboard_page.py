from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, XL


class DashboardPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardPage")

        self.title = QLabel("Dashboard")
        apply_property(self.title, "role", "title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel("Temporary home. Personalized rows arrive in a later phase.")
        self.subtitle.setObjectName("dashboardSubtitle")
        apply_property(self.subtitle, "role", "subtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addStretch()
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addStretch()

    def refresh(self, app_state: AppState) -> None:
        if app_state.current_user is None:
            self.subtitle.setText("Browsing as guest. Sign in to save watchlists and ratings.")
            return
        self.subtitle.setText(f"Hello, {app_state.current_user.name}. Personalized rows arrive later.")
