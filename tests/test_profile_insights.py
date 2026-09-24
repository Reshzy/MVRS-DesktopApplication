from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

from app.schemas.user_schema import GenrePreference, UserPreferences
from app.services.history_service import HistoryService
from app.services.rating_service import RatingService
from app.services.user_service import UserService
from app.services.watchlist_service import WatchlistService
from app.ui.app_window import MainWindow
from app.ui.theme import theme_tokens
from app.utils.constants import THEME_LIGHT
from tests.test_auth import VALID_REGISTER
from tests.test_movies import FULL_DETAILS


def _sign_in(main_window: MainWindow, auth_service):
    user = auth_service.register(**VALID_REGISTER)
    user.onboarding_completed = True
    main_window.show_dashboard()
    return user


def test_guest_insights_prompts_sign_in(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.sidebar.button("insights"), Qt.MouseButton.LeftButton)

    page = main_window.insights_page
    assert main_window.stack.currentWidget() is page
    assert page.guest.isVisible()
    assert "sign in" in page.guest.title_label.text().lower()
    assert not page.scroll.isVisible()


def test_profile_edit_name_and_theme(main_window: MainWindow, auth_service, qtbot) -> None:
    user = _sign_in(main_window, auth_service)
    page = main_window.profile_page
    page._ask_name = lambda **_kwargs: "Ada Byron"

    qtbot.mouseClick(main_window.sidebar.button("profile"), Qt.MouseButton.LeftButton)
    assert page.name_label.text() == "Ada Lovelace"
    assert page.email_label.text() == "ada@example.com"
    assert page.edit_name_button.isVisible()
    assert page.theme_combo.isVisible()

    qtbot.mouseClick(page.edit_name_button, Qt.MouseButton.LeftButton)
    assert page.name_label.text() == "Ada Byron"
    assert main_window.app_state.current_user is not None
    assert main_window.app_state.current_user.name == "Ada Byron"
    assert "Ada Byron" in main_window.topbar.greeting_label.text()

    light_index = page.theme_combo.findData(THEME_LIGHT)
    page.theme_combo.setCurrentIndex(light_index)
    assert main_window.user_service is not None
    assert main_window.user_service.get_theme(user.id) == THEME_LIGHT
    assert main_window.app_state.theme == THEME_LIGHT
    assert theme_tokens(THEME_LIGHT)["BACKGROUND"] in QApplication.instance().styleSheet()


def test_insights_page_shows_counts_and_opens_details(
    main_window: MainWindow,
    auth_service,
    db_session,
    qtbot,
) -> None:
    user = _sign_in(main_window, auth_service)
    UserService(db_session).save_preferences(
        user.id,
        UserPreferences(favorite_genres=[GenrePreference(tmdb_genre_id=18, name="Drama")]),
    )
    HistoryService(db_session).mark_watched(user.id, FULL_DETAILS)
    WatchlistService(db_session).add(user.id, FULL_DETAILS)
    RatingService(db_session).set_rating(user.id, FULL_DETAILS, 5)

    qtbot.mouseClick(main_window.sidebar.button("insights"), Qt.MouseButton.LeftButton)
    page = main_window.insights_page
    assert main_window.stack.currentWidget() is page
    qtbot.waitUntil(lambda: page.scroll.isVisible(), timeout=3000)
    assert page.watched_value.text() == "1"
    assert page.watchlist_value.text() == "1"
    assert page.average_value.text() == "5.0"
    assert "Drama" in page.favorite_genres_label.text()
    assert page.most_watched_label.text() == "Drama"
    button = page.findChild(QPushButton, "insightsHighest0")
    assert button is not None
    assert "Fight Club" in button.text()

    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=3000)
    assert main_window.stack.currentWidget() is details
    assert main_window.sidebar.current_id() == "insights"
    assert details.title_label.text() == "Fight Club"
