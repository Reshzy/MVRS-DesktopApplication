from app.models.user import User
from app.state.app_state import AppState
from app.utils.constants import DEFAULT_THEME, THEME_LIGHT


def _user() -> User:
    return User(name="Ada Lovelace", email="ada@example.com", password_hash="hashed")


def test_default_state_is_signed_out() -> None:
    state = AppState()

    assert state.current_user is None
    assert state.is_authenticated is False
    assert state.guest_mode is False
    assert state.selected_movie is None
    assert state.previous_page is None
    assert state.active_filters == {}
    assert state.theme == DEFAULT_THEME
    assert state.auth_return_page is None


def test_set_current_user_clears_guest_session() -> None:
    state = AppState()
    user = _user()
    state.enter_guest_mode()
    state.auth_return_page = "movie_details"
    state.theme = THEME_LIGHT

    state.set_current_user(user)

    assert state.current_user is user
    assert state.is_authenticated is True
    assert state.guest_mode is False
    assert state.auth_return_page is None
    assert state.theme == THEME_LIGHT


def test_enter_guest_mode_clears_user_and_resets_theme() -> None:
    state = AppState()
    state.set_current_user(_user())
    state.theme = THEME_LIGHT
    state.auth_return_page = "watchlist"

    state.enter_guest_mode()

    assert state.current_user is None
    assert state.is_authenticated is False
    assert state.guest_mode is True
    assert state.auth_return_page is None
    assert state.theme == DEFAULT_THEME


def test_clear_current_user_leaves_signed_out_home_state() -> None:
    state = AppState()
    state.enter_guest_mode()
    state.auth_return_page = "discover"
    state.theme = THEME_LIGHT
    state.selected_movie = {"tmdb_id": 550}

    state.clear_current_user()

    assert state.current_user is None
    assert state.guest_mode is False
    assert state.auth_return_page is None
    assert state.theme == DEFAULT_THEME
    assert state.is_authenticated is False
    assert state.selected_movie == {"tmdb_id": 550}
