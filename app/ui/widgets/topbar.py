from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from app.models.user import User
from app.ui.theme import apply_property
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
        self.search_input.returnPressed.connect(self._emit_search)

        self.profile_button = QPushButton("Profile")
        self.profile_button.setObjectName("topBarProfileButton")
        apply_property(self.profile_button, "variant", "secondary")
        self.profile_button.clicked.connect(self.profile_requested.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(LG, MD, LG, MD)
        layout.setSpacing(MD)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.greeting_label)
        layout.addWidget(self.profile_button)
        self.search_input.setMaximumWidth(360)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_user(self, user: User | None) -> None:
        if user is None:
            self.greeting_label.setText("Guest")
            return
        self.greeting_label.setText(f"Hello, {user.name}")

    def _emit_search(self) -> None:
        self.search_requested.emit(self.search_input.text().strip())
