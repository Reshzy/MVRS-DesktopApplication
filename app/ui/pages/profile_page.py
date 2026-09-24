from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.user_service import UserService, UserServiceError
from app.state.app_state import AppState
from app.ui.dialogs.edit_profile_dialog import EditProfileDialog
from app.ui.theme import apply_property, style_button
from app.ui.theme.spacing import LG, MD, SM, XL
from app.utils.constants import DEFAULT_THEME, THEME_LABELS

AskNameFn = Callable[..., str | None]


class ProfilePage(QWidget):
    edit_preferences_requested = Signal()
    name_updated = Signal()
    theme_changed = Signal(str)
    sign_in_requested = Signal()

    def __init__(
        self,
        user_service: UserService | None = None,
        parent: QWidget | None = None,
        *,
        ask_name: AskNameFn | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("profilePage")
        self._user_service = user_service
        self._ask_name = ask_name or EditProfileDialog.ask
        self._app_state: AppState | None = None
        self._syncing_theme = False

        self.title = QLabel("Profile")
        apply_property(self.title, "role", "title")

        self.subtitle = QLabel("Your account, taste settings, and appearance.")
        self.subtitle.setObjectName("profileSubtitle")
        apply_property(self.subtitle, "role", "muted")
        self.subtitle.setWordWrap(True)

        self.guest_label = QLabel("Sign in to save preferences.")
        self.guest_label.setObjectName("profileGuestLabel")
        apply_property(self.guest_label, "role", "subtitle")
        self.guest_label.setWordWrap(True)

        self.sign_in_button = QPushButton("Sign in")
        self.sign_in_button.setObjectName("profileSignInButton")
        apply_property(self.sign_in_button, "variant", "primary")
        style_button(self.sign_in_button, tooltip="Sign in to save preferences")
        self.sign_in_button.clicked.connect(self.sign_in_requested.emit)
        self.sign_in_button.setMaximumWidth(180)

        self.error_label = QLabel()
        self.error_label.setObjectName("profileErrorLabel")
        apply_property(self.error_label, "role", "error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.name_label = QLabel()
        self.name_label.setObjectName("profileNameLabel")
        apply_property(self.name_label, "role", "heading")

        self.email_label = QLabel()
        self.email_label.setObjectName("profileEmailLabel")
        apply_property(self.email_label, "role", "muted")

        self.edit_name_button = QPushButton("Edit name")
        self.edit_name_button.setObjectName("profileEditNameButton")
        apply_property(self.edit_name_button, "variant", "secondary")
        style_button(self.edit_name_button, tooltip="Change the name shown in the app")
        self.edit_name_button.clicked.connect(self._edit_name)
        self.edit_name_button.setMaximumWidth(180)

        account = self._card(
            "Account",
            "The name shown in the app. Email stays the same.",
            self.name_label,
            self.email_label,
            self.edit_name_button,
        )

        self.summary_label = QLabel("No preferences yet. You can add them any time.")
        self.summary_label.setObjectName("profileSummaryLabel")
        apply_property(self.summary_label, "role", "body")
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.edit_button = QPushButton("Edit preferences")
        self.edit_button.setObjectName("profileEditButton")
        apply_property(self.edit_button, "variant", "primary")
        style_button(self.edit_button, tooltip="Edit favorite genres and viewing preferences")
        self.edit_button.clicked.connect(self.edit_preferences_requested.emit)
        self.edit_button.setMaximumWidth(220)

        preferences = self._card(
            "Preferences",
            "These choices shape recommendations. Edit them any time.",
            self.summary_label,
            self.edit_button,
        )

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("profileThemeCombo")
        self.theme_combo.setMinimumWidth(180)
        self.theme_combo.setMaximumWidth(240)
        self.theme_combo.setToolTip("Choose dark or light appearance")
        for value, label in THEME_LABELS:
            self.theme_combo.addItem(label, value)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        appearance = self._card(
            "Appearance",
            "Optional. Dark is the default cinematic look.",
            self.theme_combo,
        )

        self._account_widgets = (account, preferences, appearance)
        for widget in self._account_widgets:
            widget.hide()
        self.subtitle.hide()

        column = QWidget()
        column.setObjectName("profileColumn")
        column.setMaximumWidth(720)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(LG)
        column_layout.addWidget(self.title)
        column_layout.addWidget(self.subtitle)
        column_layout.addWidget(self.guest_label)
        column_layout.addWidget(self.sign_in_button, alignment=Qt.AlignmentFlag.AlignLeft)
        column_layout.addWidget(self.error_label)
        column_layout.addWidget(account)
        column_layout.addWidget(preferences)
        column_layout.addWidget(appearance)
        column_layout.addStretch()

        content = QWidget()
        content.setObjectName("profileContent")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(XL, XL, XL, XL)
        content_layout.addWidget(column, 1)
        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setObjectName("profileScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def refresh(self, app_state: AppState) -> None:
        self._app_state = app_state
        user = app_state.current_user
        signed_in = user is not None
        self.guest_label.setVisible(not signed_in)
        self.sign_in_button.setVisible(not signed_in)
        self.subtitle.setVisible(signed_in)
        for widget in self._account_widgets:
            widget.setVisible(signed_in)
        self._set_error("")
        if user is None:
            return
        self.name_label.setText(user.name)
        self.email_label.setText(user.email)
        if self._user_service is None:
            self.summary_label.setText("Preferences are unavailable.")
            self.edit_button.setEnabled(False)
            self.edit_name_button.setEnabled(False)
            self.theme_combo.setEnabled(False)
            return
        self.edit_button.setEnabled(True)
        self.edit_name_button.setEnabled(True)
        self.theme_combo.setEnabled(True)
        try:
            preferences = self._user_service.get_preferences(user.id)
            theme = self._user_service.get_theme(user.id)
        except UserServiceError as exc:
            self.summary_label.setText(str(exc))
            return
        self.summary_label.setText(preferences.summary())
        self._select_theme(theme)

    def _edit_name(self) -> None:
        self._set_error("")
        if self._app_state is None or self._app_state.current_user is None or self._user_service is None:
            return
        user = self._app_state.current_user
        name = self._ask_name(parent=self, name=user.name, email=user.email)
        if name is None:
            return
        try:
            self._user_service.update_profile(user.id, name)
        except UserServiceError as exc:
            self._set_error(str(exc))
            return
        self.name_label.setText(user.name)
        self.name_updated.emit()

    def _on_theme_changed(self, _index: int) -> None:
        if self._syncing_theme:
            return
        self._set_error("")
        if self._app_state is None or self._app_state.current_user is None or self._user_service is None:
            return
        theme = self.theme_combo.currentData()
        if not isinstance(theme, str):
            theme = DEFAULT_THEME
        try:
            saved = self._user_service.save_theme(self._app_state.current_user.id, theme)
        except UserServiceError as exc:
            self._set_error(str(exc))
            self._select_theme(self._app_state.theme)
            return
        self._app_state.theme = saved
        self.theme_changed.emit(saved)

    def _select_theme(self, theme: str) -> None:
        index = self.theme_combo.findData(theme if theme else DEFAULT_THEME)
        self._syncing_theme = True
        self.theme_combo.setCurrentIndex(index if index >= 0 else 0)
        self._syncing_theme = False

    def _set_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))

    @staticmethod
    def _card(title: str, hint: str, *widgets: QWidget) -> QFrame:
        frame = QFrame()
        frame.setObjectName(f"profile{title.replace(' ', '')}Card")
        apply_property(frame, "role", "card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(LG, LG, LG, LG)
        layout.setSpacing(SM)
        heading = QLabel(title)
        apply_property(heading, "role", "heading")
        caption = QLabel(hint)
        apply_property(caption, "role", "caption")
        caption.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(caption)
        layout.addSpacing(MD)
        for widget in widgets:
            if isinstance(widget, QPushButton):
                layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignLeft)
            else:
                layout.addWidget(widget)
        return frame
