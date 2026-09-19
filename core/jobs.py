from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool

class JobSignals(QObject):
    started=Signal()
    finished=Signal(object)
    failed=Signal(str)

class Job(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__(); self.fn=fn; self.args=args; self.kwargs=kwargs; self.signals=JobSignals()
    def run(self):
        self.signals.started.emit()
        try: self.signals.finished.emit(self.fn(*self.args,**self.kwargs))
        except Exception as exc: self.signals.failed.emit(str(exc))

class JobRunner(QObject):
    def __init__(self):
        super().__init__(); self.pool=QThreadPool.globalInstance()
    def submit(self,fn,*args,**kwargs):
        job=Job(fn,*args,**kwargs); self.pool.start(job); return job.signals
