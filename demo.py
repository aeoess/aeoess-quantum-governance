#!/usr/bin/env python3
"""Quantum Governance Demo — four scenarios showing APS governing quantum compute.

Run: cd ~/aeoess-quantum-governance && ~/aeoess-attribution-experiment/venv/bin/python3 demo.py

Demo 1: PERMITTED — Bell state on real hardware (passes budget + fidelity)
Demo 2: DENIED_BUDGET — Shots exceed delegation limit
Demo 3: DENIED_FIDELITY — Physics facets set unrealistically high
Demo 4: HYBRID WORKFLOW — Multi-agent delegation chain with narrowing
"""

import os
import sys
import json
import warnings
import time

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*urllib3.*")

from qiskit import QuantumCircuit

from delegation import QuantumDelegation, narrow, generate_keypair
from gateway import QuantumIntent, evaluate
from receipt import QuantumReceipt

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

BACKEND = "ibm_kingston"  # 156 qubits, Open Plan


def save_receipt(receipt: QuantumReceipt, filename: str):
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, "w") as f:
        f.write(receipt.to_json(indent=2))
    print(f"  Saved: {path}")


def bell_circuit() -> QuantumCircuit:
    """Simple 2-qubit Bell state: |00> + |11>"""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


def main():
    print("=" * 60)
    print("AEOESS Quantum Governance — Proof of Concept")
    print("=" * 60)
    print()

    # Setup: generate gateway + agent keypairs
    gw_privkey, gw_pubkey, gw_pubhex = generate_keypair()
    principal_privkey, principal_pubkey, principal_pubhex = generate_keypair()
    agent_privkey, agent_pubkey, agent_pubhex = generate_keypair()
    executor_privkey, executor_pubkey, executor_pubhex = generate_keypair()

    print(f"Gateway public key:   {gw_pubhex[:16]}...")
    print(f"Principal public key: {principal_pubhex[:16]}...")
    print(f"Agent A public key:   {agent_pubhex[:16]}...")
    print(f"Executor public key:  {executor_pubhex[:16]}...")
    print()

    # ══════════════════════════════════════
    # DEMO 1: PERMITTED — Real hardware execution
    # ══════════════════════════════════════
    print("─" * 60)
    print("DEMO 1: PERMITTED (Bell state on real hardware)")
    print("─" * 60)

    delegation1 = QuantumDelegation(
        delegation_id="del-quantum-001",
        delegated_to=agent_pubhex,
        delegated_by=principal_pubhex,
        max_shots=4000,
        max_circuit_depth=20,
        max_qubits=5,
        allowed_backends=[BACKEND],
        min_t1_us=20.0,      # realistic: most qubits exceed this
        min_t2_us=10.0,
        max_readout_error=0.1,  # 10% — generous
        max_gate_error=0.05,    # 5% — generous
        max_calibration_age_hours=24.0,
    )
    delegation1.sign(principal_privkey)
    print(f"  Delegation signed: {delegation1.delegation_id}")
    print(f"  Constraints: max_shots={delegation1.max_shots}, min_T1={delegation1.min_t1_us}us, max_gate_error={delegation1.max_gate_error}")

    intent1 = QuantumIntent(
        agent_id=agent_pubhex,
        circuit=bell_circuit(),
        backend_name=BACKEND,
        shots=1000,
        delegation_id=delegation1.delegation_id,
    )

    receipt1 = evaluate(intent1, delegation1, gw_privkey, execute=True)
    print(f"  Decision: {receipt1.decision}")
    if receipt1.execution_result:
        print(f"  Job ID: {receipt1.execution_result.get('job_id', 'N/A')}")
        counts = receipt1.execution_result.get("counts", {})
        if counts:
            print(f"  Counts: {dict(list(counts.items())[:5])}")
    if receipt1.calibration_snapshot:
        print(f"  Fidelity: {receipt1.overall_fidelity}")
        for q in receipt1.calibration_snapshot.get("qubits", []):
            print(f"    Qubit {q['qubit']}: T1={q['t1_us']}us T2={q['t2_us']}us readout_err={q['readout_error']}")
    print(f"  Signature valid: {receipt1.verify(gw_pubkey)}")
    save_receipt(receipt1, "demo1-permitted.json")
    print()

    # ══════════════════════════════════════
    # DEMO 2: DENIED_BUDGET — Shots exceed limit
    # ══════════════════════════════════════
    print("─" * 60)
    print("DEMO 2: DENIED_BUDGET (shots exceed delegation limit)")
    print("─" * 60)

    delegation2 = QuantumDelegation(
        delegation_id="del-quantum-002",
        delegated_to=agent_pubhex,
        delegated_by=principal_pubhex,
        max_shots=100,  # very tight limit
        max_circuit_depth=5,
        max_qubits=2,
        allowed_backends=[BACKEND],
    )
    delegation2.sign(principal_privkey)

    intent2 = QuantumIntent(
        agent_id=agent_pubhex,
        circuit=bell_circuit(),
        backend_name=BACKEND,
        shots=5000,  # exceeds max_shots=100
        delegation_id=delegation2.delegation_id,
    )

    receipt2 = evaluate(intent2, delegation2, gw_privkey, execute=False)
    print(f"  Decision: {receipt2.decision}")
    print(f"  Denial reasons: {receipt2.denial_reasons}")
    print(f"  Signature valid: {receipt2.verify(gw_pubkey)}")
    save_receipt(receipt2, "demo2-denied-budget.json")
    print()

    # ══════════════════════════════════════
    # DEMO 3: DENIED_FIDELITY — Physics constraints too strict
    # ══════════════════════════════════════
    print("─" * 60)
    print("DEMO 3: DENIED_FIDELITY (unrealistic physics requirements)")
    print("─" * 60)

    delegation3 = QuantumDelegation(
        delegation_id="del-quantum-003",
        delegated_to=agent_pubhex,
        delegated_by=principal_pubhex,
        max_shots=4000,
        max_circuit_depth=20,
        max_qubits=5,
        allowed_backends=[BACKEND],
        min_t1_us=500.0,    # 500us — most qubits are 100-300us, many below
        min_t2_us=400.0,    # 400us — unrealistically high
        max_readout_error=0.001,  # 0.1% — extremely tight
        max_gate_error=0.0001,    # 0.01% — impossible on current hardware
    )
    delegation3.sign(principal_privkey)
    print(f"  Constraints: min_T1={delegation3.min_t1_us}us, min_T2={delegation3.min_t2_us}us, max_gate_error={delegation3.max_gate_error}")

    intent3 = QuantumIntent(
        agent_id=agent_pubhex,
        circuit=bell_circuit(),
        backend_name=BACKEND,
        shots=1000,
        delegation_id=delegation3.delegation_id,
    )

    receipt3 = evaluate(intent3, delegation3, gw_privkey, execute=False)
    print(f"  Decision: {receipt3.decision}")
    if receipt3.denial_reasons:
        for r in receipt3.denial_reasons[:5]:
            print(f"    - {r}")
        if len(receipt3.denial_reasons) > 5:
            print(f"    ... and {len(receipt3.denial_reasons) - 5} more")
    print(f"  Signature valid: {receipt3.verify(gw_pubkey)}")
    save_receipt(receipt3, "demo3-denied-fidelity.json")
    print()

    # ══════════════════════════════════════
    # DEMO 4: HYBRID WORKFLOW — Multi-agent delegation chain
    # ══════════════════════════════════════
    print("─" * 60)
    print("DEMO 4: HYBRID WORKFLOW (planner → executor with narrowing)")
    print("─" * 60)

    # Principal creates broad delegation for planner agent
    parent_del = QuantumDelegation(
        delegation_id="del-quantum-parent",
        delegated_to=agent_pubhex,
        delegated_by=principal_pubhex,
        max_shots=10000,
        max_circuit_depth=50,
        max_qubits=10,
        allowed_backends=["ibm_fez", "ibm_marrakesh", "ibm_kingston"],
        min_t1_us=20.0,
        max_gate_error=0.05,
    )
    parent_del.sign(principal_privkey)
    print(f"  Parent delegation: {parent_del.delegation_id}")
    print(f"    max_shots={parent_del.max_shots}, backends={parent_del.allowed_backends}")

    # Planner narrows for executor: fewer shots, single backend, tighter physics
    child_del = QuantumDelegation(
        delegation_id="del-quantum-child",
        delegated_to=executor_pubhex,
        delegated_by=agent_pubhex,
        max_shots=2000,      # narrowed from 10000
        max_circuit_depth=20, # narrowed from 50
        max_qubits=5,         # narrowed from 10
        allowed_backends=[BACKEND],  # narrowed from 3 backends
        min_t1_us=30.0,       # stricter than parent's 20
        max_gate_error=0.03,  # stricter than parent's 0.05
    )

    # Verify narrowing passes
    try:
        narrow(parent_del, child_del)
        print(f"  Child delegation: {child_del.delegation_id} (narrowing valid)")
        print(f"    max_shots={child_del.max_shots}, backends={child_del.allowed_backends}, min_T1={child_del.min_t1_us}us")
    except ValueError as e:
        print(f"  NARROWING FAILED: {e}")
        return

    child_del.sign(agent_privkey)

    # Executor runs with the narrowed delegation
    intent4 = QuantumIntent(
        agent_id=executor_pubhex,
        circuit=bell_circuit(),
        backend_name=BACKEND,
        shots=500,
        delegation_id=child_del.delegation_id,
    )

    receipt4 = evaluate(intent4, child_del, gw_privkey, execute=False)  # don't burn more QPU time
    print(f"  Decision: {receipt4.decision}")
    print(f"  Signature valid: {receipt4.verify(gw_pubkey)}")
    save_receipt(receipt4, "demo4-hybrid-workflow.json")
    print()

    # ══════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    results = [
        ("Demo 1", receipt1.decision),
        ("Demo 2", receipt2.decision),
        ("Demo 3", receipt3.decision),
        ("Demo 4", receipt4.decision),
    ]
    for name, decision in results:
        icon = "✓" if decision == "PERMITTED" else "✗"
        print(f"  {icon} {name}: {decision}")
    print()
    print(f"All receipts saved to {RESULTS_DIR}/")
    print(f"Gateway public key for verification: {gw_pubhex}")


if __name__ == "__main__":
    main()
