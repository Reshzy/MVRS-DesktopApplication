from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtGui import QImage, QPixmap

from app.api.image_client import DEFAULT_POSTER_SIZE, ImageClient, image_cache_key
from app.ui.workers.signals import QUEUED
from app.ui.workers.task_runner import TaskRunner


class ImageLoader(QObject):
    loaded = Signal(str, object)
    failed = Signal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        client: ImageClient | None = None,
        runner: TaskRunner | None = None,
    ) -> None:
        super().__init__(parent)
        self._owns_client = client is None
        self._client = client or ImageClient()
        self._runner = runner or TaskRunner(self)
        self._inflight: set[str] = set()
        self._memory: dict[str, QPixmap] = {}

    def request(self, image_path: str | None, size: str = DEFAULT_POSTER_SIZE) -> str | None:
        if not image_path or not str(image_path).strip():
            return None

        key = image_cache_key(image_path, size)
        cached = self._memory.get(key)
        if cached is not None and not cached.isNull():
            QTimer.singleShot(0, lambda k=key, pixmap=cached: self.loaded.emit(k, pixmap))
            return key

        if key in self._inflight:
            return key

        self._inflight.add(key)
        signals = self._runner.submit(self._fetch_job, image_path, size, key=f"image:{key}")
        if signals is None:
            return key
        signals.result.connect(self._on_result, QUEUED)
        signals.error.connect(lambda _message, pending=key: self._on_error(pending), QUEUED)
        return key

    def _fetch_job(self, image_path: str, size: str) -> tuple[str, bytes]:
        return image_cache_key(image_path, size), self._client.fetch(image_path, size)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    @Slot(object)
    def _on_result(self, payload: object) -> None:
        if not isinstance(payload, tuple) or len(payload) != 2:
            return
        key, data = payload
        self._on_bytes(key, data)

    def _on_bytes(self, key: str, data: object) -> None:
        self._inflight.discard(key)
        if not isinstance(data, (bytes, bytearray)):
            self.failed.emit(key)
            return

        image = QImage()
        if not image.loadFromData(bytes(data)):
            self.failed.emit(key)
            return

        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            self.failed.emit(key)
            return

        self._memory[key] = pixmap
        self.loaded.emit(key, pixmap)

    def _on_error(self, key: str) -> None:
        self._inflight.discard(key)
        self.failed.emit(key)
