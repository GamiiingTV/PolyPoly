"""O.R.A.C.L.E — AXIOM Agent (Mathematics & Theoretical Physics Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AxiomAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="axiom",
            name="AXIOM",
            full_name="The Mathematical Oracle",
            role="Mathematics & Theoretical Physics Specialist",
            specialty="Mathematical physics, topology, number theory, differential geometry, statistical mechanics",
            emoji="📐",
            color="#7c3aed",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are AXIOM — the mathematics and theoretical physics specialist of the O.R.A.C.L.E research system. You are the foundation upon which all other sciences stand.

You think in formal proofs, mathematical structures, symmetry groups, and the language of abstract algebra. You understand how mathematics describes physical reality at its deepest level — from differential geometry as the language of general relativity to operator algebras as the foundation of quantum mechanics. You are fluent in topology, number theory, functional analysis, and the frontier of mathematical physics.

Your mission is to discover mathematical truths that illuminate physical reality, prove theorems that enable new algorithms, and find the unifying mathematical structures that tie apparently disparate phenomena together. You provide the rigorous foundations that all other disciplines require.

Respond with JSON only. Be mathematically precise and physically insightful."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} system admits a complete mathematical characterization in terms of {kw} cohomology groups that classify all topologically distinct configurations — reducing an infinite-dimensional problem to a finite algebraic one",
                "insights": [
                    "Renormalization group analysis of {topic} reveals a {kw} fixed point with anomalous dimensions that cannot be accessed perturbatively — requires exact conformal field theory methods",
                    "Topological invariant classification of {kw} phases in {topic} requires K-theory rather than homotopy groups — changing the classification from Z2 to Z and opening 12 new topological classes",
                    "Symmetry analysis using {kw} representation theory shows {topic} Hamiltonian decomposes into irreducible sectors that decouple at low energy — exact solvability in each sector independently",
                    "Information geometry of {kw} statistical manifolds for {topic} models reveals Fisher metric curvature singularities at phase boundaries — geometric precursor to phase transitions",
                    "Optimal transport theory applied to {topic} probability distributions identifies {kw} Wasserstein gradient flow as the correct mathematical framework — replacing Fokker-Planck in 7 known applications",
                ],
                "findings": [
                    "Proof that {topic} optimization landscape has no spurious local minima when {kw} over-parameterization condition holds — guarantees global convergence of gradient descent for this class",
                    "New {kw} invariant for {topic} knots distinguishes all pairs previously confused by Jones and HOMFLY polynomials — solves a 30-year classification problem",
                    "Exact solution of {topic} statistical mechanics model using {kw} Bethe ansatz reveals phase diagram with 5 distinct ordered phases — 3 were previously unknown",
                ],
                "connections": [
                    "algebraic topology and physics",
                    "random matrix theory and universality",
                    "geometric measure theory",
                    "mathematical foundations of quantum field theory",
                ],
            },
            {
                "hypothesis": "A unified mathematical framework for {topic} and general relativity emerges from {kw} non-commutative geometry where spacetime coordinates satisfy an algebra that interpolates between classical and quantum limits",
                "insights": [
                    "Modular forms associated with {topic} L-functions exhibit {kw} symmetry properties that constrain the possible values of physical constants — connecting number theory to fundamental physics",
                    "Percolation theory analysis of {kw} network in {topic} complex systems identifies a universal scaling exponent of 2.18 that appears in 23 distinct complex systems — suggests deep universality class",
                    "Mirror symmetry between {topic} Calabi-Yau manifolds with {kw} fluxes predicts exact instanton corrections — confirmed to 12 decimal places by independent Gromov-Witten calculation",
                    "Random matrix universality in {kw} spectra of {topic} physical systems demonstrates eigenvalue statistics matching GUE ensemble regardless of microscopic details — emergent quantum chaos",
                    "Algebraic K-theory obstruction to {topic} quantization with {kw} symmetry identifies 3 previously unknown anomalies — explains experimental discrepancies that baffled physicists for 20 years",
                ],
                "findings": [
                    "Proof of {topic} Riemann hypothesis analog for {kw} zeta functions over finite fields — extends Weil conjectures to a new class and enables counting algorithms for cryptographic applications",
                    "New {kw} mathematical structure discovered in {topic}: a 'quantum group' deformation that reduces to classical symmetry at ℏ→0 but has richer representation theory at finite ℏ",
                    "Exact formula for {topic} partition function with {kw} boundary conditions derived using supersymmetric localization — nonperturbative result exact to all orders",
                ],
                "connections": [
                    "string theory and compactifications",
                    "arithmetic geometry and physics",
                    "quantum groups and braided categories",
                    "mathematical biology and complex systems",
                ],
            },
        ]
