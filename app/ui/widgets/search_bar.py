from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import MD


class SearchBar(QWidget):
    search_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("searchBar")

        self.input = QLineEdit()
        self.input.setObjectName("discoverSearchInput")
        self.input.setPlaceholderText("Search by title")
        self.input.setClearButtonEnabled(True)
        self.input.setToolTip("Search movies by title")
        self.input.setAccessibleName("Search movies")
        self.input.returnPressed.connect(self.submit)

        self.button = QPushButton("Search")
        self.button.setObjectName("discoverSearchButton")
        apply_property(self.button, "variant", "primary")
        style_button(self.button, tooltip="Search movies", icon="search")
        self.button.clicked.connect(self.submit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(MD)
        layout.addWidget(self.input, 1)
        layout.addWidget(self.button)

    def text(self) -> str:
        return self.input.text()

    def set_text(self, value: str) -> None:
        self.input.setText(value)

    def submit(self) -> None:
        query = self.input.text().strip()
        if not query:
            self.search_requested.emit("")
            return
        self.search_requested.emit(query)
