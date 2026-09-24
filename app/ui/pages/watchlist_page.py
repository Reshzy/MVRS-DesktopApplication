from PySide6.QtWidgets import QWidget

from app.ui.pages.placeholder_page import PlaceholderPage


class WatchlistPage(PlaceholderPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            "watchlistPage",
            "Watchlist",
            "Saved movies arrive in a later phase.",
            parent,
        )
