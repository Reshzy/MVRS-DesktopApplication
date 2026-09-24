from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QDialog

from app.models.interaction import Interaction
from app.models.rating import Rating
from app.models.user import User
from app.models.watch_history import WatchHistory
from app.models.watchlist import Watchlist
from app.ui.app_window import MainWindow
from app.ui.dialogs.sign_in_dialog import SignInDialog
from app.utils.constants import LIKE
from tests.fakes import FakeMovieService, sample_movie
from tests.test_auth import VALID_REGISTER


def _enter_guest(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    assert main_window.app_state.guest_mode is True
    assert main_window.app_state.current_user is None


def _user_count(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(User)) or 0)


def _persisted_counts(session: Session) -> tuple[int, int, int, int]:
    return (
        int(session.scalar(select(func.count()).select_from(Watchlist)) or 0),
        int(session.scalar(select(func.count()).select_from(WatchHistory)) or 0),
        int(session.scalar(select(func.count()).select_from(Rating)) or 0),
        int(session.scalar(select(func.count()).select_from(Interaction)) or 0),
    )


def _open_guest_details(main_window: MainWindow, qtbot):
    _enter_guest(main_window, qtbot)
    main_window.show_movie_details(sample_movie(1, "Fight Club"))
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=5000)
    return details


def test_guest_browse_does_not_create_account(main_window: MainWindow, db_session: Session, qtbot) -> None:
    _enter_guest(main_window, qtbot)

    assert main_window.app_state.is_authenticated is False
    assert main_window.stack.currentWidget() is main_window.dashboard_page
    assert main_window.topbar.greeting_label.text() == "Guest"
    assert main_window.sidebar.logout_button.text() == "Exit"
    assert _user_count(db_session) == 0


def test_guest_can_search_filter_and_open_details(
    main_window: MainWindow, movie_service: FakeMovieService, qtbot
) -> None:
    _enter_guest(main_window, qtbot)
    QThreadPool.globalInstance().waitForDone(4000)
    qtbot.mouseClick(main_window.sidebar.button("discover"), Qt.MouseButton.LeftButton)
    page = main_window.discover_page
    qtbot.waitUntil(lambda: page.states.currentWidget() is page.scroll, timeout=5000)

    page.search_bar.set_text("inception")
    qtbot.mouseClick(page.search_bar.button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: bool(movie_service.search_calls) and movie_service.search_calls[-1] == ("inception", 1),
        timeout=5000,
    )
    qtbot.waitUntil(lambda: bool(page.cards), timeout=5000)

    qtbot.waitUntil(lambda: page.filters.genre_combo.count() > 1, timeout=5000)
    page.filters.genre_combo.setCurrentIndex(page.filters.genre_combo.findData(28))
    before = len(movie_service.discover_calls)
    qtbot.mouseClick(page.filters.apply_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: len(movie_service.discover_calls) > before, timeout=5000)
    assert movie_service.discover_calls[-1].with_genres == "28"

    qtbot.mouseClick(page.cards[0], Qt.MouseButton.LeftButton)
    details = main_window.movie_details_page
    qtbot.waitUntil(lambda: details.states.currentWidget() is details.content, timeout=5000)
    assert main_window.stack.currentWidget() is details
    assert "sign in" in details.status_label.text().lower()
    assert main_window.app_state.guest_mode is True


