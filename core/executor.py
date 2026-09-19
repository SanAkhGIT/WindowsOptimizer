from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

@dataclass
class OperationResult:
    tweak_id: str
    status: str
    message: str
    timestamp: str

class Executor:
    def __init__(self, log_dir=None):
        self.log_dir=Path(log_dir or (Path.home()/"WindowsOptimizerBackups")); self.log_dir.mkdir(parents=True,exist_ok=True)
    def apply(self,tweaks):
        results=[]
        for t in tweaks:
            try: msg=t.apply() if t.apply else "No apply action defined."; status="APPLIED"
            except Exception as e: msg=str(e); status="FAILED"
            results.append(OperationResult(t.id,status,msg,datetime.now().isoformat(timespec="seconds")))
        stamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S"); (self.log_dir/f"apply_{stamp}.json").write_text(json.dumps([r.__dict__ for r in results],indent=2),encoding="utf-8"); return results
