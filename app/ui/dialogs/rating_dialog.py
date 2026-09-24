from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, MD, XL
from app.ui.widgets.rating_widget import RatingWidget
from app.utils.constants import MAX_RATING


class RatingDialog(QDialog):
    def __init__(
        self,
        title: str = "Rate movie",
        message: str = "Choose a rating from 1 to 5 stars.",
        initial_rating: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ratingDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(360)

        heading = QLabel(title)
        heading.setObjectName("ratingDialogHeading")
        apply_property(heading, "role", "heading")

        body = QLabel(message)
        body.setObjectName("ratingDialogMessage")
        apply_property(body, "role", "body")
        body.setWordWrap(True)

        self.rating_widget = RatingWidget(initial_rating, self)
        self.rating_widget.setObjectName("ratingDialogStars")

        self.save_button = QPushButton("Save rating")
        self.save_button.setObjectName("ratingDialogSave")
        apply_property(self.save_button, "variant", "primary")
        style_button(self.save_button, tooltip="Save this rating")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._save)
        self.save_button.setEnabled(self.rating_widget.rating() > 0)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("ratingDialogCancel")
        apply_property(self.cancel_button, "variant", "secondary")
        style_button(self.cancel_button, tooltip="Cancel without saving")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.clicked.connect(self.reject)
        self.rating_widget.stars[0].setFocus()

        self.rating_widget.ratingChanged.connect(self._on_rating_changed)

        actions = QHBoxLayout()
        actions.setSpacing(MD)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, LG)
        layout.setSpacing(LG)
        layout.addWidget(heading)
        layout.addWidget(body)
        layout.addWidget(self.rating_widget)
        layout.addLayout(actions)

    def rating(self) -> int:
        return self.rating_widget.rating()

    def _on_rating_changed(self, rating: int) -> None:
        self.save_button.setEnabled(rating > 0)

    def _save(self) -> None:
        if self.rating() <= 0:
            return
        self.accept()

    @classmethod
    def ask(
        cls,
        parent: QWidget | None = None,
        title: str = "Rate movie",
        message: str = f"Choose a rating from 1 to {MAX_RATING} stars.",
        initial_rating: int | None = None,
    ) -> int | None:
        dialog = cls(title, message, initial_rating, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.rating()
        return None
