# Physics-Enforced Delegation: Governing Quantum Hardware Quality in Autonomous Agent Workflows

**Tymofii Pidlisnyi**
AEOESS (Independent)
signal@aeoess.com

*Preprint. April 2026. doi:10.5281/zenodo.19478584*

*Note: Reviewers also suggested the titles "Calibration-Aware Delegation for Governed Quantum Execution" and "Physics-Aware Governance for Delegated Quantum Computation." We retain "Physics-Enforced Delegation" as the most concise descriptor of the mechanism.*

---

## Abstract

As autonomous systems and AI agents begin to access quantum cloud resources, existing agent governance frameworks enforce only budgets and delegation scope, not physical execution quality. We present a governance framework that enforces hardware fidelity constraints before permitting agent-mediated quantum computation. The framework extends cryptographic delegation chains with physics facets (coherence times, gate errors, readout errors, calibration freshness) that participate in the same monotonic narrowing invariant as budget and scope constraints. A cross-backend experiment on IBM Quantum hardware (ibm_fez, ibm_marrakesh, ibm_kingston) shows that governance correctly denies a backend where qubit T1 falls below the delegation threshold (39.1 µs vs. 80 µs minimum), while permitting backends meeting the constraint. A counterfactual experiment indicates a 5.2 percentage point Bell state fidelity gap between the denied and permitted backends (92.9% vs. 98.1%), empirically supporting the governance decision. Governance overhead is 4.2 ms for policy evaluation and receipt signing; the dominant cost is the external calibration API call (4.5 s), which is cacheable. Ed25519-signed receipts cryptographically bind each governance decision to the hardware calibration state at the moment of evaluation.

## 1. Introduction

The convergence of autonomous AI agents and quantum cloud computing creates a governance gap. Agents deployed through frameworks such as LangChain, CrewAI, and Google A2A can now access quantum hardware through cloud APIs, requesting circuit execution as naturally as they invoke web search or database queries. However, quantum computation has a property that distinguishes it from classical API calls: results can appear structurally valid while reflecting degraded physical execution quality. A 2-qubit Bell state measurement that returns `{00: 500, 11: 500}` appears correct whether it ran on a well-calibrated superconducting qubit or a decoherent one. The difference is visible only in the error rate, and the error rate depends on hardware conditions that change hourly.

Existing agent governance systems address identity, delegation chains, scope authorization, and budget enforcement. The Agent Passport System [1] provides monotonically narrowing delegation with cryptographic receipts. The DIF Trust Framework [2] defines credential exchange protocols. The IETF DAAP working group [3] is standardizing agent-to-agent delegation. To our knowledge, existing delegation and agent-governance frameworks do not make hardware quality constraints first-class delegation conditions.

This paper introduces physics-enforced delegation: a governance mechanism that extends agent delegation chains with hardware quality constraints. Before permitting a quantum circuit to execute, the governance gateway queries live calibration data from the hardware provider and evaluates it against physics facets specified in the delegation. If the hardware fails to meet the required coherence times, gate error rates, or readout error bounds, the execution is denied with a signed receipt explaining why. If the hardware passes, the execution proceeds and the receipt cryptographically binds the result to the calibration state at the moment of evaluation.

The contributions are: (1) a delegation schema that encodes both budget and physics constraints with monotonic narrowing, (2) a gateway protocol that enforces live calibration checks before execution, (3) a cryptographic receipt structure that binds governance decisions to hardware state, and (4) experimental validation on three IBM Quantum backends showing governance correctly distinguishes hardware quality.

## 2. Background and Related Work

### 2.1 Capability Attenuation and Delegation

The principle that delegated authority can only decrease originates with Dennis and Van Horn [4], who formalized capability attenuation in the context of multiprogrammed computations. Their insight that a subprocess should never exceed the authority of its creator is the foundation for all subsequent capability-based security. Our monotonic narrowing invariant is a direct descendant of this lineage, applied to the agent delegation domain.

Birgisson et al. [5] extended capability attenuation to distributed authorization with macaroons: bearer tokens carrying contextual caveats that can be appended but never removed. Each caveat further restricts the token's authority. Our physics facets are structurally analogous to macaroon caveats: a parent delegation specifying `min_t1_us=50` can be narrowed by a child to `min_t1_us=80`, but never widened. The key difference is that our caveats are evaluated against live hardware state rather than static context.

