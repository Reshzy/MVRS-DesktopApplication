from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from app.ui.theme.colors import TEXT_SECONDARY

ICON_SIZE = 16


def make_icon(name: str, color: str = TEXT_SECONDARY, size: int = ICON_SIZE) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), max(1.4, size / 11), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    _draw(painter, name, QRectF(1.5, 1.5, size - 3, size - 3), QColor(color))
    painter.end()
    return QIcon(pixmap)


def _draw(painter: QPainter, name: str, rect: QRectF, color: QColor) -> None:
    drawer = {
        "home": _draw_home,
        "discover": _draw_search,
        "search": _draw_search,
        "recommendations": _draw_spark,
        "watchlist": _draw_bookmark,
        "history": _draw_clock,
        "insights": _draw_bars,
        "profile": _draw_person,
        "logout": _draw_logout,
        "back": _draw_back,
        "empty": _draw_film,
        "film": _draw_film,
        "error": _draw_alert,
        "guest": _draw_person,
    }.get(name, _draw_dot)
    drawer(painter, rect, color)


def _draw_home(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    path = QPainterPath()
    path.moveTo(rect.center().x(), rect.top())
    path.lineTo(rect.right(), rect.center().y())
    path.lineTo(rect.right() - rect.width() * 0.18, rect.center().y())
    path.lineTo(rect.right() - rect.width() * 0.18, rect.bottom())
    path.lineTo(rect.left() + rect.width() * 0.18, rect.bottom())
    path.lineTo(rect.left() + rect.width() * 0.18, rect.center().y())
    path.lineTo(rect.left(), rect.center().y())
    path.closeSubpath()
    painter.drawPath(path)


def _draw_search(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    diameter = rect.width() * 0.58
    painter.drawEllipse(QRectF(rect.left(), rect.top(), diameter, diameter))
    painter.drawLine(rect.left() + diameter * 0.78, rect.top() + diameter * 0.78, rect.right(), rect.bottom())


def _draw_spark(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    cx, cy = rect.center().x(), rect.center().y()
    painter.drawLine(QPointF(cx, rect.top()), QPointF(cx, rect.bottom()))
    painter.drawLine(QPointF(rect.left(), cy), QPointF(rect.right(), cy))
    inset = rect.width() * 0.22
    painter.drawLine(QPointF(rect.left() + inset, rect.top() + inset), QPointF(rect.right() - inset, rect.bottom() - inset))
    painter.drawLine(QPointF(rect.right() - inset, rect.top() + inset), QPointF(rect.left() + inset, rect.bottom() - inset))


def _draw_bookmark(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    path = QPainterPath()
    path.moveTo(rect.left() + 2, rect.top())
    path.lineTo(rect.right() - 2, rect.top())
    path.lineTo(rect.right() - 2, rect.bottom())
    path.lineTo(rect.center().x(), rect.bottom() - rect.height() * 0.28)
    path.lineTo(rect.left() + 2, rect.bottom())
    path.closeSubpath()
    painter.drawPath(path)


def _draw_clock(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    painter.drawEllipse(rect)
    center = rect.center()
    painter.drawLine(center, QPointF(center.x(), rect.top() + rect.height() * 0.28))
    painter.drawLine(center, QPointF(rect.right() - rect.width() * 0.22, center.y() + 1))


def _draw_bars(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    gap = rect.width() / 4
    painter.drawLine(
        QPointF(rect.left() + gap * 0.5, rect.bottom()),
        QPointF(rect.left() + gap * 0.5, rect.top() + rect.height() * 0.45),
    )
    painter.drawLine(QPointF(rect.left() + gap * 1.7, rect.bottom()), QPointF(rect.left() + gap * 1.7, rect.top()))
    painter.drawLine(
        QPointF(rect.left() + gap * 2.9, rect.bottom()),
        QPointF(rect.left() + gap * 2.9, rect.top() + rect.height() * 0.28),
    )


def _draw_person(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    head = QRectF(0, 0, rect.width() * 0.38, rect.width() * 0.38)
    head.moveCenter(QPointF(rect.center().x(), rect.top() + rect.height() * 0.28))
    painter.drawEllipse(head)
    path = QPainterPath()
    path.moveTo(rect.left() + 1, rect.bottom())
    path.quadTo(rect.center().x(), rect.center().y() + 1, rect.right() - 1, rect.bottom())
    painter.drawPath(path)


def _draw_logout(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    painter.drawRoundedRect(QRectF(rect.left(), rect.top(), rect.width() * 0.55, rect.height()), 2, 2)
    painter.drawLine(QPointF(rect.center().x(), rect.center().y()), QPointF(rect.right(), rect.center().y()))
    painter.drawLine(QPointF(rect.right() - rect.width() * 0.22, rect.top() + rect.height() * 0.28), QPointF(rect.right(), rect.center().y()))
    painter.drawLine(QPointF(rect.right() - rect.width() * 0.22, rect.bottom() - rect.height() * 0.28), QPointF(rect.right(), rect.center().y()))


def _draw_back(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    painter.drawLine(QPointF(rect.left() + 1, rect.center().y()), QPointF(rect.right(), rect.center().y()))
    painter.drawLine(QPointF(rect.left() + 1, rect.center().y()), QPointF(rect.left() + rect.width() * 0.42, rect.top() + 1))
    painter.drawLine(QPointF(rect.left() + 1, rect.center().y()), QPointF(rect.left() + rect.width() * 0.42, rect.bottom() - 1))


def _draw_film(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    painter.drawRoundedRect(rect, 2, 2)
    painter.drawLine(QPointF(rect.left() + rect.width() * 0.28, rect.top()), QPointF(rect.left() + rect.width() * 0.28, rect.bottom()))
    painter.drawLine(QPointF(rect.right() - rect.width() * 0.28, rect.top()), QPointF(rect.right() - rect.width() * 0.28, rect.bottom()))


def _draw_alert(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    path = QPainterPath()
    path.moveTo(rect.center().x(), rect.top())
    path.lineTo(rect.right(), rect.bottom() - 1)
    path.lineTo(rect.left(), rect.bottom() - 1)
    path.closeSubpath()
    painter.drawPath(path)
    painter.drawLine(QPointF(rect.center().x(), rect.top() + rect.height() * 0.38), QPointF(rect.center().x(), rect.bottom() - rect.height() * 0.32))
    painter.drawPoint(QPointF(rect.center().x(), rect.bottom() - rect.height() * 0.18))


def _draw_dot(painter: QPainter, rect: QRectF, _color: QColor) -> None:
    painter.drawEllipse(rect.adjusted(rect.width() * 0.3, rect.height() * 0.3, -rect.width() * 0.3, -rect.height() * 0.3))


def icon_size(size: int = ICON_SIZE) -> QSize:
    return QSize(size, size)
