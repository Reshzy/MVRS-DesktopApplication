from __future__ import annotations

import pytest
from pydantic import ValidationError
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QDialog

from app.schemas.user_schema import ProfileUpdateRequest
from app.ui.dialogs.confirm_dialog import ConfirmDialog
from app.ui.dialogs.edit_profile_dialog import EditProfileDialog
from app.ui.dialogs.rating_dialog import RatingDialog
from app.ui.widgets.rating_widget import RatingWidget


def test_rating_widget_click_emits_and_fills(qtbot, themed_app) -> None:
    widget = RatingWidget()
    qtbot.addWidget(widget)
    widget.show()

    ratings: list[int] = []
    widget.ratingChanged.connect(ratings.append)

    qtbot.mouseClick(widget.stars[3], Qt.MouseButton.LeftButton)

    assert ratings == [4]
    assert widget.rating() == 4
    assert widget.stars[0].property("filled") == "true"
    assert widget.stars[3].property("filled") == "true"
    assert widget.stars[4].property("filled") == "false"


def test_rating_widget_hover_previews_then_restores(qtbot, themed_app) -> None:
    widget = RatingWidget(2)
    qtbot.addWidget(widget)
    widget.show()

    themed_app.sendEvent(widget.stars[4], QEvent(QEvent.Type.Enter))

    assert widget.stars[4].property("preview") == "true"
    assert widget.stars[0].property("preview") == "true"
    assert widget.rating() == 2

    themed_app.sendEvent(widget.stars[4], QEvent(QEvent.Type.Leave))
    assert widget.stars[4].property("preview") == "false"
    assert widget.stars[1].property("filled") == "true"
    assert widget.stars[2].property("filled") == "false"


def test_rating_widget_set_rating_does_not_emit(qtbot, themed_app) -> None:
    widget = RatingWidget()
    qtbot.addWidget(widget)
    ratings: list[int] = []
    widget.ratingChanged.connect(ratings.append)

    widget.set_rating(5)

    assert widget.rating() == 5
    assert ratings == []
    assert widget.stars[4].property("filled") == "true"


def test_rating_dialog_save_and_cancel(qtbot, themed_app) -> None:
    dialog = RatingDialog(initial_rating=1)
    qtbot.addWidget(dialog)
    dialog.show()

    qtbot.mouseClick(dialog.rating_widget.stars[2], Qt.MouseButton.LeftButton)
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.rating() == 3

    canceled = RatingDialog()
    qtbot.addWidget(canceled)
    canceled.show()
    assert canceled.save_button.isEnabled() is False
    qtbot.mouseClick(canceled.cancel_button, Qt.MouseButton.LeftButton)
    assert canceled.result() == QDialog.DialogCode.Rejected


def test_confirm_dialog_accepts_and_rejects(qtbot, themed_app) -> None:
    accepted = ConfirmDialog("Remove", "Remove this title?", confirm_label="Remove")
    qtbot.addWidget(accepted)
    accepted.show()
    qtbot.mouseClick(accepted.confirm_button, Qt.MouseButton.LeftButton)
    assert accepted.result() == QDialog.DialogCode.Accepted

    rejected = ConfirmDialog("Remove", "Remove this title?", confirm_variant="primary")
    qtbot.addWidget(rejected)
    rejected.show()
    qtbot.mouseClick(rejected.cancel_button, Qt.MouseButton.LeftButton)
    assert rejected.result() == QDialog.DialogCode.Rejected


def test_edit_profile_dialog_validates_and_returns_name(qtbot, themed_app) -> None:
    dialog = EditProfileDialog(name="Ada", email="ada@example.com")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.email_input.isReadOnly()
    assert dialog.email_input.isEnabled() is False

    dialog.name_input.clear()
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert dialog.error_label.isVisible()
    assert "name" in dialog.error_label.text().lower()
    assert dialog.result() != QDialog.DialogCode.Accepted

    dialog.name_input.setText("  Ada Lovelace  ")
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.profile_name() == "Ada Lovelace"


def test_profile_update_schema_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdateRequest(name="   ")
