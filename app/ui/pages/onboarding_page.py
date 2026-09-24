from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.schemas.movie_schema import GenreDTO, MoviePageDTO, MovieSummaryDTO
from app.schemas.user_schema import GenrePreference, MoviePreference, UserPreferences
from app.services.movie_service import MovieService
from app.services.user_service import UserService, UserServiceError
from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, MD, SM, XL
from app.ui.widgets.flow_layout import FlowLayout
from app.ui.widgets.search_bar import SearchBar
from app.ui.workers.task_runner import TaskRunner
from app.utils.constants import (
    LANGUAGE_NAMES,
    MAX_FAVORITE_MOVIES,
    MAX_INTEREST_LENGTH,
    MAX_INTERESTS,
    MINIMUM_RATINGS,
    RELEASE_PERIODS,
)
from app.utils.helpers import format_validation_error


@dataclass
class _AsyncResult:
    request_id: int
    value: object = None
    error: str | None = None


class _ChipWrap(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.flow = FlowLayout(self, spacing=SM)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self.fit()
        super().resizeEvent(event)

    def fit(self) -> None:
        if self.flow.count() == 0:
            self.setMinimumHeight(0)
            self.hide()
            return
        width = self.width() if self.width() > 120 else 680
        self.show()
        self.setMinimumHeight(self.flow.heightForWidth(width))


class OnboardingPage(QWidget):
    completed = Signal()
    cancelled = Signal()

    def __init__(
        self,
        user_service: UserService | None = None,
        movie_service: MovieService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("onboardingPage")
        self._user_service = user_service
        self._movie_service = movie_service
        self._runner = TaskRunner(self)
        self._user_id: int | None = None
        self._editing = False
        self._genre_request_id = 0
        self._search_request_id = 0
        self._genres: list[GenreDTO] = []
        self._genre_ids: dict[int, str] = {}
        self._movies: dict[int, str] = {}
        self._search_results: list[MovieSummaryDTO] = []
        self._interests: list[str] = []

        self.title = QLabel("Set your preferences")
        self.title.setObjectName("onboardingTitle")
        apply_property(self.title, "role", "title")

        self.subtitle = QLabel("Nothing here is required. You can change this later in Profile.")
        self.subtitle.setObjectName("onboardingSubtitle")
        apply_property(self.subtitle, "role", "subtitle")
        self.subtitle.setWordWrap(True)

        self.error_label = QLabel()
        self.error_label.setObjectName("onboardingError")
        apply_property(self.error_label, "role", "error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        genre_heading, genre_hint = self._section(
            "Favorite genres",
            "Pick any genres you usually enjoy.",
        )
        self.genre_status = QLabel("Loading genres...")
        self.genre_status.setObjectName("onboardingGenreStatus")
        apply_property(self.genre_status, "role", "caption")
        self.genre_status.setWordWrap(True)
        self.genre_retry = QPushButton("Retry")
        self.genre_retry.setObjectName("onboardingGenreRetry")
        apply_property(self.genre_retry, "variant", "secondary")
        self.genre_retry.clicked.connect(self._retry_genres)
        self.genre_retry.hide()
        genre_status_row = QHBoxLayout()
        genre_status_row.setContentsMargins(0, 0, 0, 0)
        genre_status_row.setSpacing(SM)
        genre_status_row.addWidget(self.genre_status, 1)
        genre_status_row.addWidget(self.genre_retry)
        self.genre_host = _ChipWrap()
        self.genre_host.setObjectName("onboardingGenreHost")
        self.genre_host.fit()

        movie_heading, movie_hint = self._section(
            "Favorite movies",
            "Search and select a few titles that represent your taste.",
        )
        self.search_bar = SearchBar(self)
        self.search_bar.input.setObjectName("onboardingMovieSearch")
        self.search_bar.input.setPlaceholderText("Search favorite movies")
        self.search_bar.button.setObjectName("onboardingMovieSearchButton")
        self.search_bar.search_requested.connect(self._on_search)
        self.search_bar.input.textChanged.connect(lambda _text: self.search_hint.hide())
        self.search_hint = QLabel()
        self.search_hint.setObjectName("onboardingSearchHint")
        apply_property(self.search_hint, "role", "error")
        self.search_hint.setWordWrap(True)
        self.search_hint.hide()
        self.results_host = QWidget()
        self.results_host.setObjectName("onboardingMovieResults")
        self.results_layout = QVBoxLayout(self.results_host)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(SM)
        self.results_host.hide()
        self.selected_host = _ChipWrap()
        self.selected_host.setObjectName("onboardingSelectedMovies")
        self.selected_host.fit()

        self.language_combo = self._combo("onboardingLanguage")
        self.language_combo.addItem("Any language", None)
        for code, label in sorted(LANGUAGE_NAMES.items(), key=lambda item: item[1]):
            self.language_combo.addItem(label, code)

        self.period_combo = self._combo("onboardingPeriod")
        self.period_combo.addItem("Any period", None)
        for value, label in RELEASE_PERIODS:
            self.period_combo.addItem(label, value)

        self.rating_combo = self._combo("onboardingRating")
        self.rating_combo.addItem("Any rating", None)
        for rating in MINIMUM_RATINGS:
            self.rating_combo.addItem(f"{rating:.0f}+", rating)

        options = QHBoxLayout()
        options.setSpacing(MD)
        options.addWidget(self._labeled("Preferred language", self.language_combo), 1)
        options.addWidget(self._labeled("Release period", self.period_combo), 1)
        options.addWidget(self._labeled("Minimum rating", self.rating_combo), 1)

        interest_heading, interest_hint = self._section(
            "Interests",
            "Optional themes, moods, or filmmakers.",
        )
        self.interest_input = QLineEdit()
        self.interest_input.setObjectName("onboardingInterestInput")
        self.interest_input.setPlaceholderText("Add an interest")
        self.interest_input.setMaxLength(MAX_INTEREST_LENGTH)
        self.interest_input.returnPressed.connect(self._add_interest)
        self.interest_add_button = QPushButton("Add")
        self.interest_add_button.setObjectName("onboardingInterestAdd")
        apply_property(self.interest_add_button, "variant", "secondary")
        self.interest_add_button.clicked.connect(self._add_interest)
        interest_row = QHBoxLayout()
        interest_row.setSpacing(MD)
        interest_row.addWidget(self.interest_input, 1)
        interest_row.addWidget(self.interest_add_button)
        self.interest_hint = QLabel()
        self.interest_hint.setObjectName("onboardingInterestHint")
        apply_property(self.interest_hint, "role", "caption")
        self.interest_hint.setWordWrap(True)
        self.interest_hint.hide()
        self.interest_host = _ChipWrap()
        self.interest_host.setObjectName("onboardingInterests")
        self.interest_host.fit()

        self.continue_button = QPushButton("Continue")
        self.continue_button.setObjectName("onboardingContinueButton")
        apply_property(self.continue_button, "variant", "primary")
        self.continue_button.clicked.connect(self._save)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("onboardingCancelButton")
        apply_property(self.cancel_button, "variant", "secondary")
        self.cancel_button.clicked.connect(self.cancelled.emit)
        self.cancel_button.hide()

        actions = QHBoxLayout()
        actions.setSpacing(MD)
        actions.addWidget(self.cancel_button)
        actions.addStretch()
        actions.addWidget(self.continue_button)

        column = QWidget()
        column.setObjectName("onboardingColumn")
        column.setMaximumWidth(760)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(MD)
        column_layout.addWidget(self.title)
        column_layout.addWidget(self.subtitle)
        column_layout.addWidget(self.error_label)
        column_layout.addSpacing(SM)
        column_layout.addWidget(genre_heading)
        column_layout.addWidget(genre_hint)
        column_layout.addLayout(genre_status_row)
        column_layout.addWidget(self.genre_host)
        column_layout.addSpacing(SM)
        column_layout.addWidget(movie_heading)
        column_layout.addWidget(movie_hint)
        column_layout.addWidget(self.search_bar)
        column_layout.addWidget(self.search_hint)
        column_layout.addWidget(self.results_host)
        column_layout.addWidget(self.selected_host)
        column_layout.addSpacing(SM)
        column_layout.addLayout(options)
        column_layout.addSpacing(SM)
        column_layout.addWidget(interest_heading)
        column_layout.addWidget(interest_hint)
        column_layout.addLayout(interest_row)
        column_layout.addWidget(self.interest_hint)
        column_layout.addWidget(self.interest_host)
        column_layout.addSpacing(LG)
        column_layout.addLayout(actions)
        column_layout.addStretch()

        content = QWidget()
        content.setObjectName("onboardingContent")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(XL, XL, XL, XL)
        content_layout.addStretch()
        content_layout.addWidget(column, 1)
        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setObjectName("onboardingScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def genre_button(self, genre_id: int) -> QPushButton | None:
        button = self.findChild(QPushButton, f"onboardingGenre{genre_id}")
        return button if isinstance(button, QPushButton) else None

    def movie_result_button(self, tmdb_id: int) -> QPushButton | None:
        button = self.findChild(QPushButton, f"onboardingMovieResult{tmdb_id}")
        return button if isinstance(button, QPushButton) else None

    def selected_movie_button(self, tmdb_id: int) -> QPushButton | None:
        button = self.findChild(QPushButton, f"onboardingSelectedMovie{tmdb_id}")
        return button if isinstance(button, QPushButton) else None

    def interest_button(self, text: str) -> QPushButton | None:
        for button in self.interest_host.findChildren(QPushButton):
            if button.property("interest") == text:
                return button
        return None

    def refresh(self, app_state: AppState) -> None:
        user = app_state.current_user
        self._user_id = user.id if user is not None else None
        self._editing = bool(user is not None and user.onboarding_completed)
        self._apply_mode()
        self._set_error("")
        self._set_search_hint("")
        self._set_interest_hint("")
        self._search_results = []
        self.search_bar.set_text("")
        self._render_search_results()
        self._load_saved()
        if self._genres:
            self._render_genres()
        else:
            self._request_genres()

    def _apply_mode(self) -> None:
        if self._editing:
            self.title.setText("Edit preferences")
            self.subtitle.setText("Update the tastes used for your recommendations.")
            self.continue_button.setText("Save preferences")
            self.cancel_button.show()
            return
        self.title.setText("Set your preferences")
        self.subtitle.setText("Nothing here is required. You can change this later in Profile.")
        self.continue_button.setText("Continue")
        self.cancel_button.hide()

    def _load_saved(self) -> None:
        self._genre_ids = {}
        self._movies = {}
        self._interests = []
        self._select_combo(self.language_combo, None)
        self._select_combo(self.period_combo, None)
        self._select_combo(self.rating_combo, None)
        if self._user_id is None or self._user_service is None:
            self._render_selected_movies()
            self._render_interests()
            return
        try:
            preferences = self._user_service.get_preferences(self._user_id)
        except UserServiceError as exc:
            self._set_error(str(exc))
            self._render_selected_movies()
            self._render_interests()
            return
        self._genre_ids = {genre.tmdb_genre_id: genre.name for genre in preferences.favorite_genres}
        self._movies = {movie.tmdb_id: movie.title for movie in preferences.favorite_movies}
        self._interests = list(preferences.interests)
        self._select_combo(self.language_combo, preferences.preferred_language)
        self._select_combo(self.period_combo, preferences.release_period)
        self._select_combo(self.rating_combo, preferences.minimum_rating)
        self._render_selected_movies()
        self._render_interests()

    def _save(self) -> None:
        self._set_error("")
        if self._user_id is None or self._user_service is None:
            self._set_error("Sign in to save preferences.")
            return
        try:
            preferences = UserPreferences(
                favorite_genres=[
                    GenrePreference(tmdb_genre_id=genre_id, name=name)
                    for genre_id, name in sorted(self._genre_ids.items(), key=lambda item: item[1].lower())
                ],
                favorite_movies=[
                    MoviePreference(tmdb_id=tmdb_id, title=title) for tmdb_id, title in self._movies.items()
                ],
                preferred_language=self._optional_text(self.language_combo),
                release_period=self._optional_text(self.period_combo),
                minimum_rating=self._optional_rating(),
                interests=list(self._interests),
            )
        except ValidationError as exc:
            self._set_error(format_validation_error(exc))
            return
        try:
            self._user_service.save_preferences(self._user_id, preferences)
        except UserServiceError as exc:
            self._set_error(str(exc))
            return
        self.completed.emit()

    def _retry_genres(self) -> None:
        self._genres = []
        self._request_genres()

    def _request_genres(self) -> None:
        if self._movie_service is None:
            self._show_genre_message("Genres are unavailable.", retry=False)
            return
        self._genre_request_id += 1
        self._show_genre_message("Loading genres...", retry=False)
        signals = self._runner.submit(self._genres_job, self._genre_request_id)
        signals.result.connect(self._on_genres)

    def _genres_job(self, request_id: int) -> _AsyncResult:
        try:
            genres = self._movie_service.get_genres() if self._movie_service is not None else []
        except Exception as exc:
            message = str(exc).strip() or "Could not load genres."
            return _AsyncResult(request_id, error=message)
        return _AsyncResult(request_id, value=genres)

    @Slot(object)
    def _on_genres(self, payload: object) -> None:
        if not isinstance(payload, _AsyncResult) or payload.request_id != self._genre_request_id:
            return
        if payload.error:
            self._show_genre_message(payload.error, retry=True)
            self._render_saved_genre_fallback()
            return
        genres = [item for item in payload.value or [] if isinstance(item, GenreDTO)]
        genres = [genre for genre in genres if genre.tmdb_genre_id > 0 and genre.name.strip()]
        if not genres:
            self._show_genre_message("No genres are available right now.", retry=True)
            self._render_saved_genre_fallback()
            return
        self._genres = genres
        self._show_genre_message("", retry=False)
        self._render_genres()

    def _render_saved_genre_fallback(self) -> None:
        if self._genres or not self._genre_ids:
            return
        self._render_genre_buttons(
            [GenreDTO(tmdb_genre_id=genre_id, name=name) for genre_id, name in self._genre_ids.items()]
        )

    def _render_genres(self) -> None:
        self._render_genre_buttons(self._genres)

    def _render_genre_buttons(self, genres: list[GenreDTO]) -> None:
        self._clear_flow(self.genre_host.flow)
        for genre in genres:
            button = QPushButton(genre.name)
            button.setObjectName(f"onboardingGenre{genre.tmdb_genre_id}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setCheckable(True)
            apply_property(button, "variant", "chip")
            button.toggled.connect(
                lambda checked, genre_id=genre.tmdb_genre_id, name=genre.name: self._toggle_genre(
                    genre_id, name, checked
                )
            )
            selected = genre.tmdb_genre_id in self._genre_ids
            button.blockSignals(True)
            button.setChecked(selected)
            button.blockSignals(False)
            apply_property(button, "selected", "true" if selected else "false")
            button.adjustSize()
            self.genre_host.flow.addWidget(button)
        self.genre_host.fit()

    def _toggle_genre(self, genre_id: int, name: str, checked: bool) -> None:
        if checked:
            self._genre_ids[genre_id] = name
        else:
            self._genre_ids.pop(genre_id, None)
        button = self.genre_button(genre_id)
        if button is not None:
            apply_property(button, "selected", "true" if checked else "false")

    def _on_search(self, query: str) -> None:
        cleaned = query.strip()
        if not cleaned:
            self._set_search_hint("Enter a movie title to search.")
            return
        if self._movie_service is None:
            self._set_search_hint("Movie search is unavailable.")
            return
        self._search_request_id += 1
        self.search_hint.setText("Searching...")
        apply_property(self.search_hint, "role", "caption")
        self.search_hint.show()
        signals = self._runner.submit(self._search_job, self._search_request_id, cleaned)
        signals.result.connect(self._on_search_result)

    def _search_job(self, request_id: int, query: str) -> _AsyncResult:
        try:
            page = self._movie_service.search_movies(query) if self._movie_service is not None else MoviePageDTO()
        except Exception as exc:
            message = str(exc).strip() or "Could not search movies."
            return _AsyncResult(request_id, error=message)
        return _AsyncResult(request_id, value=page)

    @Slot(object)
    def _on_search_result(self, payload: object) -> None:
        if not isinstance(payload, _AsyncResult) or payload.request_id != self._search_request_id:
            return
        if payload.error:
            self._search_results = []
            self._render_search_results()
            self._set_search_hint(payload.error)
            return
        page = payload.value if isinstance(payload.value, MoviePageDTO) else MoviePageDTO()
        self._search_results = page.results[:8]
        self._render_search_results()
        if not self._search_results:
            self._set_search_hint("No movies found.")
            return
        self._set_search_hint("")

    def _render_search_results(self) -> None:
        self._clear_box(self.results_layout)
        if not self._search_results:
            self.results_host.hide()
            return
        for movie in self._search_results:
            year = movie.release_date.year if movie.release_date else None
            label = f"{movie.title} ({year})" if year else movie.title
            button = QPushButton(label)
            button.setObjectName(f"onboardingMovieResult{movie.tmdb_id}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_property(button, "variant", "chip")
            selected = movie.tmdb_id in self._movies
            apply_property(button, "selected", "true" if selected else "false")
            button.clicked.connect(lambda _checked=False, chosen=movie: self._toggle_movie(chosen))
            self.results_layout.addWidget(button)
        self.results_host.show()

    def _toggle_movie(self, movie: MovieSummaryDTO) -> None:
        if movie.tmdb_id in self._movies:
            self._movies.pop(movie.tmdb_id, None)
            self._set_search_hint("")
        elif len(self._movies) >= MAX_FAVORITE_MOVIES:
            self._set_search_hint(f"You can save up to {MAX_FAVORITE_MOVIES} favorite movies.")
        else:
            self._movies[movie.tmdb_id] = movie.title
            self._set_search_hint("")
        self._render_selected_movies()
        self._render_search_results()

    def _render_selected_movies(self) -> None:
        self._clear_flow(self.selected_host.flow)
        for tmdb_id, title in self._movies.items():
            button = QPushButton(f"{title}  ×")
            button.setObjectName(f"onboardingSelectedMovie{tmdb_id}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_property(button, "variant", "chip")
            apply_property(button, "selected", "true")
            button.clicked.connect(lambda _checked=False, movie_id=tmdb_id: self._remove_movie(movie_id))
            button.adjustSize()
            self.selected_host.flow.addWidget(button)
        self.selected_host.fit()

    def _remove_movie(self, tmdb_id: int) -> None:
        self._movies.pop(tmdb_id, None)
        self._render_selected_movies()
        self._render_search_results()

    def _add_interest(self) -> None:
        text = " ".join(self.interest_input.text().split())
        if not text:
            self._set_interest_hint("Enter an interest first.")
            return
        if len(text) > MAX_INTEREST_LENGTH:
            self._set_interest_hint(f"Keep interests to {MAX_INTEREST_LENGTH} characters.")
            return
        if any(text.casefold() == item.casefold() for item in self._interests):
            self._set_interest_hint("That interest is already added.")
            return
        if len(self._interests) >= MAX_INTERESTS:
            self._set_interest_hint(f"You can save up to {MAX_INTERESTS} interests.")
            return
        self.interest_input.clear()
        self._interests.append(text)
        self._set_interest_hint("")
        self._render_interests()

    def _render_interests(self) -> None:
        self._clear_flow(self.interest_host.flow)
        for interest in self._interests:
            button = QPushButton(f"{interest}  ×")
            button.setObjectName("onboardingInterestChip")
            button.setProperty("interest", interest)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_property(button, "variant", "chip")
            apply_property(button, "selected", "true")
            button.clicked.connect(lambda _checked=False, value=interest: self._remove_interest(value))
            button.adjustSize()
            self.interest_host.flow.addWidget(button)
        self.interest_host.fit()

    def _remove_interest(self, interest: str) -> None:
        self._interests = [item for item in self._interests if item != interest]
        self._render_interests()

    def _optional_text(self, combo: QComboBox) -> str | None:
        value = combo.currentData()
        if value is None or not str(value).strip():
            return None
        return str(value)

    def _optional_rating(self) -> float | None:
        value = self.rating_combo.currentData()
        if not isinstance(value, (int, float)):
            return None
        return float(value)

    def _show_genre_message(self, message: str, *, retry: bool) -> None:
        self.genre_status.setText(message)
        self.genre_status.setVisible(bool(message))
        self.genre_retry.setVisible(retry)

    def _set_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))

    def _set_search_hint(self, message: str) -> None:
        apply_property(self.search_hint, "role", "error" if message else "caption")
        self.search_hint.setText(message)
        self.search_hint.setVisible(bool(message))

    def _set_interest_hint(self, message: str) -> None:
        self.interest_hint.setText(message)
        self.interest_hint.setVisible(bool(message))

    @staticmethod
    def _section(title: str, hint: str) -> tuple[QLabel, QLabel]:
        heading = QLabel(title)
        apply_property(heading, "role", "heading")
        caption = QLabel(hint)
        apply_property(caption, "role", "caption")
        caption.setWordWrap(True)
        return heading, caption

    @staticmethod
    def _combo(object_name: str) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName(object_name)
        combo.setMinimumWidth(160)
        return combo

    @staticmethod
    def _labeled(label: str, combo: QComboBox) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SM)
        caption = QLabel(label)
        apply_property(caption, "role", "caption")
        layout.addWidget(caption)
        layout.addWidget(combo)
        return box

    @staticmethod
    def _select_combo(combo: QComboBox, value: object) -> None:
        if value is None:
            combo.setCurrentIndex(0)
            return
        index = combo.findData(value)
        combo.setCurrentIndex(index if index >= 0 else 0)

    @staticmethod
    def _clear_flow(layout: FlowLayout) -> None:
        layout.clear()

    @staticmethod
    def _clear_box(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
