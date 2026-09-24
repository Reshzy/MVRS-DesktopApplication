from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, SM

NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("home", "Home"),
    ("discover", "Discover"),
    ("recommendations", "Recommendations"),
    ("watchlist", "Watchlist"),
    ("history", "History"),
    ("insights", "Insights"),
    ("profile", "Profile"),
)


class Sidebar(QFrame):
    navigate_requested = Signal(str)
    logout_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        apply_property(self, "role", "sidebar")

        title = QLabel("MVRS")
        apply_property(title, "role", "heading")

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.setSpacing(SM)
        layout.addWidget(title)

        for page_id, label in NAV_ITEMS:
            button = QPushButton(label)
            button.setObjectName(f"sidebar{label.replace(' ', '')}Button")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(36)
            apply_property(button, "variant", "nav")
            button.clicked.connect(lambda _checked=False, dest=page_id: self.navigate_requested.emit(dest))
            self._group.addButton(button)
            self._buttons[page_id] = button
            layout.addWidget(button)

        layout.addStretch()

        self.logout_button = QPushButton("Logout")
        self.logout_button.setObjectName("sidebarLogoutButton")
        self.logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_property(self.logout_button, "variant", "muted")
        self.logout_button.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.logout_button)

    def current_id(self) -> str | None:
        for page_id, button in self._buttons.items():
            if button.isChecked():
                return page_id
        return None

    def button(self, page_id: str) -> QPushButton:
        return self._buttons[page_id]

    def set_current(self, page_id: str) -> None:
        button = self._buttons.get(page_id)
        if button is None:
            return
        button.setChecked(True)
        apply_property(button, "variant", "nav")
