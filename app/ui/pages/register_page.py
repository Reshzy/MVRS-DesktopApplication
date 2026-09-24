from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from pydantic import ValidationError

from app.services.auth_service import AuthService, DuplicateEmailError
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, XL
from app.ui.widgets.password_field import PasswordField
from app.utils.helpers import format_validation_error


class RegisterPage(QWidget):
    register_succeeded = Signal()
    login_requested = Signal()

    def __init__(self, auth_service: AuthService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("registerPage")
        self._auth_service = auth_service

        title = QLabel("Create account")
        apply_property(title, "role", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Save preferences and get recommendations that improve with you.")
        apply_property(subtitle, "role", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        self.error_label = QLabel()
        self.error_label.setObjectName("registerErrorLabel")
        apply_property(self.error_label, "role", "error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.name_input = QLineEdit()
        self.name_input.setObjectName("registerNameInput")
        self.name_input.setPlaceholderText("Name")

        self.email_input = QLineEdit()
        self.email_input.setObjectName("registerEmailInput")
        self.email_input.setPlaceholderText("Email")

        self.password_field = PasswordField("Password")
        self.password_field.setObjectName("registerPasswordField")
        self.password_field.edit.setObjectName("registerPasswordInput")

        self.confirm_field = PasswordField("Confirm password")
        self.confirm_field.setObjectName("registerConfirmField")
        self.confirm_field.edit.setObjectName("registerConfirmInput")

        self.submit_button = QPushButton("Register")
        self.submit_button.setObjectName("registerSubmitButton")
        apply_property(self.submit_button, "variant", "primary")
        self.submit_button.clicked.connect(self._submit)

        self.login_link = QPushButton("Back to login")
        self.login_link.setObjectName("registerLoginLink")
        apply_property(self.login_link, "variant", "link")
        self.login_link.clicked.connect(self.login_requested.emit)

        card = QFrame()
        apply_property(card, "role", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(XL, XL, XL, XL)
        card_layout.setSpacing(MD)
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(self.name_input)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_field)
        card_layout.addWidget(self.confirm_field)
        card_layout.addWidget(self.submit_button)
        card_layout.addWidget(self.login_link, alignment=Qt.AlignmentFlag.AlignCenter)

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
        self.name_input.clear()
        self.email_input.clear()
        self.password_field.clear()
        self.confirm_field.clear()
        self._set_error("")

    def _submit(self) -> None:
        self._set_error("")
        try:
            self._auth_service.register(
                name=self.name_input.text(),
                email=self.email_input.text(),
                password=self.password_field.text(),
                confirm_password=self.confirm_field.text(),
            )
        except ValidationError as exc:
            self._set_error(format_validation_error(exc))
            return
        except DuplicateEmailError as exc:
            self._set_error(str(exc))
            return

        self.register_succeeded.emit()

    def _set_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))
