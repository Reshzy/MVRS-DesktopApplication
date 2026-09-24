from __future__ import annotations


class RequestGate:
    """Monotonic token used to drop stale worker results after newer requests."""

    def __init__(self) -> None:
        self._current = 0

    def begin(self) -> int:
        self._current += 1
        return self._current

    def is_current(self, request_id: int) -> bool:
        return request_id == self._current

    @property
    def current(self) -> int:
        return self._current
