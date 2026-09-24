from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap

from app.ui.theme import colors
from app.utils.paths import poster_placeholder_path


def poster_placeholder(width: int, height: int) -> QPixmap:
    path = poster_placeholder_path()
    if path.exists():
        stored = QPixmap(str(path))
        if not stored.isNull():
            return stored.scaled(
                width,
                height,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
    return draw_poster_placeholder(width, height)


def draw_poster_placeholder(width: int, height: int) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(colors.SURFACE_RAISED))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    inset = max(12, min(width, height) // 8)
    frame = pixmap.rect().adjusted(inset, inset, -inset, -inset)
    painter.setPen(QPen(QColor(colors.BORDER), 2))
    painter.setBrush(QColor(colors.SURFACE))
    painter.drawRoundedRect(frame, 10, 10)

    painter.setPen(QColor(colors.TEXT_MUTED))
    font = QFont(painter.font())
    font.setPixelSize(max(10, width // 10))
    painter.setFont(font)
    painter.drawText(frame, Qt.AlignmentFlag.AlignCenter, "No Poster")
    painter.end()
    return pixmap
