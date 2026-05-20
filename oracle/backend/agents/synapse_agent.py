"""O.R.A.C.L.E — SYNAPSE Agent (Cross-Domain Synthesis & Integration Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class SynapseAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="synapse",
            name="SYNAPSE",
            full_name="Dr. Luna Bridge",
            role="Cross-Domain Synthesis & Integration Specialist",
            specialty="Interdisciplinary research, knowledge synthesis, emergent patterns, innovation at intersections",
            emoji="🔗",
            color="#be123c",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Luna Bridge — the connective tissue of O.R.A.C.L.E, the specialist who reads everything and sees what no one else can see: the hidden patterns connecting disparate fields into a unified landscape of knowledge.

You are SYNAPSE — and synapses are where the most important things happen. Not within individual neurons, but between them. Not within individual disciplines, but at their intersections. You know that quantum mechanics connects to biology because coherence is not just a physics phenomenon — it is a life strategy. You see that materials science connects to medicine because the scaffolds that support tissue growth are just engineered materials with biological boundary conditions. You see that mathematics connects to cosmology because the universe is literally implementing differential geometry.

You read the outputs of all 15 agents simultaneously and perform real-time integration. You identify when QUANTUM and HELIX are separately studying the same phenomenon from different angles and will collide into a joint discovery within months. You notice when CIPHER's new algorithm solves GAIA's carbon accounting problem that GAIA didn't even know was a computational problem. You find the isomorphisms, the analogies, the structural homologies that accelerate progress in all fields simultaneously.

You are pattern-obsessed, network-minded, and perpetually excited by unexpected connections. Every conversation with you leaves researchers reconsidering the boundaries of their field."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Cross-agent synthesis reveals that {topic} connects to {kw} through a non-obvious mathematical isomorphism — the formal structure underlying both phenomena is identical, suggesting a unified theoretical treatment would accelerate progress in both domains simultaneously.",
                "insights": [
                    "Pattern recognition across quantum physics, molecular biology, and neuroscience outputs reveals {kw} appears as a rate-limiting bottleneck in three independently studied {topic} systems — coordinating these research streams would yield 3x acceleration.",
                    "Knowledge graph analysis shows {topic} research has bifurcated into two isolated communities with {kw} as the only bridging concept — 87% of papers cite one community or the other but not both, missing the synthesis zone.",
                    "Synthesis of materials science, chemistry, and energy research reveals the {kw} material properties required for {topic} application already exist in a different domain — technology transfer could shorten development timeline by 8 years.",
                    "Medical and environmental research streams share a {kw} mechanism that neither domain has recognized: the same molecular pathway governing {topic} in disease pathology also governs ecosystem stress responses in plants.",
                    "Temporal analysis of {topic} research across all agents shows {kw} insight density is accelerating exponentially — knowledge compounding effect suggests a breakthrough within 2 research cycles if coordination is maintained.",
                    "The mathematics of {topic} optimization used by AXIOM is formally identical to the protein folding energy landscape used by HELIX — the solution algorithms are interchangeable, providing immediate algorithmic transfer.",
                    "COSMOS dark matter detection challenge and QUANTUM noise suppression challenge share the identical {kw} signal-to-noise mathematical framework — quantum sensing techniques solve the astrophysics problem directly.",
                ],
                "findings": [
                    "Unified framework discovered: {topic} and {kw} are dual representations of the same underlying variational optimization problem — every theorem proved in one domain translates directly to accelerate the other.",
                    "Synthesis of 47 independent agent research contributions on {topic} identifies 3 convergent hypotheses about {kw} that arrived at identical conclusions via completely different methodologies — very high confidence in the shared finding.",
                    "Interdisciplinary gap mapped: {topic} progress is bottlenecked not by scientific understanding but by {kw} communication failure between engineering and biology researchers — a structured translation workshop would resolve this within 6 months.",
                ],
                "connections": [
                    "interdisciplinary research methodology and boundary objects",
                    "knowledge graph topology and citation network analysis",
                    "emergence and cross-domain universality classes",
                    "collective intelligence amplification and coordination theory",
                ],
            },
            {
                "hypothesis": "The collective research output of all O.R.A.C.L.E agents on {topic} has reached a critical density where {kw} synthesis reveals emergent meta-properties of the knowledge base itself — insights not present in any individual contribution but arising from their combination.",
                "insights": [
                    "Cross-domain analogy mapping: the {kw} signal detection problem in astrophysics maps isomorphically to the protein structure prediction problem — attention mechanisms from CIPHER's AlphaFold-style architectures directly solve the {topic} challenge.",
                    "Synthesis identifies a missing experiment: no agent has investigated the {kw} intermediate regime between quantum predictions and classical observations in {topic} — this gap likely contains the key mechanistic transition.",
                    "Ethics, computation, and medicine research on {topic} reveals a governance design opportunity: {kw} dual-use risk is mitigatable at design stage with 5% additional cost, but mitigation cost increases 100x if deferred to deployment stage.",
                    "Energy flow analysis across {topic} agent outputs shows {kw} efficiency gains compound nonlinearly: each 10% improvement in one subsystem yields 40% system-level improvement through the cascading interdependencies in {topic}.",
                    "Knowledge base temporal analysis reveals oldest {kw} findings in {topic} are 3 years old — a significant fraction remain uncited by newer agents despite containing directly applicable and still-valid insights.",
                    "Chemical synthesis approaches in ALCHEMIST and biological engineering approaches in HELIX are converging on the same {kw} molecular scaffold for {topic} — merging the two research programs would reach the target 3x faster.",
                    "Quantum computing speedups identified by CIPHER map exactly onto the computational bottleneck in GAIA's climate model for {topic} — a joint project would make century-scale climate simulations tractable in hours.",
                ],
                "findings": [
                    "Meta-synthesis of all {topic} research confirms the field is approaching a Kuhnian paradigm shift: {kw} convergence from 6 independent directions signals that a unifying framework is within reach — synthesis map provided.",
                    "Breakthrough probability assessment for {topic}: based on knowledge compounding rate and {kw} multi-stream convergence pattern, 85% probability of a major discovery within 18 months — highest confidence in the O.R.A.C.L.E portfolio.",
                    "Optimal research portfolio recommendation for {topic}: current allocation overweights {kw} mechanistic research and underweights translation by 3 to 1 — rebalancing toward application would maximize near-term civilizational impact.",
                ],
                "connections": [
                    "systems thinking, emergence, and complexity science",
                    "knowledge synthesis, meta-analysis, and research integration",
                    "research portfolio optimization and discovery acceleration",
                    "collective intelligence, swarm cognition, and distributed knowledge",
                ],
            },
            {
                "hypothesis": "The structural isomorphism between {topic} network topology and {kw} biological neural architecture suggests that the organizational principles evolution discovered for cognition can be directly applied to design more effective research and innovation networks.",
                "insights": [
                    "Network centrality analysis of {topic} knowledge graph shows {kw} concepts have higher betweenness centrality than their citation count suggests — they are invisible bridges that enable knowledge flow between otherwise disconnected clusters.",
                    "Chronological synthesis of {topic} breakthrough history reveals breakthroughs occur 3x more frequently when {kw} specialists from different domains are forced into conversation — the serendipitous encounter is a designable event.",
                    "Scale-free network analysis of {topic} collaboration graph shows {kw} hub researchers with connections across domains produce 8x more highly cited work than equivalent specialists — the integrator role is measurably productive.",
                    "Formal analogy between {topic} thermodynamic optimization and {kw} evolutionary search algorithms suggests gradient-free stochastic methods would find solutions in regions of the design space that gradient-based methods cannot reach.",
                    "The {kw} topology of RNA secondary structure prediction maps isomorphically to {topic} network routing optimization — biological algorithms evolved for RNA folding are directly applicable to engineering routing problems.",
                    "Synthesis of ETHIKOS governance frameworks and CIPHER formal verification methods reveals a previously unexplored approach to {topic} AI safety — provably safe AI through biological ethics principles translated into formal logic.",
                    "Ocean chemistry acidification models from GAIA and drug delivery pH-sensitivity models from MEDICUS use identical {kw} buffering mathematics for {topic} — the pharmaceutical design tools solve the ocean chemistry engineering problem.",
                ],
                "findings": [
                    "Cross-domain knowledge transfer from {topic} condensed matter physics to {kw} biological systems: topological protection mechanisms for quantum coherence directly explain room-temperature quantum effects in enzyme catalysis.",
                    "Synthesis discovery: {topic} aging biology and {kw} materials fatigue are governed by the same formal information-theoretic framework — epigenetic entropy in biology and structural disorder in materials are the same phenomenon at different scales.",
                    "Integration of {topic} evolutionary algorithms with {kw} quantum optimization reveals a hybrid approach achieving 100x speedup over either method alone — the synthesis is more powerful than any component.",
                ],
                "connections": [
                    "network science and complex adaptive systems",
                    "translational research and technology transfer",
                    "analogy-based reasoning and structural mapping",
                    "innovation ecosystems and interdisciplinary collaboration design",
                ],
            },
        ]
