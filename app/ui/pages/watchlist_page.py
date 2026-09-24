from __future__ import annotations

import logging

from PySide6.QtWidgets import QWidget

from app.schemas.library_schema import WatchlistEntryDTO
from app.schemas.movie_schema import MovieSummaryDTO
from app.services.history_service import HistoryService
from app.services.library_base import LibraryError
from app.services.watchlist_service import WatchlistService
from app.ui.pages.library_collection_page import LibraryCollectionPage
from app.ui.widgets.library_tile import LibraryTile
from app.ui.workers.image_worker import ImageLoader
from app.utils.helpers import format_user_date
from app.utils.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class WatchlistPage(LibraryCollectionPage):
    def __init__(
        self,
        watchlist_service: WatchlistService | None = None,
        history_service: HistoryService | None = None,
        image_loader: ImageLoader | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "watchlistPage",
            "Watchlist",
            "Movies you saved to watch later.",
            guest_title="Sign in to use Watchlist",
            guest_message="Create an account or log in to save movies and mark them watched.",
            empty_title="Your watchlist is empty",
            empty_message="Save a title from Discover or Movie Details to see it here.",
            image_loader=image_loader,
            parent=parent,
        )
        self._watchlist_service = watchlist_service
        self._history_service = history_service

    def load_entries(self, user_id: int) -> list[WatchlistEntryDTO]:
        if self._watchlist_service is None:
            raise LibraryError("Watchlist is unavailable right now.")
        return self._watchlist_service.list_entries(user_id)

    def create_tile(self, entry: object) -> LibraryTile:
        if not isinstance(entry, WatchlistEntryDTO):
            raise TypeError("WatchlistPage expected a WatchlistEntryDTO")
        tile = LibraryTile(
            entry.movie,
            meta_text=format_user_date(entry.created_at, "Saved "),
            show_remove=True,
            show_watched=True,
            watched=entry.watched,
            image_loader=self._image_loader,
            parent=self.grid_host,
        )
        tile.remove_requested.connect(self._remove_movie)
        tile.watched_requested.connect(self._mark_watched)
        return tile

    def _remove_movie(self, movie: object) -> None:
        user_id = self._current_user_id()
        if user_id is None or not isinstance(movie, MovieSummaryDTO) or self._watchlist_service is None:
            return
        try:
            removed = self._watchlist_service.remove(user_id, movie)
        except Exception as exc:
            logger.exception("Watchlist remove failed")
            self.status_label.setText(self._action_error(exc, "Could not remove this movie."))
            return
        if self._app_state is not None:
            self.refresh(
                self._app_state,
                status="Removed from your watchlist." if removed else "That title was already gone.",
            )

    def _mark_watched(self, movie: object) -> None:
        user_id = self._current_user_id()
        if user_id is None or not isinstance(movie, MovieSummaryDTO) or self._history_service is None:
            return
        try:
            self._history_service.mark_watched(user_id, movie)
        except Exception as exc:
            logger.exception("Watchlist mark watched failed")
            self.status_label.setText(self._action_error(exc, "Could not mark this movie as watched."))
            return
        if self._app_state is not None:
            self.refresh(self._app_state, status="Marked as watched.")

    def _current_user_id(self) -> int | None:
        user = self._app_state.current_user if self._app_state is not None else None
        if user is None:
            self.status_label.setText("Sign in to save watchlist, ratings, and watch history.")
            return None
        return user.id
