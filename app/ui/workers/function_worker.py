from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QRunnable

from app.ui.workers.signals import WorkerSignals
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class FunctionWorker(QRunnable):
    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        signals: WorkerSignals,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = signals
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            kwargs = dict(self._kwargs)
            if _accepts_progress(self._fn):
                kwargs["progress"] = self.signals.progress.emit
            result = self._fn(*self._args, **kwargs)
            self.signals.result.emit(result)
        except Exception as exc:
            logger.exception("Background worker failed")
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()


def _accepts_progress(fn: Callable[..., Any]) -> bool:
    try:
        return "progress" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False
