#!/usr/bin/env python3
"""GHZ Counterfactual: 4-qubit GHZ state on denied vs permitted backend.
Strengthens the paper by showing fidelity gap holds beyond Bell state.
Run: cd ~/aeoess-quantum-governance && ~/aeoess-attribution-experiment/venv/bin/python3 experiment_ghz_counterfactual.py
"""
import json, warnings, time
from datetime import datetime, timezone
warnings.filterwarnings("ignore")

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

service = QiskitRuntimeService()

# 4-qubit GHZ: H on q0, then CNOT chain q0->q1->q2->q3
# Ideal output: 50% |0000⟩, 50% |1111⟩
qc = QuantumCircuit(4)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.cx(2, 3)
qc.measure_all()

SHOTS = 1000
results = {}

for bname in ["ibm_fez", "ibm_kingston"]:
    print(f"\n{'='*50}")
    print(f"  {bname} — 4-qubit GHZ (no governance)")
    print(f"{'='*50}")
    t0 = time.time()
    backend = service.backend(bname)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_qc = pm.run(qc)
    print(f"  Transpiled depth: {isa_qc.depth()}")
    sampler = SamplerV2(mode=backend)
    print(f"  Submitting {SHOTS} shots...")
    job = sampler.run([isa_qc], shots=SHOTS)
    print(f"  Job: {job.job_id()} — waiting...")
    result = job.result()
    t1 = time.time()
    counts = result[0].data.meas.get_counts()

    # GHZ fidelity: correct = |0000⟩ + |1111⟩
    correct = counts.get("0000", 0) + counts.get("1111", 0)
    total = sum(counts.values())
    wrong = total - correct
    fid = correct / total if total else 0
    err = wrong / total if total else 1

    # Show top counts
    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])[:6]
    print(f"  Top counts: {dict(sorted_counts)}")
    print(f"  GHZ fidelity: {fid*100:.1f}%  Error: {err*100:.1f}%  Time: {t1-t0:.0f}s")

    results[bname] = {"counts": counts, "correct": correct, "wrong": wrong,
        "fidelity": round(fid, 5), "error": round(err, 5),
        "job_id": job.job_id(), "transpiled_depth": isa_qc.depth(), "time": round(t1-t0,1)}

fez, king = results["ibm_fez"], results["ibm_kingston"]
gap = king["fidelity"] - fez["fidelity"]

print(f"\n{'='*60}")
print(f"GHZ COUNTERFACTUAL VERDICT")
print(f"{'='*60}")
print(f"  ibm_fez (DENIED):     {fez['fidelity']*100:.1f}% fidelity  {fez['error']*100:.1f}% error  depth={fez['transpiled_depth']}")
print(f"  ibm_kingston (PERMIT): {king['fidelity']*100:.1f}% fidelity  {king['error']*100:.1f}% error  depth={king['transpiled_depth']}")
print(f"  Gap: {gap*100:.1f} percentage points")
if gap > 0.005:
    print(f"  >>> Fidelity gap HOLDS on GHZ — governance decision consistent across circuit types <<<")
elif gap < -0.005:
    print(f"  >>> Gap reversed on GHZ — interesting, needs investigation <<<")
else:
    print(f"  >>> Gap inconclusive on GHZ <<<")

with open("results/ghz_counterfactual.json", "w") as f:
    json.dump({"experiment": "ghz-counterfactual", "circuit": "4-qubit GHZ",
        "ts": datetime.now(timezone.utc).isoformat(),
        "results": results, "fidelity_gap_pp": round(gap*100, 2)}, f, indent=2)
print(f"\nSaved: results/ghz_counterfactual.json")
