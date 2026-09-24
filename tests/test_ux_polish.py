from datetime import date

from PySide6.QtCore import QSize, Qt

from app.schemas.movie_schema import MovieSummaryDTO
from app.ui.app_window import MainWindow
from app.ui.dialogs.confirm_dialog import ConfirmDialog
from app.ui.theme import load_stylesheet
from app.ui.theme.icons import make_icon
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.loading_widget import LoadingWidget
from app.ui.widgets.movie_card import MovieCard
from app.ui.widgets.topbar import TopBar


def test_icons_are_consistent_and_non_null(themed_app) -> None:
    for name in ("home", "discover", "watchlist", "profile", "search", "error", "empty"):
        icon = make_icon(name)
        assert not icon.isNull()
        assert not icon.pixmap(QSize(16, 16)).isNull()


def test_stylesheet_includes_focus_and_loading_polish() -> None:
    stylesheet = load_stylesheet()
    assert "QPushButton:focus" in stylesheet
    assert 'QPushButton[variant="nav"]:checked' in stylesheet
    assert "QProgressBar#loadingProgress" in stylesheet
    assert "QFrame#movieCard:focus" in stylesheet


def test_sidebar_has_icons_tooltips_and_active_state(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    home = main_window.sidebar.button("home")
    discover = main_window.sidebar.button("discover")

    assert not home.icon().isNull()
    assert "Home" in home.toolTip()
    assert "Ctrl+1" in home.toolTip()
    assert home.isChecked()
    assert not discover.isChecked()

    qtbot.mouseClick(discover, Qt.MouseButton.LeftButton)
    assert discover.isChecked()
    assert "Discover" in discover.toolTip()
    assert not main_window.sidebar.logout_button.icon().isNull()


def test_topbar_search_button_and_tooltips(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    assert "Search" in main_window.topbar.search_input.toolTip()
    assert "profile" in main_window.topbar.profile_button.toolTip().lower()
    assert not main_window.topbar.profile_button.icon().isNull()

    main_window.topbar.search_input.setText("dune")
    qtbot.mouseClick(main_window.topbar.search_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.discover_page


def test_topbar_hides_greeting_when_narrow(qtbot, themed_app) -> None:
    bar = TopBar()
    qtbot.addWidget(bar)
    bar.resize(1100, 68)
    bar.show()
    qtbot.waitExposed(bar)
    assert bar.greeting_label.isVisible()
    assert bar.search_button.text() == "Search"

    bar.resize(640, 68)
    bar._apply_compact_layout(640)
    assert not bar.greeting_label.isVisible()
    assert bar.search_button.text() == ""


def test_movie_card_tooltip_and_keyboard(qtbot, themed_app) -> None:
    movie = MovieSummaryDTO(
        tmdb_id=42,
        title="Arrival",
        release_date=date(2016, 11, 11),
        vote_average=8.0,
    )
    card = MovieCard(movie)
    qtbot.addWidget(card)
    card.show()

    assert "Arrival" in card.toolTip()
    assert "2016" in card.toolTip()
    assert card.focusPolicy() == Qt.FocusPolicy.StrongFocus

    opened: list[int] = []
    card.clicked.connect(lambda item: opened.append(item.tmdb_id))
    card.setFocus()
    qtbot.keyClick(card, Qt.Key.Key_Return)
    assert opened == [42]


def test_loading_and_empty_states_have_visible_chrome(qtbot, themed_app) -> None:
    loading = LoadingWidget("Loading movies...")
    qtbot.addWidget(loading)
    loading.show()
    assert loading.progress.minimum() == 0
    assert loading.progress.maximum() == 0
    assert loading.icon_label.pixmap() is not None

    empty = EmptyState("Nothing here", "Try another search.")
    qtbot.addWidget(empty)
    empty.show()
    assert empty.icon_label.pixmap() is not None
    empty.set_content("Could not load", "Offline", retry=True)
    assert empty.retry_button.isVisible()
    assert empty.icon_label.pixmap() is not None


def test_confirm_dialog_defaults_cancel_for_danger(qtbot, themed_app) -> None:
    dialog = ConfirmDialog("Log out", "Leave this session?", confirm_label="Log out")
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.cancel_button.isDefault()
    assert dialog.confirm_button.toolTip() == "Log out"


def test_login_enter_submits(main_window: MainWindow, auth_service, db_session, qtbot) -> None:
    user = auth_service.register(
        name="Ada Lovelace",
        email="ada@example.com",
        password="password123",
        confirm_password="password123",
    )
    user.onboarding_completed = True
    db_session.commit()
    main_window.app_state.clear_current_user()

    qtbot.mouseClick(main_window.welcome_page.login_button, Qt.MouseButton.LeftButton)
    main_window.login_page.email_input.setText("ada@example.com")
    main_window.login_page.password_field.set_text("password123")
    main_window.login_page.password_field.edit.setFocus()
    qtbot.keyClick(main_window.login_page.password_field.edit, Qt.Key.Key_Return)

    assert main_window.stack.currentWidget() is main_window.dashboard_page


def test_shell_shortcuts_navigate_and_focus_search(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    assert "home" in main_window._nav_shortcuts
    main_window._shortcut_navigate("discover")
    assert main_window.stack.currentWidget() is main_window.discover_page
    main_window._focus_search()
    assert main_window.topbar.search_input.hasFocus()


def test_movie_details_escape_goes_back(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    main_window.navigate("discover")
    movie = MovieSummaryDTO(tmdb_id=7, title="Heat", release_date=date(1995, 12, 15), vote_average=8.3)
    main_window.show_movie_details(movie)
    assert main_window.stack.currentWidget() is main_window.movie_details_page
    assert "Esc" in main_window.movie_details_page.back_button.toolTip()
    main_window.movie_details_page.go_back()
    assert main_window.stack.currentWidget() is main_window.discover_page


def test_welcome_and_filter_tooltips(main_window: MainWindow) -> None:
    assert main_window.welcome_page.login_button.toolTip()
    assert main_window.welcome_page.guest_button.toolTip()
    assert main_window.discover_page.filters.genre_combo.toolTip()
    assert main_window.discover_page.filters.apply_button.toolTip()
