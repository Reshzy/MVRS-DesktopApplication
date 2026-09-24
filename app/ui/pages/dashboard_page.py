from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.state.app_state import AppState
from app.ui.theme import apply_property
from app.ui.theme.spacing import LG, XL
from app.ui.workers import TaskRunner


class DashboardPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardPage")
        self._runner = TaskRunner(self)

        self.title = QLabel("Dashboard")
        apply_property(self.title, "role", "title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel("Temporary home. Personalized rows arrive in a later phase.")
        self.subtitle.setObjectName("dashboardSubtitle")
        apply_property(self.subtitle, "role", "subtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setWordWrap(True)

        self.demo_button = QPushButton("Simulate slow task")
        self.demo_button.setObjectName("dashboardWorkerDemoButton")
        apply_property(self.demo_button, "variant", "secondary")
        self.demo_button.clicked.connect(self._start_slow_task)

        self.demo_status = QLabel("Worker demo idle.")
        self.demo_status.setObjectName("dashboardWorkerStatus")
        apply_property(self.demo_status, "role", "caption")
        self.demo_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(XL, XL, XL, XL)
        layout.setSpacing(LG)
        layout.addStretch()
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.demo_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.demo_status)
        layout.addStretch()

    def refresh(self, app_state: AppState) -> None:
        if app_state.current_user is None:
            self.subtitle.setText("Browsing as guest. Sign in to save watchlists and ratings.")
            return
        self.subtitle.setText(f"Hello, {app_state.current_user.name}. Personalized rows arrive later.")

    def _start_slow_task(self) -> None:
        self.demo_button.setEnabled(False)
        self.demo_status.setText("Working in the background...")
        signals = self._runner.submit(_simulated_slow_task)
        signals.progress.connect(self._on_progress)
        signals.result.connect(self._on_result)
        signals.error.connect(self._on_error)
        signals.finished.connect(lambda: self.demo_button.setEnabled(True))

    def _on_progress(self, value: int) -> None:
        self.demo_status.setText(f"Working in the background... {value}%")

    def _on_result(self, value: object) -> None:
        self.demo_status.setText(str(value))

    def _on_error(self, message: str) -> None:
        self.demo_status.setText(message)


def _simulated_slow_task(progress=None) -> str:
    steps = 5
    for index in range(steps):
        time.sleep(0.2)
        if progress is not None:
            progress(int((index + 1) / steps * 100))
    return "Background task finished."
