from __future__ import annotations

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QPushButton
from sqlalchemy.orm import Session

from app.schemas.user_schema import GenrePreference, UserPreferences
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.ui.app_window import MainWindow
from tests.fakes import FakeMovieService
from tests.test_auth import VALID_REGISTER


def _sign_in_with_preferences(
    main_window: MainWindow,
    auth_service: AuthService,
    db_session: Session,
    qtbot,
    preferences: UserPreferences,
) -> None:
    user = auth_service.register(**VALID_REGISTER)
    UserService(db_session).save_preferences(user.id, preferences)
    main_window.app_state.clear_current_user()
    qtbot.mouseClick(main_window.welcome_page.login_button, Qt.MouseButton.LeftButton)
    main_window.login_page.email_input.setText(VALID_REGISTER["email"])
    main_window.login_page.password_field.set_text(VALID_REGISTER["password"])
    qtbot.mouseClick(main_window.login_page.submit_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.dashboard_page


def _wait_row_content(page, section: str, qtbot, timeout: int = 4000) -> None:
    row = page.row(section)
    qtbot.waitUntil(lambda: row.states.currentWidget() is row.scroll, timeout=timeout)


def _wait_public_rows(page, qtbot) -> None:
    for section in ("trending", "popular", "recent", "continue"):
        _wait_row_content(page, section, qtbot)


def _open_guest_dashboard(main_window: MainWindow, qtbot, *, wait: bool = True) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.dashboard_page
    if wait:
        _wait_public_rows(main_window.dashboard_page, qtbot)


def test_guest_dashboard_loads_public_rows(
    main_window: MainWindow,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    _open_guest_dashboard(main_window, qtbot)
    page = main_window.dashboard_page

    recommended = page.row("recommended")
    assert recommended.states.currentWidget() is recommended.empty
    assert "sign in" in recommended.empty.title_label.text().lower()
    assert recommended.cards == []

    assert [card.movie.title for card in page.row("trending").cards] == ["Fight Club", "Inception"]
    assert [card.movie.title for card in page.row("popular").cards] == ["Fight Club", "Inception"]
    assert page.row("recent").cards
    assert page.row("continue").cards
    assert movie_service.trending_calls == 1
    assert movie_service.popular_calls == [1]
    assert any(call.sort_by == "primary_release_date.desc" for call in movie_service.discover_calls)
    assert any(call.sort_by == "vote_average.desc" for call in movie_service.discover_calls)
    assert movie_service.similar_calls == []


def test_authenticated_dashboard_shows_recommendations(
    main_window: MainWindow,
    auth_service: AuthService,
    db_session: Session,
    qtbot,
) -> None:
    _sign_in_with_preferences(
        main_window,
        auth_service,
        db_session,
        qtbot,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=28, name="Action")]),
    )
    page = main_window.dashboard_page
    _wait_row_content(page, "recommended", qtbot)
    _wait_public_rows(page, qtbot)
    assert page.greeting.text() == "Hello, Ada Lovelace"
    assert page.row("recommended").cards[0].movie.title == "Inception"


def test_card_opens_details_and_view_all_routes(
    main_window: MainWindow,
    auth_service: AuthService,
    db_session: Session,
    qtbot,
) -> None:
    _sign_in_with_preferences(
        main_window,
        auth_service,
        db_session,
        qtbot,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=28, name="Action")]),
    )
    page = main_window.dashboard_page
    _wait_row_content(page, "trending", qtbot)
    _wait_row_content(page, "recommended", qtbot)

    qtbot.mouseClick(page.row("trending").cards[0], Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)
    assert main_window.stack.currentWidget() is details
    assert details.title_label.text() == "Fight Club"

    qtbot.mouseClick(details.back_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: main_window.stack.currentWidget() is page, timeout=3000)

    qtbot.mouseClick(page.row("recommended").view_all_button, Qt.MouseButton.LeftButton)
    recommendations = main_window.recommendations_page
    assert main_window.stack.currentWidget() is recommendations
    qtbot.waitUntil(lambda: recommendations.states.currentWidget() is not recommendations.loading, timeout=4000)

    main_window.navigate("home")
    _wait_row_content(page, "recent", qtbot)
    qtbot.mouseClick(page.row("recent").view_all_button, Qt.MouseButton.LeftButton)
    discover = main_window.discover_page
    assert main_window.stack.currentWidget() is discover
    qtbot.waitUntil(
        lambda: discover.states.currentWidget() in {discover.scroll, discover.empty, discover.error},
        timeout=5000,
    )
    assert discover.filters.sort_combo.currentData() == "primary_release_date.desc"


def test_independent_section_failure_and_retry(
    main_window: MainWindow,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    movie_service.fail_methods.add("get_trending_movies")
    _open_guest_dashboard(main_window, qtbot, wait=False)
    page = main_window.dashboard_page
    trending = page.row("trending")
    qtbot.waitUntil(lambda: trending.states.currentWidget() is trending.error, timeout=4000)
    _wait_row_content(page, "popular", qtbot)
    _wait_row_content(page, "recent", qtbot)
    _wait_row_content(page, "continue", qtbot)
    assert "internet" in trending.error.message_label.text().lower()
    assert page.row("popular").cards
    assert page.row("recent").cards

    movie_service.fail_methods.clear()
    qtbot.mouseClick(trending.error.retry_button, Qt.MouseButton.LeftButton)
    _wait_row_content(page, "trending", qtbot)
    assert page.row("trending").cards


def test_dashboard_stays_responsive_during_load(
    main_window: MainWindow,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    movie_service.delay = 0.2
    clicks: list[int] = []
    ping = QPushButton("Ping")
    ping.clicked.connect(lambda: clicks.append(1))
    qtbot.addWidget(ping)
    ping.show()

    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    page = main_window.dashboard_page
    assert page.row("trending").states.currentWidget() is page.row("trending").loading
    qtbot.wait(40)
    qtbot.mouseClick(ping, Qt.MouseButton.LeftButton)
    _wait_public_rows(page, qtbot)

    assert clicks == [1]
    QThreadPool.globalInstance().waitForDone(2000)


def test_dashboard_search_and_profile_shortcuts(
    main_window: MainWindow,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    _open_guest_dashboard(main_window, qtbot)
    page = main_window.dashboard_page

    page.search_bar.set_text("   ")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is page
    assert page.search_hint.isVisible()
    assert "title" in page.search_hint.text().lower()
    assert movie_service.search_calls == []

    page.search_bar.set_text("dune")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)
    discover = main_window.discover_page
    assert main_window.stack.currentWidget() is discover
    qtbot.waitUntil(lambda: ("dune", 1) in movie_service.search_calls, timeout=3000)

    main_window.navigate("home")
    qtbot.mouseClick(page.profile_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.profile_page


def test_continue_exploring_uses_watch_history(
    main_window: MainWindow,
    auth_service: AuthService,
    db_session: Session,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    _sign_in_with_preferences(main_window, auth_service, db_session, qtbot, UserPreferences())
    page = main_window.dashboard_page
    _wait_public_rows(page, qtbot)

    user = main_window.app_state.current_user
    assert user is not None
    inception = next(movie for movie in movie_service.movies if movie.title == "Inception")
    main_window.history_service.mark_watched(user.id, inception)

    main_window.navigate("discover")
    main_window.navigate("home")
    _wait_row_content(page, "continue", qtbot)
    assert inception.tmdb_id in movie_service.similar_calls
    assert page.row("continue").cards
