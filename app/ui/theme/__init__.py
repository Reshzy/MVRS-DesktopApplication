from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from app.ui.theme import colors, fonts, spacing
from app.ui.theme.icons import ICON_SIZE, make_icon
from app.utils.constants import DEFAULT_THEME, THEMES
from app.utils.paths import theme_qss_path

THEME_PATH = theme_qss_path()


def normalize_theme(theme: str | None) -> str:
    value = (theme or DEFAULT_THEME).strip().lower()
    return value if value in THEMES else DEFAULT_THEME


def theme_tokens(theme: str = DEFAULT_THEME) -> dict[str, str]:
    return {
        **colors.palette(normalize_theme(theme)),
        **fonts.as_dict(),
        **spacing.as_dict(),
    }


def load_stylesheet(theme: str = DEFAULT_THEME) -> str:
    template = THEME_PATH.read_text(encoding="utf-8")
    return template.format_map(theme_tokens(theme))


def apply_theme(app: QApplication, theme: str = DEFAULT_THEME) -> None:
    app.setStyle("Fusion")
    font = QFont(fonts.FAMILY)
    font.setPixelSize(fonts.BODY_SIZE)
    app.setFont(font)
    app.setStyleSheet(load_stylesheet(theme))


def apply_property(widget: QWidget, name: str, value: str) -> None:
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)


def style_button(
    button: QPushButton,
    *,
    tooltip: str | None = None,
    icon: str | None = None,
    icon_size: int = ICON_SIZE,
) -> None:
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        button.setToolTip(tooltip)
        if not button.accessibleName():
            button.setAccessibleName(tooltip)
    if icon:
        button.setIcon(make_icon(icon))
        button.setIconSize(QSize(icon_size, icon_size))
