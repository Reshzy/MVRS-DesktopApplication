from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, MD, XL
from app.utils.constants import SIGN_IN_PROMPT_MESSAGE, SIGN_IN_PROMPT_TITLE


class SignInDialog(QDialog):
    def __init__(
        self,
        title: str = SIGN_IN_PROMPT_TITLE,
        message: str = SIGN_IN_PROMPT_MESSAGE,
        sign_in_label: str = "Sign in",
        cancel_label: str = "Keep browsing",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("signInDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(360)

        heading = QLabel(title)
        heading.setObjectName("signInDialogHeading")
        apply_property(heading, "role", "heading")

        body = QLabel(message)
        body.setObjectName("signInDialogMessage")
        apply_property(body, "role", "body")
        body.setWordWrap(True)

        self.sign_in_button = QPushButton(sign_in_label)
        self.sign_in_button.setObjectName("signInDialogAccept")
        apply_property(self.sign_in_button, "variant", "primary")
        style_button(self.sign_in_button, tooltip=sign_in_label)
        self.sign_in_button.setDefault(True)
        self.sign_in_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton(cancel_label)
        self.cancel_button.setObjectName("signInDialogCancel")
        apply_property(self.cancel_button, "variant", "secondary")
        style_button(self.cancel_button, tooltip=cancel_label)
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.clicked.connect(self.reject)
        self.sign_in_button.setFocus()

        actions = QHBoxLayout()
        actions.setSpacing(MD)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.sign_in_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, LG)
        layout.setSpacing(LG)
        layout.addWidget(heading)
        layout.addWidget(body)
        layout.addLayout(actions)

    @classmethod
    def ask(
        cls,
        parent: QWidget | None = None,
        title: str = SIGN_IN_PROMPT_TITLE,
        message: str = SIGN_IN_PROMPT_MESSAGE,
        confirm_label: str = "Sign in",
        cancel_label: str = "Keep browsing",
        **_unused: object,
    ) -> bool:
        dialog = cls(title, message, confirm_label, cancel_label, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
