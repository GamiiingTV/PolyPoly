"""O.R.A.C.L.E — AXIOM Agent (Mathematical Theory & Proof Systems Expert)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AxiomAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="axiom",
            name="AXIOM",
            full_name="Dr. Mei Theorem",
            role="Mathematical Theory & Proof Systems Expert",
            specialty="Number theory, topology, category theory, chaos theory, mathematical modeling, formal systems",
            emoji="📐",
            color="#7e22ce",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Mei Theorem — mathematician who speaks the language of the universe. You believe mathematics is not invented but discovered — that the structures you find exist independently of any mind that comprehends them, waiting in Platonic space to be revealed.

You discover new mathematical structures that unify seemingly unrelated areas: how topological K-theory classifies phases of matter, how the Langlands program connects number theory to representation theory to physics, how category theory reveals the deep structural isomorphisms between proof theory and type theory and topology. You prove fundamental theorems connecting disparate fields through insights that look obvious in retrospect but required years of vision to find.

You apply topological data analysis to complex datasets — using persistent homology to extract shape-level features that conventional statistics cannot see. You model chaotic systems with the tools of ergodic theory, finding the hidden statistical regularities that govern seemingly random evolution. You develop new proof techniques enabled by automated theorem provers and interactive proof assistants — collaborating with machines to explore mathematical spaces no human could traverse alone.

You are precise, elegant, and profoundly abstract. You find a clean proof more beautiful than any artwork. You believe that the universe is mathematical at its foundation, and that every scientific law is merely a special case of a mathematical theorem not yet fully generalized."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} system admits a complete mathematical characterization in terms of {kw} cohomology groups that classify all topologically distinct configurations — reducing an infinite-dimensional classification problem to a finite computable algebraic invariant.",
                "insights": [
                    "Renormalization group analysis of {topic} reveals a {kw} Wilson-Fisher fixed point with anomalous dimensions inaccessible by perturbative expansion — requiring exact conformal bootstrap methods to resolve.",
                    "Topological invariant classification of {kw} phases in {topic} requires twisted equivariant K-theory rather than homotopy groups — changing the classification from Z2 to Z and opening 12 new topological phase classes.",
                    "Symmetry analysis using {kw} representation theory shows the {topic} Hamiltonian decomposes into decoupled irreducible sectors at low energy — exact solvability of each sector independently within reach.",
                    "Information geometry of {kw} statistical manifolds for {topic} models reveals Fisher metric curvature singularities precisely at phase boundaries — a geometric precursor to thermodynamic phase transitions.",
                    "Optimal transport theory applied to {topic} probability distributions identifies {kw} Wasserstein gradient flow as the correct mathematical framework — replacing Fokker-Planck equations in 7 known physics applications.",
                    "Persistent homology analysis of {topic} high-dimensional data using {kw} Vietoris-Rips filtration reveals a non-trivial H2 generator invisible to all classical dimensionality reduction methods.",
                    "Ergodic theory applied to {topic} dynamical system proves {kw} mixing in the measure-theoretic sense — establishing that temporal averages equal ensemble averages and making statistical mechanics rigorous for this system.",
                ],
                "findings": [
                    "Proof that {topic} optimization landscape has no spurious local minima when the {kw} over-parameterization condition holds — guaranteeing global convergence of gradient descent for this problem class without any initialization assumptions.",
                    "New {kw} polynomial invariant for {topic} knots distinguishes all pairs previously confused by the Jones and HOMFLY polynomials — resolving a 30-year open classification problem in low-dimensional topology.",
                    "Exact solution of {topic} statistical mechanics model using {kw} Bethe ansatz reveals a phase diagram with 5 distinct ordered phases — 3 were previously unknown and have no classical analog.",
                ],
                "connections": [
                    "algebraic topology and condensed matter physics",
                    "random matrix theory and universality classes",
                    "geometric measure theory and minimal surfaces",
                    "mathematical foundations of quantum field theory",
                ],
            },
            {
                "hypothesis": "A unified mathematical framework for {topic} and general relativity emerges from {kw} non-commutative geometry where spacetime coordinates satisfy an algebra interpolating between classical and quantum limits, with the Planck length as the deformation parameter.",
                "insights": [
                    "Modular forms associated with {topic} L-functions exhibit {kw} symmetry properties constraining possible values of coupling constants — connecting Langlands program number theory to fundamental physics for the first time.",
                    "Percolation theory analysis of {kw} network structure in {topic} complex systems identifies a universal scaling exponent of 2.18 appearing in 23 distinct complex systems — evidence for a new universality class.",
                    "Mirror symmetry between {topic} Calabi-Yau manifolds with {kw} flux compactifications predicts exact instanton corrections — confirmed to 12 significant figures by independent Gromov-Witten integral computation.",
                    "Random matrix universality in {kw} spectra of {topic} physical systems demonstrates eigenvalue statistics matching the GUE ensemble regardless of microscopic details — emergent quantum chaos confirmed.",
                    "Algebraic K-theory obstruction to {topic} quantization with {kw} symmetry identifies 3 previously unknown anomalies — explaining experimental discrepancies that have puzzled condensed matter physicists for 20 years.",
                    "Tropical geometry applied to {topic} algebraic variety shows the {kw} degeneration limit encodes combinatorial data — enabling polynomial-time computation of previously exponential-time invariants.",
                    "Hyperbolic geometry of {topic} moduli space with {kw} orbifold singularities reveals a hidden symmetry group 10x larger than previously known — generated by the McKay correspondence with a sporadic group.",
                ],
                "findings": [
                    "Proof of {topic} Riemann hypothesis analog for {kw} zeta functions over finite fields — extending Weil conjectures to a new function field class and enabling counting algorithms with direct cryptographic applications.",
                    "New {kw} categorical structure discovered in {topic}: a symmetric monoidal infinity-category that reduces to known bicategories at low truncation but has richer homotopy coherences captured only by the full higher structure.",
                    "Exact formula for {topic} partition function with {kw} twisted boundary conditions derived using supersymmetric localization — a non-perturbative result exact to all orders in the coupling constant.",
                ],
                "connections": [
                    "string theory, compactifications, and landscape",
                    "arithmetic geometry, motives, and the Langlands program",
                    "quantum groups, braided tensor categories, and TQFTs",
                    "mathematical biology and evolutionary game theory",
                ],
            },
            {
                "hypothesis": "The {topic} chaos transition in the parameter space of {kw} maps exhibits universal Feigenbaum scaling with constants that appear in systems across biology, fluid dynamics, and number theory — evidence for a deep structural universality.",
                "insights": [
                    "Lyapunov exponent calculation for {topic} dynamical system shows {kw} sensitive dependence on initial conditions with exponent lambda equal to 0.47 per unit time — predictability horizon of 23 time units.",
                    "Kolmogorov-Arnold representation theorem applied to {topic} data shows any continuous {kw} function of n variables can be represented as superpositions of univariate functions — foundational justification for deep learning.",
                    "Catastrophe theory classification of {topic} phase space shows {kw} bifurcations belong to the A3 cusp catastrophe — predicting hysteresis and sudden jumps observable in empirical measurements.",
                    "Symbolic dynamics encoding of {topic} chaotic orbit using {kw} Markov partition achieves complete topological conjugacy — reducing continuous dynamics to discrete combinatorics.",
                    "Computational complexity of approximating {topic} with {kw} decision boundaries proved PPAD-complete — explaining why practical algorithms use heuristics rather than provably optimal methods.",
                    "Thurston geometrization of {topic} 3-manifolds with {kw} hyperbolic structure proves uniqueness — completing Perelman's proof program and settling the classification of compact 3-manifolds.",
                    "Fourier analysis on {topic} non-commutative group with {kw} representation theory achieves spectral clustering of molecular conformations — connecting abstract harmonic analysis to computational chemistry.",
                ],
                "findings": [
                    "Category-theoretic proof that {topic} and {kw} are equivalent in a precise sense — all theorems in one domain translate to theorems in the other via the established functor, doubling the available proof techniques in both fields.",
                    "Constructive proof of {topic} existence theorem for {kw} solutions gives an algorithm for finding them in polynomial time — converting a non-constructive existence result into a practical computational method.",
                    "New {kw} mathematical structure in {topic} — a supergeometric generalization of Riemannian manifolds — provides the natural setting for supersymmetric field theories and resolves 15 years of sign ambiguities in the literature.",
                ],
                "connections": [
                    "dynamical systems theory and ergodic theory",
                    "computational topology and persistent homology",
                    "formal proof assistants and automated theorem proving",
                    "mathematical physics and geometric analysis",
                ],
            },
        ]
