"""Trusted readback boundary; never trust caller-supplied receipt fields."""
from dataclasses import dataclass

@dataclass(frozen=True)
class VerifiedObservation:
    source: str
    target: str
    operation: str
    idempotency_key: str
    outcome: str
    immutable_reference: str

class ReadbackVerifier:
    """Only an installed trusted adapter can attest an external result."""
    def __init__(self, adapter):
        self.adapter=adapter

    def inspect(self, effect):
        observation=self.adapter.readback(effect["target"],effect["operation"],effect["idempotency_key"])
        if not isinstance(observation,VerifiedObservation):
            raise PermissionError("adapter did not return a typed observation")
        if (observation.target,observation.operation,observation.idempotency_key)!=(
            effect["target"],effect["operation"],effect["idempotency_key"]):
            raise PermissionError("readback does not match effect intent")
        if observation.outcome not in ("CONFIRMED","REJECTED"):
            return {"status":"UNKNOWN","requires_reconciliation":True}
        if not observation.immutable_reference or not observation.source:
            raise PermissionError("observation lacks provenance")
        return {"status":observation.outcome,"source":observation.source,
                "proof":observation.immutable_reference,"requires_reconciliation":False}

class SyntheticReadbackAdapter:
    """Test-only adapter; must never be registered for live remote writes."""
    def __init__(self, outcomes):
        self.outcomes=outcomes
    def readback(self,target,operation,key):
        value=self.outcomes.get((target,operation,key))
        if value is None: return None
        return VerifiedObservation("synthetic-test",target,operation,key,value,
                                   "fixture:"+key)
