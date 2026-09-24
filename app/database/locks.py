from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from typing import TypeVar

_SESSION_LOCK = threading.RLock()

F = TypeVar("F", bound=Callable)


@contextmanager
def session_lock() -> Iterator[None]:
    """Serialize access to the process-wide SQLAlchemy session.

    Workers and the UI share one session. SQLAlchemy sessions are not
    thread-safe, so every read/write must take this lock for the whole
    operation, not per-statement.
    """
    with _SESSION_LOCK:
        yield


def session_guard(fn: F) -> F:
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with session_lock():
            return fn(*args, **kwargs)

    return wrapped  # type: ignore[return-value]
