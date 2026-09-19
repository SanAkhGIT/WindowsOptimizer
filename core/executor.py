from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
from core.verification import verify_tweak
from core.operation_receipts import ReceiptItem, complete, new_receipt, save

@dataclass
class OperationResult:
    tweak_id:str
    status:str
    message:str
    verification:str
    timestamp:str

class Executor:
    def __init__(self,log_dir=None):
        self.log_dir=Path(log_dir or (Path.home()/"WindowsOptimizerBackups")); self.log_dir.mkdir(parents=True,exist_ok=True)
    def apply(self,tweaks):
        results=[]
        receipt=new_receipt('manual')
        for tweak in tweaks:
            try:
                message=tweak.apply() if tweak.apply else "No apply action defined."
                verified,verification=verify_tweak(tweak)
                status="VERIFIED" if verified is True else ("APPLIED" if verified is None else "UNVERIFIED")
            except Exception as exc:
                message=str(exc); verification="Not run because the operation failed."; status="FAILED"
            results.append(OperationResult(tweak.id,status,message,verification,datetime.now().isoformat(timespec="seconds")))
        stamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        (self.log_dir/f"apply_{stamp}.json").write_text(json.dumps([r.__dict__ for r in results],indent=2),encoding="utf-8")
        receipt_items = tuple(
            ReceiptItem("tweak", r.tweak_id, "apply", r.status, r.message, r.verification)
            for r in results
        )
        save(complete(receipt, receipt_items), self.log_dir.parent)
        return results
