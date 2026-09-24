from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme.spacing import LG, MD, XL, XXL


def _apply_property(widget: QWidget, name: str, value: str) -> None:
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class ThemePreviewPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("themePreviewPage")

        title = QLabel("Theme Preview")
        _apply_property(title, "role", "title")

        subtitle = QLabel("Dark cinematic tokens applied globally from theme.qss.")
        _apply_property(subtitle, "role", "subtitle")

        heading = QLabel("Components")
        _apply_property(heading, "role", "heading")

        body = QLabel("Primary, secondary, danger, and muted button states with form inputs and cards.")
        _apply_property(body, "role", "body")
        body.setWordWrap(True)

        caption = QLabel("This page is a visual check only. Auth screens arrive in the next phase.")
        _apply_property(caption, "role", "caption")

        primary = QPushButton("Primary")
        _apply_property(primary, "variant", "primary")
        secondary = QPushButton("Secondary")
        _apply_property(secondary, "variant", "secondary")
        danger = QPushButton("Danger")
        _apply_property(danger, "variant", "danger")
        muted = QPushButton("Muted")
        _apply_property(muted, "variant", "muted")

        buttons = QHBoxLayout()
        buttons.setSpacing(MD)
        buttons.addWidget(primary)
        buttons.addWidget(secondary)
        buttons.addWidget(danger)
        buttons.addWidget(muted)
        buttons.addStretch()

        email = QLineEdit()
        email.setPlaceholderText("Email")
        password = QLineEdit()
        password.setPlaceholderText("Password")
        password.setEchoMode(QLineEdit.EchoMode.Password)

        card = QFrame()
        _apply_property(card, "role", "card")
        card_title = QLabel("Sample card")
        _apply_property(card_title, "role", "subheading")
        card_body = QLabel("Cards use the surface color, a thin border, and generous padding.")
        _apply_property(card_body, "role", "muted")
        card_body.setWordWrap(True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(LG, LG, LG, LG)
        card_layout.setSpacing(MD)
        card_layout.addWidget(card_title)
        card_layout.addWidget(card_body)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        _apply_property(sidebar, "role", "sidebar")
        sidebar_title = QLabel("Sidebar")
        _apply_property(sidebar_title, "role", "subheading")
        sidebar_item = QLabel("Home")
        _apply_property(sidebar_item, "role", "body")
        sidebar_muted = QLabel("Discover")
        _apply_property(sidebar_muted, "role", "muted")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(LG, XL, LG, XL)
        sidebar_layout.setSpacing(MD)
        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(sidebar_item)
        sidebar_layout.addWidget(sidebar_muted)
        sidebar_layout.addStretch()

        content = QVBoxLayout()
        content.setContentsMargins(XXL, XL, XXL, XL)
        content.setSpacing(LG)
        content.addWidget(title)
        content.addWidget(subtitle)
        content.addSpacing(MD)
        content.addWidget(heading)
        content.addWidget(body)
        content.addLayout(buttons)
        content.addWidget(email)
        content.addWidget(password)
        content.addWidget(card)
        content.addWidget(caption)
        content.addStretch()

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(sidebar)
        row.addLayout(content, 1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, XXL, XXL)
        root.setSpacing(0)
        root.addLayout(row)
