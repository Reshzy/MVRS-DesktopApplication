from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, XL


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("confirmDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(360)

        heading = QLabel(title)
        apply_property(heading, "role", "heading")

        body = QLabel(message)
        apply_property(body, "role", "body")
        body.setWordWrap(True)

        self.confirm_button = QPushButton(confirm_label)
        self.confirm_button.setObjectName("confirmDialogAccept")
        apply_property(self.confirm_button, "variant", "danger")
        self.confirm_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton(cancel_label)
        self.cancel_button.setObjectName("confirmDialogCancel")
        apply_property(self.cancel_button, "variant", "secondary")
        self.cancel_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.setSpacing(MD)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.confirm_button)

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
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
    ) -> bool:
        dialog = cls(title, message, confirm_label, cancel_label, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
