from PySide6.QtCore import Qt

from app.ui.app_window import MainWindow


def test_welcome_navigates_to_login(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.login_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.login_page


def test_welcome_navigates_to_register(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.register_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.register_page


def test_login_register_and_back_navigation(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.login_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.login_page.register_link, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.register_page

    qtbot.mouseClick(main_window.register_page.login_link, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.login_page


def test_guest_browse_opens_dashboard(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.dashboard_page
    assert main_window.app_state.current_user is None


def test_invalid_login_shows_error(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.login_button, Qt.MouseButton.LeftButton)
    main_window.login_page.email_input.setText("nobody@example.com")
    main_window.login_page.password_field.set_text("password123")
    qtbot.mouseClick(main_window.login_page.submit_button, Qt.MouseButton.LeftButton)

    assert main_window.stack.currentWidget() is main_window.login_page
    assert main_window.login_page.error_label.isVisible()
    assert main_window.login_page.error_label.text()


def test_successful_register_opens_onboarding(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.register_button, Qt.MouseButton.LeftButton)
    main_window.register_page.name_input.setText("Ada Lovelace")
    main_window.register_page.email_input.setText("ada@example.com")
    main_window.register_page.password_field.set_text("password123")
    main_window.register_page.confirm_field.set_text("password123")
    qtbot.mouseClick(main_window.register_page.submit_button, Qt.MouseButton.LeftButton)

    assert main_window.stack.currentWidget() is main_window.onboarding_page
    assert main_window.app_state.current_user is not None
    assert main_window.app_state.current_user.email == "ada@example.com"


def test_successful_login_opens_dashboard(main_window: MainWindow, auth_service, qtbot) -> None:
    auth_service.register(
        name="Ada Lovelace",
        email="ada@example.com",
        password="password123",
        confirm_password="password123",
    )
    main_window.app_state.clear_current_user()

    qtbot.mouseClick(main_window.welcome_page.login_button, Qt.MouseButton.LeftButton)
    main_window.login_page.email_input.setText("ada@example.com")
    main_window.login_page.password_field.set_text("password123")
    qtbot.mouseClick(main_window.login_page.submit_button, Qt.MouseButton.LeftButton)

    assert main_window.stack.currentWidget() is main_window.dashboard_page
    assert main_window.app_state.current_user is not None
    assert main_window.app_state.current_user.email == "ada@example.com"


def test_guest_shell_sidebar_navigation(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    assert main_window.sidebar.isVisible()
    assert main_window.topbar.isVisible()
    assert main_window.sidebar.current_id() == "home"

    qtbot.mouseClick(main_window.sidebar.button("discover"), Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.discover_page
    assert main_window.sidebar.current_id() == "discover"

    qtbot.mouseClick(main_window.sidebar.button("profile"), Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.profile_page
    assert main_window.current_page_id() == "profile"


def test_topbar_profile_and_search_shortcuts(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.topbar.profile_button, Qt.MouseButton.LeftButton)
    assert main_window.stack.currentWidget() is main_window.profile_page

    main_window.topbar.search_input.setText("dune")
    qtbot.keyClick(main_window.topbar.search_input, Qt.Key.Key_Return)
    assert main_window.stack.currentWidget() is main_window.discover_page


def test_logout_clears_state_and_returns_to_welcome(main_window: MainWindow, qtbot) -> None:
    qtbot.mouseClick(main_window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(main_window.sidebar.logout_button, Qt.MouseButton.LeftButton)

    assert main_window.stack.currentWidget() is main_window.welcome_page
    assert main_window.app_state.current_user is None
    assert not main_window.sidebar.isVisible()
    assert not main_window.topbar.isVisible()


def test_logout_cancel_keeps_current_page(qtbot, themed_app, auth_service, app_state) -> None:
    window = MainWindow(
        auth_service=auth_service,
        app_state=app_state,
        confirm_logout=lambda **_kwargs: False,
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.mouseClick(window.welcome_page.guest_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.sidebar.logout_button, Qt.MouseButton.LeftButton)

    assert window.stack.currentWidget() is window.dashboard_page
    assert window.sidebar.isVisible()
