from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import httpx
import pytest
from PIL import Image
from PySide6.QtCore import QEvent, QPointF, QThreadPool, Qt
from PySide6.QtGui import QEnterEvent, QPixmap
from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget

from app.api.exceptions import ImageFetchError
from app.api.image_client import ImageClient, build_image_url
from app.schemas.movie_schema import MovieSummaryDTO
from app.ui.widgets.movie_card import POSTER_HEIGHT, POSTER_RATIO, POSTER_WIDTH, MovieCard
from app.ui.workers.image_worker import ImageLoader


def _png_bytes(width: int = 20, height: int = 30, color: tuple[int, int, int] = (90, 40, 40)) -> bytes:
    image = Image.new("RGB", (width, height), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _movie(index: int, poster_path: str | None = "/poster.jpg") -> MovieSummaryDTO:
    return MovieSummaryDTO(
        tmdb_id=1000 + index,
        title=f"Sample Movie {index}",
        poster_path=poster_path,
        release_date=date(2000 + (index % 20), 6, 1),
        vote_average=6.0 + (index % 40) / 10,
    )


def _client(tmp_path: Path, handler) -> ImageClient:
    http_client = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    return ImageClient(cache_dir=tmp_path / "images", http_client=http_client)


def test_image_client_writes_and_reuses_cache(tmp_path: Path) -> None:
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, content=_png_bytes())

    client = _client(tmp_path, handler)
    first = client.fetch("/poster.jpg")
    second = client.fetch("/poster.jpg")

    assert first == second
    assert calls["count"] == 1
    assert client.cached_bytes("/poster.jpg") == first
    assert build_image_url("/poster.jpg").endswith("/w342/poster.jpg")


def test_image_client_wraps_download_errors(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"missing")

    client = _client(tmp_path, handler)
    with pytest.raises(ImageFetchError):
        client.fetch("/missing.jpg")


def test_image_loader_emits_pixmap_on_main_thread(qtbot, themed_app, tmp_path: Path) -> None:
    loaded: list[tuple[str, QPixmap]] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_png_bytes())

    loader = ImageLoader(client=_client(tmp_path, handler))
    loader.loaded.connect(lambda key, pixmap: loaded.append((key, pixmap)))
    key = loader.request("/poster.jpg")

    qtbot.waitUntil(lambda: bool(loaded), timeout=2000)
    assert loaded[0][0] == key
    assert isinstance(loaded[0][1], QPixmap)
    assert not loaded[0][1].isNull()
    QThreadPool.globalInstance().waitForDone(2000)
    loader.close()


def test_movie_card_shows_title_year_rating(qtbot, themed_app) -> None:
    movie = _movie(1)
    card = MovieCard(movie)
    qtbot.addWidget(card)
    card.show()

    assert card.title_label.text() == "Sample Movie 1"
    assert card.year_label.text() == "2001"
    assert card.rating_label.text() == "6.1"
    assert card.poster_label.pixmap() is not None
    assert not card.poster_label.pixmap().isNull()
    assert card.width() >= POSTER_WIDTH
    assert POSTER_RATIO == (2, 3)
    assert POSTER_HEIGHT == POSTER_WIDTH * 3 // 2


def test_movie_card_click_and_hover(qtbot, themed_app) -> None:
    movie = _movie(2, poster_path=None)
    card = MovieCard(movie)
    qtbot.addWidget(card)
    card.show()

    clicked: list[MovieSummaryDTO] = []
    card.clicked.connect(clicked.append)
    qtbot.mouseClick(card, Qt.MouseButton.LeftButton)
    assert clicked[0].tmdb_id == 1002

    point = QPointF(card.rect().center())
    card.enterEvent(QEnterEvent(point, point, point))
    assert card.property("hovered") == "true"
    card.leaveEvent(QEvent(QEvent.Type.Leave))
    assert card.property("hovered") == "false"


def test_movie_card_grid_loads_posters_without_freezing(qtbot, themed_app, tmp_path: Path) -> None:
    payload = _png_bytes(40, 60, (120, 70, 40))

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=payload)

    loader = ImageLoader(client=_client(tmp_path, handler))
    host = QWidget()
    grid = QGridLayout(host)
    cards: list[MovieCard] = []
    clicks: list[int] = []

    for index in range(24):
        card = MovieCard(_movie(index, poster_path=f"/poster-{index}.jpg"), image_loader=loader)
        card.clicked.connect(lambda movie: clicks.append(movie.tmdb_id))
        grid.addWidget(card, index // 6, index % 6)
        cards.append(card)

    ping = QPushButton("Ping")
    ping.clicked.connect(lambda: clicks.append(1))
    grid.addWidget(ping, 4, 0)
    qtbot.addWidget(host)
    host.show()

    qtbot.wait(40)
    qtbot.mouseClick(ping, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: all(card.has_loaded_poster for card in cards), timeout=4000)
    assert all(card.poster_label.pixmap().width() <= POSTER_WIDTH for card in cards)
    assert all(card.poster_label.pixmap().height() <= POSTER_HEIGHT for card in cards)

    assert 1 in clicks
    assert all(card.title_label.text().startswith("Sample Movie") for card in cards)
    qtbot.mouseClick(cards[0], Qt.MouseButton.LeftButton)
    assert 1000 in clicks
    QThreadPool.globalInstance().waitForDone(2000)
    loader.close()


def test_movie_card_keeps_placeholder_when_download_fails(qtbot, themed_app, tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, content=b"nope")

    failed: list[str] = []
    loader = ImageLoader(client=_client(tmp_path, handler))
    loader.failed.connect(failed.append)
    card = MovieCard(_movie(3, poster_path="/broken.jpg"), image_loader=loader)
    qtbot.addWidget(card)
    card.show()

    qtbot.waitUntil(lambda: bool(failed), timeout=2000)
    assert not card.has_loaded_poster
    assert card.poster_label.pixmap() is not None
    assert not card.poster_label.pixmap().isNull()
    QThreadPool.globalInstance().waitForDone(2000)
    loader.close()