def test_guest_protected_actions_do_not_persist(
    main_window: MainWindow, db_session: Session, qtbot
) -> None:
    details = _open_guest_details(main_window, qtbot)

    qtbot.mouseClick(details.watchlist_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(details.watched_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(details.like_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(details.star_buttons[3], Qt.MouseButton.LeftButton)

    assert main_window.stack.currentWidget() is details
    assert main_window.app_state.current_user is None
    assert details.watchlist_button.text() == "Add to Watchlist"
    assert _user_count(db_session) == 0
    assert _persisted_counts(db_session) == (0, 0, 0, 0)
    if main_window.watchlist_service is not None:
        assert main_window.watchlist_service.list_entries(1) == []
    if main_window.interaction_service is not None:
        assert main_window.interaction_service.has(1, 1001, LIKE) is False


def test_guest_can_cancel_sign_in_prompt_and_keep_browsing(
    main_window: MainWindow, qtbot
) -> None:
    details = _open_guest_details(main_window, qtbot)
    prompts: list[str] = []

    def _cancel(**kwargs) -> bool:
        prompts.append(str(kwargs.get("title", "")))
        return False

    main_window._prompt_sign_in = _cancel
    qtbot.mouseClick(details.watchlist_button, Qt.MouseButton.LeftButton)

    assert prompts
    assert main_window.stack.currentWidget() is details
    assert main_window.app_state.guest_mode is True
    assert main_window.app_state.current_user is None


def test_guest_sign_in_prompt_opens_login_and_back_returns(
    qtbot, themed_app, auth_service, app_state, movie_service: FakeMovieService
) -> None:
    window = MainWindow(
        auth_service=auth_service,
        app_state=app_state,
        confirm_logout=lambda **_kwargs: True,
        prompt_sign_in=lambda **_kwargs: True,
        movie_service=movie_service,
    )
    qtbot.addWidget(window)
    window.show()

    details = _open_guest_details(window, qtbot)
    qtbot.mouseClick(details.watchlist_button, Qt.MouseButton.LeftButton)

    assert window.stack.currentWidget() is window.login_page
    assert window.app_state.guest_mode is True
    assert window.app_state.auth_return_page == "movie_details"

    qtbot.mouseClick(window.login_page.back_link, Qt.MouseButton.LeftButton)
    assert window.stack.currentWidget() is window.movie_details_page
    assert window.app_state.guest_mode is True
    assert window.app_state.current_user is None
    window.close()


def test_guest_page_sign_in_buttons_open_login(main_window: MainWindow, qtbot) -> None:
    _enter_guest(main_window, qtbot)

    qtbot.mouseClick(main_window.sidebar.button("watchlist"), Qt.MouseButton.LeftButton)
    assert main_window.watchlist_page.empty.action_button.isVisible()
    qtbot.mouseClick(main_window.watchlist_page.empty.action_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.login_page

    qtbot.mouseClick(main_window.login_page.back_link, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.watchlist_page

    qtbot.mouseClick(main_window.sidebar.button("recommendations"), Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.recommendations_page.guest.action_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.login_page

    qtbot.mouseClick(main_window.login_page.back_link, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.sidebar.button("insights"), Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.insights_page.guest.action_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.login_page

    qtbot.mouseClick(main_window.login_page.back_link, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.sidebar.button("profile"), Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.profile_page.sign_in_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.login_page


def test_guest_cannot_load_personalized_recommendations(main_window: MainWindow, qtbot) -> None:
    _enter_guest(main_window, qtbot)
    qtbot.mouseClick(main_window.sidebar.button("recommendations"), Qt.MouseButton.LeftButton)

    page = main_window.recommendations_page
    assert page.states.currentWidget() is page.guest
    assert page.cards == []
    assert "sign in" in page.status_label.text().lower()


def test_sign_in_dialog_accepts_and_cancels(qtbot, themed_app) -> None:
    accepted = SignInDialog()
    qtbot.addWidget(accepted)
    accepted.show()
    qtbot.mouseClick(accepted.sign_in_button, Qt.MouseButton.LeftButton)
    assert accepted.result() == QDialog.DialogCode.Accepted

    canceled = SignInDialog()
    qtbot.addWidget(canceled)
    canceled.show()
    qtbot.mouseClick(canceled.cancel_button, Qt.MouseButton.LeftButton)
    assert canceled.result() == QDialog.DialogCode.Rejected


def test_guest_login_clears_guest_mode(main_window: MainWindow, auth_service, db_session, qtbot) -> None:
    user = auth_service.register(**VALID_REGISTER)
    user.onboarding_completed = True
    db_session.commit()
    main_window.app_state.clear_current_user()

    _enter_guest(main_window, qtbot)
    qtbot.mouseClick(main_window.sidebar.button("profile"), Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.profile_page.sign_in_button, Qt.MouseButton.LeftButton)

    main_window.login_page.email_input.setText("ada@example.com")
    main_window.login_page.password_field.set_text("password123")
    qtbot.mouseClick(main_window.login_page.submit_button, Qt.MouseButton.LeftButton)

    assert main_window.app_state.guest_mode is False
    assert main_window.app_state.is_authenticated is True
    assert main_window.stack.currentWidget() is main_window.dashboard_page
    assert main_window.sidebar.logout_button.text() == "Logout"
