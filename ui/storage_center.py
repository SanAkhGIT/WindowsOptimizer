from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox

from modules.storage_center import (
    candidates, system_drive, recycle_bin_status, cleanup_temp,
    cleanup_crash_dumps, cleanup_update_downloads, empty_recycle_bin,
    open_storage_settings, open_cleanup_recommendations, run_disk_cleanup,
)


class StorageCenterPanel(QWidget):
    def __init__(self, output, run_job, is_admin, parent=None):
        super().__init__(parent)
        self.output, self.run_job, self.is_admin = output, run_job, is_admin
        self._build()

    def _build(self):
        layout=QVBoxLayout(self)
        title=QLabel("Storage Center"); title.setObjectName("section"); layout.addWidget(title)
        info=QLabel("Analyze first. Cleanup actions show an explicit confirmation and use age-based or Windows-supported cleanup paths. Downloads and arbitrary user data are never silently deleted.")
        info.setObjectName("muted"); info.setWordWrap(True); layout.addWidget(info)

        row=QHBoxLayout()
        for label,fn in [
            ("Analyze",self.analyze),("Storage Sense",self.open_storage),
            ("Cleanup recommendations",self.open_recommendations),("Disk Cleanup",self.disk_cleanup),
            ("Recycle Bin status",self.recycle_status)
        ]:
            b=QPushButton(label); b.clicked.connect(fn); row.addWidget(b)
        layout.addLayout(row)

        actions=QHBoxLayout()
        for label,fn in [
            ("Clean user temp",self.clean_temp),("Clean crash dumps",self.clean_crash),
            ("Clean Update cache",self.clean_update),("Empty Recycle Bin",self.empty_bin)
        ]:
            b=QPushButton(label); b.clicked.connect(fn); actions.addWidget(b)
        layout.addLayout(actions)

        self.table=QTableWidget(0,5)
        self.table.setHorizontalHeaderLabels(["Category","Size","Risk","Path","Description"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table,1)

    def analyze(self):
        self.run_job(self._analysis,done=self._show,fail=self._error)

    def _analysis(self):
        drive=system_drive(); items=candidates()
        lines=[f"System drive: {drive['free']/1024**3:.1f} GB free / {drive['total']/1024**3:.1f} GB"]
        for x in items: lines.append(f"{x.name}: {x.size_bytes/1024**2:.1f} MB | {x.risk} | {x.path}")
        return "\n".join(lines),items

    def _show(self,result):
        text,items=result if isinstance(result,tuple) else (str(result),[])
        self.output.setPlainText(text)
        self.table.setRowCount(len(items))
        for i,x in enumerate(items):
            vals=[x.name,f"{x.size_bytes/1024**2:.1f} MB",x.risk,x.path,x.description]
            for j,v in enumerate(vals): self.table.setItem(i,j,QTableWidgetItem(str(v)))

    def _confirm(self,title,message):
        return QMessageBox.question(self,title,message) == QMessageBox.StandardButton.Yes

    def clean_temp(self):
        if self._confirm("Clean temporary files","Remove user temporary files older than 48 hours? In-use files will be skipped."):
            self.run_job(cleanup_temp,done=self._show_result,fail=self._error)

    def clean_crash(self):
        if self._confirm("Clean crash dumps","Remove user crash dumps older than 14 days?"):
            self.run_job(cleanup_crash_dumps,done=self._show_result,fail=self._error)

    def clean_update(self):
        if not self.is_admin():
            QMessageBox.warning(self,"Administrator required","Run as Administrator to clean the Windows Update download cache.")
            return
        if self._confirm("Clean Update cache","Remove files from the Windows Update download cache? Windows can recreate these files."):
            self.run_job(cleanup_update_downloads,done=self._show_result,fail=self._error)

    def empty_bin(self):
        if self._confirm("Empty Recycle Bin","Permanently remove items currently in the Recycle Bin?"):
            self.run_job(empty_recycle_bin,done=self._show_result,fail=self._error)

    def recycle_status(self):
        self.run_job(recycle_bin_status,done=self._show_result,fail=self._error)

    def open_storage(self):
        self.run_job(open_storage_settings,done=self._show_result,fail=self._error)

    def open_recommendations(self):
        self.run_job(open_cleanup_recommendations,done=self._show_result,fail=self._error)

    def disk_cleanup(self):
        self.run_job(run_disk_cleanup,done=self._show_result,fail=self._error)

    def _show_result(self,value):
        self.output.setPlainText(str(value))
    def _error(self,error):
        self.output.setPlainText(f"Operation failed:\n{error}")
