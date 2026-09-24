from __future__ import annotations

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QPushButton

from app.ui.app_window import MainWindow
from tests.fakes import FakeMovieService


def _open_discover(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.sidebar.button("discover"), Qt.MouseButton.LeftButton)
    page = main_window.discover_page
    qtbot.waitUntil(lambda: page.states.currentWidget() is not page.loading, timeout=3000)


def test_empty_search_does_not_call_service(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    _open_discover(main_window, qtbot)
    page = main_window.discover_page
    before = len(movie_service.search_calls)

    page.search_bar.set_text("   ")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)

    assert len(movie_service.search_calls) == before
    assert page.search_hint.isVisible()
    assert "title" in page.search_hint.text().lower()


def test_search_loads_cards_in_background(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    _open_discover(main_window, qtbot)
    page = main_window.discover_page
    movie_service.delay = 0.2

    clicks: list[int] = []
    ping = QPushButton("Ping")
    ping.clicked.connect(lambda: clicks.append(1))
    qtbot.addWidget(ping)
    ping.show()

    page.search_bar.set_text("inception")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)
    assert page.states.currentWidget() is page.loading

    qtbot.wait(40)
    qtbot.mouseClick(ping, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page.states.currentWidget() is page.scroll, timeout=3000)

    assert clicks == [1]
    assert movie_service.search_calls[-1] == ("inception", 1)
    assert [card.movie.title for card in page.cards] == ["Fight Club", "Inception"]
    QThreadPool.globalInstance().waitForDone(2000)


def test_filters_use_discover_endpoint(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    _open_discover(main_window, qtbot)
    page = main_window.discover_page
    qtbot.waitUntil(lambda: page.filters.genre_combo.count() > 1, timeout=3000)

    page.filters.genre_combo.setCurrentIndex(page.filters.genre_combo.findData(28))
    page.filters.rating_combo.setCurrentIndex(page.filters.rating_combo.findData(7.0))
    page.filters.year_combo.setCurrentIndex(page.filters.year_combo.findData(2024))
    page.filters.language_combo.setCurrentIndex(page.filters.language_combo.findData("en"))
    page.filters.sort_combo.setCurrentIndex(page.filters.sort_combo.findData("vote_average.desc"))
    before = len(movie_service.discover_calls)
    qtbot.mouseClick(page.filters.apply_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: len(movie_service.discover_calls) > before, timeout=3000)

    filters = movie_service.discover_calls[-1]
    assert filters.with_genres == "28"
    assert filters.vote_average_gte == 7.0
    assert filters.primary_release_year == 2024
    assert filters.with_original_language == "en"
    assert filters.sort_by == "vote_average.desc"


def test_empty_and_error_states(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    page = main_window.discover_page
    movie_service.empty = True
    _open_discover(main_window, qtbot)
    assert page.states.currentWidget() is page.empty

    movie_service.empty = False
    movie_service.fail = True
    qtbot.mouseClick(page.filters.apply_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page.states.currentWidget() is page.error, timeout=3000)
    assert "internet" in page.error.message_label.text().lower()


def test_pagination_and_card_opens_details(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    _open_discover(main_window, qtbot)
    page = main_window.discover_page
    assert page.next_button.isEnabled()
    assert not page.prev_button.isEnabled()

    qtbot.mouseClick(page.next_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: movie_service.discover_calls[-1].page == 2, timeout=3000)
    qtbot.waitUntil(lambda: "Page 2 of 2" in page.page_label.text(), timeout=3000)
    assert page.prev_button.isEnabled()
    assert not page.next_button.isEnabled()

    qtbot.mouseClick(page.cards[0], Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.movie_details_page
    assert main_window.app_state.selected_movie.title == "Fight Club"
    assert main_window.movie_details_page.title_label.text() == "Fight Club"

    qtbot.mouseClick(main_window.movie_details_page.back_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is page


def test_topbar_search_opens_discover_with_query(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    main_window.topbar.search_input.setText("dune")
    qtbot.keyClick(main_window.topbar.search_input, Qt.Key.Key_Return)

    page = main_window.discover_page
    assert main_window.stack.currentWidget() is page
    qtbot.waitUntil(lambda: ("dune", 1) in movie_service.search_calls, timeout=3000)
    assert page.search_bar.text() == "dune"
