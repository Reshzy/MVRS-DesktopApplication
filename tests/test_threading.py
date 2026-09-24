from __future__ import annotations

import time

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QPushButton

from app.ui.workers.request_gate import RequestGate
from app.ui.workers.task_runner import TaskRunner
from tests.fakes import FakeMovieService
from tests.test_auth import VALID_REGISTER
from tests.test_movies import FULL_DETAILS


def test_request_gate_drops_stale_results() -> None:
    gate = RequestGate()
    first = gate.begin()
    second = gate.begin()
    assert gate.is_current(second)
    assert not gate.is_current(first)


def test_stale_worker_result_is_ignored(qtbot, themed_app) -> None:
    runner = TaskRunner()
    gate = RequestGate()
    accepted: list[str] = []

    def slow() -> tuple[int, str]:
        time.sleep(0.25)
        return first, "old"

    def fast() -> tuple[int, str]:
        return second, "new"

    first = gate.begin()
    first_signals = runner.submit(slow)
    second = gate.begin()
    second_signals = runner.submit(fast)
    assert first_signals is not None
    assert second_signals is not None

    def take(payload: object) -> None:
        request_id, value = payload
        if gate.is_current(request_id):
            accepted.append(value)

    first_signals.result.connect(take)
    second_signals.result.connect(take)

    qtbot.waitUntil(lambda: accepted == ["new"], timeout=2000)
    qtbot.wait(80)
    assert accepted == ["new"]
    QThreadPool.globalInstance().waitForDone(2000)


def test_rapid_search_keeps_latest_results(main_window, movie_service: FakeMovieService, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    QThreadPool.globalInstance().waitForDone(4000)
    qtbot.mouseClick(main_window.sidebar.button("discover"), Qt.MouseButton.LeftButton)
    page = main_window.discover_page
    qtbot.waitUntil(lambda: page.states.currentWidget() is not page.loading, timeout=8000)

    movie_service.echo_query = True
    movie_service.query_delays = {"slow-query": 0.35, "inception": 0.05}

    page.search_bar.set_text("slow-query")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)
    page.search_bar.set_text("inception")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: page.states.currentWidget() is page.scroll, timeout=4000)
    qtbot.waitUntil(lambda: bool(page.cards) and page.cards[0].movie.title == "inception", timeout=4000)
    qtbot.waitUntil(lambda: ("slow-query", 1) in movie_service.search_calls, timeout=4000)
    QThreadPool.globalInstance().waitForDone(2000)
    assert ("inception", 1) in movie_service.search_calls
    assert page.cards[0].movie.title == "inception"


def test_insights_load_in_background(main_window, auth_service, qtbot) -> None:
    user = auth_service.register(**VALID_REGISTER)
    user.onboarding_completed = True
    main_window.show_dashboard()
    assert main_window.history_service is not None
    main_window.history_service.mark_watched(user.id, FULL_DETAILS)

    clicks: list[int] = []
    ping = QPushButton("Ping")
    ping.clicked.connect(lambda: clicks.append(1))
    qtbot.addWidget(ping)
    ping.show()

    qtbot.mouseClick(main_window.sidebar.button("insights"), Qt.MouseButton.LeftButton)
    page = main_window.insights_page
    assert page.loading.isVisible() or page.scroll.isVisible()
    qtbot.mouseClick(ping, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page.scroll.isVisible(), timeout=3000)

    assert clicks == [1]
    assert page.watched_value.text() == "1"
    assert not page.loading.isVisible()


def test_library_page_shows_loading_then_tiles(main_window, auth_service, qtbot) -> None:
    user = auth_service.register(**VALID_REGISTER)
    user.onboarding_completed = True
    main_window.show_dashboard()
    movie = FULL_DETAILS
    assert main_window.watchlist_service is not None
    main_window.watchlist_service.add(user.id, movie)

    qtbot.mouseClick(main_window.sidebar.button("watchlist"), Qt.MouseButton.LeftButton)
    page = main_window.watchlist_page
    qtbot.waitUntil(lambda: page.states.currentWidget() is page.scroll, timeout=3000)
    assert [tile.card.movie.title for tile in page.tiles] == ["Fight Club"]


def test_offline_recommendation_error_is_clean(
    main_window, auth_service, movie_service: FakeMovieService, qtbot
) -> None:
    user = auth_service.register(**VALID_REGISTER)
    user.onboarding_completed = True
    main_window.show_dashboard()
    movie_service.fail = True

    qtbot.mouseClick(main_window.sidebar.button("recommendations"), Qt.MouseButton.LeftButton)
    page = main_window.recommendations_page
    qtbot.waitUntil(lambda: page.states.currentWidget() is page.error, timeout=4000)
    assert page.error.retry_button.isVisible()
    assert page.error.message_label.text()
    movie_service.fail = False
    QThreadPool.globalInstance().waitForDone(2000)
