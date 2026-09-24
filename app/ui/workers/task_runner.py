from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThreadPool, Slot

from app.ui.workers.function_worker import FunctionWorker
from app.ui.workers.signals import QUEUED, WorkerSignals


class TaskRunner(QObject):
    """Submit callables to QThreadPool and deliver results through signals."""

    def __init__(self, parent: QObject | None = None, pool: QThreadPool | None = None) -> None:
        super().__init__(parent)
        self._pool = pool or QThreadPool.globalInstance()
        self._inflight: dict[str, WorkerSignals] = {}

    def is_inflight(self, key: str) -> bool:
        return key in self._inflight

    def submit(
        self,
        fn: Callable[..., Any],
        *args: Any,
        key: str | None = None,
        **kwargs: Any,
    ) -> WorkerSignals | None:
        if key and key in self._inflight:
            return None
        signals = WorkerSignals(self)
        if key:
            self._inflight[key] = signals
            signals.finished.connect(lambda pending=key: self._clear_key(pending), QUEUED)
        worker = FunctionWorker(fn, *args, signals=signals, **kwargs)
        self._pool.start(worker)
        return signals

    @Slot(str)
    def _clear_key(self, key: str) -> None:
        self._inflight.pop(key, None)

    def bind(
        self,
        signals: WorkerSignals | None,
        on_result: Callable[[object], Any],
        on_error: Callable[[str], Any] | None = None,
    ) -> bool:
        if signals is None:
            return False
        signals.result.connect(on_result, QUEUED)
        if on_error is not None:
            signals.error.connect(on_error, QUEUED)
        return True
