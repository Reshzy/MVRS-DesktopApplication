from __future__ import annotations

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QPushButton

from app.ui.app_window import MainWindow
from app.utils.constants import LIKE
from tests.fakes import FakeMovieService
from tests.test_auth import VALID_REGISTER


def _open_discover(main_window: MainWindow, qtbot) -> None:
    if main_window.app_state.current_user is None:
        qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    else:
        main_window.show_dashboard()
    qtbot.mouseClick(main_window.sidebar.button("discover"), Qt.MouseButton.LeftButton)
    page = main_window.discover_page
    qtbot.waitUntil(lambda: page.states.currentWidget() is not page.loading, timeout=3000)


def _open_details(main_window: MainWindow, qtbot):
    _open_discover(main_window, qtbot)
    qtbot.mouseClick(main_window.discover_page.cards[0], Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)
    return details


def test_details_load_in_background(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    _open_discover(main_window, qtbot)
    movie_service.delay = 0.2
    details = main_window.movie_details_page

    clicks: list[int] = []
    ping = QPushButton("Ping")
    ping.clicked.connect(lambda: clicks.append(1))
    qtbot.addWidget(ping)
    ping.show()

    qtbot.mouseClick(main_window.discover_page.cards[0], Qt.MouseButton.LeftButton)
    assert details.states.currentWidget() is details.loading
    assert details.title_label.text() == "Fight Club"

    qtbot.wait(40)
    qtbot.mouseClick(ping, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)

    assert clicks == [1]
    assert movie_service.details_calls[-1] == 1001
    assert "2h 19m" in details.meta_label.text()
    assert "Drama" in details.genre_label.text()
    assert details.director_label.text() == "Director: David Fincher"
    assert "Brad Pitt" in details.cast_label.text()
    assert "Overview for movie 1." in details.overview_label.text()
    QThreadPool.globalInstance().waitForDone(2000)


def test_details_error_state(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    _open_discover(main_window, qtbot)
    movie_service.fail = True
    qtbot.mouseClick(main_window.discover_page.cards[0], Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.error, timeout=3000)
    assert "internet" in details.error.message_label.text().lower()


def test_similar_movie_opens_details_and_back_stack(
    main_window: MainWindow, movie_service: FakeMovieService, qtbot
) -> None:
    details = _open_details(main_window, qtbot)
    assert details.similar_cards
    assert details.similar_cards[0].movie.title == "Inception"

    qtbot.mouseClick(details.similar_cards[0], Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: details.title_label.text() == "Inception", timeout=3000)
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)
    assert main_window.stack.currentWidget() is details
    assert main_window.app_state.selected_movie.title == "Inception"

    qtbot.mouseClick(details.back_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: details.title_label.text() == "Fight Club", timeout=3000)
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)

    qtbot.mouseClick(details.back_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.discover_page


def test_guest_actions_prompt_sign_in(main_window: MainWindow, qtbot) -> None:
    details = _open_details(main_window, qtbot)
    assert "sign in" in details.status_label.text().lower()

    qtbot.mouseClick(details.watchlist_button, Qt.MouseButton.LeftButton)
    assert "sign in" in details.status_label.text().lower()
    assert details.watchlist_button.text() == "Add to Watchlist"


def test_signed_in_actions_persist(main_window: MainWindow, auth_service, qtbot) -> None:
    user = auth_service.register(**VALID_REGISTER)
    details = _open_details(main_window, qtbot)

    qtbot.mouseClick(details.watchlist_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(details.watched_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(details.star_buttons[3], Qt.MouseButton.LeftButton)
    qtbot.mouseClick(details.like_button, Qt.MouseButton.LeftButton)

    assert main_window.watchlist_service is not None
    assert main_window.history_service is not None
    assert main_window.rating_service is not None
    assert main_window.interaction_service is not None
    assert main_window.watchlist_service.is_saved(user.id, 1001)
    assert main_window.history_service.has_watched(user.id, 1001)
    assert main_window.rating_service.get_rating(user.id, 1001) == 4
    assert main_window.interaction_service.has(user.id, 1001, LIKE)
    assert details.watchlist_button.text() == "Remove from Watchlist"
    assert details.watched_button.text() == "Watched"
