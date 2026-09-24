from PySide6.QtWidgets import QWidget

from app.ui.pages.placeholder_page import PlaceholderPage


class ProfilePage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "profilePage",
            "Profile",
            "Account and preference editing arrive later.",
            parent,
        )
