import os
import time

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

    @staticmethod
    def _emit(signal, value=None):
        try:
            signal.emit() if value is None else signal.emit(value)
            return True
        except RuntimeError:
            return False

    def run(self):
        logger = get_logger("jobs")
        operation = getattr(self.fn, "__qualname__", repr(self.fn))
        logger.info("Job started | operation=%s | args=%r", operation, self.args)
        self._emit(self.signals.started)
        try:
            result = self.fn(*self.args, **self.kwargs)
            logger.info("Job finished | operation=%s | result_type=%s", operation, type(result).__name__)
            self._emit(self.signals.finished, result)
        except Exception as exc:
            log_exception(logger, f"Job failed | operation={operation}", exc)
            self._emit(self.signals.failed, f"{type(exc).__name__}: {exc}")


class JobRunner(QObject):
    """Shared worker facade.

    A runner owns its jobs until their terminal signal is delivered.  Callers
    can therefore safely connect UI slots without QRunnable lifetime races.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool.globalInstance()
        # Windows operations are predominantly subprocess/IO bound. Use the CPU topology
        # as a practical worker ceiling while retaining a minimum of four slots.
        self.pool.setMaxThreadCount(max(4, self.pool.idealThreadCount()))
        self._active_jobs = set()
        self._started_at = {}

    @property
    def active_count(self):
        return len(self._active_jobs)

    def submit(self, fn, *args, job_priority=0, **kwargs):
        """Submit one task; higher priority tasks are scheduled first."""
        job = Job(fn, *args, **kwargs)
        self._active_jobs.add(job)
        self._started_at[job] = time.monotonic()

        def release(*_args):
            self._active_jobs.discard(job)
            self._started_at.pop(job, None)

        job.signals.finished.connect(release)
        job.signals.failed.connect(release)
        self.pool.start(job, int(job_priority))
        return job.signals

    def submit_many(self, tasks):
        """Start independent tasks concurrently on the shared worker pool.

        Each task is ``(fn, args, kwargs)`` or ``(fn, args, kwargs, priority)``.
        Use priorities to keep interactive/telemetry work responsive while
        allowing slower inventory work to run in parallel.
        """
        signals = []
        for task in tasks:
            if len(task) == 3:
                fn, args, kwargs = task
                priority = 0
            elif len(task) == 4:
                fn, args, kwargs, priority = task
            else:
                raise ValueError("tasks must contain 3 or 4 items")
            signals.append(self.submit(fn, *args, job_priority=priority, **kwargs))
        return signals

    def capacity(self):
        """Return worker-pool capacity for diagnostics and smart scheduling."""
        active = self.pool.activeThreadCount()
        maximum = self.pool.maxThreadCount()
        return {
            "logical_cpus": os.cpu_count() or 1,
            "max_workers": maximum,
            "active_jobs": self.active_count,
            "active_workers": active,
            "available_workers": max(0, maximum - active),
        }