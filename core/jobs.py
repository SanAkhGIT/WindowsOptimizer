from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool


class JobSignals(QObject):
    started = Signal()
    finished = Signal(object)
    failed = Signal(str)


class Job(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = JobSignals()
        self.setAutoDelete(True)

    def run(self):
        self.signals.started.emit()
        try:
            self.signals.finished.emit(self.fn(*self.args, **self.kwargs))
        except Exception as exc:
            self.signals.failed.emit(f"{type(exc).__name__}: {exc}")


class JobRunner(QObject):
    """Small shared thread-pool facade for Windows operations and telemetry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool.globalInstance()

    def submit(self, fn, *args, **kwargs):
        job = Job(fn, *args, **kwargs)
        self.pool.start(job)
        return job.signals
