from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, MD, XL


class WelcomePage(QWidget):
    login_requested = Signal()
    register_requested = Signal()
    guest_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("welcomePage")

        title = QLabel("Movie Recommendation System")
        title.setObjectName("welcomeTitle")
        apply_property(title, "role", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Discover films that match your taste, history, and mood.")
        subtitle.setObjectName("welcomeSubtitle")
        apply_property(subtitle, "role", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("welcomeLoginButton")
        apply_property(self.login_button, "variant", "primary")
        style_button(self.login_button, tooltip="Sign in to your account")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.login_requested.emit)

        self.register_button = QPushButton("Register")
        self.register_button.setObjectName("welcomeRegisterButton")
        apply_property(self.register_button, "variant", "secondary")
        style_button(self.register_button, tooltip="Create a new account")
        self.register_button.clicked.connect(self.register_requested.emit)

        self.guest_button = QPushButton("Browse as Guest")
        self.guest_button.setObjectName("welcomeGuestButton")
        apply_property(self.guest_button, "variant", "link")
        style_button(self.guest_button, tooltip="Browse without saving ratings or watchlists")
        self.guest_button.clicked.connect(self.guest_requested.emit)
        self.login_button.setFocus()

        actions = QHBoxLayout()
        actions.setSpacing(MD)
        actions.addStretch()
        actions.addWidget(self.login_button)
        actions.addWidget(self.register_button)
        actions.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(actions)
        layout.addWidget(self.guest_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
