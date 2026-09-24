from PySide6.QtWidgets import QWidget

from app.ui.pages.placeholder_page import PlaceholderPage


class InsightsPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "insightsPage",
            "Insights",
            "Taste insights arrive in a later phase.",
            parent,
        )
