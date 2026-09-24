import time

from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QPushButton

from app.ui.workers import TaskRunner


def test_worker_emits_result_and_finished(qtbot, themed_app) -> None:
    runner = TaskRunner()
    results: list[object] = []
    finished = []

    signals = runner.submit(lambda: "ok")
    signals.result.connect(results.append)
    signals.finished.connect(lambda: finished.append(True))

    qtbot.waitUntil(lambda: bool(finished), timeout=2000)
    assert results == ["ok"]
    QThreadPool.globalInstance().waitForDone(1000)


def test_worker_emits_error_on_failure(qtbot, themed_app) -> None:
    runner = TaskRunner()
    errors: list[str] = []

    def boom() -> None:
        raise RuntimeError("worker exploded")

    signals = runner.submit(boom)
    signals.error.connect(errors.append)

    qtbot.waitUntil(lambda: bool(errors), timeout=2000)
    assert "worker exploded" in errors[0]
    QThreadPool.globalInstance().waitForDone(1000)


def test_worker_emits_progress(qtbot, themed_app) -> None:
    runner = TaskRunner()
    updates: list[int] = []
    finished = []

    def job(progress=None) -> str:
        if progress is not None:
            progress(40)
            progress(100)
        return "done"

    signals = runner.submit(job)
    signals.progress.connect(updates.append)
    signals.finished.connect(lambda: finished.append(True))

    qtbot.waitUntil(lambda: bool(finished), timeout=2000)
    assert updates == [40, 100]
    QThreadPool.globalInstance().waitForDone(1000)


def test_ui_stays_responsive_during_slow_task(qtbot, themed_app) -> None:
    clicks: list[int] = []
    button = QPushButton("Click me")
    button.setObjectName("workerResponsiveButton")
    button.clicked.connect(lambda: clicks.append(1))
    qtbot.addWidget(button)
    button.show()

    runner = TaskRunner()
    results: list[object] = []

    signals = runner.submit(lambda: time.sleep(0.35) or "done")
    signals.result.connect(results.append)

    qtbot.wait(80)
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: results == ["done"], timeout=2000)

    assert clicks == [1]
    QThreadPool.globalInstance().waitForDone(1000)
