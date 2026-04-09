# Quantum Governance — APS for Quantum Compute

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19478584.svg)](https://doi.org/10.5281/zenodo.19478584)

**APS (Agent Passport System) governing IBM Quantum hardware execution.**

This is not API rate limiting. The gateway queries real-time hardware calibration data and enforces **physical quality constraints** before permitting execution. The receipt cryptographically binds the execution result to the hardware state at the moment of execution.

## What This Proves

Traditional agent governance enforces: budgets, scopes, delegation chains.

Quantum governance adds: **hardware fidelity as a first-class constraint dimension.**

Before an agent can execute a quantum circuit, the gateway:
1. Checks **budget facets**: shots, circuit depth, qubit count, backend allowlist
2. Fetches **live calibration** from IBM Quantum: T1/T2 coherence times, readout errors, gate errors
3. Evaluates **physics facets** from the delegation: is every qubit above the minimum T1? Is every gate below the maximum error rate? Is the calibration data fresh enough?
4. If all pass: executes via SamplerV2 and produces a **signed receipt** binding the decision, calibration snapshot, and execution result

The receipt is Ed25519-signed. A verifier can confirm: this circuit ran on this hardware in this physical state at this time, authorized by this delegation chain.

## Delegation Schema

```python
QuantumDelegation(
    # Budget facets (standard)
    max_shots=4000,
    max_circuit_depth=20,
    max_qubits=5,
    allowed_backends=["ibm_kingston"],

    # Physics facets (THE NOVELTY)
    min_t1_us=20.0,           # minimum T1 coherence in microseconds
    min_t2_us=10.0,           # minimum T2 dephasing time
    max_readout_error=0.05,   # max 5% readout error per qubit
    max_gate_error=0.01,      # max 1% gate error
    max_calibration_age_hours=4.0,  # calibration must be fresh
)
```

Delegations support **monotonic narrowing**: a child delegation can only be MORE restrictive than its parent. A planner agent can delegate to an executor with tighter physics requirements.

## Run

```bash
cd ~/aeoess-quantum-governance
~/aeoess-attribution-experiment/venv/bin/python3 demo.py
```

## Demo Scenarios

| Demo | Decision | Why |
|------|----------|-----|
| 1. Bell state | PERMITTED | Budget and fidelity checks pass, runs on real hardware |
| 2. Excess shots | DENIED_BUDGET | 5000 shots requested, delegation allows 100 |
| 3. Strict physics | DENIED_FIDELITY | min_T1=500us, no qubit meets this on current hardware |
| 4. Hybrid workflow | PERMITTED | Planner narrows delegation for executor, narrowing validated |

## Architecture

```
Agent Intent
    |
    v
[Budget Gate] ── shots, depth, qubits, backend
    |
    v
[Calibration Fetch] ── live T1, T2, gate errors from IBM
    |
    v
[Fidelity Gate] ── delegation physics facets vs live hardware
    |
    v
[Execute] ── SamplerV2 on IBM Quantum
    |
    v
[Receipt] ── Ed25519-signed proof binding decision + calibration + result
```

## Files

| File | Purpose |
|------|---------|
| `delegation.py` | Quantum delegation with budget + physics facets, monotonic narrowing |
| `calibration.py` | Live IBM Quantum calibration fetch + fidelity checking |
| `gateway.py` | Enforcement engine: budget gate, fidelity gate, execute, receipt |
| `receipt.py` | Ed25519-signed receipts with calibration snapshots |
| `demo.py` | Four demo scenarios |

## License

Apache-2.0. Part of [AEOESS](https://aeoess.com).

## Paper

T. Pidlisnyi, "Physics-Enforced Delegation: Governing Quantum Hardware Quality in Autonomous Agent Workflows," Zenodo, 2026. [doi:10.5281/zenodo.19478584](https://doi.org/10.5281/zenodo.19478584)