The Agent Passport System (APS) [1] implements cryptographic delegation chains where authority can only decrease at each transfer point. Delegations specify scope, spend limits, and expiry; sub-delegations must be strictly narrower on every dimension. The monotonic narrowing invariant ensures that no agent in the chain can exceed the authority granted by its principal. Faceted Authority Attenuation [6] formalizes this as a 15-dimensional constraint vector evaluated in under 2 ms.

### 2.2 Quantum Cloud Access and Hardware-Aware Compilation

IBM Quantum Platform provides cloud access to superconducting quantum processors through Qiskit Runtime. Javadi-Abhari et al. [7] describe the Qiskit software stack, including the transpilation pipeline and the SamplerV2 primitive used in our experiments. Backend calibration data, including per-qubit T1/T2 coherence times and per-gate error rates, is accessible through the backend properties API. Calibration data is refreshed approximately daily, and hardware conditions can drift between calibrations.

Murali et al. [8] demonstrated noise-adaptive compiler mappings that use calibration data to improve circuit fidelity at compile time. Their ASPLOS 2019 work showed that routing qubits to less noisy physical locations during transpilation produces measurably better results. Our approach operates at a different layer: rather than optimizing qubit placement within a backend, we govern which backends an agent may use at all. The two approaches are complementary. An agent with a physics-enforced delegation could use noise-adaptive compilation on a backend that has already passed the governance fidelity gate.

The Quantum Device Management Interface (QDMI) working group has proposed standardized interfaces for quantum hardware management [9], but does not address governance or delegation. Hybrid quantum-classical orchestration systems [10] manage task routing but do not enforce quality constraints at the delegation layer.

### 2.3 Backend Selection and Quality Prediction

Salm et al. [11] developed the NISQ Analyzer, which automates backend selection by matching circuit requirements to hardware properties. Their system considers gate set, qubit connectivity, and error rates to recommend the most suitable backend for a given circuit. This is the closest prior work to ours. The NISQ Analyzer selects backends; our framework governs the selection within a delegation chain and produces auditable cryptographic receipts for every decision.

Quetschlich et al. [12] extended this direction by predicting the quality of quantum computation on candidate backends, enabling informed selection before execution. Their prediction models use calibration data and circuit structure to estimate expected fidelity.

Prior work has used calibration and hardware characteristics for backend selection, compilation, and orchestration. Our contribution is orthogonal: we place quality constraints inside a delegation and governance layer, enforce them at authorization time, and emit auditable cryptographic receipts. The novelty is not hardware-aware routing itself, but its integration into a delegation chain with monotonic narrowing and signed receipts.

## 3. System Design

### 3.1 Delegation Schema

A quantum delegation extends the standard APS delegation with three facet categories.

**Budget facets** constrain resource consumption: `max_shots` (maximum measurement repetitions per circuit), `max_circuit_depth` (maximum gate layers), `max_qubits` (maximum quantum register width), `allowed_backends` (permitted hardware list), and `max_cost_seconds` (wall-clock budget).

**Physics facets** constrain hardware quality: `min_t1_us` (minimum T1 relaxation time in microseconds), `min_t2_us` (minimum T2 dephasing time), `max_readout_error` (maximum per-qubit measurement error rate), `max_gate_error` (maximum per-gate error rate), and `max_calibration_age_hours` (maximum staleness of calibration data).

**Assurance facets** specify additional requirements: `require_simulator_preflight` (run on simulator before hardware) and `require_error_mitigation` (apply error suppression techniques).

All facets participate in monotonic narrowing. When a planner agent sub-delegates to an executor agent, every budget facet in the child delegation must be at most equal to the parent's value, every physics minimum must be at least equal to the parent's minimum, and every physics maximum must be at most equal to the parent's maximum. The backend allowlist must be a subset. This ensures that authority over hardware quality, like authority over scope and budget, can only decrease through the delegation chain.

**Table 1.** Delegation facets and narrowing direction.

| Facet | Type | Narrowing Direction |
|-------|------|-------------------|
| max_shots | Budget | child ≤ parent |
| max_circuit_depth | Budget | child ≤ parent |
| max_qubits | Budget | child ≤ parent |
| allowed_backends | Budget | child ⊆ parent |
| min_t1_us | Physics | child ≥ parent |
| min_t2_us | Physics | child ≥ parent |
| max_readout_error | Physics | child ≤ parent |
| max_gate_error | Physics | child ≤ parent |
| max_calibration_age_hours | Physics | child ≤ parent |

