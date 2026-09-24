from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.schemas.library_schema import HistoryEntryDTO
from app.services.history_service import HistoryService
from app.services.library_base import LibraryError
from app.ui.pages.library_collection_page import LibraryCollectionPage
from app.ui.widgets.library_tile import LibraryTile
from app.ui.workers.image_worker import ImageLoader
from app.utils.constants import MAX_RATING
from app.utils.helpers import format_user_date


class HistoryPage(LibraryCollectionPage):
    def __init__(
        self,
        history_service: HistoryService | None = None,
        image_loader: ImageLoader | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "historyPage",
            "History",
            "Movies you have marked as watched.",
            guest_title="Sign in to track history",
            guest_message="Create an account or log in to keep watch history and ratings.",
            empty_title="No watch history yet",
            empty_message="Mark a movie as watched to see it here.",
            image_loader=image_loader,
            parent=parent,
        )
        self._history_service = history_service

    def load_entries(self, user_id: int) -> list[HistoryEntryDTO]:
        if self._history_service is None:
            raise LibraryError("History is unavailable right now.")
        return self._history_service.list_entries(user_id)

    def create_tile(self, entry: object) -> LibraryTile:
        if not isinstance(entry, HistoryEntryDTO):
            raise TypeError("HistoryPage expected a HistoryEntryDTO")
        watched = format_user_date(entry.watched_at, "Watched ")
        rating = f"Your rating: {entry.rating}/{MAX_RATING}" if entry.rating is not None else "Not rated"
        return LibraryTile(
            entry.movie,
            meta_text=f"{watched}  ·  {rating}",
            image_loader=self._image_loader,
            parent=self.grid_host,
        )
