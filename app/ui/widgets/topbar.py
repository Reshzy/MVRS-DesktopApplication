from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from app.models.user import User
from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, MD


class TopBar(QWidget):
    search_requested = Signal(str)
    profile_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("topBar")

        self.title_label = QLabel("Home")
        self.title_label.setObjectName("topBarTitle")
        apply_property(self.title_label, "role", "subheading")

        self.greeting_label = QLabel("Guest")
        self.greeting_label.setObjectName("topBarGreeting")
        apply_property(self.greeting_label, "role", "muted")

        self.search_input = QLineEdit()
        self.search_input.setObjectName("topBarSearch")
        self.search_input.setPlaceholderText("Search movies")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setToolTip("Search by title (Ctrl+F)")
        self.search_input.setAccessibleName("Search movies")
        self.search_input.returnPressed.connect(self._emit_search)

        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("topBarSearchButton")
        apply_property(self.search_button, "variant", "primary")
        style_button(self.search_button, tooltip="Search movies", icon="search")
        self.search_button.clicked.connect(self._emit_search)

        self.profile_button = QPushButton("Profile")
        self.profile_button.setObjectName("topBarProfileButton")
        apply_property(self.profile_button, "variant", "secondary")
        style_button(self.profile_button, tooltip="Open profile (Ctrl+7)", icon="profile")
        self.profile_button.clicked.connect(self.profile_requested.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(LG, MD, LG, MD)
        layout.setSpacing(MD)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.search_button)
        layout.addWidget(self.greeting_label)
        layout.addWidget(self.profile_button)
        self._apply_compact_layout(self.width())

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_user(self, user: User | None) -> None:
        if user is None:
            self.greeting_label.setText("Guest")
            self.greeting_label.setToolTip("Browsing as a guest")
            return
        self.greeting_label.setText(f"Hello, {user.name}")
        self.greeting_label.setToolTip(user.email)

    def resizeEvent(self, event: QEvent) -> None:  # type: ignore[override]
        self._apply_compact_layout(self.width())
        super().resizeEvent(event)

    def _apply_compact_layout(self, width: int) -> None:
        compact = width > 0 and width < 760
        self.greeting_label.setVisible(not compact)
        if compact:
            self.search_input.setMaximumWidth(200)
            self.search_button.setText("")
            return
        self.search_input.setMaximumWidth(320 if width < 980 else 360)
        self.search_button.setText("Search")

    def _emit_search(self) -> None:
        self.search_requested.emit(self.search_input.text().strip())
