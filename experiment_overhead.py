#!/usr/bin/env python3
"""Governance Overhead Benchmark: How much latency does the fidelity check add?
Run: cd ~/aeoess-quantum-governance && ~/aeoess-attribution-experiment/venv/bin/python3 experiment_overhead.py
"""
import json, warnings, time
from datetime import datetime, timezone
warnings.filterwarnings("ignore")

from delegation import QuantumDelegation
from calibration import fetch_calibration, check_fidelity

delegation = QuantumDelegation(
    delegation_id="overhead-bench", delegated_by="p", delegated_to="a",
    min_t1_us=80.0, min_t2_us=40.0, max_readout_error=0.05, max_gate_error=0.01,
    max_calibration_age_hours=48.0, require_simulator_preflight=False, require_error_mitigation=False)

backend = "ibm_kingston"
qubits = [0, 1]
N_RUNS = 5

print(f"Governance Overhead Benchmark — {N_RUNS} runs on {backend}")
print("=" * 60)

timings = []
for i in range(N_RUNS):
    # Step 1: Calibration fetch
    t0 = time.time()
    snap = fetch_calibration(backend, qubits)
    t_cal = time.time()

    # Step 2: Policy evaluation
    passes, reasons = check_fidelity(snap, delegation)
    t_pol = time.time()

    # Step 3: Receipt signing (simulate)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = Ed25519PrivateKey.generate()
    sig = key.sign(b"test-receipt-payload-" + str(i).encode())
    t_sig = time.time()

    cal_ms = (t_cal - t0) * 1000
    pol_ms = (t_pol - t_cal) * 1000
    sig_ms = (t_sig - t_pol) * 1000
    total_ms = (t_sig - t0) * 1000

    print(f"  Run {i+1}: cal={cal_ms:.0f}ms  policy={pol_ms:.1f}ms  sign={sig_ms:.1f}ms  TOTAL={total_ms:.0f}ms")
    timings.append({"run": i+1, "calibration_ms": round(cal_ms,1), "policy_ms": round(pol_ms,2),
        "signing_ms": round(sig_ms,2), "total_ms": round(total_ms,1)})

avg_cal = sum(t["calibration_ms"] for t in timings) / N_RUNS
avg_pol = sum(t["policy_ms"] for t in timings) / N_RUNS
avg_sig = sum(t["signing_ms"] for t in timings) / N_RUNS
avg_tot = sum(t["total_ms"] for t in timings) / N_RUNS

print(f"\nAverages ({N_RUNS} runs):")
print(f"  Calibration fetch: {avg_cal:.0f}ms")
print(f"  Policy evaluation: {avg_pol:.1f}ms")
print(f"  Receipt signing:   {avg_sig:.1f}ms")
print(f"  TOTAL overhead:    {avg_tot:.0f}ms")
print(f"\nIBM Quantum queue time: typically 10-120 seconds")
print(f"Governance overhead as % of queue: {avg_tot/10000*100:.1f}% to {avg_tot/120000*100:.2f}%")

with open("results/overhead.json", "w") as f:
    json.dump({"experiment": "overhead-benchmark", "backend": backend, "n_runs": N_RUNS,
        "timings": timings, "averages": {"cal_ms": round(avg_cal,1), "policy_ms": round(avg_pol,2),
        "signing_ms": round(avg_sig,2), "total_ms": round(avg_tot,1)},
        "ts": datetime.now(timezone.utc).isoformat()}, f, indent=2)
print(f"\nSaved: results/overhead.json")
