from pydantic import ValidationError
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.schemas.user_schema import ProfileUpdateRequest
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, XL
from app.utils.helpers import format_validation_error


class EditProfileDialog(QDialog):
    def __init__(
        self,
        name: str = "",
        email: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("editProfileDialog")
        self.setWindowTitle("Edit profile")
        self.setModal(True)
        self.setMinimumWidth(380)
        self._name = name.strip()

        heading = QLabel("Edit profile")
        heading.setObjectName("editProfileHeading")
        apply_property(heading, "role", "heading")

        body = QLabel("Update the name shown in the app. Email stays the same.")
        body.setObjectName("editProfileMessage")
        apply_property(body, "role", "muted")
        body.setWordWrap(True)

        self.error_label = QLabel()
        self.error_label.setObjectName("editProfileError")
        apply_property(self.error_label, "role", "error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.name_input = QLineEdit()
        self.name_input.setObjectName("editProfileNameInput")
        self.name_input.setPlaceholderText("Name")
        self.name_input.setText(name)
        self.name_input.setMaxLength(120)

        self.email_input = QLineEdit()
        self.email_input.setObjectName("editProfileEmailInput")
        self.email_input.setPlaceholderText("Email")
        self.email_input.setText(email)
        self.email_input.setReadOnly(True)
        self.email_input.setEnabled(False)

        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("editProfileSave")
        apply_property(self.save_button, "variant", "primary")
        self.save_button.clicked.connect(self._save)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("editProfileCancel")
        apply_property(self.cancel_button, "variant", "secondary")
        self.cancel_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.setSpacing(MD)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, LG)
        layout.setSpacing(LG)
        layout.addWidget(heading)
        layout.addWidget(body)
        layout.addWidget(self.error_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.email_input)
        layout.addLayout(actions)

    def profile_name(self) -> str:
        return self._name

    def _save(self) -> None:
        self._set_error("")
        try:
            payload = ProfileUpdateRequest(name=self.name_input.text())
        except ValidationError as exc:
            self._set_error(format_validation_error(exc))
            return
        self._name = payload.name
        self.accept()

    def _set_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))

    @classmethod
    def ask(
        cls,
        parent: QWidget | None = None,
        name: str = "",
        email: str = "",
    ) -> str | None:
        dialog = cls(name, email, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.profile_name()
        return None
