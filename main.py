from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config.settings import get_settings
from app.database.init_db import init_database
from app.ui.app_window import MainWindow
from app.ui.theme import apply_theme
from app.utils.logging_config import setup_logging
from app.utils.paths import app_icon_path


def main() -> int:
    setup_logging()
    if "--smoke-test" in sys.argv:
        from app.packaging_smoke import run_smoke_test

        return run_smoke_test()

    settings = get_settings()
    init_database()

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    icon_path = app_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    apply_theme(app)

    window = MainWindow()
    window.setWindowTitle(settings.app_name)
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
