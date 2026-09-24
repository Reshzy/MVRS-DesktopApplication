from PySide6.QtWidgets import QWidget

from app.ui.pages.placeholder_page import PlaceholderPage


class HistoryPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "historyPage",
            "History",
            "Watch history arrives in a later phase.",
            parent,
        )
