from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.user import User


@dataclass
class AppState:
    current_user: User | None = None
    selected_movie: Any = None
    previous_page: str | None = None
    active_filters: dict[str, Any] = field(default_factory=dict)

    def set_current_user(self, user: User | None) -> None:
        self.current_user = user

    def clear_current_user(self) -> None:
        self.current_user = None
