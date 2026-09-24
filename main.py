from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config.settings import get_settings
from app.database.init_db import init_database
from app.ui.app_window import MainWindow
from app.utils.logging_config import setup_logging


def main() -> int:
    setup_logging()
    settings = get_settings()
    init_database()

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)

    window = MainWindow()
    window.setWindowTitle(settings.app_name)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