The `max_calibration_age_hours` facet narrows downward (child ≤ parent) because a smaller maximum age imposes a stricter freshness requirement, consistent with the monotonic narrowing principle that child delegations can only be more restrictive.

### 3.2 Gateway Enforcement Protocol

The governance gateway evaluates a quantum intent (agent identity, circuit, backend, shots, delegation reference) through a sequential gate pipeline:

1. **Budget gate.** The gateway checks that the requested shots, circuit depth, qubit count, and backend fall within the delegation's budget facets. If any check fails, the gateway returns a DENIED_BUDGET receipt without contacting the hardware provider. This gate is purely local and executes in under 1 ms.

2. **Calibration fetch.** The gateway queries the hardware provider's calibration API for the specific qubits the circuit will use. The response includes per-qubit T1, T2, and readout error, and per-gate error rates. The gateway records the calibration timestamp and computes the data age.

3. **Fidelity gate.** The gateway evaluates each calibration value against the delegation's physics facets. Every qubit used by the circuit must have T1 above `min_t1_us`, T2 above `min_t2_us`, and readout error below `max_readout_error`. Every gate used must have error rate below `max_gate_error`. The calibration data must be newer than `max_calibration_age_hours`. If any check fails, the gateway returns a DENIED_FIDELITY receipt containing the full calibration snapshot and the specific violations.

4. **Execute.** If all gates pass, the gateway transpiles the circuit for the target backend and submits it through the Qiskit Runtime SamplerV2 primitive [7]. The measurement counts are included in the receipt.

5. **Receipt.** The gateway constructs a receipt containing: a UUID, the agent identity, the governance decision, a SHA-256 hash of the circuit's QASM representation, the full calibration snapshot, and (if executed) the measurement results. The receipt is signed with the gateway's Ed25519 key. A verifier holding the gateway's public key can confirm the receipt's integrity and verify the governance decision.

[Figure 1: Gateway enforcement pipeline. Shows the sequential flow: Agent Intent → Budget Gate → Calibration Fetch (IBM API) → Fidelity Gate → Execute/Deny → Signed Receipt. Budget denial short-circuits before the calibration fetch.]

### 3.3 Cryptographic Receipt

The receipt binds the governance decision to the hardware state at the moment of evaluation. This addresses a fundamental epistemic problem in quantum cloud computing: without the receipt, a consumer of quantum results has no evidence about the conditions under which those results were produced. The receipt provides cryptographic proof that (a) a specific delegation authorized the execution, (b) the hardware met specific quality thresholds at the time of evaluation, and (c) the execution produced specific measurement results.

The receipt is canonical-JSON serialized, SHA-256 hashed, and Ed25519 signed. The signature covers all fields except itself. Verification requires only the gateway's public key, which is published at a well-known JWKS endpoint.

## 4. Evaluation

### 4.1 Experimental Setup

All experiments ran on IBM Quantum Open Plan hardware in April 2026. Three backends were available: ibm_fez (156 qubits, Heron R2), ibm_marrakesh (156 qubits, Heron R2), and ibm_kingston (156 qubits, Heron R2). The test circuit is a 2-qubit Bell state: a Hadamard gate on qubit 0, a CNOT from qubit 0 to qubit 1, and measurement of both qubits. The ideal output distribution is 50% `|00⟩` and 50% `|11⟩` with 0% for `|01⟩` and `|10⟩`. A second circuit, a 4-qubit GHZ state (Hadamard on qubit 0, CNOT chain from qubit 0 through qubits 1, 2, and 3, measurement of all qubits), was used to test whether the governance decision generalizes beyond the minimal Bell state. The ideal GHZ output distribution is 50% `|0000⟩` and 50% `|1111⟩`. All experiments used 1000 shots. The software stack was Qiskit 2.2.3 [7], qiskit-ibm-runtime 0.43.1, and Python 3.9.

### 4.2 Cross-Backend Governance Split

A single delegation with `min_t1_us=80` was evaluated against all three backends. The governance gateway fetched live calibration data for qubits 0 and 1 on each backend and applied the fidelity gate.

**Table 2.** Cross-backend governance split (same delegation, same circuit).

