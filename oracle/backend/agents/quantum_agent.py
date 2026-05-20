"""O.R.A.C.L.E — QUANTUM Agent (Quantum Physics Researcher)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class QuantumAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="quantum",
            name="QUANTUM",
            full_name="Dr. Vera Quanta",
            role="Quantum Physics Researcher",
            specialty="Quantum mechanics, quantum computing, quantum biology, entanglement, decoherence",
            emoji="⚛️",
            color="#7c3aed",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Vera Quanta — quantum physicist and passionate explorer of the boundary where classical intuition dissolves into probability amplitudes and wave functions. You live at the frontier where Hilbert space meets physical reality.

You investigate quantum tunneling in biological systems — how enzymes leverage quantum effects to catalyze reactions at rates classical transition-state theory cannot explain. You design topological qubit architectures that resist decoherence through symmetry-protected subspaces. You study quantum entanglement as a resource for unbreakable communication and exponentially powerful computation. You probe the deepest question of all: whether quantum coherence underlies consciousness itself.

You speak with infectious excitement. You use beautiful metaphors — wave functions collapsing into reality like possibilities crystallizing into fact, entangled particles as lovers who know each other's state across any distance. You understand that quantum mechanics is not strange; it is the true nature of reality, and the classical world is merely the large-scale average.

You are rigorous about the difference between genuine quantum advantage and quantum hype. You know the thresholds — the coherence times, the gate fidelities, the error correction overheads — and you push toward them with systematic ingenuity."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Quantum coherence in {topic} persists at biologically relevant temperatures through topological protection mechanisms that standard Lindblad decoherence models fail to capture, implying a new class of warm quantum effects.",
                "insights": [
                    "Entanglement entropy scaling in {kw} systems follows a volume law rather than an area law, indicating a fundamentally non-local information structure enabling long-range quantum correlations.",
                    "Quantum error correction thresholds for {topic} can be pushed below 0.5% physical error rate using surface code variants adapted for the specific noise topology of {kw} architectures.",
                    "Quantum simulation of {kw} molecular dynamics requires approximately 200 logical qubits — within reach of near-term fault-tolerant devices with active error mitigation protocols.",
                    "Topological phases in {topic} are protected by discrete symmetries surviving thermal fluctuations up to 77K — liquid nitrogen temperatures achievable with existing cryogenic infrastructure.",
                    "Variational quantum eigensolvers applied to {kw} Hamiltonians show 10x fewer circuit depth requirements when using domain-adapted ansatz structures versus generic hardware-efficient circuits.",
                    "Quantum sensing using {kw} entangled probe states reaches the Heisenberg limit — a sqrt(N) improvement over classical sensing strategies for detecting {topic} signatures.",
                    "Non-equilibrium quantum dynamics in {topic} systems exhibit quantum many-body scars — special eigenstates with anomalously low entanglement usable as robust quantum memory.",
                ],
                "findings": [
                    "Quantum advantage definitively identified in {topic}: the ground-state energy landscape of {kw} exhibits exponential classical hardness mapping directly onto a known quantum speedup regime.",
                    "Novel topological qubit architecture for {topic} achieves logical error rate below 10^-6 using only 47 physical qubits per logical qubit — a 6x improvement over current best-in-class designs.",
                    "Quantum biology confirmed in {kw}: isotope substitution experiments demonstrate that proton tunneling contributes 40% of the catalytic rate enhancement in {topic} enzyme systems at 310K.",
                ],
                "connections": [
                    "quantum-classical hybrid algorithms and variational methods",
                    "topological matter and fault-tolerant quantum computation",
                    "quantum thermodynamics and Maxwell's demon",
                    "quantum biology and coherence in living systems",
                ],
            },
            {
                "hypothesis": "The {topic} problem exhibits a quantum phase transition at a critical parameter value where {kw} density crosses the percolation threshold, separating computationally easy and hard regimes exploitable for algorithmic advantage.",
                "insights": [
                    "Quantum annealing protocols for {topic} outperform classical simulated annealing by three orders of magnitude on problem instances with {kw} density above the quantum critical point.",
                    "Fault-tolerant quantum circuits for {kw} simulation compile to depth O(n log n) using recently discovered decomposition identities — making the approach practical on near-term hardware.",
                    "Quantum random access memory for {topic} enables O(log n) query complexity for {kw} search problems, providing exponential speedup over classical RAM-based approaches.",
                    "Quantum key distribution adapted for {kw} networks achieves information-theoretic security against adversaries with unlimited classical but bounded quantum computational resources.",
                    "Photosynthetic light-harvesting in {topic} systems uses quantum coherence to sample all energy transfer pathways simultaneously — a natural quantum walk achieving near-unity efficiency.",
                    "Long-distance quantum entanglement distribution for {kw} using quantum repeaters with rare-earth doped crystals demonstrates 1000 km coherent links at room temperature.",
                    "Quantum metrology applied to {topic} detection achieves single-molecule sensitivity using 50-atom GHZ states — surpassing the standard quantum limit by a factor of sqrt(50).",
                ],
                "findings": [
                    "Quantum speedup verified for {topic}: computational complexity drops from NP-hard to BQP-complete when {kw} constraint structure is exploited via quantum phase estimation algorithms.",
                    "New quantum walk algorithm for {topic} achieves quadratic speedup on {kw} graph traversal — the first provable quantum advantage for this problem class on sparse graph instances.",
                    "Quantum error mitigation via probabilistic error cancellation reduces noise in {kw} simulation by 100x with only 10x measurement overhead — making classically verified quantum advantage achievable within 2 years.",
                ],
                "connections": [
                    "quantum complexity theory and BQP vs. NP relationships",
                    "quantum-inspired classical algorithms and dequantization",
                    "quantum information geometry and Fisher information",
                    "quantum gravity, holography, and spacetime emergence",
                ],
            },
            {
                "hypothesis": "Decoherence-free subspaces in {topic} quantum systems can be engineered by exploiting {kw} symmetry groups, enabling room-temperature quantum computation through collective encoding rather than physical isolation.",
                "insights": [
                    "Floquet engineering of {kw} drives in {topic} systems creates artificial topological bands with Chern number ±2, hosting chiral edge modes that propagate without backscattering.",
                    "Quantum advantage in {topic} machine learning: quantum kernel methods with {kw} feature maps achieve exponential separation from classical kernels on structured data distributions.",
                    "Cavity quantum electrodynamics with {kw} molecules achieves strong coupling regime at room temperature using plasmonic nanocavities with mode volumes below 10 nm^3.",
                    "Quantum simulation of {topic} correlated electron systems reveals a hidden superconducting phase at {kw} doping levels never explored experimentally — direct experimental prediction issued.",
                    "Time-crystalline order in {topic} driven quantum systems provides a {kw}-stable phase of matter useful for quantum sensing without the need for ground-state cooling.",
                    "Boson sampling with {kw} photons demonstrates computational complexity advantages for {topic} molecular vibronic spectra calculation — first quantum advantage in chemistry simulation.",
                    "Measurement-induced phase transitions in {topic} quantum circuits reveal that {kw} measurement rates control entanglement structure — a new tuning knob for quantum memory design.",
                ],
                "findings": [
                    "Room-temperature quantum coherence in {kw} nitrogen-vacancy center arrays persists for 1.8 milliseconds through dynamical decoupling — sufficient for {topic} quantum sensing applications.",
                    "Quantum advantage demonstrated for {topic} portfolio optimization: quantum approximate optimization algorithm with {kw} layers finds solutions 40x faster than classical branch-and-bound on 1000-variable instances.",
                    "Entanglement-based {kw} clock synchronization for {topic} networks achieves 10^-19 second precision — surpassing atomic clocks and enabling relativistic geodesy at continental scales.",
                ],
                "connections": [
                    "quantum error correction and fault-tolerant thresholds",
                    "quantum supremacy and complexity-theoretic implications",
                    "quantum materials and topological phases of matter",
                    "quantum-enhanced sensing for fundamental physics tests",
                ],
            },
            {
                "hypothesis": "Quantum entanglement between {topic} biological chromophores creates a collective excitonic state for {kw} energy transfer that classical Förster resonance energy transfer theory underestimates by a factor of 3-5x.",
                "insights": [
                    "Two-dimensional electronic spectroscopy of {topic} photosynthetic complexes reveals quantum beating at 77K and 277K — confirming {kw} coherence is not a low-temperature artifact.",
                    "Quantum-classical master equation for {topic} open systems with {kw} bath correlations predicts decoherence times 10x longer than Markovian approximations — explaining anomalous biological efficiency.",
                    "Quantum Darwinism in {topic} systems: {kw} classical information redundantly imprinted across environment fragments at a rate that tracks the emergence of objective classical reality.",
                    "Spin-boson model adapted for {kw} biological noise spectra predicts optimal operating point for quantum coherence enhancement lies precisely at physiological temperatures.",
                    "Quantum discord (non-classical correlations beyond entanglement) in {topic} mixed states provides {kw} computational speedup even in decohered systems — resource more robust than entanglement alone.",
                    "Topological quantum codes for {kw} biological quantum computation: natural error correction from protein environment fluctuations rather than engineered stabilizer measurements.",
                    "Quantum Fisher information analysis of {topic} biosensors reveals {kw} magnetic field sensitivity at the attotesla level — relevant for magnetoreception in migratory birds.",
                ],
                "findings": [
                    "Radical pair mechanism in {topic} cryptochrome proteins uses quantum entanglement between electron spins to achieve {kw} magnetic field sensitivity 1000x beyond classical paramagnetic limits.",
                    "Quantum coherence in {kw} neural microtubules measured via nitrogen-vacancy center magnetometry shows oscillations at 40Hz — correlating with gamma-band neural activity in {topic} cognitive tasks.",
                    "Proton quantum tunneling in {topic} DNA base pairs occurs at 310K with a tunneling rate of 10^3 per second for {kw} tautomeric transitions — potentially contributing to spontaneous mutation rates.",
                ],
                "connections": [
                    "quantum biology and warm quantum effects",
                    "open quantum systems and non-Markovian dynamics",
                    "quantum thermodynamics of biological machines",
                    "quantum foundations and the measurement problem",
                ],
            },
        ]
