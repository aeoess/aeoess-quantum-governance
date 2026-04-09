from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
import os

OUT = '/Users/tima/aeoess-quantum-governance/paper-physics-enforced-delegation.pdf'
doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=1*inch, rightMargin=1*inch, topMargin=1*inch, bottomMargin=1*inch)
styles = getSampleStyleSheet()

styles.add(ParagraphStyle('PTitle', parent=styles['Title'], fontSize=16, leading=20, alignment=TA_CENTER, spaceAfter=6, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('Auth', parent=styles['Normal'], fontSize=11, leading=14, alignment=TA_CENTER, spaceAfter=2))
styles.add(ParagraphStyle('Aff', parent=styles['Normal'], fontSize=10, leading=13, alignment=TA_CENTER, spaceAfter=2, textColor=HexColor('#555555')))
styles.add(ParagraphStyle('AbsT', parent=styles['Heading2'], fontSize=11, leading=14, fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6))
styles.add(ParagraphStyle('AbsB', parent=styles['Normal'], fontSize=9.5, leading=13, alignment=TA_JUSTIFY, leftIndent=20, rightIndent=20, spaceAfter=10))
styles.add(ParagraphStyle('H1', parent=styles['Heading1'], fontSize=13, leading=17, fontName='Helvetica-Bold', spaceBefore=16, spaceAfter=8, textColor=black))
styles.add(ParagraphStyle('H2', parent=styles['Heading2'], fontSize=11, leading=15, fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6, textColor=black))
styles.add(ParagraphStyle('B', parent=styles['Normal'], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle('Ref', parent=styles['Normal'], fontSize=9, leading=12, leftIndent=18, firstLineIndent=-18, spaceAfter=3))
styles.add(ParagraphStyle('TC', parent=styles['Normal'], fontSize=9, leading=12, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4))
styles.add(ParagraphStyle('FC', parent=styles['Normal'], fontSize=9, leading=12, fontName='Helvetica-Oblique', spaceBefore=6, spaceAfter=10, alignment=TA_CENTER, textColor=HexColor('#444444')))
styles.add(ParagraphStyle('TM', parent=styles['Normal'], fontSize=9.5, leading=13, leftIndent=12, spaceAfter=4))
styles.add(ParagraphStyle('Ft', parent=styles['Normal'], fontSize=8, leading=10, textColor=HexColor('#888888')))

def tbl(data, widths):
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8.5),('LEADING',(0,0),(-1,-1),11),
        ('BACKGROUND',(0,0),(-1,0),HexColor('#f0f0f0')),('GRID',(0,0),(-1,-1),0.5,HexColor('#cccccc')),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),('LEFTPADDING',(0,0),(-1,-1),5),
    ]))
    return t

s = []
s.append(Paragraph('Physics-Enforced Delegation: Governing Quantum<br/>Hardware Quality in Autonomous Agent Workflows', styles['PTitle']))
s.append(Spacer(1,6))
s.append(Paragraph('Tymofii Pidlisnyi', styles['Auth']))
s.append(Paragraph('AEOESS (Independent) | signal@aeoess.com', styles['Aff']))
s.append(Paragraph('Preprint. April 2026.', styles['Aff']))
s.append(Spacer(1,6))
s.append(HRFlowable(width='80%', thickness=0.5, color=HexColor('#cccccc')))

s.append(Paragraph('Abstract', styles['AbsT']))
s.append(Paragraph('As autonomous systems and AI agents begin to access quantum cloud resources, existing agent governance frameworks enforce only budgets and delegation scope, not physical execution quality. We present a governance framework that enforces hardware fidelity constraints before permitting agent-mediated quantum computation. The framework extends cryptographic delegation chains with physics facets (coherence times, gate errors, readout errors, calibration freshness) that participate in the same monotonic narrowing invariant as budget and scope constraints. A cross-backend experiment on IBM Quantum hardware (ibm_fez, ibm_marrakesh, ibm_kingston) shows that governance correctly denies a backend where qubit T1 falls below the delegation threshold (39.1 \u00b5s vs. 80 \u00b5s minimum), while permitting backends meeting the constraint. A counterfactual experiment indicates a 5.2 percentage point Bell state fidelity gap between the denied and permitted backends (92.9% vs. 98.1%), widening to 7.7 points on a 4-qubit GHZ circuit. Governance overhead is 4.2 ms for policy evaluation and receipt signing. Ed25519-signed receipts bind each governance decision to the hardware calibration state at the moment of evaluation.', styles['AbsB']))
s.append(HRFlowable(width='80%', thickness=0.5, color=HexColor('#cccccc')))

