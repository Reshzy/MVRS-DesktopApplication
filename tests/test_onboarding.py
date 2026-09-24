from __future__ import annotations

from PySide6.QtCore import Qt

from app.schemas.user_schema import GenrePreference, MoviePreference, UserPreferences
from app.services.user_service import UserService
from app.ui.app_window import MainWindow
from tests.fakes import FakeMovieService


def _register(main_window: MainWindow, qtbot, email: str = "ada@example.com") -> None:
    qtbot.mouseClick(main_window.welcome_page.register_button, Qt.MouseButton.LeftButton)
    main_window.register_page.name_input.setText("Ada Lovelace")
    main_window.register_page.email_input.setText(email)
    main_window.register_page.password_field.set_text("password123")
    main_window.register_page.confirm_field.set_text("password123")
    qtbot.mouseClick(main_window.register_page.submit_button, Qt.MouseButton.LeftButton)


def _login(main_window: MainWindow, qtbot, email: str = "ada@example.com") -> None:
    qtbot.mouseClick(main_window.welcome_page.login_button, Qt.MouseButton.LeftButton)
    main_window.login_page.email_input.setText(email)
    main_window.login_page.password_field.set_text("password123")
    qtbot.mouseClick(main_window.login_page.submit_button, Qt.MouseButton.LeftButton)


def test_onboarding_saves_preferences_and_later_login_skips_it(
    main_window: MainWindow,
    movie_service: FakeMovieService,
    qtbot,
) -> None:
    _register(main_window, qtbot)
    page = main_window.onboarding_page
    assert main_window.stack.currentWidget() is page
    assert not main_window.sidebar.isVisible()

    qtbot.waitUntil(lambda: page.genre_button(18) is not None, timeout=3000)
    drama = page.genre_button(18)
    assert drama is not None
    qtbot.mouseClick(drama, Qt.MouseButton.LeftButton)
    assert drama.isChecked()
    assert drama.property("selected") == "true"

    before = len(movie_service.search_calls)
    page.search_bar.set_text("   ")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)
    assert len(movie_service.search_calls) == before
    assert page.search_hint.isVisible()
    assert "title" in page.search_hint.text().lower()

    page.search_bar.set_text("fight")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page.movie_result_button(1001) is not None, timeout=3000)
    result = page.movie_result_button(1001)
    assert result is not None
    qtbot.mouseClick(result, Qt.MouseButton.LeftButton)
    assert page.selected_movie_button(1001) is not None
    assert movie_service.search_calls[-1][0] == "fight"

    page.language_combo.setCurrentIndex(page.language_combo.findData("en"))
    page.period_combo.setCurrentIndex(page.period_combo.findData("2010s"))
    page.rating_combo.setCurrentIndex(page.rating_combo.findData(7.0))
    page.interest_input.setText("mind-bending")
    qtbot.mouseClick(page.interest_add_button, Qt.MouseButton.LeftButton)
    assert page.interest_button("mind-bending") is not None

    qtbot.mouseClick(page.continue_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.dashboard_page
    user = main_window.app_state.current_user
    assert user is not None
    assert user.onboarding_completed is True

    preferences = main_window.user_service.get_preferences(user.id)
    assert [genre.name for genre in preferences.favorite_genres] == ["Drama"]
    assert preferences.favorite_movies[0].title == "Fight Club"
    assert preferences.preferred_language == "en"
    assert preferences.release_period == "2010s"
    assert preferences.minimum_rating == 7.0
    assert preferences.interests == ["mind-bending"]

    qtbot.mouseClick(main_window.sidebar.logout_button, Qt.MouseButton.LeftButton)
    _login(main_window, qtbot)
    assert main_window.stack.currentWidget() is main_window.dashboard_page


def test_genre_load_failure_can_retry(main_window: MainWindow, movie_service: FakeMovieService, qtbot) -> None:
    movie_service.fail = True
    _register(main_window, qtbot, email="grace@example.com")
    page = main_window.onboarding_page

    qtbot.waitUntil(lambda: page.genre_retry.isVisible(), timeout=3000)
    assert "internet" in page.genre_status.text().lower()

    movie_service.fail = False
    qtbot.mouseClick(page.genre_retry, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page.genre_button(28) is not None, timeout=3000)
    assert not page.genre_retry.isVisible()


def test_profile_can_edit_saved_preferences(
    main_window: MainWindow,
    auth_service,
    db_session,
    qtbot,
) -> None:
    user = auth_service.register(
        name="Ada Lovelace",
        email="ada@example.com",
        password="password123",
        confirm_password="password123",
    )
    UserService(db_session).save_preferences(
        user.id,
        UserPreferences(
            favorite_genres=[GenrePreference(tmdb_genre_id=18, name="Drama")],
            favorite_movies=[MoviePreference(tmdb_id=550, title="Fight Club")],
            preferred_language="ja",
            release_period="1990s",
            minimum_rating=8,
            interests=["noir"],
        ),
    )
    main_window.app_state.clear_current_user()

    _login(main_window, qtbot)
    assert main_window.stack.currentWidget() is main_window.dashboard_page

    qtbot.mouseClick(main_window.sidebar.button("profile"), Qt.MouseButton.LeftButton)
    profile = main_window.profile_page
    assert "Drama" in profile.summary_label.text()
    assert "Fight Club" in profile.summary_label.text()

    qtbot.mouseClick(profile.edit_button, Qt.MouseButton.LeftButton)
    page = main_window.onboarding_page
    assert main_window.stack.currentWidget() is page
    assert page.cancel_button.isVisible()
    qtbot.waitUntil(lambda: page.genre_button(18) is not None and page.genre_button(18).isChecked(), timeout=3000)

    qtbot.mouseClick(page.cancel_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is profile
    assert "Drama" in profile.summary_label.text()

    qtbot.mouseClick(profile.edit_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page.genre_button(18) is not None and page.genre_button(18).isChecked(), timeout=3000)
    drama = page.genre_button(18)
    action = page.genre_button(28)
    assert drama is not None and action is not None
    qtbot.mouseClick(drama, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(action, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(page.continue_button, Qt.MouseButton.LeftButton)

    assert main_window.stack.currentWidget() is profile
    assert "Action" in profile.summary_label.text()
    assert "Drama" not in profile.summary_label.text()
    loaded = main_window.user_service.get_preferences(user.id)
    assert [genre.name for genre in loaded.favorite_genres] == ["Action"]
    assert loaded.preferred_language == "ja"
    assert loaded.favorite_movies[0].title == "Fight Club"