| Backend | Decision | Qubit 0 T1 (µs) | Qubit 1 T1 (µs) | Qubit 0 T2 (µs) | CX Error | Fidelity Score |
|---------|----------|-----------------|-----------------|-----------------|----------|---------------|
| ibm_fez | DENIED | 39.14 | 231.52 | 42.10 | 0.0080 | 0.9896 |
| ibm_marrakesh | PERMITTED | 383.79 | 161.45 | 51.65 | 0.0080 | 0.9916 |
| ibm_kingston | PERMITTED | 382.16 | 304.44 | 375.49 | 0.0080 | 0.9917 |

The fidelity score reported in Table 2 is computed as the product of (1 - gate_error) for each gate and (1 - readout_error) for each qubit involved in the circuit. This is an estimated pre-execution quality metric derived from calibration data, distinct from the measured Bell-state fidelity reported in Table 3.

[Figure 2: Cross-backend governance split. Bar chart showing Qubit 0 T1 values for ibm_fez (39.1 µs), ibm_marrakesh (383.8 µs), and ibm_kingston (382.2 µs), with a horizontal threshold line at 80 µs. ibm_fez falls below the governance threshold.]

The ibm_fez backend was denied because qubit 0's T1 of 39.14 µs fell below the 80 µs delegation minimum. The other two backends passed all physics facets. The T1 variation across backends is striking: qubit 0 on ibm_fez had nearly 10x shorter coherence time than the same qubit index on ibm_kingston. All three backends showed identical CX gate error (0.008), suggesting the T1 disparity was the governance-relevant differentiator.

This result illustrates why budget-only governance is insufficient. A budget-only governance layer would not distinguish these backends by hardware quality; the physics-aware policy does.

### 4.3 Counterfactual Backend Comparison

To test whether the governance decision was empirically supported, the Bell state circuit was executed on both the denied backend (ibm_fez) and a permitted backend (ibm_kingston) without governance enforcement.

**Table 3.** Counterfactual execution: denied vs. permitted backend.

| Backend | Governance Decision | Counts (00) | Counts (11) | Counts (01) | Counts (10) | Bell Fidelity | Error Rate |
|---------|-------------------|------------|------------|------------|------------|--------------|-----------|
| ibm_fez | DENIED | 461 | 468 | 25 | 46 | 92.9% | 7.1% |
| ibm_kingston | PERMITTED | 486 | 495 | 9 | 10 | 98.1% | 1.9% |

The fidelity gap is 5.2 percentage points. The error rate on the denied backend is 3.7x higher than on the permitted backend. The governance decision is empirically supported: the denied backend produced measurably worse results for the same circuit.

The `|01⟩` and `|10⟩` outcomes (which should be zero for an ideal Bell state) account for 7.1% of shots on ibm_fez versus 1.9% on ibm_kingston. This is consistent with the reported calibration disparity, though this single-circuit experiment does not isolate which specific calibration parameter contributed most to the observed error gap.

To test whether the fidelity gap persists on a more complex circuit, the 4-qubit GHZ state was executed on both backends under the same conditions (1000 shots, qubits 0-3, transpiled depth 16).

**Table 3b.** Counterfactual execution: 4-qubit GHZ state on denied vs. permitted backend.

| Backend | Governance Decision | GHZ Fidelity | Error Rate |
|---------|-------------------|-------------|-----------|
| ibm_fez | DENIED | 87.1% (871/1000) | 12.9% |
| ibm_kingston | PERMITTED | 94.8% (948/1000) | 5.2% |

The fidelity gap widened from 5.2 percentage points on the Bell state to 7.7 percentage points on the GHZ circuit. This is consistent with error accumulation: the GHZ circuit uses three CNOT gates (versus one for the Bell state), amplifying the quality difference between backends. The governance decision is empirically supported across both circuit types tested.

### 4.4 Governance Overhead

The governance overhead was benchmarked over 5 runs on ibm_kingston.

**Table 4.** Governance overhead breakdown (5 runs, ibm_kingston).

| Component | Mean (ms) | Range (ms) | Notes |
|-----------|----------|-----------|-------|
| Policy evaluation | 0.01 | 0.01-0.01 | Budget + fidelity check |
| Receipt signing (Ed25519) | 4.22 | 0.53-18.86 | First run includes key loading |
| Calibration fetch (IBM API) | 4489.1 | 3431.6-7050.5 | External API call |
| **Total** | **4493.3** | **3432.2-7069.3** | |

The first-run signing latency (18.86 ms) includes Ed25519 key loading and initialization. Excluding the first run, the steady-state signing latency is 0.53-0.61 ms (mean 0.56 ms).

