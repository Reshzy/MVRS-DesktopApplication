from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, XL


class PlaceholderPage(QWidget):
    def __init__(
        self,
        object_name: str,
        title: str,
        subtitle: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self._default_subtitle = subtitle

        self.title = QLabel(title)
        apply_property(self.title, "role", "title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel(subtitle)
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
            self.subtitle.setText(self._default_subtitle)
            return
        self.subtitle.setText(f"{self._default_subtitle} Signed in as {app_state.current_user.name}.")
