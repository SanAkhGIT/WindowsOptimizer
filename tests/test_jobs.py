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
