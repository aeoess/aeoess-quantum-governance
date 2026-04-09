#!/usr/bin/env python3
"""Calibration Drift Monitor — runs periodically, logs governance decisions over time."""
import sys, json, warnings, os
from datetime import datetime, timezone
warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/tima/aeoess-quantum-governance")

from delegation import QuantumDelegation
from calibration import fetch_calibration, check_fidelity

delegation = QuantumDelegation(
    delegation_id="drift-monitor",
    delegated_by="aeoess-research-principal",
    delegated_to="drift-monitor-agent",
    min_t1_us=80.0, min_t2_us=40.0,
    max_readout_error=0.05, max_gate_error=0.01,
    max_calibration_age_hours=48.0,
    require_simulator_preflight=False, require_error_mitigation=False)

backends = ["ibm_fez", "ibm_marrakesh", "ibm_kingston"]
ts = datetime.now(timezone.utc).isoformat()
entry = {"timestamp": ts, "backends": {}}

for b in backends:
    try:
        snap = fetch_calibration(b, [0, 1])
        passes, reasons = check_fidelity(snap, delegation)
        entry["backends"][b] = {
            "decision": "PERMIT" if passes else "DENY",
            "q0_t1": snap.qubit_data[0].t1_us,
            "q1_t1": snap.qubit_data[1].t1_us,
            "q0_t2": snap.qubit_data[0].t2_us,
            "q1_t2": snap.qubit_data[1].t2_us,
            "fidelity": snap.overall_fidelity_score,
            "cal_age_h": snap.calibration_age_hours,
            "reasons": reasons if not passes else []
        }
    except Exception as e:
        entry["backends"][b] = {"decision": "ERROR", "error": str(e)}

# Append to drift log
log_path = "/Users/tima/aeoess-quantum-governance/results/drift_log.jsonl"
with open(log_path, "a") as f:
    f.write(json.dumps(entry) + "\n")

print(f"[{ts}] Logged: " + " | ".join(
    f"{b}={entry['backends'][b]['decision']}" for b in backends))