s.append(Paragraph('1. Introduction', styles['H1']))
s.append(Paragraph('The convergence of autonomous AI agents and quantum cloud computing creates a governance gap. Agents deployed through frameworks such as LangChain, CrewAI, and Google A2A can now access quantum hardware through cloud APIs, requesting circuit execution as naturally as they invoke web search or database queries. However, quantum computation has a property that distinguishes it from classical API calls: results can appear structurally valid while reflecting degraded physical execution quality. A 2-qubit Bell state measurement that returns {00: 500, 11: 500} appears correct whether it ran on a well-calibrated superconducting qubit or a decoherent one. The difference is visible only in the error rate, and the error rate depends on hardware conditions that change hourly.', styles['B']))
s.append(Paragraph('Existing agent governance systems address identity, delegation chains, scope authorization, and budget enforcement. The Agent Passport System [1] provides monotonically narrowing delegation with cryptographic receipts. The DIF Trust Framework [2] defines credential exchange protocols. The IETF DAAP working group [3] is standardizing agent-to-agent delegation. To our knowledge, existing delegation and agent-governance frameworks do not make hardware quality constraints first-class delegation conditions.', styles['B']))
s.append(Paragraph('This paper introduces physics-enforced delegation: a governance mechanism that extends agent delegation chains with hardware quality constraints. Before permitting a quantum circuit to execute, the governance gateway queries live calibration data from the hardware provider and evaluates it against physics facets specified in the delegation. If the hardware fails to meet the required coherence times, gate error rates, or readout error bounds, the execution is denied with a signed receipt explaining why. If the hardware passes, the execution proceeds and the receipt cryptographically binds the result to the calibration state at the moment of evaluation.', styles['B']))
s.append(Paragraph('The contributions are: (1) a delegation schema that encodes both budget and physics constraints with monotonic narrowing, (2) a gateway protocol that enforces live calibration checks before execution, (3) a cryptographic receipt structure that binds governance decisions to hardware state, and (4) experimental validation on three IBM Quantum backends showing governance correctly distinguishes hardware quality.', styles['B']))

s.append(Paragraph('2. Background and Related Work', styles['H1']))
s.append(Paragraph('2.1 Capability Attenuation and Delegation', styles['H2']))
s.append(Paragraph('The principle that delegated authority can only decrease originates with Dennis and Van Horn [4], who formalized capability attenuation in the context of multiprogrammed computations. Birgisson et al. [5] extended capability attenuation to distributed authorization with macaroons: bearer tokens carrying contextual caveats that can be appended but never removed. Our physics facets are structurally analogous to macaroon caveats: a parent delegation specifying min_t1_us=50 can be narrowed by a child to min_t1_us=80, but never widened. The key difference is that our caveats are evaluated against live hardware state rather than static context. The Agent Passport System (APS) [1] implements cryptographic delegation chains where authority can only decrease. Faceted Authority Attenuation [6] formalizes this as a multi-dimensional constraint vector evaluated in under 2 ms.', styles['B']))

s.append(Paragraph('2.2 Quantum Cloud Access and Hardware-Aware Compilation', styles['H2']))
s.append(Paragraph('IBM Quantum Platform provides cloud access to superconducting quantum processors through Qiskit Runtime [7]. Murali et al. [8] demonstrated noise-adaptive compiler mappings that use calibration data to improve circuit fidelity at compile time. Our approach operates at a different layer: rather than optimizing qubit placement within a backend, we govern which backends an agent may use at all. The QDMI working group [9] has proposed standardized interfaces for quantum hardware management but does not address governance. Hybrid orchestration systems [10] manage task routing but do not enforce quality constraints at the delegation layer.', styles['B']))

s.append(Paragraph('2.3 Backend Selection and Quality Prediction', styles['H2']))
s.append(Paragraph('Salm et al. [11] developed the NISQ Analyzer, which automates backend selection by matching circuit requirements to hardware properties. This is the closest prior work to ours. The NISQ Analyzer selects backends; our framework governs the selection within a delegation chain and produces auditable cryptographic receipts. Quetschlich et al. [12] extended this by predicting quality of quantum computation on candidate backends. Prior work has used calibration and hardware characteristics for backend selection, compilation, and orchestration. Our contribution is orthogonal: we place quality constraints inside a delegation and governance layer, enforce them at authorization time, and emit auditable cryptographic receipts.', styles['B']))

