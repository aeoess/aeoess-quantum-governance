"""Quantum Execution Receipt — cryptographically signed proof of governance decision.

The receipt binds: the governance decision (permit/deny), the circuit hash,
the live hardware calibration snapshot, and the execution result into a single
Ed25519-signed artifact. A verifier can confirm: this circuit ran on this
hardware in this state at this time, authorized by this delegation.
"""

import json
import hashlib
import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


@dataclass
class QuantumReceipt:
    receipt_id: str
    agent_id: str
    decision: str  # PERMITTED, DENIED_BUDGET, DENIED_FIDELITY, DENIED_DELEGATION
    timestamp: float
    circuit_hash: str
    backend_name: str
    shots_requested: int
    delegation_id: str
    calibration_snapshot: Optional[Dict] = None
    denial_reasons: Optional[List[str]] = None
    execution_result: Optional[Dict] = None
    overall_fidelity: Optional[float] = None
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def canonical_bytes(self) -> bytes:
        d = self.to_dict()
        d.pop("signature", None)
        return json.dumps(d, sort_keys=True, separators=(",", ":"), default=str).encode()

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def sign(self, private_key: Ed25519PrivateKey):
        sig = private_key.sign(self.canonical_bytes())
        self.signature = sig.hex()

    def verify(self, public_key: Ed25519PublicKey) -> bool:
        if not self.signature:
            return False
        try:
            public_key.verify(bytes.fromhex(self.signature), self.canonical_bytes())
            return True
        except Exception:
            return False

    def to_json(self, indent=2) -> str:
        d = self.to_dict()
        d["content_hash"] = self.content_hash()
        return json.dumps(d, indent=indent, default=str)


def verify_receipt_json(receipt_json: str, public_key: Ed25519PublicKey) -> bool:
    """Verify a receipt from its JSON representation."""
    d = json.loads(receipt_json)
    sig = d.pop("signature", None)
    d.pop("content_hash", None)
    if not sig:
        return False
    canonical = json.dumps(d, sort_keys=True, separators=(",", ":"), default=str).encode()
    try:
        public_key.verify(bytes.fromhex(sig), canonical)
        return True
    except Exception:
        return False
