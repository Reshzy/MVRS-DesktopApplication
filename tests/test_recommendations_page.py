from __future__ import annotations

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QPushButton
from sqlalchemy.orm import Session

from app.schemas.user_schema import GenrePreference, UserPreferences
from app.services.auth_service import AuthService
from app.services.interaction_service import InteractionService
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


def _open_recommendations(main_window: MainWindow, qtbot, *, wait_for_cards: bool = True) -> None:
    qtbot.mouseClick(main_window.sidebar.button("recommendations"), Qt.MouseButton.LeftButton)
    page = main_window.recommendations_page
    if wait_for_cards:
        qtbot.waitUntil(lambda: page.states.currentWidget() is not page.loading, timeout=4000)


def test_guest_sees_sign_in_prompt(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    _open_recommendations(main_window, qtbot, wait_for_cards=False)
    page = main_window.recommendations_page
    assert page.states.currentWidget() is page.guest
    assert "sign in" in page.guest.title_label.text().lower()
    assert movie_service.popular_calls == []
    assert page.cards == []


def test_page_shows_cards_reasons_and_opens_details(
    main_window: MainWindow,
    auth_service: AuthService,
    db_session: Session,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    _sign_in_with_preferences(
        main_window,
        auth_service,
        db_session,
        qtbot,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=28, name="Action")]),
    )
    _open_recommendations(main_window, qtbot)
    page = main_window.recommendations_page
    assert page.states.currentWidget() is page.scroll
    assert [card.movie.title for card in page.cards][0] == "Inception"
    assert page.tiles
    assert page.tiles[0].reason_label.text()
    assert all("cosine" not in tile.reason_label.text().lower() for tile in page.tiles)

    qtbot.mouseClick(page.cards[0], Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)
    assert main_window.stack.currentWidget() is details
    assert details.title_label.text() == "Inception"


def test_refresh_reloads_in_background(
    main_window: MainWindow,
    auth_service: AuthService,
    db_session: Session,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    _sign_in_with_preferences(
        main_window,
        auth_service,
        db_session,
        qtbot,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=18, name="Drama")]),
    )
    _open_recommendations(main_window, qtbot)
    page = main_window.recommendations_page
    before = len(movie_service.popular_calls)
    movie_service.delay = 0.2

    clicks: list[int] = []
    ping = QPushButton("Ping")
    ping.clicked.connect(lambda: clicks.append(1))
    qtbot.addWidget(ping)
    ping.show()

    qtbot.mouseClick(page.refresh_button, Qt.MouseButton.LeftButton)
    assert page.states.currentWidget() is page.loading
    qtbot.wait(40)
    qtbot.mouseClick(ping, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page.states.currentWidget() is page.scroll, timeout=4000)

    assert clicks == [1]
    assert len(movie_service.popular_calls) > before
    QThreadPool.globalInstance().waitForDone(2000)


def test_recommendations_update_after_like(
    main_window: MainWindow,
    auth_service: AuthService,
    db_session: Session,
    qtbot,
) -> None:
    _sign_in_with_preferences(main_window, auth_service, db_session, qtbot, UserPreferences())
    _open_recommendations(main_window, qtbot)
    page = main_window.recommendations_page
    assert page.cards[0].movie.title == "Inception"

    fight_club = next(card for card in page.cards if card.movie.title == "Fight Club")
    qtbot.mouseClick(fight_club, Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)
    qtbot.mouseClick(details.like_button, Qt.MouseButton.LeftButton)
    assert InteractionService(db_session).has(main_window.app_state.current_user.id, 1001, "like")

    qtbot.mouseClick(details.back_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: main_window.stack.currentWidget() is page, timeout=3000)
    qtbot.waitUntil(lambda: page.states.currentWidget() is page.scroll, timeout=4000)
    assert page.cards[0].movie.title == "Fight Club"


def test_error_state_can_retry(
    main_window: MainWindow,
    auth_service: AuthService,
    db_session: Session,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    _sign_in_with_preferences(main_window, auth_service, db_session, qtbot, UserPreferences())
    movie_service.fail = True
    _open_recommendations(main_window, qtbot)
    page = main_window.recommendations_page
    assert page.states.currentWidget() is page.error
    assert "connection" in page.error.message_label.text().lower()

    movie_service.fail = False
    qtbot.mouseClick(page.error.retry_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page.states.currentWidget() is page.scroll, timeout=4000)
    assert page.cards
