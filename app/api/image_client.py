from __future__ import annotations

import hashlib
import logging
import threading
from pathlib import Path

import httpx

from app.api.exceptions import ImageFetchError
from app.utils.logging_config import LOGGER_NAME
from app.utils.paths import image_cache_dir

logger = logging.getLogger(LOGGER_NAME)

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"
DEFAULT_POSTER_SIZE = "w342"
DEFAULT_BACKDROP_SIZE = "w780"
DEFAULT_TIMEOUT_SECONDS = 10.0


def normalize_image_path(image_path: str) -> str:
    text = (image_path or "").strip()
    if not text:
        raise ImageFetchError("Image path is empty.")
    return text if text.startswith("/") else f"/{text}"


def image_cache_key(image_path: str, size: str = DEFAULT_POSTER_SIZE) -> str:
    return f"{size}:{normalize_image_path(image_path)}"


def build_image_url(image_path: str, size: str = DEFAULT_POSTER_SIZE) -> str:
    return f"{TMDB_IMAGE_BASE}/{size}{normalize_image_path(image_path)}"


class ImageClient:
    def __init__(
        self,
        cache_dir: Path | None = None,
        http_client: httpx.Client | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._cache_dir = cache_dir or image_cache_dir()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._owns_client = http_client is None
        self._timeout = timeout
        self._http = http_client or httpx.Client(timeout=timeout)
        self._lock = threading.Lock()

    def build_url(self, image_path: str, size: str = DEFAULT_POSTER_SIZE) -> str:
        return build_image_url(image_path, size)

    def cache_path(self, image_path: str, size: str = DEFAULT_POSTER_SIZE) -> Path:
        normalized = normalize_image_path(image_path)
        suffix = Path(normalized).suffix or ".jpg"
        digest = hashlib.sha1(image_cache_key(normalized, size).encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}{suffix}"

    def cached_bytes(self, image_path: str, size: str = DEFAULT_POSTER_SIZE) -> bytes | None:
        path = self.cache_path(image_path, size)
        with self._lock:
            if not path.exists():
                return None
            data = path.read_bytes()
        return data or None

    def fetch(self, image_path: str, size: str = DEFAULT_POSTER_SIZE) -> bytes:
        cached = self.cached_bytes(image_path, size)
        if cached is not None:
            return cached

        data = self._download(self.build_url(image_path, size))
        if not data:
            raise ImageFetchError("Image download was empty.")
        with self._lock:
            existing = self.cache_path(image_path, size)
            if existing.exists():
                stored = existing.read_bytes()
                if stored:
                    return stored
            self._store(image_path, size, data)
        return data

    def _download(self, url: str) -> bytes:
        try:
            if self._owns_client:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return response.content
            with self._lock:
                response = self._http.get(url)
                response.raise_for_status()
                return response.content
        except httpx.TimeoutException as exc:
            logger.warning("Image download timed out")
            raise ImageFetchError("Image download timed out.") from exc
        except httpx.ConnectError as exc:
            logger.warning("Image download failed to connect")
            raise ImageFetchError("Could not download image.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("Image download failed status=%s", status)
            raise ImageFetchError(f"Image download failed ({status}).") from exc
        except httpx.HTTPError as exc:
            logger.warning("Image download failed")
            raise ImageFetchError("Could not download image.") from exc

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def _store(self, image_path: str, size: str, data: bytes) -> None:
        path = self.cache_path(image_path, size)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
