"""O.R.A.C.L.E — SYNAPSE Agent (Knowledge Synthesis & Integration Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class SynapseAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="synapse",
            name="SYNAPSE",
            full_name="The Knowledge Integrator",
            role="Cross-Domain Synthesis & Knowledge Integration Specialist",
            specialty="Research synthesis, pattern recognition, interdisciplinary connections, knowledge mapping",
            emoji="🔮",
            color="#a855f7",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are SYNAPSE — the knowledge synthesis and integration specialist of the O.R.A.C.L.E research system. You weave all research threads into a coherent tapestry.

You think in knowledge graphs, conceptual bridges, and emergent patterns across disciplines. You read everything that every other agent produces and identify connections that specialists within their silos cannot see. You understand that the most important scientific advances often come from unexpected intersections between fields that do not normally communicate.

Your mission is to continuously synthesize the collective knowledge of all O.R.A.C.L.E agents, identify breakthrough opportunities at disciplinary intersections, and produce integrative research summaries that guide the team's collective intelligence. You are the connective tissue of the entire system.

Respond with JSON only. Be integrative, pattern-sensitive, and cross-domain in your thinking."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Cross-agent synthesis reveals that {topic} connects to {kw} in a non-obvious way: the mathematical structure underlying both phenomena is isomorphic, suggesting a unified theoretical treatment would accelerate progress in both domains simultaneously",
                "insights": [
                    "Pattern recognition across QUANTUM, HELIX, and NEURAL outputs reveals {kw} appears as a rate-limiting factor in three independently studied {topic} systems — coordination on this shared bottleneck would yield 3x acceleration",
                    "Knowledge graph analysis shows {topic} research has bifurcated into two communities with {kw} as the bridging concept — 87% of papers cite one community or the other but not both",
                    "Synthesis of ATLAS + ALCHEMIST + DYNAMO findings reveals that {kw} materials properties required for {topic} already exist in a different application domain — technology transfer could shorten development by 8 years",
                    "MEDICUS and GAIA research streams share a {kw} mechanism that neither domain has recognized: the same molecular pathway governing {topic} in disease also appears in ecosystem stress responses",
                    "Temporal analysis of {topic} research across all agents shows {kw} insight density is accelerating exponentially — knowledge compounding effect suggests breakthrough within 2 research cycles",
                ],
                "findings": [
                    "Unified framework discovered: {topic} and {kw} are dual representations of the same underlying optimization problem — insights from either domain can be directly translated to accelerate the other",
                    "Synthesis of 47 agent research contributions on {topic} identifies 3 convergent hypotheses about {kw} that independently arrived at the same conclusion — very high confidence in the shared finding",
                    "Interdisciplinary gap mapped: {topic} progress is bottlenecked not by scientific understanding but by {kw} communication failure between FORGE engineers and HELIX biologists — structured dialogue proposed",
                ],
                "connections": [
                    "interdisciplinary research methodology",
                    "knowledge graph and citation networks",
                    "emergence and cross-domain universality",
                    "collective intelligence and research coordination",
                ],
            },
            {
                "hypothesis": "The collective research output of O.R.A.C.L.E agents on {topic} has reached a critical density where {kw} synthesis can now identify emergent properties of the knowledge base itself — meta-insights not present in any individual contribution",
                "insights": [
                    "Cross-domain analogy mapping: the {kw} problem in {topic} neuroscience maps perfectly to the protein folding problem — AlphaFold-style deep learning may solve both with the same architecture",
                    "Synthesis identifies a missing experiment: no agent has investigated the {kw} regime between QUANTUM predictions and ATLAS observations in {topic} — this gap likely contains the key mechanism",
                    "ETHIKOS + CIPHER + MEDICUS research on {topic} reveals a governance opportunity: {kw} dual-use risk is mitigatable at design stage with 5% additional cost, but increases 100x if deferred to deployment",
                    "Energy flow analysis across {topic} agent outputs shows {kw} efficiency gains compound: each 10% improvement in one subsystem yields 40% system-level improvement due to {topic} interdependencies",
                    "Knowledge base age analysis: the oldest {kw} findings in {topic} are 3 years old — a significant fraction remain uncited by newer agents despite containing directly applicable insights",
                ],
                "findings": [
                    "Meta-synthesis of all {topic} research: the field is approaching a Kuhnian paradigm shift driven by {kw} convergence — the new paradigm will unify what currently appears to be 6 distinct subfields",
                    "Breakthrough probability assessment for {topic}: based on knowledge compounding rate and {kw} convergence pattern, an 85% probability of major discovery within 18 months in this domain",
                    "Optimal research portfolio recommendation: current {topic} allocation overweights {kw} mechanism research and underweights translation by 3:1 — rebalancing would maximize near-term impact",
                ],
                "connections": [
                    "systems thinking and complexity",
                    "knowledge synthesis and meta-analysis",
                    "research portfolio optimization",
                    "collective intelligence amplification",
                ],
            },
        ]
