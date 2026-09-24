from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.services.user_service import UserService, UserServiceError
from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, SM, XL


class ProfilePage(QWidget):
    edit_preferences_requested = Signal()

    def __init__(self, user_service: UserService | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("profilePage")
        self._user_service = user_service

        self.title = QLabel("Profile")
        apply_property(self.title, "role", "title")

        self.guest_label = QLabel("Sign in to save preferences.")
        self.guest_label.setObjectName("profileGuestLabel")
        apply_property(self.guest_label, "role", "subtitle")
        self.guest_label.setWordWrap(True)

        self.name_label = QLabel()
        self.name_label.setObjectName("profileNameLabel")
        apply_property(self.name_label, "role", "heading")

        self.email_label = QLabel()
        self.email_label.setObjectName("profileEmailLabel")
        apply_property(self.email_label, "role", "muted")

        preferences_heading = QLabel("Preferences")
        apply_property(preferences_heading, "role", "heading")

        preferences_hint = QLabel("These choices shape recommendations. Edit them any time.")
        apply_property(preferences_hint, "role", "caption")
        preferences_hint.setWordWrap(True)

        self.summary_label = QLabel("No preferences yet. You can add them any time.")
        self.summary_label.setObjectName("profileSummaryLabel")
        apply_property(self.summary_label, "role", "body")
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.edit_button = QPushButton("Edit preferences")
        self.edit_button.setObjectName("profileEditButton")
        apply_property(self.edit_button, "variant", "primary")
        self.edit_button.clicked.connect(self.edit_preferences_requested.emit)
        self.edit_button.setMaximumWidth(220)

        self._account_widgets = (
            self.name_label,
            self.email_label,
            preferences_heading,
            preferences_hint,
            self.summary_label,
            self.edit_button,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(SM)
        layout.addWidget(self.title)
        layout.addWidget(self.guest_label)
        layout.addSpacing(LG)
        layout.addWidget(self.name_label)
        layout.addWidget(self.email_label)
        layout.addSpacing(LG)
        layout.addWidget(preferences_heading)
        layout.addWidget(preferences_hint)
        layout.addWidget(self.summary_label)
        layout.addSpacing(SM)
        layout.addWidget(self.edit_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()

    def refresh(self, app_state: AppState) -> None:
        user = app_state.current_user
        signed_in = user is not None
        self.guest_label.setVisible(not signed_in)
        for widget in self._account_widgets:
            widget.setVisible(signed_in)
        if user is None:
            return
        self.name_label.setText(user.name)
        self.email_label.setText(user.email)
        if self._user_service is None:
            self.summary_label.setText("Preferences are unavailable.")
            self.edit_button.setEnabled(False)
            return
        self.edit_button.setEnabled(True)
        try:
            preferences = self._user_service.get_preferences(user.id)
        except UserServiceError as exc:
            self.summary_label.setText(str(exc))
            return
        self.summary_label.setText(preferences.summary())
