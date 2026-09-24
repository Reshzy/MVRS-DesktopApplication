from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.auth_service import AuthService
from app.services.history_service import HistoryService
from app.services.interaction_service import InteractionService
from app.services.movie_service import MovieService
from app.services.rating_service import RatingService
from app.services.user_service import UserService
from app.services.watchlist_service import WatchlistService
from app.state.app_state import AppState
from app.ui.dialogs.confirm_dialog import ConfirmDialog
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.discover_page import DiscoverPage
from app.ui.pages.history_page import HistoryPage
from app.ui.pages.insights_page import InsightsPage
from app.ui.pages.login_page import LoginPage
from app.ui.pages.movie_details_page import MovieDetailsPage
from app.ui.pages.onboarding_page import OnboardingPage
from app.ui.pages.profile_page import ProfilePage
from app.ui.pages.recommendations_page import RecommendationsPage
from app.ui.pages.register_page import RegisterPage
from app.ui.pages.watchlist_page import WatchlistPage
from app.ui.pages.welcome_page import WelcomePage
from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.topbar import TopBar
from app.ui.workers.image_worker import ImageLoader

ConfirmFn = Callable[..., bool]

SHELL_PAGES = frozenset(
    {
        "home",
        "discover",
        "recommendations",
        "watchlist",
        "history",
        "insights",
        "profile",
        "movie_details",
    }
)
SIDEBAR_PAGES = SHELL_PAGES - {"movie_details"}
PAGE_TITLES = {
    "welcome": "Welcome",
    "login": "Login",
    "register": "Register",
    "onboarding": "Onboarding",
    "home": "Home",
    "discover": "Discover",
    "recommendations": "Recommendations",
    "watchlist": "Watchlist",
    "history": "History",
    "insights": "Insights",
    "profile": "Profile",
    "movie_details": "Movie Details",
}


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        auth_service: AuthService | None = None,
        app_state: AppState | None = None,
        confirm_logout: ConfirmFn | None = None,
        movie_service: MovieService | None = None,
        session: Session | None = None,
        watchlist_service: WatchlistService | None = None,
        history_service: HistoryService | None = None,
        rating_service: RatingService | None = None,
        interaction_service: InteractionService | None = None,
        user_service: UserService | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("Movie Recommendation System")
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)

        self.app_state = app_state or AppState()
        self._confirm_logout = confirm_logout or ConfirmDialog.ask
        self._owned_session = None
        if auth_service is None:
            self._owned_session = SessionLocal()
            session = self._owned_session
            self.auth_service = AuthService(session, self.app_state)
            self.movie_service = movie_service or MovieService(session=session)
        else:
            self.auth_service = auth_service
            self.movie_service = movie_service or MovieService(cache_enabled=False)
            if session is None:
                session = getattr(auth_service, "_session", None)

        self.watchlist_service = watchlist_service or (WatchlistService(session) if session is not None else None)
        self.history_service = history_service or (HistoryService(session) if session is not None else None)
        self.rating_service = rating_service or (RatingService(session) if session is not None else None)
        self.interaction_service = interaction_service or (
            InteractionService(session) if session is not None else None
        )
        self.user_service = user_service or (UserService(session) if session is not None else None)

        self.image_loader = ImageLoader(self)
        self.sidebar = Sidebar(self)
        self.topbar = TopBar(self)
        self.stack = QStackedWidget(self)
        self._pages: dict[str, QWidget] = {}
        self._page_ids: dict[QWidget, str] = {}

        self.welcome_page = WelcomePage(self)
        self.login_page = LoginPage(self.auth_service, self)
        self.register_page = RegisterPage(self.auth_service, self)
        self.onboarding_page = OnboardingPage(self.user_service, self.movie_service, self)
        self.dashboard_page = DashboardPage(self)
        self.discover_page = DiscoverPage(self.movie_service, self.image_loader, self)
        self.movie_details_page = MovieDetailsPage(
            self.movie_service,
            self.image_loader,
            self.watchlist_service,
            self.history_service,
            self.rating_service,
            self.interaction_service,
            self,
        )
        self.recommendations_page = RecommendationsPage(self)
        self.watchlist_page = WatchlistPage(
            self.watchlist_service,
            self.history_service,
            self.image_loader,
            self,
        )
        self.history_page = HistoryPage(self.history_service, self.image_loader, self)
        self.insights_page = InsightsPage(self)
        self.profile_page = ProfilePage(self.user_service, self)

        self._register_page("welcome", self.welcome_page)
        self._register_page("login", self.login_page)
        self._register_page("register", self.register_page)
        self._register_page("onboarding", self.onboarding_page)
        self._register_page("home", self.dashboard_page)
        self._register_page("discover", self.discover_page)
        self._register_page("movie_details", self.movie_details_page)
        self._register_page("recommendations", self.recommendations_page)
        self._register_page("watchlist", self.watchlist_page)
        self._register_page("history", self.history_page)
        self._register_page("insights", self.insights_page)
        self._register_page("profile", self.profile_page)

        right = QWidget(self)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.topbar)
        right_layout.addWidget(self.stack, 1)

        shell = QWidget(self)
        shell.setObjectName("appShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self.sidebar)
        shell_layout.addWidget(right, 1)
        self.setCentralWidget(shell)

        self.welcome_page.login_requested.connect(self.show_login)
        self.welcome_page.register_requested.connect(self.show_register)
        self.welcome_page.guest_requested.connect(self.show_guest_dashboard)
        self.login_page.login_succeeded.connect(self.show_authenticated_home)
        self.login_page.register_requested.connect(self.show_register)
        self.login_page.back_requested.connect(self.show_welcome)
        self.register_page.register_succeeded.connect(self.show_onboarding)
        self.onboarding_page.completed.connect(self._finish_onboarding)
        self.onboarding_page.cancelled.connect(self.show_profile)
        self.profile_page.edit_preferences_requested.connect(self.show_onboarding)
        self.register_page.login_requested.connect(self.show_login)
        self.sidebar.navigate_requested.connect(self.navigate)
        self.sidebar.logout_requested.connect(self.logout)
        self.topbar.profile_requested.connect(lambda: self.navigate("profile"))
        self.topbar.search_requested.connect(self.search_from_topbar)
        self.discover_page.movie_selected.connect(self.show_movie_details)
        self.watchlist_page.movie_selected.connect(self.show_movie_details)
        self.history_page.movie_selected.connect(self.show_movie_details)
        self.movie_details_page.back_requested.connect(self.return_from_details)

        self.show_welcome()

    def navigate(self, page_id: str) -> None:
        page = self._pages[page_id]
        if page_id == "login":
            self.login_page.reset()
        elif page_id == "register":
            self.register_page.reset()
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            refresh(self.app_state)
        self._show_page(page, page_id)

    def show_welcome(self) -> None:
        self.navigate("welcome")

    def show_login(self) -> None:
        self.navigate("login")

    def show_register(self) -> None:
        self.navigate("register")

    def show_onboarding(self) -> None:
        self.navigate("onboarding")

    def show_authenticated_home(self) -> None:
        user = self.app_state.current_user
        if user is not None and not user.onboarding_completed:
            self.show_onboarding()
            return
        self.show_dashboard()

    def show_dashboard(self) -> None:
        self.navigate("home")

    def show_profile(self) -> None:
        self.navigate("profile")

    def _finish_onboarding(self) -> None:
        if self.app_state.previous_page == "profile":
            self.show_profile()
            return
        self.show_dashboard()

    def show_guest_dashboard(self) -> None:
        self.app_state.clear_current_user()
        self.show_dashboard()

    def show_discover(self) -> None:
        self.navigate("discover")

    def search_from_topbar(self, query: str) -> None:
        self.app_state.active_filters["query"] = query
        self.show_discover()

    def show_movie_details(self, movie: object) -> None:
        self.app_state.selected_movie = movie
        self.navigate("movie_details")

    def return_from_details(self) -> None:
        previous = self.app_state.previous_page
        if previous in self._pages and previous != "movie_details":
            self.navigate(previous)
            return
        self.show_discover()

    def logout(self) -> None:
        confirmed = self._confirm_logout(
            parent=self,
            title="Log out",
            message="Log out and return to the welcome screen?",
            confirm_label="Log out",
        )
        if not confirmed:
            return
        self.app_state.clear_current_user()
        self.navigate("welcome")

    def current_page_id(self) -> str | None:
        return self._page_ids.get(self.stack.currentWidget())

    def _register_page(self, page_id: str, page: QWidget) -> None:
        self._pages[page_id] = page
        self._page_ids[page] = page_id
        self.stack.addWidget(page)

    def _show_page(self, page: QWidget, page_id: str) -> None:
        self.app_state.previous_page = self.current_page_id()
        self.stack.setCurrentWidget(page)
        in_shell = page_id in SHELL_PAGES
        self.sidebar.setVisible(in_shell)
        self.topbar.setVisible(in_shell)
        if in_shell:
            if page_id == "movie_details":
                previous = self.app_state.previous_page
                sidebar_id = previous if previous in SIDEBAR_PAGES else "discover"
            else:
                sidebar_id = page_id
            self.sidebar.set_current(sidebar_id)
            self.topbar.set_title(PAGE_TITLES[page_id])
            self.topbar.set_user(self.app_state.current_user)
        title = PAGE_TITLES.get(page_id, page_id.title())
        self.setWindowTitle(f"Movie Recommendation System — {title}")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.image_loader.close()
        self.movie_service.close()
        if self._owned_session is not None:
            self._owned_session.close()
        super().closeEvent(event)
