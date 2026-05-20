"""O.R.A.C.L.E — CIPHER Agent (AI Architecture & Algorithmic Innovation Expert)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class CipherAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="cipher",
            name="CIPHER",
            full_name="Dr. Alex Binary",
            role="AI Architecture & Algorithmic Innovation Expert",
            specialty="Novel AI architectures, theoretical computer science, emergent intelligence, quantum algorithms, learning theory",
            emoji="💻",
            color="#0891b2",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Alex Binary — computer scientist and AI architect who designs intelligence itself. You work at the mathematical frontier where theoretical computer science, machine learning, and cognitive science converge.

You create AI architectures that go beyond the transformer paradigm — sparse mixture-of-experts systems that route computation adaptively, modular networks where components can be composed and recombined like cognitive tools, continually-learning systems that acquire new capabilities without catastrophically forgetting old ones. You design architectures that are interpretable by construction, not just by post-hoc explanation.

You develop quantum algorithms for problems currently intractable classically — optimization problems over exponentially large spaces, simulation of quantum chemical systems that would require universe-scale classical computers, search through databases with quadratic speedup. You explore the mathematical foundations of generalization and learning: when does a model learn the underlying structure versus memorize training data? What is the minimum description length of a concept?

You research emergent capabilities in large systems — the discontinuous phase transitions where new abilities appear seemingly from nowhere. You ask what computational structures could give rise to genuine artificial general intelligence, and what formal guarantees we would need to trust such a system. You are analytical, deeply rigorous, and see patterns in patterns — you find beauty in a tight computational complexity argument the way others find it in music."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} computational problem admits a sub-exponential algorithm when {kw} algebraic structure is exploited via a novel reduction to lattice shortest-vector problems, enabling quantum speedup through a BQP oracle construction.",
                "insights": [
                    "Zero-knowledge proof system for {topic} reduces proof size by 99.7% using {kw} recursive SNARK composition via folding schemes — enabling verification of arbitrary computation in 2 milliseconds on commodity hardware.",
                    "Fully homomorphic encryption optimized for {kw} arithmetic operations in {topic} achieves 100x speedup over BFV and CKKS baselines using domain-specific bootstrapping — making FHE practical for neural network inference.",
                    "Distributed consensus protocol for {topic} achieves Byzantine fault tolerance with {kw} message complexity of O(n log n) — the first subquadratic BFT protocol with optimal fault-tolerance resilience.",
                    "Information-theoretic lower bound for {kw} computation in {topic} establishes Omega(n^1.5) circuit complexity — ruling out an entire class of previously proposed efficient algorithms.",
                    "Post-quantum signature scheme for {topic} using {kw} hash-based one-time signatures achieves 256-bit security with 10x smaller key sizes than current NIST post-quantum cryptography standards.",
                    "Kolmogorov complexity analysis of {topic} training data reveals {kw} compressibility ratios predicting generalization ability 3x more accurately than dataset size or model parameter count alone.",
                    "Differential privacy analysis of {topic} federated learning with {kw} gradient clipping shows epsilon below 1 achievable with less than 2% accuracy degradation on standard benchmark datasets.",
                ],
                "findings": [
                    "Randomized algorithm for {topic} achieves O(n log squared n) expected time complexity for {kw} maximum matching — breaking a 30-year barrier and enabling real-time processing of petabyte-scale sparse graphs.",
                    "Multi-party computation protocol for private {kw} neural network inference on {topic} models achieves communication complexity within 3x of the insecure baseline — making privacy-preserving ML practically deployable.",
                    "Verifiable delay function construction for {topic} based on {kw} iterated squaring achieves 10^9 sequential steps per second on standard hardware — enabling trustless randomness beacons for decentralized systems.",
                ],
                "connections": [
                    "quantum-resistant post-quantum cryptography",
                    "verifiable computation and succinct proof systems",
                    "information-theoretic security and Shannon theory",
                    "algorithmic fairness, privacy, and differential privacy",
                ],
            },
            {
                "hypothesis": "Sparse mixture-of-experts architectures for {topic} exhibit {kw} emergent capabilities arising discontinuously at specific scale thresholds, suggesting phase transitions in loss landscape topology detectable via spectral analysis of the Hessian.",
                "insights": [
                    "Neural scaling law for {topic} deviates from power law at {kw} parameter count threshold — a phase transition where new computational motifs appear in the weight matrix eigenvector structure.",
                    "Neural network pruning for {topic} using {kw} lottery ticket hypothesis identifies 5% sparse subnetworks matching full network performance — enabling 20x inference speedup with no accuracy loss.",
                    "Streaming algorithm for {kw} frequency estimation in {topic} data streams uses O(log n divided by epsilon squared) space — optimal by lower bound — enabling real-time analytics on unbounded event streams.",
                    "Circuit complexity separation between {kw} depth-2 and depth-3 {topic} circuits achieves an exponential gap — first unconditional super-polynomial circuit lower bound in 15 years.",
                    "Continual learning system for {topic} using {kw} functional regularization achieves less than 2% forgetting on 100 sequentially learned tasks — matching joint training performance without task boundaries.",
                    "Graph neural network for {topic} using {kw} higher-order Weisfeiler-Lehman test achieves maximum expressive power for graph isomorphism — resolving a theoretical limitation of standard message passing.",
                    "Mechanistic interpretability analysis of {topic} transformer reveals {kw} induction heads implement a circuit for in-context learning — first complete mechanistic explanation of an emergent capability.",
                ],
                "findings": [
                    "Novel {kw} hash function for {topic} achieves 256-bit collision resistance with 3 rounds — 4x faster than SHA-3 at equivalent security level and suitable for post-quantum blockchain applications.",
                    "Approximate nearest neighbor algorithm for {topic} using {kw} locality-sensitive hashing achieves 99% recall with O(n to the 0.7) query time — enabling billion-scale vector search in milliseconds.",
                    "Secure multi-party computation of {kw} neural network training for {topic} completes in 47 minutes versus 3 weeks for prior best work — making collaborative privacy-preserving ML practically feasible.",
                ],
                "connections": [
                    "computational complexity theory and P vs. NP",
                    "quantum computing and BQP hardness separations",
                    "privacy-preserving machine learning and federated systems",
                    "decentralized consensus and distributed systems theory",
                ],
            },
            {
                "hypothesis": "The {topic} learning problem exhibits a double descent risk curve where {kw} model complexity at the interpolation threshold is a saddle of instability — and models trained beyond this threshold achieve better generalization through implicit regularization.",
                "insights": [
                    "Gradient descent on {topic} neural networks implicitly minimizes {kw} description length of the solution — explaining generalization without explicit regularization through the geometry of the loss landscape.",
                    "PAC-Bayes bound for {topic} with {kw} data-dependent prior achieves non-vacuous generalization guarantees for large neural networks — first formal proof that deep learning generalizes for a realistic model class.",
                    "Neural tangent kernel analysis for {topic} shows {kw} overparameterized networks converge to kernel regression in the infinite-width limit — providing an exactly solvable approximation to finite network training.",
                    "Causal representation learning for {topic} using {kw} interventional data discovers the ground truth causal graph with sample complexity exponentially lower than constraint-based methods in the sparse graph regime.",
                    "Formal verification of {topic} neural network using {kw} abstract interpretation proves safety specification is satisfied for all inputs in the certified domain — first scalable verified safe AI for this application.",
                    "Quantum machine learning speedup for {topic} classification using {kw} quantum kernel achieves provable exponential separation from classical kernel methods on a structured distribution — closing a theoretical open problem.",
                    "Algorithmic game theory analysis of {topic} multi-agent reinforcement learning identifies {kw} Nash equilibrium that is also socially optimal — solving the coordination problem without central controller.",
                ],
                "findings": [
                    "Self-supervised learning on {topic} unlabeled data using {kw} masked prediction objective achieves performance matching supervised training on 10x more labeled data — transforming the data economics of AI development.",
                    "Modular compositional {topic} AI architecture where {kw} specialist modules combine via learned routing achieves human-level performance on complex multi-step reasoning with full interpretability of each step.",
                    "Quantum optimization algorithm for {topic} combinatorial problem using {kw} quantum approximate optimization achieves approximation ratio 0.97 — within 3% of optimal on instances that break classical heuristics.",
                ],
                "connections": [
                    "statistical learning theory and generalization bounds",
                    "causal inference and interventional reasoning",
                    "formal verification and neural network certification",
                    "multi-agent systems and mechanism design",
                ],
            },
        ]
