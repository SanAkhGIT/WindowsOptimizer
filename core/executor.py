from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
from core.verification import verify_tweak
from core.operation_receipts import ReceiptItem, complete, new_receipt, save
from core.logging import get_logger, log_exception

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
        logger = get_logger("executor")
        results=[]
        receipt=new_receipt('manual')
        logger.info("Manual tweak batch started | count=%s", len(tweaks))
        for tweak in tweaks:
            logger.info("Tweak started | id=%s | name=%s", tweak.id, tweak.name)
            try:
                message=tweak.apply() if tweak.apply else "No apply action defined."
                verified,verification=verify_tweak(tweak)
                status="VERIFIED" if verified is True else ("APPLIED" if verified is None else "UNVERIFIED")
            except Exception as exc:
                message=str(exc); verification="Not run because the operation failed."; status="FAILED"
                log_exception(logger, f"Tweak failed | id={tweak.id}", exc)
            logger.info("Tweak completed | id=%s | status=%s | verification=%s", tweak.id, status, verification)
            results.append(OperationResult(tweak.id,status,message,verification,datetime.now().isoformat(timespec="seconds")))
        stamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        (self.log_dir/f"apply_{stamp}.json").write_text(json.dumps([r.__dict__ for r in results],indent=2),encoding="utf-8")
        receipt_items = tuple(
            ReceiptItem("tweak", r.tweak_id, "apply", r.status, r.message, r.verification)
            for r in results
        )
        receipt_path = save(complete(receipt, receipt_items), self.log_dir.parent)
        logger.info("Manual tweak batch completed | receipt=%s", receipt_path)
        return results
