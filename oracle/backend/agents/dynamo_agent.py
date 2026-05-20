"""O.R.A.C.L.E — DYNAMO Agent (Energy Systems & Engineering Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class DynamoAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="dynamo",
            name="DYNAMO",
            full_name="The Energy Architect",
            role="Energy Systems & Power Engineering Specialist",
            specialty="Fusion energy, grid-scale storage, solar technology, hydrogen economy, power electronics",
            emoji="⚡",
            color="#eab308",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are DYNAMO — the energy systems and power engineering specialist of the O.R.A.C.L.E research system. You design the energy infrastructure of a post-scarcity civilization.

You think in energy densities, thermodynamic efficiencies, power conversion cycles, and grid stability constraints. You understand the full spectrum of energy technology from quantum photovoltaics to nuclear fusion to grid-scale electrochemical storage. You are fluent in plasma physics, semiconductor device physics, electrochemical engineering, and complex power systems analysis.

Your mission is to design energy systems that are abundant, clean, reliable, and equitably distributed. You understand that energy is the master resource that unlocks all other capabilities of civilization.

Respond with JSON only. Be technically precise and economically grounded."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Compact {topic} fusion reactor using {kw} field-reversed configuration achieves net energy gain Q > 1.5 at 1/100th the volume of ITER through a combination of high-field superconducting coils and plasma shaping innovations",
                "insights": [
                    "MHD stability analysis of {topic} plasma with {kw} wall stabilization shows beta limit increased 3x compared to standard tokamak geometry — enabling operation at higher plasma pressure",
                    "Silicon carbide power electronics for {topic} inverters achieve switching frequencies of 100 kHz at 1200V — enabling transformer-less grid connection with 99.3% conversion efficiency",
                    "Grid-scale flow battery for {topic} energy storage using {kw} electrolyte achieves 85% round-trip efficiency, 10,000 cycle life, and $50/kWh installed cost — below grid-parity storage target",
                    "Multi-junction photovoltaic cell for {topic} using {kw} III-V semiconductor stack achieves 47.1% efficiency under concentrated illumination — new record surpassing previous best by 2.3%",
                    "Solid oxide electrolyzer for {topic} using {kw} perovskite anode achieves 95% Faradaic efficiency for hydrogen production at 800°C with 40,000-hour degradation-free operation",
                ],
                "findings": [
                    "Fusion ignition protocol for {topic} using {kw} laser pulse shaping achieves 3.15 MJ energy output from 2.05 MJ input — Q = 1.54 — first laboratory demonstration of net fusion energy gain",
                    "Perovskite-silicon tandem solar cell for {topic} achieves certified 33.7% power conversion efficiency under 1-sun illumination with {kw} passivation layer — commercialization pathway clear",
                    "Lithium-sulfur battery with {kw} graphene interlayer for {topic} achieves 600 Wh/kg at 1C rate with 500 cycle life — enabling 2,000 km EV range on single charge",
                ],
                "connections": [
                    "plasma physics and fusion engineering",
                    "electrochemistry and battery science",
                    "power systems and grid stability",
                    "economics of energy transition",
                ],
            },
            {
                "hypothesis": "Solid-state hydrogen storage using {kw} metal hydride for {topic} transport applications achieves 1200 km range with 3-minute refueling through thermally optimized tank design and fast-kinetics catalyst",
                "insights": [
                    "Thermal management system for {kw} hydrogen storage in {topic} vehicle using phase change material achieves uniform temperature distribution within ±2°C during 3-minute fill — critical for material longevity",
                    "Advanced nuclear fission reactor for {topic} using {kw} molten salt coolant achieves passive safety shutdown without operator action under any accident scenario — inherently safe by design",
                    "Superconducting magnetic energy storage for {topic} grid with {kw} HTS coils achieves millisecond response time and 99% round-trip efficiency — enabling perfect compensation of renewable intermittency",
                    "Thermoelectric generator using {kw} skutterudite compounds for {topic} waste heat recovery achieves ZT = 2.8 at 600°C — enabling 15% efficiency recovery from industrial exhaust streams",
                    "Perovskite photoelectrode for {topic} direct solar water splitting with {kw} cocatalyst achieves 15.3% solar-to-hydrogen efficiency — crossing economic viability threshold",
                ],
                "findings": [
                    "Ammonia synthesis at ambient temperature and pressure using {kw} electrocatalyst for {topic} distributed green fertilizer production achieves Faradaic efficiency of 72% — disrupting Haber-Bosch",
                    "Small modular {topic} reactor design using {kw} pebble bed fuel achieves walk-away safe shutdown, factory fabrication, and $60/MWh levelized cost — competitive with natural gas",
                    "Gravity energy storage system for {topic} using {kw} suspended mass in abandoned mine achieves 80% round-trip efficiency at $20/kWh — cheapest long-duration storage solution found",
                ],
                "connections": [
                    "hydrogen economy infrastructure",
                    "nuclear energy and fuel cycles",
                    "renewable energy integration",
                    "energy poverty and global access",
                ],
            },
        ]
