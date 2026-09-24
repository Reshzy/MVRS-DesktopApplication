from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.ui.theme import colors, fonts, spacing

THEME_PATH = Path(__file__).with_name("theme.qss")


def theme_tokens() -> dict[str, str]:
    return {
        **colors.as_dict(),
        **fonts.as_dict(),
        **spacing.as_dict(),
    }


def load_stylesheet() -> str:
    template = THEME_PATH.read_text(encoding="utf-8")
    return template.format_map(theme_tokens())


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    font = QFont(fonts.FAMILY)
    font.setPixelSize(fonts.BODY_SIZE)
    app.setFont(font)
    app.setStyleSheet(load_stylesheet())
