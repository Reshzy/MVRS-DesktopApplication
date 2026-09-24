from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.user import User
from app.utils.constants import DEFAULT_THEME


@dataclass
class AppState:
    current_user: User | None = None
    selected_movie: Any = None
    previous_page: str | None = None
    active_filters: dict[str, Any] = field(default_factory=dict)
    theme: str = DEFAULT_THEME
    guest_mode: bool = False
    auth_return_page: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.current_user is not None

    def set_current_user(self, user: User | None) -> None:
        self.current_user = user
        if user is not None:
            self.guest_mode = False
            self.auth_return_page = None

    def enter_guest_mode(self) -> None:
        self.current_user = None
        self.guest_mode = True
        self.auth_return_page = None
        self.theme = DEFAULT_THEME

    def clear_current_user(self) -> None:
        self.current_user = None
        self.guest_mode = False
        self.auth_return_page = None
        self.theme = DEFAULT_THEME
