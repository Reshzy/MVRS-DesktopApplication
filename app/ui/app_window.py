from PySide6.QtWidgets import QMainWindow, QStackedWidget

from app.ui.pages.theme_preview_page import ThemePreviewPage
from app.ui.pages.welcome_page import WelcomePage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("Movie Recommendation System")
        self.resize(1280, 800)

        self.stack = QStackedWidget(self)
        self.theme_preview_page = ThemePreviewPage(self)
        self.welcome_page = WelcomePage(self)
        self.stack.addWidget(self.theme_preview_page)
        self.stack.addWidget(self.welcome_page)
        self.setCentralWidget(self.stack)
