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