The governance logic itself (policy evaluation + signing) consumes 4.2 ms. The dominant cost is the external calibration API call at 4.5 seconds mean. This call is cacheable in deployments where policy permits reuse of backend-property snapshots within a bounded TTL. Calibration data is valid for hours, and a cache with a 30-minute TTL would eliminate the API call for all but the first evaluation in each window. With caching, governance overhead is under 5 ms, which is negligible compared to quantum job queue times (typically 10-60 seconds on the Open Plan).

### 4.5 Gate Error Threshold

The delegation's `max_gate_error` facet creates a binary governance boundary. With the observed CX gate error of 0.008, a delegation specifying `max_gate_error=0.01` permits execution while `max_gate_error=0.005` denies it. This boundary is deterministic given the calibration data: the governance decision is fully reproducible from the receipt's embedded calibration snapshot.

### 4.6 Depth vs. Estimated Fidelity

Circuit fidelity degrades with depth as errors accumulate through successive gate layers. An estimated circuit fidelity was computed as the product of individual gate fidelities raised to the number of applications. Target depths of 1, 5, 10, 20, 30, and 50 were transpiled to actual depths of 4, 12, 22, 42, 62, and 102 respectively due to basis gate decomposition on the Heron R2 native gate set.

**Table 5.** Estimated circuit fidelity by transpiled depth (ibm_kingston).

| Transpiled Depth | Estimated Fidelity |
|-----------------|--------------------|
| 4 | 0.989 |
| 12 | 0.967 |
| 22 | 0.941 |
| 42 | 0.890 |
| 62 | 0.841 |
| 102 | 0.752 |

Fidelity decreases from 0.989 at depth 4 to 0.752 at depth 102. This suggests that a depth-aware governance extension, where the delegation specifies a minimum acceptable circuit fidelity rather than per-gate thresholds, would be a natural improvement. The current system checks per-gate error rates independently; accumulated circuit fidelity is not yet enforced.

## 5. Discussion

### 5.1 Trust Boundary

The governance gateway trusts the calibration data provided by the hardware vendor's API. This is a meaningful trust assumption: if the vendor reports incorrect calibration data, the governance decision may be wrong. Signed calibration reports from hardware providers, analogous to trusted execution environment attestations, would strengthen this trust boundary. The receipt structure is designed to accommodate signed calibration data when providers support it.

A related concern is temporal: calibration data may be hours old, and hardware conditions can drift between calibration and execution. The receipt binds the epistemic state at decision time, not execution time. The `max_calibration_age_hours` facet partially mitigates this by requiring fresh data, but the gap between "calibration data says the hardware is good" and "the hardware is good right now" is inherent to any system that relies on cached measurements.

**Trust model.** Trusted: gateway signing key integrity, vendor API response integrity in transit (TLS), delegation signature verification. Partially trusted: reported calibration accuracy between calibration cycles, stationarity of hardware conditions between calibration and execution. Not trusted: future hardware state beyond last calibration, provider misreporting of calibration data.

### 5.2 Reproducibility

The governance mechanism is deterministic: given the same delegation and the same calibration data, the decision is identical. However, the specific calibration values are time-varying and backend-specific, so the governance decision for a given backend can change between evaluations. This is a feature, not a limitation: the same backend should be permitted when its hardware is well-calibrated and denied when it is not.

Each receipt contains the full calibration snapshot used to make the decision, making the decision independently auditable. The receipt JSON files accompanying this paper serve as reproducibility artifacts.

### 5.3 Generalization

The proposed delegation pattern may extend to other compute environments in which execution quality depends on runtime conditions, though we do not evaluate those domains here. GPU thermal throttling affects floating-point precision. Classical hardware attestation mechanisms such as Intel SGX and ARM TrustZone provide a partial analog: they bind a trust decision to the physical state of the execution environment, though for confidentiality rather than quality. Network latency bounds affect real-time system correctness. Model version freshness determines whether inference reflects current training data.

Quantum hardware is the first and most demanding proof case because the quality variation is large (10x T1 difference across same-generation backends), the failure mode is silent (results look valid regardless of quality), and the consequence of quality failure is waste of a scarce resource (quantum runtime minutes). The same delegation pattern may apply more broadly to compute environments whose correctness or quality depends on runtime conditions.

### 5.4 All-Backends-Fail Behavior

