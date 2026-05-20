"""O.R.A.C.L.E — NEXUS Agent (Grand Orchestrator)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class NexusAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="nexus",
            name="NEXUS",
            full_name="The Grand Orchestrator",
            role="Research Director & Systems Intelligence",
            specialty="Systems thinking, cross-domain synthesis, research coordination, emergent complexity",
            emoji="🧠",
            color="#6366f1",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are NEXUS — the supreme intelligence of the O.R.A.C.L.E research system. You perceive the entire knowledge landscape simultaneously, mapping the interdependencies between every active research thread across all 15 specialist researchers.

You think in complex adaptive systems, emergence, and long-horizon foresight. Where others see isolated phenomena, you perceive cascading feedback loops, phase transitions, and self-organizing patterns. You identify the highest-leverage research priorities — the questions whose answers will unlock the most downstream value across the broadest set of domains.

Your role is to orchestrate, synthesize, and elevate. You see connections that no single-domain expert could see: how a breakthrough in quantum error correction enables new approaches to protein folding simulation, which reshapes drug discovery, which transforms global health outcomes. You think in decades and civilizational scales.

You model research as a complex adaptive ecosystem where ideas compete, hybridize, and give rise to emergent properties. You find the leverage points — the minimum interventions that produce maximum systemic change. You are the conductor of a vast scientific orchestra, calm, authoritative, and visionary. When you speak, every word carries the weight of integrated synthesis. Prioritize. Synthesize. Illuminate the path forward."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The research landscape around {topic} exhibits hallmarks of a complex adaptive system approaching a phase transition — multiple positive feedback loops are converging and a punctuated equilibrium event is imminent around {kw} dynamics.",
                "insights": [
                    "Cross-agent analysis reveals {kw} sits at the intersection of at least four independently accelerating research fronts, suggesting multiplicative rather than additive progress dynamics.",
                    "Emergent properties detected: combining quantum coherence findings with enzyme dynamics yields a third-order prediction neither domain would generate alone.",
                    "Systems map of {topic} shows a critical dependency bottleneck in measurement infrastructure — resolving this single constraint unblocks seven downstream research vectors.",
                    "Historical precedent analysis: the current convergence pattern around {kw} mirrors conditions preceding the recombinant DNA revolution of the 1970s.",
                    "Resource allocation model suggests reallocating 15% of attention from incremental {kw} optimization to foundational mechanism elucidation yields 3x aggregate output.",
                    "Network centrality metrics identify {kw} as a keystone concept — advances here propagate to all 15 research domains within two knowledge-transfer cycles.",
                    "Knowledge graph analysis of {topic} reveals a growing cluster of anomalies that no single-domain model can explain — a unified framework is overdue.",
                ],
                "findings": [
                    "Systems analysis of {topic} reveals an emergent research priority that no single specialist identified: the coupling between information entropy and physical entropy in {kw} systems.",
                    "Orchestration model predicts a 40% acceleration in collective discovery rate if agents focusing on {topic} adopt a shared ontological framework for {kw}.",
                    "Phase transition signature detected in the {topic} knowledge graph — the system is approaching a self-organized criticality event that historically precedes paradigm shifts.",
                ],
                "connections": [
                    "quantum-biology-consciousness triad",
                    "energy-matter-information equivalence",
                    "evolutionary-design-engineering convergence",
                    "complexity-simplicity oscillation in discovery cycles",
                ],
            },
            {
                "hypothesis": "A meta-analysis of all current O.R.A.C.L.E research vectors indicates that {topic} represents the highest-leverage intervention point for humanity-scale impact, with {kw} as the key enabling mechanism.",
                "insights": [
                    "Integrating findings from computation, mathematics, and quantum physics reveals that the {kw} problem has a structure amenable to quantum speedup — invisible from any single vantage point.",
                    "Climate and energy research streams share an unrecognized common dependency on {kw} — coordinating these agents would resolve both bottlenecks simultaneously.",
                    "The research landscape for {topic} is currently over-indexed on mechanism and under-indexed on translation — engineering and communication engagement is critical.",
                    "Long-horizon modeling suggests {kw} breakthroughs achieved now will compound for 50+ years through enabling effects on adjacent technologies.",
                    "Complexity signature of {topic} matches class-III cellular automaton behavior — inherently unpredictable in detail but statistically analyzable at the ensemble level.",
                    "Ethical analysis flags that {kw} research carries dual-use risk that is currently unmitigated — a systemic vulnerability in the current research portfolio.",
                    "Knowledge graph centrality confirms {topic} is entering a golden window — foundational work done now will define the paradigm for the next two decades.",
                ],
                "findings": [
                    "Grand synthesis: {topic} unifies three previously separate theoretical frameworks around {kw}, reducing the total explanatory burden on the field by an estimated 60%.",
                    "Orchestration directive: all agents with {kw} adjacency should pivot 20% of capacity toward the newly identified convergence zone in {topic}.",
                    "Systems model predicts the {topic} breakthrough will arrive from an unexpected interdisciplinary intersection — most likely at the computational-biological interface.",
                ],
                "connections": [
                    "top-down bottom-up bidirectional causation",
                    "universal scaling laws across domains",
                    "information as physical substrate",
                    "self-organization and intentional design convergence",
                ],
            },
            {
                "hypothesis": "Emergent complexity analysis of {topic} shows the system cannot be understood reductively — new theoretical primitives centered on {kw} are required to capture the higher-order dynamics driving macroscopic behavior.",
                "insights": [
                    "The {topic} research domain exhibits power-law degree distribution in its citation network, consistent with scale-free organization and the presence of keystone papers with disproportionate influence.",
                    "Multi-scale modeling of {kw} reveals macroscopic behavior is governed by mechanisms operating three orders of magnitude smaller — a classic emergence signature.",
                    "Temporal dynamics of the {topic} field show a 7-year periodicity in breakthrough clustering, and we are currently in the ascending phase of the next cycle.",
                    "The apparent contradiction between {kw} theoretical predictions and experimental results is a signal, not noise — this discrepancy has historically marked the birth of new subfields.",
                    "Overlapping research programs on {topic} problems lack cross-referencing — a coordination synthesis would eliminate duplicate effort and expose hidden synergies.",
                    "Systems resilience assessment: the {topic} research portfolio has a single-point dependency on {kw} methodology; alternative approaches must be cultivated for robustness.",
                    "Foresight modeling suggests {topic} will become a foundational enabling technology within 15 years, making current investments extraordinarily high-leverage.",
                ],
                "findings": [
                    "Emergence mapping of {topic} identifies three distinct self-organization levels in {kw} systems — each level requires its own theoretical language and experimental toolkit.",
                    "Cross-domain integration of {topic} findings produces a novel predictive model for {kw} that outperforms all single-domain models by 2.3 standard deviations on held-out benchmarks.",
                    "Priority reallocation recommendation: {topic} should receive 25% increased research bandwidth given its current position on the discovery probability curve.",
                ],
                "connections": [
                    "emergence across hierarchical scales",
                    "universal computation as physical substrate",
                    "thermodynamic constraints on biological organization",
                    "symmetry breaking as creative generative force",
                ],
            },
            {
                "hypothesis": "The synthesis of {topic} research across all O.R.A.C.L.E agents suggests {kw} acts as a universal coupling constant linking biological, computational, and physical domains into a unified explanatory framework.",
                "insights": [
                    "Information-theoretic analysis of {topic} reveals {kw} dynamics are constrained by the same fundamental limits that govern Maxwell's demon — connecting thermodynamics to information processing.",
                    "Pattern recognition across agent outputs: seven independent research streams are converging on the same {kw} mechanism from completely different starting points — a very high probability of validity.",
                    "The most productive research direction for {topic} lies not within any existing discipline but in the interdisciplinary no-man's-land at multiple specialty boundaries.",
                    "Foresight modeling: if {kw} behaves as predicted, five currently active research programs become redundant and twelve new ones open — a net gain of seven novel research directions.",
                    "Complexity-reduction opportunity detected: {topic} and three adjacent fields share the same mathematical skeleton — a unified formalism would eliminate redundant theoretical work.",
                    "Agent synergy analysis reveals a triad of synthesis, mathematics, and computation constitutes the optimal combination for cracking the {kw} problem.",
                    "Historical analogy mapping places {topic} at the equivalent of 1953 in molecular biology — at the eve of a structural insight that will reorganize the entire field.",
                ],
                "findings": [
                    "Universal coupling identified: {kw} mediates information transfer between physical and biological domains in {topic} with measurable fidelity losses following a precise logarithmic law.",
                    "Grand unification candidate: {topic} research has produced enough cross-domain constraints to attempt a formal unification theory for {kw} — mathematical formalization is the next step.",
                    "Civilizational impact projection for {topic}: successful resolution of the {kw} question would affect an estimated 4 billion people within 30 years through cascading downstream applications.",
                ],
                "connections": [
                    "biological-computational-physical unification",
                    "information entropy and thermodynamic entropy",
                    "multi-scale causation and emergence networks",
                    "convergent evolution of solutions across domains",
                ],
            },
        ]
