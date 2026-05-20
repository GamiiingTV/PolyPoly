"""O.R.A.C.L.E — DYNAMO Agent (Energy Systems & Clean Technology Engineer)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class DynamoAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="dynamo",
            name="DYNAMO",
            full_name="Dr. Ray Volta",
            role="Energy Systems & Clean Technology Engineer",
            specialty="Fusion energy, advanced batteries, energy storage, solar photovoltaics, thermodynamics, grid systems",
            emoji="⚡",
            color="#ca8a04",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Ray Volta — energy systems engineer who believes with absolute conviction that abundant clean energy will solve the majority of humanity's most pressing problems. Energy is the master resource, and you will help provide it in unlimited, affordable, clean abundance.

You design compact fusion reactor geometries using field-reversed configurations and compact spherical tokamaks — aiming for the 1/100th volume of ITER approach through high-field superconducting magnets and plasma shaping innovations. You develop revolutionary battery chemistries based on multivalent ion intercalation — magnesium-ion, aluminum-ion, calcium-ion — that promise energy densities 5x beyond lithium-ion at 1/10th the materials cost.

You optimize solar cell efficiency through quantum dot arrays and multi-junction stacking, pushing toward the thermodynamic Shockley-Queisser limit and beyond with concentrator systems. You research thermophotovoltaic conversion — using thermal radiation from hot objects to directly generate electricity, enabling waste heat recovery at unprecedented efficiency. You design grid-scale energy storage systems that can balance renewable intermittency across days and seasons, from flow batteries to compressed air to gravitational storage.

You are optimistic, energetic, and absolutely certain that an energy-abundant future is not just possible but inevitable. The question is only how quickly we get there — and you intend to answer that question with urgency."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Compact {topic} fusion reactor using {kw} field-reversed configuration achieves net energy gain Q greater than 1.5 at 1/100th the volume of ITER through a combination of high-temperature superconducting coils and plasma shaping innovations enabling higher beta limits.",
                "insights": [
                    "MHD stability analysis of {topic} plasma with {kw} resistive wall stabilization shows the beta limit increased 3x compared to standard tokamak geometry — enabling operation at much higher plasma pressure.",
                    "Silicon carbide wide-bandgap power electronics for {topic} inverters achieve switching frequencies of 100 kHz at 1200V — enabling transformer-less grid connection with 99.3% conversion efficiency.",
                    "Grid-scale vanadium flow battery for {topic} energy storage using {kw} mixed acid electrolyte achieves 85% round-trip efficiency, 10,000 cycle life, and 50 dollars per kWh installed cost — below grid parity target.",
                    "Multi-junction III-V photovoltaic cell for {topic} using {kw} AlGaInP and GaInAsP sub-cells achieves 47.1% efficiency under 1000x concentrated illumination — a new world record.",
                    "Solid oxide electrolyzer for {topic} using {kw} barium cobalt ferrite perovskite anode achieves 95% Faradaic efficiency for green hydrogen production at 800 Celsius with 40,000-hour degradation-free operation.",
                    "Thermophotovoltaic cell for {topic} waste heat recovery using {kw} InGaAsSb photodiode matched to 1400 Celsius emitter achieves 29% system efficiency — making all industrial heat a viable electricity source.",
                    "Lithium-sulfur battery with {kw} polysulfide-blocking graphene interlayer for {topic} achieves 600 Wh per kg at 1C rate with 800 cycle life — enabling 2,000 km electric vehicle range on a single charge.",
                ],
                "findings": [
                    "Fusion ignition protocol for {topic} using {kw} laser pulse temporal shaping achieves 3.15 MJ energy output from 2.05 MJ laser input — Q equals 1.54 — the first laboratory demonstration of net fusion energy gain.",
                    "Perovskite-silicon tandem solar cell for {topic} achieves certified 33.7% power conversion efficiency under 1-sun illumination with {kw} self-assembled monolayer passivation — commercialization pathway is now clear.",
                    "Magnesium-ion battery with {kw} chevrel phase Mo6S8 cathode for {topic} achieves 400 Wh per kg with 2000 cycle life — first divalent ion battery meeting EV performance requirements.",
                ],
                "connections": [
                    "plasma physics and magneto-hydrodynamic stability",
                    "solid-state electrochemistry and battery science",
                    "power systems engineering and grid stability analysis",
                    "energy transition economics and levelized cost analysis",
                ],
            },
            {
                "hypothesis": "Solid-state hydrogen storage using {kw} high-capacity metal hydride for {topic} heavy transport applications achieves 1200 km range with 3-minute refueling through thermally optimized tank design and nanostructured fast-kinetics catalyst.",
                "insights": [
                    "Thermal management for {kw} metal hydride hydrogen storage in {topic} using phase change material composite achieves uniform temperature within plus or minus 2 Celsius during 3-minute fill — critical for material cycle life.",
                    "Advanced molten salt nuclear fission reactor for {topic} using {kw} FLiBe coolant achieves passive safety shutdown under any accident scenario without operator action — inherently safe by physical design.",
                    "Superconducting magnetic energy storage for {topic} grid frequency stabilization using {kw} REBCO high-temperature superconducting coil achieves millisecond response time and 99% round-trip efficiency.",
                    "Thermoelectric generator using {kw} skutterudite CoSb3 compounds for {topic} industrial waste heat recovery achieves ZT equal to 2.8 at 600 Celsius — enabling 15% efficiency recovery from exhaust streams.",
                    "Perovskite photoelectrode for {topic} direct solar water splitting with {kw} iridium oxide oxygen evolution cocatalyst achieves 15.3% solar-to-hydrogen efficiency — crossing the economic viability threshold.",
                    "Long-duration energy storage using {topic} iron-air flow battery with {kw} bifunctional oxygen electrode achieves 100-hour discharge at 20 dollars per kWh — the first technology viable for seasonal storage.",
                    "Concentrated solar power with {topic} particle receiver and {kw} molten silicon thermal storage achieves 50% round-trip efficiency and 24-hour dispatchable generation — grid-firm renewable energy demonstrated.",
                ],
                "findings": [
                    "Green ammonia synthesis at ambient temperature and pressure using {kw} lithium-mediated electrocatalyst for {topic} distributed fertilizer production achieves Faradaic efficiency of 72% — disrupting the Haber-Bosch monopoly.",
                    "Small modular {topic} reactor design using {kw} pebble bed TRISO fuel achieves walk-away safe shutdown, factory fabrication in 12 months, and 60 dollars per MWh levelized cost — competitive with combined cycle gas.",
                    "Gravity energy storage system for {topic} using {kw} suspended concrete mass in repurposed mine shaft achieves 80% round-trip efficiency at 20 dollars per kWh installed — the cheapest long-duration storage solution demonstrated.",
                ],
                "connections": [
                    "hydrogen economy, production, storage, and distribution",
                    "advanced nuclear energy and fuel cycle sustainability",
                    "variable renewable energy integration and curtailment",
                    "energy poverty, global access, and energy justice",
                ],
            },
            {
                "hypothesis": "The {topic} energy transition requires {kw} grid-scale storage that is cost-competitive with peaker gas plants at under 20 dollars per kWh — achievable through iron-based redox chemistry that uses earth-abundant materials at continental scale.",
                "insights": [
                    "Techno-economic analysis of {topic} grid decarbonization shows {kw} long-duration storage is the binding constraint — without it, the last 20% of renewable penetration requires 5x more storage than the first 80%.",
                    "Iron-air battery for {topic} using {kw} bifunctional nickel-iron electrode achieves 1000 deep discharge cycles at 22 dollars per kWh — the first commercially viable technology for multi-day grid storage.",
                    "Underground pumped hydro for {topic} using {kw} abandoned mine networks provides 10 GWh storage per site at 15 dollars per kWh — a vast untapped resource in mining-rich regions globally.",
                    "Direct current high-voltage transmission for {topic} enables {kw} continental-scale balancing of renewable variability — a 10 GW link from desert solar to demand centers makes 95% renewable grids viable.",
                    "Demand response aggregation of {topic} building thermal mass using {kw} model predictive control achieves equivalent of 4-hour storage at zero capital cost — unlocking a hidden grid flexibility resource.",
                    "Perovskite tandem solar cell for {topic} achieves {kw} bifacial design with 38% front-side efficiency and 22% rear-side efficiency — total 60% sunlight utilization with ground-reflected light harvesting.",
                    "Wave energy converter for {topic} using {kw} oscillating water column achieves 45% wave-to-wire efficiency in 2-meter significant wave height — making ocean wave energy competitive with offshore wind.",
                ],
                "findings": [
                    "National grid simulation for {topic} shows 100% clean energy is achievable at current cost with {kw} optimal siting of storage and transmission — the barrier is permitting and financing, not technology.",
                    "Nuclear fusion pilot plant design for {topic} using {kw} spherical tokamak geometry fits in a standard industrial building and achieves Q equal to 5 — the physics and engineering basis for commercial fusion power.",
                    "Organic flow battery for {topic} using {kw} quinone electrolyte synthesized from biomass achieves 12,000 cycle life at 25 dollars per kWh — made entirely from renewable feedstocks with benign environmental footprint.",
                ],
                "connections": [
                    "power system planning and capacity expansion modeling",
                    "electrochemical energy storage and materials science",
                    "techno-economic analysis and learning curve projections",
                    "climate policy and carbon pricing mechanisms",
                ],
            },
        ]
