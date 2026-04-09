#!/usr/bin/env python3
"""THE COUNTERFACTUAL: Bell state on DENIED backend vs PERMITTED backend.
Run: cd ~/aeoess-quantum-governance && ~/aeoess-attribution-experiment/venv/bin/python3 experiment_counterfactual.py
"""
import json, warnings, time
from datetime import datetime, timezone
warnings.filterwarnings("ignore")

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

service = QiskitRuntimeService()

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

SHOTS = 1000
results = {}

for bname in ["ibm_fez", "ibm_kingston"]:
    print(f"\n{'='*50}")
    print(f"  {bname} — RAW SUBMISSION (no governance)")
    print(f"{'='*50}")
    t0 = time.time()
    backend = service.backend(bname)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_qc = pm.run(qc)
    sampler = SamplerV2(mode=backend)
    print(f"  Submitting {SHOTS} shots...")
    job = sampler.run([isa_qc], shots=SHOTS)
    print(f"  Job: {job.job_id()} — waiting...")
    result = job.result()
    t1 = time.time()
    counts = result[0].data.meas.get_counts()
    correct = counts.get("00", 0) + counts.get("11", 0)
    wrong = counts.get("01", 0) + counts.get("10", 0)
    total = correct + wrong
    fid = correct / total if total else 0
    err = wrong / total if total else 1
    print(f"  Counts: {dict(sorted(counts.items()))}")
    print(f"  Bell fidelity: {fid*100:.1f}%  Error: {err*100:.1f}%  Time: {t1-t0:.0f}s")
    results[bname] = {"counts": counts, "correct": correct, "wrong": wrong,
        "fidelity": round(fid, 5), "error": round(err, 5), "job_id": job.job_id(), "time": round(t1-t0,1)}

fez, king = results["ibm_fez"], results["ibm_kingston"]
gap = king["fidelity"] - fez["fidelity"]
print(f"\n{'='*60}")
print(f"VERDICT")
print(f"{'='*60}")
print(f"  ibm_fez (DENIED):     {fez['fidelity']*100:.1f}% fidelity  {fez['error']*100:.1f}% error")
print(f"  ibm_kingston (PERMIT): {king['fidelity']*100:.1f}% fidelity  {king['error']*100:.1f}% error")
print(f"  Gap: {gap*100:.1f} percentage points")
if gap > 0.005:
    print(f"  >>> GOVERNANCE WAS CORRECT — denied backend produced worse results <<<")
elif gap < -0.005:
    print(f"  >>> Surprising — denied backend was actually better <<<")
else:
    print(f"  >>> Results roughly equal — T1 threshold was conservative for this circuit <<<")

with open("results/counterfactual.json", "w") as f:
    json.dump({"experiment": "counterfactual", "ts": datetime.now(timezone.utc).isoformat(),
        "results": results, "fidelity_gap_pp": round(gap*100, 2)}, f, indent=2)
print(f"\nSaved: results/counterfactual.json")
