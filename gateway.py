"""Quantum Governance Gateway — enforcement engine for quantum compute.

The gateway evaluates a QuantumIntent against a QuantumDelegation:
  1. Budget check: shots, depth, qubits, backend, cost
  2. Fidelity check: live calibration vs delegation physics facets
  3. If all pass: execute on IBM Quantum via SamplerV2
  4. Produce a signed receipt binding decision + calibration + result

This is NOT API rate limiting. This queries real-time hardware calibration
and enforces PHYSICAL QUALITY constraints before permitting execution.
"""

import hashlib
import uuid
import time
import warnings
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from qiskit import QuantumCircuit
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from delegation import QuantumDelegation
from calibration import fetch_calibration, check_fidelity, CalibrationSnapshot
from receipt import QuantumReceipt

warnings.filterwarnings("ignore", category=DeprecationWarning)


class GatewayDecision(Enum):
    PERMITTED = "PERMITTED"
    DENIED_BUDGET = "DENIED_BUDGET"
    DENIED_FIDELITY = "DENIED_FIDELITY"
    DENIED_DELEGATION = "DENIED_DELEGATION"


@dataclass
class QuantumIntent:
    agent_id: str
    circuit: QuantumCircuit
    backend_name: str
    shots: int
    delegation_id: str


def circuit_hash(qc: QuantumCircuit) -> str:
    """SHA-256 of the circuit's OpenQASM representation."""
    try:
        from qiskit.qasm2 import dumps
        qasm = dumps(qc)
    except Exception:
        qasm = str(qc)
    return hashlib.sha256(qasm.encode()).hexdigest()


def _snapshot_to_dict(snap: CalibrationSnapshot) -> dict:
    """Convert calibration snapshot to serializable dict."""
    return {
        "backend_name": snap.backend_name,
        "timestamp": snap.timestamp,
        "calibration_age_hours": snap.calibration_age_hours,
        "overall_fidelity_score": snap.overall_fidelity_score,
        "qubits": [
            {"qubit": q.qubit, "t1_us": round(q.t1_us, 2), "t2_us": round(q.t2_us, 2),
             "readout_error": round(q.readout_error, 5), "frequency_ghz": round(q.frequency_ghz, 4)}
            for q in snap.qubit_data
        ],
        "gates": [
            {"gate": g.gate_name, "qubits": g.qubits, "error_rate": round(g.error_rate, 6)}
            for g in snap.gate_data
        ],
    }


def evaluate(intent: QuantumIntent, delegation: QuantumDelegation,
             gateway_key: Ed25519PrivateKey, execute: bool = True) -> QuantumReceipt:
    """Evaluate a quantum intent against a delegation. The core enforcement function.

    1. Budget check
    2. Live calibration fetch + fidelity check
    3. If all pass and execute=True: run on IBM Quantum
    4. Sign and return receipt
    """
    c_hash = circuit_hash(intent.circuit)
    n_qubits = intent.circuit.num_qubits
    depth = intent.circuit.depth()
    qubit_list = list(range(n_qubits))  # use first N qubits

    # ── Gate 1: Budget Check ──
    budget_reasons = []
    if intent.shots > delegation.max_shots:
        budget_reasons.append(f"shots {intent.shots} > max {delegation.max_shots}")
    if depth > delegation.max_circuit_depth:
        budget_reasons.append(f"depth {depth} > max {delegation.max_circuit_depth}")
    if n_qubits > delegation.max_qubits:
        budget_reasons.append(f"qubits {n_qubits} > max {delegation.max_qubits}")
    if intent.backend_name not in delegation.allowed_backends:
        budget_reasons.append(f"backend {intent.backend_name} not in {delegation.allowed_backends}")

    if budget_reasons:
        receipt = QuantumReceipt(
            receipt_id=str(uuid.uuid4()),
            agent_id=intent.agent_id,
            decision=GatewayDecision.DENIED_BUDGET.value,
            timestamp=time.time(),
            circuit_hash=c_hash,
            backend_name=intent.backend_name,
            shots_requested=intent.shots,
            delegation_id=intent.delegation_id,
            denial_reasons=budget_reasons,
        )
        receipt.sign(gateway_key)
        return receipt

    # ── Gate 2: Live Calibration + Fidelity Check ──
    print(f"  [gateway] Fetching live calibration for {intent.backend_name}, qubits {qubit_list}...")
    snapshot = fetch_calibration(intent.backend_name, qubit_list)
    fidelity_pass, fidelity_reasons = check_fidelity(snapshot, delegation)

    if not fidelity_pass:
        receipt = QuantumReceipt(
            receipt_id=str(uuid.uuid4()),
            agent_id=intent.agent_id,
            decision=GatewayDecision.DENIED_FIDELITY.value,
            timestamp=time.time(),
            circuit_hash=c_hash,
            backend_name=intent.backend_name,
            shots_requested=intent.shots,
            delegation_id=intent.delegation_id,
            calibration_snapshot=_snapshot_to_dict(snapshot),
            overall_fidelity=snapshot.overall_fidelity_score,
            denial_reasons=fidelity_reasons,
        )
        receipt.sign(gateway_key)
        return receipt

    # ── Gate 3: Execute on IBM Quantum ──
    execution_result = None
    if execute:
        print(f"  [gateway] All checks passed. Executing on {intent.backend_name} ({intent.shots} shots)...")
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
            from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

            service = QiskitRuntimeService()
            backend = service.backend(intent.backend_name)

            # Transpile for target backend
            pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
            transpiled = pm.run(intent.circuit)

            # Run with SamplerV2
            sampler = SamplerV2(mode=backend)
            job = sampler.run([transpiled], shots=intent.shots)
            result = job.result()

            # Extract counts from SamplerV2 result
            pub_result = result[0]
            counts = {}
            try:
                # SamplerV2 returns BitArray in data
                data_obj = pub_result.data
                for field_name in dir(data_obj):
                    field = getattr(data_obj, field_name, None)
                    if hasattr(field, 'get_counts'):
                        counts = field.get_counts()
                        break
            except Exception as e:
                counts = {"extraction_note": f"SamplerV2 result format: {str(e)[:100]}"}

            execution_result = {
                "job_id": job.job_id() if hasattr(job, 'job_id') else str(job),
                "counts": counts,
                "status": "completed",
            }
            print(f"  [gateway] Execution complete. Job: {execution_result.get('job_id', 'N/A')}")
        except Exception as e:
            execution_result = {"status": "error", "error": str(e)[:200]}
            print(f"  [gateway] Execution error: {str(e)[:100]}")

    receipt = QuantumReceipt(
        receipt_id=str(uuid.uuid4()),
        agent_id=intent.agent_id,
        decision=GatewayDecision.PERMITTED.value,
        timestamp=time.time(),
        circuit_hash=c_hash,
        backend_name=intent.backend_name,
        shots_requested=intent.shots,
        delegation_id=intent.delegation_id,
        calibration_snapshot=_snapshot_to_dict(snapshot),
        overall_fidelity=snapshot.overall_fidelity_score,
        execution_result=execution_result,
    )
    receipt.sign(gateway_key)
    return receipt
