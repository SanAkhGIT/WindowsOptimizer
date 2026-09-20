from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from core.jobs import JobRunner


def _wait_for_terminal(signals, timeout_ms=3000):
    loop = QEventLoop()
    result = {"finished": [], "failed": []}
    signals.finished.connect(lambda value: (result["finished"].append(value), loop.quit()))
    signals.failed.connect(lambda error: (result["failed"].append(error), loop.quit()))
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    return result


def test_job_runner_releases_completed_job():
    app = QCoreApplication.instance() or QCoreApplication([])
    runner = JobRunner()
    signals = runner.submit(lambda: "ok")

    result = _wait_for_terminal(signals)

    assert result["finished"] == ["ok"]
    assert result["failed"] == []
    assert runner.active_count == 0
    app.processEvents()


def test_job_runner_reports_failure_and_releases_job():
    app = QCoreApplication.instance() or QCoreApplication([])
    runner = JobRunner()

    def fail():
        raise ValueError("expected failure")

    signals = runner.submit(fail)
    result = _wait_for_terminal(signals)

    assert result["finished"] == []
    assert result["failed"]
    assert "ValueError: expected failure" in result["failed"][0]
    assert runner.active_count == 0
    app.processEvents()


def test_job_runner_runs_independent_tasks_in_parallel():
    app = QCoreApplication.instance() or QCoreApplication([])
    runner = JobRunner()
    signals = runner.submit_many([
        (lambda: "one", (), {}),
        (lambda: "two", (), {}),
        (lambda: "three", (), {}),
    ])
    results = []
    loop = QEventLoop()
    remaining = {"count": len(signals)}
    for signal in signals:
        signal.finished.connect(results.append)
        signal.finished.connect(lambda _value: (remaining.__setitem__("count", remaining["count"] - 1), loop.quit() if remaining["count"] == 0 else None))
    QTimer.singleShot(3000, loop.quit)
    loop.exec()
    assert sorted(results) == ["one", "three", "two"]
    assert runner.active_count == 0
    assert runner.capacity()["max_workers"] >= 4
    app.processEvents()

def test_task_plan_runs_dependency_graph():
    app = QCoreApplication.instance() or QCoreApplication([])
    runner = JobRunner()
    from core.jobs import TaskPlan, TaskSpec
    completed = []
    loop = QEventLoop()
    plan = TaskPlan([
        TaskSpec("network", lambda: "network", resource="network"),
        TaskSpec("storage", lambda: "storage", resource="storage"),
        TaskSpec("summary", lambda: "summary", depends_on=("network", "storage"), resource="summary"),
    ])
    def complete(name, value, error):
        completed.append((name, value, error))
        if name == "summary":
            loop.quit()
    runner.submit_plan(plan, on_complete=complete)
    QTimer.singleShot(3000, loop.quit)
    loop.exec()
    assert ("summary", "summary", None) in completed
    assert runner.active_count == 0
    app.processEvents()


def test_task_plan_rejects_unknown_dependency():
    from core.jobs import TaskPlan, TaskSpec
    try:
        TaskPlan([TaskSpec("a", lambda: None, depends_on=("missing",))])
    except ValueError as exc:
        assert "Unknown task dependencies" in str(exc)
    else:
        raise AssertionError("expected dependency validation failure")