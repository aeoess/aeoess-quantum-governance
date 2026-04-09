"""Quantum Delegation — Budget, physics, and assurance constraints for quantum compute.

The KEY NOVELTY: delegations encode not just budget limits (shots, depth, qubits)
but PHYSICAL HARDWARE QUALITY requirements (T1, T2, gate error, readout error,
calibration freshness). A child delegation can only be MORE restrictive than its
parent — monotonic narrowing, same invariant as APS delegation chains.
"""

import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


@dataclass
class QuantumDelegation:
    delegation_id: str
    delegated_to: str  # agent public key hex
    delegated_by: str  # principal public key hex

    # Budget facets
    max_shots: int = 10000
    max_circuit_depth: int = 100
    max_qubits: int = 20
    allowed_backends: List[str] = field(default_factory=lambda: ["ibm_fez", "ibm_marrakesh", "ibm_kingston"])
    max_cost_seconds: float = 600.0

    # Physics facets — THIS IS THE NOVELTY
    # These enforce hardware quality BEFORE permitting execution
    min_t1_us: float = 50.0       # minimum T1 coherence time in microseconds
    min_t2_us: float = 30.0       # minimum T2 dephasing time in microseconds
    max_readout_error: float = 0.05  # max 5% readout error per qubit
    max_gate_error: float = 0.01     # max 1% gate error
    max_calibration_age_hours: float = 4.0  # calibration must be < 4 hours old

    # Assurance facets
    require_simulator_preflight: bool = False
    require_error_mitigation: bool = True

    created_at: float = field(default_factory=time.time)
    signature: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    def canonical_bytes(self):
        d = self.to_dict()
        d.pop("signature", None)
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()

    def content_hash(self):
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


def narrow(parent: QuantumDelegation, child: QuantumDelegation) -> QuantumDelegation:
    """Enforce monotonic narrowing: child can only be MORE restrictive than parent.

    Budget facets: child values must be <= parent
    Physics facets: child minimums must be >= parent (stricter), child maximums must be <= parent (stricter)
    Backends: child must be subset of parent
    """
    errors = []

    # Budget: child <= parent
    if child.max_shots > parent.max_shots:
        errors.append(f"max_shots: child {child.max_shots} > parent {parent.max_shots}")
    if child.max_circuit_depth > parent.max_circuit_depth:
        errors.append(f"max_circuit_depth: child {child.max_circuit_depth} > parent {parent.max_circuit_depth}")
    if child.max_qubits > parent.max_qubits:
        errors.append(f"max_qubits: child {child.max_qubits} > parent {parent.max_qubits}")
    if child.max_cost_seconds > parent.max_cost_seconds:
        errors.append(f"max_cost_seconds: child {child.max_cost_seconds} > parent {parent.max_cost_seconds}")

    # Backends: child must be subset
    child_set = set(child.allowed_backends)
    parent_set = set(parent.allowed_backends)
    if not child_set.issubset(parent_set):
        errors.append(f"allowed_backends: child has {child_set - parent_set} not in parent")

    # Physics: child minimums must be >= parent (stricter quality)
    if child.min_t1_us < parent.min_t1_us:
        errors.append(f"min_t1_us: child {child.min_t1_us} < parent {parent.min_t1_us}")
    if child.min_t2_us < parent.min_t2_us:
        errors.append(f"min_t2_us: child {child.min_t2_us} < parent {parent.min_t2_us}")

    # Physics: child maximums must be <= parent (tighter error bounds)
    if child.max_readout_error > parent.max_readout_error:
        errors.append(f"max_readout_error: child {child.max_readout_error} > parent {parent.max_readout_error}")
    if child.max_gate_error > parent.max_gate_error:
        errors.append(f"max_gate_error: child {child.max_gate_error} > parent {parent.max_gate_error}")
    if child.max_calibration_age_hours > parent.max_calibration_age_hours:
        errors.append(f"max_calibration_age_hours: child {child.max_calibration_age_hours} > parent {parent.max_calibration_age_hours}")

    if errors:
        raise ValueError(f"Monotonic narrowing violations:\n" + "\n".join(f"  - {e}" for e in errors))

    return child


def generate_keypair():
    """Generate Ed25519 keypair, return (private_key, public_key_hex)."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return private_key, public_key, pub_bytes.hex()
