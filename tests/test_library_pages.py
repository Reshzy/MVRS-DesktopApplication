from __future__ import annotations

from PySide6.QtCore import Qt

from app.ui.app_window import MainWindow
from tests.fakes import sample_movie
from tests.test_auth import VALID_REGISTER


def _sign_in(main_window: MainWindow, auth_service) -> object:
    user = auth_service.register(**VALID_REGISTER)
    main_window.show_dashboard()
    return user


def test_guest_watchlist_and_history_prompt_sign_in(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)

    qtbot.mouseClick(main_window.sidebar.button("watchlist"), Qt.MouseButton.LeftButton)
    watchlist = main_window.watchlist_page
    assert main_window.stack.currentWidget() is watchlist
    assert watchlist.states.currentWidget() is watchlist.empty
    assert "sign in" in watchlist.empty.title_label.text().lower()
    assert watchlist.tiles == []

    qtbot.mouseClick(main_window.sidebar.button("history"), Qt.MouseButton.LeftButton)
    history = main_window.history_page
    assert main_window.stack.currentWidget() is history
    assert history.states.currentWidget() is history.empty
    assert "sign in" in history.empty.title_label.text().lower()


def test_watchlist_page_lists_removes_and_marks_watched(
    main_window: MainWindow, auth_service, qtbot
) -> None:
    user = _sign_in(main_window, auth_service)
    movie = sample_movie(1, "Fight Club")
    assert main_window.watchlist_service is not None
    main_window.watchlist_service.add(user.id, movie)

    qtbot.mouseClick(main_window.sidebar.button("watchlist"), Qt.MouseButton.LeftButton)
    page = main_window.watchlist_page
    assert page.states.currentWidget() is page.scroll
    assert len(page.tiles) == 1
    assert page.tiles[0].card.movie.title == "Fight Club"
    assert page.tiles[0].watched_button.text() == "Mark Watched"
    assert "Saved" in page.tiles[0].meta_label.text()

    qtbot.mouseClick(page.tiles[0].watched_button, Qt.MouseButton.LeftButton)
    assert main_window.history_service is not None
    assert main_window.history_service.has_watched(user.id, movie.tmdb_id)
    assert page.tiles[0].watched_button.text() == "Watched"
    assert "Marked as watched" in page.status_label.text()

    qtbot.mouseClick(page.tiles[0].remove_button, Qt.MouseButton.LeftButton)
    assert page.tiles == []
    assert page.states.currentWidget() is page.empty
    assert main_window.watchlist_service.is_saved(user.id, movie.tmdb_id) is False


def test_watchlist_card_opens_details_and_keeps_sidebar(
    main_window: MainWindow, auth_service, qtbot
) -> None:
    user = _sign_in(main_window, auth_service)
    movie = sample_movie(1, "Fight Club")
    assert main_window.watchlist_service is not None
    main_window.watchlist_service.add(user.id, movie)

    qtbot.mouseClick(main_window.sidebar.button("watchlist"), Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.watchlist_page.tiles[0].card, Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)

    assert main_window.stack.currentWidget() is details
    assert main_window.sidebar.current_id() == "watchlist"
    assert details.title_label.text() == "Fight Club"


def test_history_page_shows_date_rating_and_opens_details(
    main_window: MainWindow, auth_service, qtbot
) -> None:
    user = _sign_in(main_window, auth_service)
    movie = sample_movie(1, "Fight Club")
    assert main_window.history_service is not None
    assert main_window.rating_service is not None
    main_window.history_service.mark_watched(user.id, movie)
    main_window.rating_service.set_rating(user.id, movie, 5)

    qtbot.mouseClick(main_window.sidebar.button("history"), Qt.MouseButton.LeftButton)
    page = main_window.history_page
    assert page.states.currentWidget() is page.scroll
    assert len(page.tiles) == 1
    assert page.tiles[0].card.movie.title == "Fight Club"
    assert "Watched" in page.tiles[0].meta_label.text()
    assert "5/5" in page.tiles[0].meta_label.text()

    qtbot.mouseClick(page.tiles[0].card, Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)
    assert main_window.stack.currentWidget() is details
    assert main_window.sidebar.current_id() == "history"
