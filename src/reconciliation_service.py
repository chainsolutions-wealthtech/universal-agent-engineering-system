"""Fail-closed, bounded reconciliation of unknown effects using readback adapters.

This layer never dispatches remote writes. Production use requires a separately
authenticated, reviewed adapter and a scoped execution mandate.
"""
import json
from src.effect_journal import EffectJournal
from src.receipt_verifier import ReadbackVerifier

class ReconciliationService:
    def __init__(self, db, adapter):
        self.db=db
        self.journal=EffectJournal(db)
        self.verifier=ReadbackVerifier(adapter)

    def reconcile_once(self, limit=25):
        if not (1 <= limit <= 100):
            raise ValueError("bounded batch required")
        rows=self.db.execute(
            """SELECT id, target, operation, idempotency_key
            FROM effects WHERE state IN ('IN_FLIGHT','UNKNOWN')
            ORDER BY created_at, id LIMIT ?""",(limit,)).fetchall()
        report={"checked":0,"resolved":0,"unknown":0}
        for eid,target,operation,key in rows:
            report["checked"]+=1
            try:
                result=self.verifier.inspect({"target":target,
                    "operation":operation,"idempotency_key":key})
            except (PermissionError, ValueError, TimeoutError, OSError):
                report["unknown"]+=1
                continue
            if result["status"]=="UNKNOWN":
                report["unknown"]+=1
                continue
            # A typed response does not imply authentication: only explicitly
            # trusted provider adapters may be installed in production.
            self.journal.resolve(eid,result["status"]=="CONFIRMED",
                {"source":result["source"],"proof":result["proof"]})
            report["resolved"]+=1
        return report
