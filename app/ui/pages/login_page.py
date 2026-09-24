from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from pydantic import ValidationError

from app.services.auth_service import AuthService, InvalidCredentialsError
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, XL
from app.ui.widgets.password_field import PasswordField
from app.utils.helpers import format_validation_error


class LoginPage(QWidget):
    login_succeeded = Signal()
    register_requested = Signal()
    back_requested = Signal()

    def __init__(self, auth_service: AuthService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("loginPage")
        self._auth_service = auth_service

        title = QLabel("Login")
        apply_property(title, "role", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Sign in to keep watchlists, ratings, and recommendations.")
        apply_property(subtitle, "role", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.error_label = QLabel()
        self.error_label.setObjectName("loginErrorLabel")
        apply_property(self.error_label, "role", "error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.email_input = QLineEdit()
        self.email_input.setObjectName("loginEmailInput")
        self.email_input.setPlaceholderText("Email")

        self.password_field = PasswordField("Password")
        self.password_field.setObjectName("loginPasswordField")
        self.password_field.edit.setObjectName("loginPasswordInput")

        self.submit_button = QPushButton("Login")
        self.submit_button.setObjectName("loginSubmitButton")
        apply_property(self.submit_button, "variant", "primary")
        self.submit_button.clicked.connect(self._submit)

        self.register_link = QPushButton("Create an account")
        self.register_link.setObjectName("loginRegisterLink")
        apply_property(self.register_link, "variant", "link")
        self.register_link.clicked.connect(self.register_requested.emit)

        self.back_link = QPushButton("Back")
        self.back_link.setObjectName("loginBackLink")
        apply_property(self.back_link, "variant", "link")
        self.back_link.clicked.connect(self.back_requested.emit)

        card = QFrame()
        apply_property(card, "role", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(XL, XL, XL, XL)
        card_layout.setSpacing(MD)
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_field)
        card_layout.addWidget(self.submit_button)
        card_layout.addWidget(self.register_link, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.back_link, alignment=Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(LG)
        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        card.setMaximumWidth(420)
        card.setMinimumWidth(360)

    def reset(self) -> None:
        self.email_input.clear()
        self.password_field.clear()
        self._set_error("")

    def _submit(self) -> None:
        self._set_error("")
        try:
            self._auth_service.login(
                email=self.email_input.text(),
                password=self.password_field.text(),
            )
        except ValidationError as exc:
            self._set_error(format_validation_error(exc))
            return
        except InvalidCredentialsError as exc:
            self._set_error(str(exc))
            return

        self.login_succeeded.emit()

    def _set_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))
