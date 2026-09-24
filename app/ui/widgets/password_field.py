from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import SM


class PasswordField(QWidget):
    returnPressed = Signal()

    def __init__(self, placeholder: str = "Password", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("passwordField")

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit.setToolTip(placeholder)
        self.edit.returnPressed.connect(self.returnPressed.emit)

        self.toggle = QPushButton("Show")
        self.toggle.setObjectName("passwordToggle")
        self.toggle.setCheckable(True)
        apply_property(self.toggle, "variant", "muted")
        style_button(self.toggle, tooltip="Show password")
        self.toggle.toggled.connect(self._on_toggled)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SM)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.toggle)

    def text(self) -> str:
        return self.edit.text()

    def set_text(self, value: str) -> None:
        self.edit.setText(value)

    def clear(self) -> None:
        self.edit.clear()
        self.toggle.setChecked(False)

    def _on_toggled(self, checked: bool) -> None:
        self.edit.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self.toggle.setText("Hide" if checked else "Show")
        self.toggle.setToolTip("Hide password" if checked else "Show password")
