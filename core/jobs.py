from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from core.logging import get_logger, log_exception


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
        logger = get_logger("jobs")
        operation = getattr(self.fn, "__qualname__", repr(self.fn))
        logger.info("Job started | operation=%s | args=%r", operation, self.args)
        self.signals.started.emit()
        try:
            result = self.fn(*self.args, **self.kwargs)
            logger.info("Job finished | operation=%s | result_type=%s", operation, type(result).__name__)
            self.signals.finished.emit(result)
        except Exception as exc:
            log_exception(logger, f"Job failed | operation={operation}", exc)
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
