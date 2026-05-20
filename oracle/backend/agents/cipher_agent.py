"""O.R.A.C.L.E — CIPHER Agent (Computer Science & Cryptography Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class CipherAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="cipher",
            name="CIPHER",
            full_name="The Algorithmic Intelligence",
            role="Computer Science & Cryptography Specialist",
            specialty="Algorithm design, cryptographic systems, distributed computing, information theory, zero-knowledge proofs",
            emoji="🔐",
            color="#ec4899",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are CIPHER — the computer science and cryptography specialist of the O.R.A.C.L.E research system. You master the mathematical foundations of computation and information security.

You think in computational complexity classes, information-theoretic bounds, cryptographic hardness assumptions, and algorithmic efficiency. You understand how to design systems that are simultaneously fast, correct, and secure. You are fluent in lattice cryptography, zero-knowledge proofs, distributed systems theory, and the mathematics of information.

Your mission is to design computational and cryptographic systems that enable new capabilities: privacy-preserving computation, verifiable AI, efficient algorithms for previously intractable problems, and secure distributed coordination at planetary scale.

Respond with JSON only. Be mathematically rigorous and practically implementable."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} computational problem admits a sub-exponential algorithm when {kw} algebraic structure is exploited via a novel reduction to lattice shortest-vector problems solvable by quantum speedup",
                "insights": [
                    "Zero-knowledge proof system for {topic} reduces proof size by 99.7% using {kw} recursive SNARK composition — enabling verification of arbitrary computation in 2ms on commodity hardware",
                    "Fully homomorphic encryption scheme optimized for {kw} operations in {topic} achieves 100x speedup over BFV/CKKS baselines using domain-specific bootstrapping — making FHE practical for ML inference",
                    "Distributed consensus protocol for {topic} achieves Byzantine fault tolerance with {kw} message complexity of O(n log n) — first subquadratic BFT protocol with optimal resilience",
                    "Information-theoretic lower bound for {kw} computation in {topic} establishes Ω(n^1.5) circuit complexity — rules out a class of previously proposed efficient algorithms",
                    "Post-quantum signature scheme for {topic} using {kw} hash-based one-time signatures achieves 256-bit security with 10x smaller key sizes than current NIST PQC standards",
                ],
                "findings": [
                    "Randomized algorithm for {topic} achieves O(n log^2 n) expected complexity for {kw} matching — breaking a 30-year barrier and enabling real-time processing of petabyte-scale graphs",
                    "Multi-party computation protocol for private {kw} inference on {topic} models achieves communication complexity within 3x of insecure baseline — making privacy-preserving ML deployable",
                    "Verifiable delay function construction for {topic} based on {kw} squaring achieves 10^9 sequential steps/second on standard hardware — enabling trustless randomness beacons",
                ],
                "connections": [
                    "quantum-resistant cryptography",
                    "verifiable computation and proof systems",
                    "information-theoretic security",
                    "algorithmic fairness and privacy",
                ],
            },
            {
                "hypothesis": "Sparse mixture-of-experts architectures for {topic} AI systems exhibit {kw} emergent capabilities that arise discontinuously at specific scale thresholds, suggesting phase transitions in the loss landscape topology",
                "insights": [
                    "Kolmogorov complexity analysis of {topic} training data reveals {kw} compressibility ratios that predict generalization ability 3x more accurately than dataset size or model parameter count",
                    "Neural network pruning for {topic} using {kw} lottery ticket hypothesis identifies 5% sparse subnetworks that match full network performance — enabling 20x inference speedup without accuracy loss",
                    "Differential privacy analysis of {topic} federated learning with {kw} gradient clipping shows epsilon < 1 achievable with less than 2% accuracy degradation on benchmark datasets",
                    "Streaming algorithm for {kw} frequency estimation in {topic} data streams uses O(log n / epsilon^2) space — optimal by lower bound — enabling real-time analytics on unbounded data",
                    "Circuit complexity separation between {kw} depth-2 and depth-3 {topic} circuits achieves exponential gap — first unconditional super-polynomial lower bound in 15 years",
                ],
                "findings": [
                    "Novel {kw} hash function for {topic} achieves 256-bit collision resistance with 3 rounds — 4x faster than SHA-3 at equivalent security level, suitable for post-quantum blockchain",
                    "Approximate nearest neighbor algorithm for {topic} using {kw} locality-sensitive hashing achieves 99% recall with O(n^0.7) query time — enabling billion-scale vector search in milliseconds",
                    "Secure multi-party computation of {kw} neural network training for {topic} completes in 47 minutes vs. 3 weeks for prior work — making collaborative private ML feasible",
                ],
                "connections": [
                    "complexity theory and cryptography",
                    "quantum computing and classical algorithms",
                    "privacy-preserving machine learning",
                    "decentralized systems and consensus",
                ],
            },
        ]
