from PySide6.QtCore import QObject, Qt, Signal

QUEUED = Qt.ConnectionType.QueuedConnection


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()
    progress = Signal(int)
