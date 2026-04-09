#!/usr/bin/env python3
"""Cross-Backend Comparison: Same delegation, three backends, different governance decisions.

This is THE experiment. If the same delegation produces PERMITTED on one backend
and DENIED_FIDELITY on another, we've proven this isn't API rate limiting —
it's physics-aware governance.
"""
import sys, os, json, warnings, time
from datetime import datetime, timezone

warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/tima/aeoess-quantum-governance")

from delegation import QuantumDelegation
from calibration import fetch_calibration, check_fidelity
from qiskit import QuantumCircuit

# The delegation — same for ALL backends
# Set physics thresholds at moderate levels to find the split
delegation = QuantumDelegation(
    delegation_id="exp-cross-backend-001",
    principal_id="aeoess-research",
    agent_id="quantum-experiment-agent",
    max_shots=1024,
    max_circuit_depth=10,
    max_qubits=5,
    allowed_backends=["ibm_fez", "ibm_marrakesh", "ibm_kingston"],
    max_cost_seconds=60.0,
    min_t1_us=100.0,        # Moderate — some qubits will fail
    min_t2_us=50.0,         # Moderate
    max_readout_error=0.05,  # 5% max
    max_gate_error=0.01,     # 1% max
    max_calibration_age_hours=48.0,
    require_simulator_preflight=False,
    require_error_mitigation=False,
)

# Simple Bell state circuit — same for all backends
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

backends = ["ibm_fez", "ibm_marrakesh", "ibm_kingston"]
results = []

print("=" * 70)
print("CROSS-BACKEND GOVERNANCE EXPERIMENT")
print(f"Delegation: min_T1={delegation.min_t1_us}µs, min_T2={delegation.min_t2_us}µs")
print(f"            max_readout_error={delegation.max_readout_error}")
print(f"            max_gate_error={delegation.max_gate_error}")
print(f"Circuit: 2-qubit Bell state (H + CX)")
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
print("=" * 70)

for backend_name in backends:
    print(f"\n--- {backend_name} ---")
    try:
        # Fetch live calibration for qubits 0,1
        snapshot = fetch_calibration(backend_name, [0, 1])
        
        # Check fidelity
        passes, reasons = check_fidelity(snapshot, delegation)
        
        # Report
        q0 = snapshot.qubit_calibrations[0]
        q1 = snapshot.qubit_calibrations[1]
        
        print(f"  Qubit 0: T1={q0.t1_us:.1f}µs  T2={q0.t2_us:.1f}µs  readout_err={q0.readout_error:.4f}")
        print(f"  Qubit 1: T1={q1.t1_us:.1f}µs  T2={q1.t2_us:.1f}µs  readout_err={q1.readout_error:.4f}")
        print(f"  Overall fidelity: {snapshot.overall_fidelity_score:.4f}")
        print(f"  Calibration age: {snapshot.calibration_age_hours:.1f}h")
        
        if passes:
            print(f"  >>> DECISION: PERMITTED <<<")
        else:
            print(f"  >>> DECISION: DENIED_FIDELITY <<<")
            for r in reasons:
                print(f"      Reason: {r}")
        
        results.append({
            "backend": backend_name,
            "decision": "PERMITTED" if passes else "DENIED_FIDELITY",
            "qubit_0": {"t1_us": q0.t1_us, "t2_us": q0.t2_us, "readout_error": q0.readout_error},
            "qubit_1": {"t1_us": q1.t1_us, "t2_us": q1.t2_us, "readout_error": q1.readout_error},
            "overall_fidelity": snapshot.overall_fidelity_score,
            "calibration_age_hours": snapshot.calibration_age_hours,
            "denial_reasons": reasons if not passes else [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({"backend": backend_name, "decision": "ERROR", "error": str(e)})

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
permitted = [r for r in results if r["decision"] == "PERMITTED"]
denied = [r for r in results if r["decision"] == "DENIED_FIDELITY"]
print(f"PERMITTED: {len(permitted)} backends — {[r['backend'] for r in permitted]}")
print(f"DENIED:    {len(denied)} backends — {[r['backend'] for r in denied]}")

if permitted and denied:
    print("\n*** SPLIT FOUND! Same delegation, different governance decisions. ***")
    print("This proves physics-aware enforcement is doing real work.")
else:
    print("\nNo split found. All backends got the same decision.")
    if not permitted:
        print("All DENIED — try relaxing physics thresholds.")
    else:
        print("All PERMITTED — try tightening physics thresholds.")
    
    # If no split, try to find the threshold
    if not denied:
        print("\nSearching for split threshold...")
        # Try progressively tighter T1 thresholds
        for t1_threshold in [150, 200, 250, 300, 350, 400]:
            split_del = QuantumDelegation(
                delegation_id="exp-threshold-search",
                principal_id="aeoess-research",
                agent_id="quantum-experiment-agent",
                max_shots=1024, max_circuit_depth=10, max_qubits=5,
                allowed_backends=backends,
                max_cost_seconds=60.0,
                min_t1_us=float(t1_threshold),
                min_t2_us=50.0,
                max_readout_error=0.05,
                max_gate_error=0.01,
                max_calibration_age_hours=48.0,
                require_simulator_preflight=False,
                require_error_mitigation=False,
            )
            decisions = {}
            for backend_name in backends:
                try:
                    snap = fetch_calibration(backend_name, [0, 1])
                    p, _ = check_fidelity(snap, split_del)
                    decisions[backend_name] = "PERMIT" if p else "DENY"
                except:
                    decisions[backend_name] = "ERROR"
            
            unique = set(decisions.values())
            marker = " *** SPLIT ***" if len(unique) > 1 else ""
            print(f"  min_T1={t1_threshold}µs → {decisions}{marker}")
            if len(unique) > 1:
                break

# Save results
out_path = "/Users/tima/aeoess-quantum-governance/results/cross_backend_experiment.json"
with open(out_path, "w") as f:
    json.dump({
        "experiment": "cross-backend-governance-comparison",
        "delegation": {
            "min_t1_us": delegation.min_t1_us,
            "min_t2_us": delegation.min_t2_us,
            "max_readout_error": delegation.max_readout_error,
            "max_gate_error": delegation.max_gate_error,
        },
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, f, indent=2)
print(f"\nResults saved to {out_path}")