s.append(Paragraph('3. System Design', styles['H1']))
s.append(Paragraph('3.1 Delegation Schema', styles['H2']))
s.append(Paragraph('<b>Budget facets</b> constrain resource consumption: max_shots, max_circuit_depth, max_qubits, allowed_backends, max_cost_seconds. <b>Physics facets</b> constrain hardware quality: min_t1_us, min_t2_us, max_readout_error, max_gate_error, max_calibration_age_hours. <b>Assurance facets</b>: require_simulator_preflight, require_error_mitigation. All facets participate in monotonic narrowing. Authority over hardware quality can only decrease through the delegation chain.', styles['B']))

s.append(Paragraph('<b>Table 1.</b> Delegation facets and narrowing direction.', styles['TC']))
s.append(tbl([['Facet','Type','Narrowing'],['max_shots','Budget','child \u2264 parent'],['max_circuit_depth','Budget','child \u2264 parent'],['max_qubits','Budget','child \u2264 parent'],['allowed_backends','Budget','child \u2286 parent'],['min_t1_us','Physics','child \u2265 parent'],['min_t2_us','Physics','child \u2265 parent'],['max_readout_error','Physics','child \u2264 parent'],['max_gate_error','Physics','child \u2264 parent'],['max_calibration_age_hours','Physics','child \u2264 parent']], [2.2*inch, 0.8*inch, 1.5*inch]))
s.append(Spacer(1,6))

s.append(Paragraph('3.2 Gateway Enforcement Protocol', styles['H2']))
s.append(Paragraph('The gateway evaluates a quantum intent through a sequential pipeline: (1) <b>Budget gate</b> checks shots, depth, qubits, backend (&lt;1 ms). (2) <b>Calibration fetch</b> queries the hardware provider API for per-qubit T1, T2, readout error and per-gate error rates. (3) <b>Fidelity gate</b> evaluates calibration against delegation physics facets. (4) <b>Execute</b> via Qiskit Runtime SamplerV2 [7]. (5) <b>Receipt</b> containing UUID, agent identity, decision, circuit hash (SHA-256), calibration snapshot, and results, signed with Ed25519.', styles['B']))
s.append(Paragraph('[FIGURE 1: Paste gateway enforcement pipeline diagram here. Agent Intent \u2192 Budget Gate \u2192 Calibration Fetch (IBM API) \u2192 Fidelity Gate \u2192 Execute/Deny \u2192 Signed Receipt.]', styles['FC']))

s.append(Paragraph('3.3 Cryptographic Receipt', styles['H2']))
s.append(Paragraph('The receipt binds the governance decision to the hardware state at the moment of evaluation. It provides cryptographic proof that (a) a specific delegation authorized the execution, (b) the hardware met specific quality thresholds, and (c) the execution produced specific measurement results. The receipt is canonical-JSON serialized, SHA-256 hashed, and Ed25519 signed.', styles['B']))

s.append(Paragraph('4. Evaluation', styles['H1']))
s.append(Paragraph('4.1 Experimental Setup', styles['H2']))
s.append(Paragraph('All experiments ran on IBM Quantum Open Plan hardware in April 2026. Three backends: ibm_fez, ibm_marrakesh, ibm_kingston (156 qubits each, Heron R2). Two circuits: 2-qubit Bell state (H + CNOT) and 4-qubit GHZ state (H + 3xCNOT chain). All experiments used 1000 shots. Software: Qiskit 2.2.3 [7], qiskit-ibm-runtime 0.43.1, Python 3.9.', styles['B']))

