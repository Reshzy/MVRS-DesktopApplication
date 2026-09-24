from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, XL


class OnboardingPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("onboardingPage")

        self.title = QLabel("Onboarding")
        apply_property(self.title, "role", "title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel("Preference setup arrives in a later phase.")
        self.subtitle.setObjectName("onboardingSubtitle")
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
            return
        self.subtitle.setText(
            f"Welcome, {app_state.current_user.name}. Preference setup arrives later."
        )
