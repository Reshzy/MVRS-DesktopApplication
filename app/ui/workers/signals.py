from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()
    progress = Signal(int)