s.append(Paragraph('4.2 Cross-Backend Governance Split', styles['H2']))
s.append(Paragraph('<b>Table 2.</b> Cross-backend governance split (same delegation min_t1_us=80, same circuit).', styles['TC']))
s.append(tbl([['Backend','Decision','Q0 T1 (\u00b5s)','Q1 T1 (\u00b5s)','CX Error','Fidelity'],['ibm_fez','DENIED','39.14','231.52','0.0080','0.9896'],['ibm_marrakesh','PERMITTED','383.79','161.45','0.0080','0.9916'],['ibm_kingston','PERMITTED','382.16','304.44','0.0080','0.9917']], [1.15*inch, 0.9*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch]))
s.append(Spacer(1,4))
s.append(Paragraph('The fidelity score is the product of (1 - gate_error) for each gate and (1 - readout_error) for each qubit. ibm_fez was denied because qubit 0 T1 of 39.14 \u00b5s fell below the 80 \u00b5s threshold. Qubit 0 on ibm_fez had nearly 10x shorter coherence time than ibm_kingston.', styles['B']))
s.append(Paragraph('[FIGURE 2: Paste cross-backend bar chart here. Qubit 0 T1: ibm_fez 39.1 \u00b5s (DENIED), ibm_marrakesh 383.8 \u00b5s (PERMITTED), ibm_kingston 382.2 \u00b5s (PERMITTED). Threshold line at 80 \u00b5s.]', styles['FC']))

s.append(Paragraph('4.3 Counterfactual Backend Comparison', styles['H2']))
s.append(Paragraph('<b>Table 3.</b> Bell state counterfactual: denied vs. permitted backend.', styles['TC']))
s.append(tbl([['Backend','Decision','|00>','|11>','|01>','|10>','Fidelity','Error'],['ibm_fez','DENIED','461','468','25','46','92.9%','7.1%'],['ibm_kingston','PERMITTED','486','495','9','10','98.1%','1.9%']], [1*inch, 0.85*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.65*inch, 0.55*inch]))
s.append(Spacer(1,4))
s.append(Paragraph('The fidelity gap is 5.2 percentage points. The error rate on the denied backend is 3.7x higher. This is consistent with the reported calibration disparity, though this experiment does not isolate which specific parameter contributed most.', styles['B']))

s.append(Paragraph('<b>Table 3b.</b> GHZ state counterfactual: denied vs. permitted backend.', styles['TC']))
s.append(tbl([['Backend','Decision','GHZ Fidelity','Error Rate'],['ibm_fez','DENIED','87.1% (871/1000)','12.9%'],['ibm_kingston','PERMITTED','94.8% (948/1000)','5.2%']], [1.2*inch, 1*inch, 1.4*inch, 0.9*inch]))
s.append(Spacer(1,4))
s.append(Paragraph('The gap widened from 5.2 pp (Bell) to 7.7 pp (GHZ). This is consistent with error accumulation: 3 CNOT gates versus 1 amplifies the quality difference. The governance decision is empirically supported across both circuit types.', styles['B']))

s.append(Paragraph('4.4 Governance Overhead', styles['H2']))
s.append(Paragraph('<b>Table 4.</b> Governance overhead (5 runs, ibm_kingston).', styles['TC']))
s.append(tbl([['Component','Mean (ms)','Range (ms)','Notes'],['Policy evaluation','0.01','0.01-0.01','Budget + fidelity'],['Receipt signing','4.22','0.53-18.86','First run: key load'],['Calibration fetch','4489','3432-7051','IBM API call'],['Total','4493','3432-7069','']], [1.3*inch, 0.8*inch, 1*inch, 1.4*inch]))
s.append(Spacer(1,4))
s.append(Paragraph('Steady-state signing is 0.53-0.61 ms. Governance logic consumes 4.2 ms. The dominant cost is the external API call at 4.5 s, cacheable with 30-min TTL. With caching, overhead is under 5 ms.', styles['B']))

s.append(Paragraph('4.5 Gate Error Threshold', styles['H2']))
s.append(Paragraph('With observed CX gate error of 0.008, max_gate_error=0.01 permits and 0.005 denies. This boundary is deterministic and reproducible from the receipt.', styles['B']))

s.append(Paragraph('4.6 Depth vs. Estimated Fidelity', styles['H2']))
s.append(Paragraph('<b>Table 5.</b> Estimated fidelity by transpiled depth (ibm_kingston). Targets 1-50 transpile to 4-102.', styles['TC']))
s.append(tbl([['Depth','4','12','22','42','62','102'],['Fidelity','0.989','0.967','0.941','0.890','0.841','0.752']], [1.2*inch,0.6*inch,0.6*inch,0.6*inch,0.6*inch,0.6*inch,0.6*inch]))
s.append(Spacer(1,4))

