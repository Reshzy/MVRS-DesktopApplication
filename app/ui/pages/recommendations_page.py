from PySide6.QtWidgets import QWidget

from app.ui.pages.placeholder_page import PlaceholderPage


class RecommendationsPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "recommendationsPage",
            "Recommendations",
            "Personalized picks arrive in a later phase.",
            parent,
        )
