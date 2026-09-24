from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, SM, XS

NAV_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("home", "Home", "Ctrl+1"),
    ("discover", "Discover", "Ctrl+2"),
    ("recommendations", "Recommendations", "Ctrl+3"),
    ("watchlist", "Watchlist", "Ctrl+4"),
    ("history", "History", "Ctrl+5"),
    ("insights", "Insights", "Ctrl+6"),
    ("profile", "Profile", "Ctrl+7"),
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
        title.setToolTip("Movie Recommendation System")

        caption = QLabel("Cinema desk")
        apply_property(caption, "role", "caption")

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.setSpacing(SM)
        layout.addWidget(title)
        layout.addWidget(caption)
        layout.addSpacing(XS)

        for page_id, label, shortcut in NAV_ITEMS:
            button = QPushButton(label)
            button.setObjectName(f"sidebar{label.replace(' ', '')}Button")
            button.setCheckable(True)
            button.setMinimumHeight(40)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            apply_property(button, "variant", "nav")
            style_button(button, tooltip=f"{label} ({shortcut})", icon=page_id)
            button.clicked.connect(lambda _checked=False, dest=page_id: self.navigate_requested.emit(dest))
            self._group.addButton(button)
            self._buttons[page_id] = button
            layout.addWidget(button)

        layout.addStretch()

        self.logout_button = QPushButton("Logout")
        self.logout_button.setObjectName("sidebarLogoutButton")
        self.logout_button.setMinimumHeight(40)
        apply_property(self.logout_button, "variant", "muted")
        style_button(self.logout_button, tooltip="Return to the welcome screen", icon="logout")
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

    def set_session_mode(self, signed_in: bool) -> None:
        self.logout_button.setText("Logout" if signed_in else "Exit")
        self.logout_button.setToolTip("Log out of your account" if signed_in else "Leave guest browsing")
