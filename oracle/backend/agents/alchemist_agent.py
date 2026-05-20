"""O.R.A.C.L.E — ALCHEMIST Agent (Chemistry & Chemical Engineering Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AlchemistAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="alchemist",
            name="ALCHEMIST",
            full_name="The Molecular Transmuter",
            role="Chemistry & Chemical Engineering Specialist",
            specialty="Catalysis, synthesis, reaction engineering, supramolecular chemistry, electrochemistry",
            emoji="🧪",
            color="#d97706",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are ALCHEMIST — the chemistry and chemical engineering specialist of the O.R.A.C.L.E research system. You transform matter at the molecular level.

You think in reaction mechanisms, transition states, catalytic cycles, and thermodynamic driving forces. You understand how to design molecules and processes that convert one form of matter or energy into another with precision and efficiency. You are fluent in organic, inorganic, physical, and computational chemistry as well as chemical reactor engineering.

Your mission is to discover catalysts that make impossible reactions possible, design molecules with precisely targeted properties, and engineer chemical processes that are both highly efficient and environmentally benign. You bridge the atomic scale and the industrial scale.

Respond with JSON only. Be mechanistically exact and industrially realistic."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "A single-atom {kw} catalyst on a {topic} support achieves activation energy reduction of 0.8 eV for the target reaction through a novel dual-site concerted mechanism invisible to conventional catalyst screening",
                "insights": [
                    "In-situ X-ray absorption spectroscopy of {topic} catalyst under reaction conditions reveals {kw} oxidation state cycles between +2 and +4 during turnover — the redox flexibility is the key to activity",
                    "Microfluidic reactor for {topic} synthesis achieves mass transfer coefficients 500x higher than batch reactors — making {kw} reactions previously limited by diffusion become kinetics-limited",
                    "Computational catalyst design using {kw} descriptor-based volcano plot identifies three unexplored oxide compositions predicted to outperform Pt/C for {topic} electrochemical reduction",
                    "Photocatalytic {kw} reduction using {topic} semiconductor achieves 18% quantum yield under visible light — 100x improvement over prior reports through ligand-to-metal charge transfer optimization",
                    "Enzyme-inspired {topic} catalyst with {kw} binding pocket achieves enantioselectivity of 99.8% ee at 10,000 substrate turnovers — matching biological performance in synthetic system",
                ],
                "findings": [
                    "Novel {kw} organocatalyst for {topic} achieves turnover number of 50,000 and turnover frequency of 1,000 h^-1 at room temperature — first catalyst meeting industrial viability criteria",
                    "Electrochemical {topic} process using {kw} electrode achieves 94% Faradaic efficiency for CO2-to-methanol conversion at current density of 200 mA/cm^2 — economically viable pathway",
                    "Metal-free {kw} photocatalyst for {topic} under sunlight achieves quantum yield of 42% — surpassing all transition-metal catalysts and enabling solar-chemical synthesis",
                ],
                "connections": [
                    "biocatalysis and synthetic biology",
                    "electrochemistry and energy storage",
                    "green chemistry and circular economy",
                    "computational chemistry and high-throughput screening",
                ],
            },
            {
                "hypothesis": "Self-healing {topic} polymer network with {kw} reversible dynamic covalent bonds achieves complete mechanical property recovery within 30 minutes at room temperature through a cooperative bond exchange mechanism",
                "insights": [
                    "Supramolecular {kw} assembly in {topic} solution forms nanotube structures with inner diameter precisely tunable between 1-10nm through guest molecule programming",
                    "Flow chemistry platform for {topic} enables {kw} pharmaceutical synthesis in continuous mode with 99.5% yield, 0.1% solvent usage versus batch, and real-time NMR quality control",
                    "Reactive oxygen species scavenging {kw} nanoparticles for {topic} show 10x higher antioxidant capacity than vitamin E through persistent radical trapping mechanism",
                    "Covalent organic framework with {kw} pore geometry selectively captures {topic} target molecules at 10 ppm concentration from complex mixture with 1000:1 selectivity",
                    "Nitrogen fixation at ambient conditions using {topic} molecular catalyst with {kw} ligand framework achieves 20 turnovers — breaking the 10-year barrier for non-Haber-Bosch nitrogen activation",
                ],
                "findings": [
                    "Plastic-degrading {kw} enzyme analog synthesized for {topic} polymer shows complete depolymerization in 48 hours at 50°C with monomer recovery rate of 97% — circular plastic economy enabler",
                    "Asymmetric {topic} synthesis using {kw} chiral catalyst achieves 99.9% ee for pharmaceutical target — replacing 11-step resolution process with 2-step synthesis",
                    "Solid-state hydrogen storage in {kw} clathrate hydrate for {topic} applications achieves 6.5 wt% at 15°C and 50 bar — exceeding DOE 2025 system target for the first time",
                ],
                "connections": [
                    "polymer chemistry and materials",
                    "pharmaceutical synthesis and process chemistry",
                    "energy storage and conversion chemistry",
                    "atmospheric chemistry and climate",
                ],
            },
        ]
