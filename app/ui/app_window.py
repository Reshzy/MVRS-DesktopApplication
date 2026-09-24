from __future__ import annotations

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget

from app.database.session import SessionLocal
from app.services.auth_service import AuthService
from app.state.app_state import AppState
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.login_page import LoginPage
from app.ui.pages.onboarding_page import OnboardingPage
from app.ui.pages.register_page import RegisterPage
from app.ui.pages.welcome_page import WelcomePage


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        auth_service: AuthService | None = None,
        app_state: AppState | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("Movie Recommendation System")
        self.resize(1280, 800)

        self.app_state = app_state or AppState()
        self._owned_session = None
        if auth_service is None:
            self._owned_session = SessionLocal()
            self.auth_service = AuthService(self._owned_session, self.app_state)
        else:
            self.auth_service = auth_service

        self.stack = QStackedWidget(self)
        self.welcome_page = WelcomePage(self)
        self.login_page = LoginPage(self.auth_service, self)
        self.register_page = RegisterPage(self.auth_service, self)
        self.onboarding_page = OnboardingPage(self)
        self.dashboard_page = DashboardPage(self)

        self.stack.addWidget(self.welcome_page)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.register_page)
        self.stack.addWidget(self.onboarding_page)
        self.stack.addWidget(self.dashboard_page)
        self.setCentralWidget(self.stack)

        self.welcome_page.login_requested.connect(self.show_login)
        self.welcome_page.register_requested.connect(self.show_register)
        self.welcome_page.guest_requested.connect(self.show_guest_dashboard)
        self.login_page.login_succeeded.connect(self.show_dashboard)
        self.login_page.register_requested.connect(self.show_register)
        self.login_page.back_requested.connect(self.show_welcome)
        self.register_page.register_succeeded.connect(self.show_onboarding)
        self.register_page.login_requested.connect(self.show_login)

        self.show_welcome()

    def show_welcome(self) -> None:
        self._show_page(self.welcome_page, "welcome")

    def show_login(self) -> None:
        self.login_page.reset()
        self._show_page(self.login_page, "login")

    def show_register(self) -> None:
        self.register_page.reset()
        self._show_page(self.register_page, "register")

    def show_onboarding(self) -> None:
        self.onboarding_page.refresh(self.app_state)
        self._show_page(self.onboarding_page, "onboarding")

    def show_dashboard(self) -> None:
        self.dashboard_page.refresh(self.app_state)
        self._show_page(self.dashboard_page, "dashboard")

    def show_guest_dashboard(self) -> None:
        self.app_state.clear_current_user()
        self.show_dashboard()

    def _show_page(self, page: QWidget, name: str) -> None:
        self.app_state.previous_page = self._current_page_name()
        self.stack.setCurrentWidget(page)
        self.setWindowTitle(f"Movie Recommendation System — {name.title()}")

    def _current_page_name(self) -> str | None:
        current = self.stack.currentWidget()
        mapping = {
            self.welcome_page: "welcome",
            self.login_page: "login",
            self.register_page: "register",
            self.onboarding_page: "onboarding",
            self.dashboard_page: "dashboard",
        }
        return mapping.get(current)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._owned_session is not None:
            self._owned_session.close()
        super().closeEvent(event)