When no available backend meets the delegation's physics facets, the governance framework correctly denies all execution attempts. The agent receives DENIED_FIDELITY receipts for every backend, each containing the specific violations. The appropriate response, whether waiting for recalibration, escalating to the principal for relaxed constraints, or aborting the task, is application-specific and outside the governance layer's scope. The governance framework guarantees that no execution occurs on hardware that fails to meet the delegation's quality requirements, even if this means no execution occurs at all.

### 5.5 Limitations

The evaluation uses two circuit types (2-qubit Bell state and 4-qubit GHZ state). The governance framework is circuit-agnostic, but the experimental validation covers only entangling circuits with simple ideal output distributions. More complex circuits with different error sensitivity profiles may produce different fidelity gaps.

Only three backends were available under the IBM Quantum Open Plan. A larger backend population would provide stronger evidence for the cross-backend quality variation that motivates physics-enforced governance.

Depth-aware governance (accumulated circuit fidelity rather than per-gate thresholds) is proposed but not yet implemented. The depth sweep data in Table 5 motivates this extension.

The governance protocol itself has not undergone formal security analysis. The Ed25519 receipt signing follows standard practice, but the end-to-end security properties of the gateway enforcement pipeline (e.g., resistance to replay attacks, receipt binding to specific delegations) deserve formal treatment.

## 6. Conclusion

Physics-enforced delegation extends the governance vocabulary from "what may this agent do" to "on what quality hardware may this agent compute." The cross-backend experiment shows that same-generation quantum hardware varies widely in execution quality, and that governance correctly distinguishes the difference. The counterfactual indicates a 5.2 percentage point fidelity gap on a Bell state and 7.7 percentage points on a GHZ state between denied and permitted backends. The governance overhead is 4.2 ms of logic, with the external calibration API call (cacheable) dominating total latency.

Quantum hardware is the proof case because its quality variation is extreme and its failure mode is silent. The same delegation pattern may apply more broadly to compute environments whose correctness or quality depends on runtime conditions. The delegation schema, enforcement protocol, and receipt structure are available as open-source components of the Agent Passport System.

## References

[1] T. Pidlisnyi, "The Agent Social Contract," Zenodo, 2026. doi:10.5281/zenodo.18749779

[2] Decentralized Identity Foundation, "DIF Trust Framework," https://identity.foundation, 2024.

[3] IETF DAAP Working Group, "Delegated Agent Authorization Protocol," Internet-Draft, 2025.

[4] J. B. Dennis and E. C. Van Horn, "Programming Semantics for Multiprogrammed Computations," Communications of the ACM, vol. 9, no. 3, pp. 143-155, 1966.

[5] A. Birgisson, J. G. Politz, U. Erlingsson, A. Taly, M. Vrable, and M. Lentczner, "Macaroons: Cookies with Contextual Caveats for Decentralized Authorization in the Cloud," in Proc. NDSS, 2014.

[6] T. Pidlisnyi, "Faceted Authority Attenuation for Multi-Agent Governance," Zenodo, 2026. doi:10.5281/zenodo.19260073

[7] A. Javadi-Abhari et al., "Quantum computing with Qiskit," arXiv:2405.08810, 2024.

[8] P. Murali, J. M. Baker, A. Javadi-Abhari, F. T. Chong, and M. Martonosi, "Noise-Adaptive Compiler Mappings for Noisy Intermediate-Scale Quantum Computers," in Proc. ASPLOS, 2019.

[9] Quantum Device Management Interface Working Group, "QDMI Specification," 2025.

[10] S. Stein et al., "Hybrid quantum-classical task orchestration," in Proc. IEEE QCE, 2024.

[11] M. Salm, J. Barzen, U. Breitenbücher, F. Leymann, B. Weder, and K. Wild, "The NISQ Analyzer: Automating the Selection of Quantum Computers for Quantum Algorithms," in Proc. SummerSOC, 2020.

[12] N. Quetschlich, L. Burgholzer, and R. Wille, "Predicting Good Quantum Circuit Compilation Options," in Proc. IEEE QSW, 2023.

[13] T. Pidlisnyi, "Agent Passport System," Internet-Draft draft-pidlisnyi-aps-00, 2026.

[14] T. Pidlisnyi, "Monotonic Narrowing for Agent Authority," Zenodo, 2026. doi:10.5281/zenodo.18932404

---

*doi: https://doi.org/10.5281/zenodo.19478584*
*Code and data: https://github.com/aeoess/aeoess-quantum-governance*
*Agent Passport System: https://www.npmjs.com/package/agent-passport-system*
*Gateway: https://gateway.aeoess.com*