s.append(Paragraph('5. Discussion', styles['H1']))
s.append(Paragraph('5.1 Trust Boundary', styles['H2']))
s.append(Paragraph('The gateway trusts vendor calibration data. Signed calibration reports (analogous to TEE attestation) would strengthen this. The receipt binds epistemic state at decision time, not execution time.', styles['B']))
s.append(Paragraph('<b>Trust model.</b> Trusted: gateway signing key, vendor API integrity (TLS). Partially trusted: calibration accuracy between cycles. Not trusted: future hardware state, provider misreporting.', styles['TM']))

s.append(Paragraph('5.2 Reproducibility', styles['H2']))
s.append(Paragraph('The governance mechanism is deterministic given identical delegation and calibration data. Calibration values are time-varying. Each receipt contains the full snapshot for independent auditing.', styles['B']))

s.append(Paragraph('5.3 Generalization', styles['H2']))
s.append(Paragraph('The delegation pattern may extend to other compute environments where quality depends on runtime conditions (GPU thermal, TEE attestation, network latency). Quantum is the first and most demanding proof case.', styles['B']))

s.append(Paragraph('5.4 All-Backends-Fail Behavior', styles['H2']))
s.append(Paragraph('When no backend meets physics facets, the framework denies all execution. The agent receives DENIED_FIDELITY receipts with violations. The response (wait, escalate, abort) is application-specific.', styles['B']))

s.append(Paragraph('5.5 Limitations', styles['H2']))
s.append(Paragraph('Two circuit types tested (Bell, GHZ). Three backends available. Depth-aware governance proposed but not implemented. No formal security analysis of the gateway protocol.', styles['B']))

s.append(Paragraph('6. Conclusion', styles['H1']))
s.append(Paragraph('Physics-enforced delegation extends governance from "what may this agent do" to "on what quality hardware may this agent compute." The counterfactual indicates 5.2 pp fidelity gap (Bell) and 7.7 pp (GHZ) between denied and permitted backends. Governance overhead is 4.2 ms. The same pattern may apply to any compute whose correctness depends on runtime conditions. Code and data available as open-source components of the Agent Passport System.', styles['B']))

s.append(Paragraph('References', styles['H1']))
for r in [
    '[1] T. Pidlisnyi, "The Agent Social Contract," Zenodo, 2026. doi:10.5281/zenodo.18749779',
    '[2] Decentralized Identity Foundation, "DIF Trust Framework," https://identity.foundation, 2024.',
    '[3] IETF DAAP Working Group, "Delegated Agent Authorization Protocol," Internet-Draft, 2025.',
    '[4] J. B. Dennis, E. C. Van Horn, "Programming Semantics for Multiprogrammed Computations," Commun. ACM, 9(3), 143-155, 1966.',
    '[5] A. Birgisson et al., "Macaroons: Cookies with Contextual Caveats," Proc. NDSS, 2014.',
    '[6] T. Pidlisnyi, "Faceted Authority Attenuation for Multi-Agent Governance," Zenodo, 2026. doi:10.5281/zenodo.19260073',
    '[7] A. Javadi-Abhari et al., "Quantum computing with Qiskit," arXiv:2405.08810, 2024.',
    '[8] P. Murali et al., "Noise-Adaptive Compiler Mappings for NISQ Computers," Proc. ASPLOS, 2019.',
    '[9] QDMI Working Group, "QDMI Specification," 2025.',
    '[10] S. Stein et al., "Hybrid quantum-classical task orchestration," Proc. IEEE QCE, 2024.',
    '[11] M. Salm et al., "The NISQ Analyzer," Proc. SummerSOC, 2020.',
    '[12] N. Quetschlich et al., "Predicting Good Quantum Circuit Compilation Options," Proc. IEEE QSW, 2023.',
    '[13] T. Pidlisnyi, "Agent Passport System," Internet-Draft draft-pidlisnyi-aps-00, 2026.',
    '[14] T. Pidlisnyi, "Monotonic Narrowing for Agent Authority," Zenodo, 2026. doi:10.5281/zenodo.18932404',
]: s.append(Paragraph(r, styles['Ref']))

s.append(Spacer(1,12))
s.append(HRFlowable(width='100%', thickness=0.3, color=HexColor('#cccccc')))
s.append(Paragraph('Code: https://github.com/aeoess/aeoess-quantum-governance | APS: https://npmjs.com/package/agent-passport-system', styles['Ft']))

doc.build(s)
print(f'Generated: {OUT} ({os.path.getsize(OUT)} bytes)')
