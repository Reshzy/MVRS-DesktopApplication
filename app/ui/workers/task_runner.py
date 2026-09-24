from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThreadPool

from app.ui.workers.function_worker import FunctionWorker
from app.ui.workers.signals import WorkerSignals


class TaskRunner(QObject):
    def __init__(self, parent: QObject | None = None, pool: QThreadPool | None = None) -> None:
        super().__init__(parent)
        self._pool = pool or QThreadPool.globalInstance()

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> WorkerSignals:
        signals = WorkerSignals(self)
        worker = FunctionWorker(fn, *args, signals=signals, **kwargs)
        self._pool.start(worker)
        return signals
