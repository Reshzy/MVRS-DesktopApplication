from PySide6.QtWidgets import QWidget

from app.ui.pages.placeholder_page import PlaceholderPage


class DiscoverPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "discoverPage",
            "Discover",
            "Search and filters arrive in a later phase.",
            parent,
        )
