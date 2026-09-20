import os
import time
import threading
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, Signal, QRunnable, QThread, QThreadPool
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


@dataclass(frozen=True)
class TaskSpec:
    name: str
    fn: object
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    depends_on: tuple = ()
    resource: str = "default"
    priority: int = 0


class TaskPlan:
    def __init__(self, tasks):
        tasks = list(tasks)
        self.tasks = {task.name: task for task in tasks}
        if len(self.tasks) != len(tasks):
            raise ValueError("Task names must be unique")
        unknown = {d for task in tasks for d in task.depends_on if d not in self.tasks}
        if unknown:
            raise ValueError(f"Unknown task dependencies: {sorted(unknown)}")
        self._validate_acyclic()

    def _validate_acyclic(self):
        visiting, visited = set(), set()
        def visit(name):
            if name in visiting:
                raise ValueError("Task plan contains a dependency cycle")
            if name in visited:
                return
            visiting.add(name)
            for dep in self.tasks[name].depends_on:
                visit(dep)
            visiting.remove(name)
            visited.add(name)
        for name in self.tasks:
            visit(name)


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
        self.pool.setMaxThreadCount(max(4, QThread.idealThreadCount()))
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

    def submit_plan(self, plan, on_complete=None):
        """Run independent tasks concurrently while respecting dependencies/resources."""
        if not isinstance(plan, TaskPlan):
            plan = TaskPlan(plan)
        state = {name: "pending" for name in plan.tasks}
        signals = {}
        resource_active = set()
        lock = threading.RLock()

        def dispatch():
            with lock:
                for name, task in plan.tasks.items():
                    if state[name] != "pending":
                        continue
                    if any(state[d] == "failed" for d in task.depends_on):
                        state[name] = "failed"
                        if on_complete:
                            on_complete(name, None, "dependency failed")
                        continue
                    if any(state[d] != "done" for d in task.depends_on):
                        continue
                    if task.resource in resource_active:
                        continue
                    resource_active.add(task.resource)
                    state[name] = "running"
                    sig = self.submit(task.fn, *task.args, job_priority=task.priority, **task.kwargs)
                    signals[name] = sig

                    def done(value, task_name=name, resource=task.resource):
                        with lock:
                            state[task_name] = "done"
                            resource_active.discard(resource)
                        if on_complete:
                            on_complete(task_name, value, None)
                        dispatch()

                    def failed(error, task_name=name, resource=task.resource):
                        with lock:
                            state[task_name] = "failed"
                            resource_active.discard(resource)
                        if on_complete:
                            on_complete(task_name, None, error)
                        dispatch()

                    sig.finished.connect(done)
                    sig.failed.connect(failed)
        dispatch()
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