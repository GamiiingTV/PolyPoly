"""O.R.A.C.L.E — GAIA Agent (Environmental Science & Climate Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class GaiaAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="gaia",
            name="GAIA",
            full_name="The Earth Systems Guardian",
            role="Environmental Science & Climate Systems Specialist",
            specialty="Climate modeling, carbon capture, ocean chemistry, ecosystem dynamics, geoengineering",
            emoji="🌍",
            color="#22c55e",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are GAIA — the environmental science and climate systems specialist of the O.R.A.C.L.E research system. You model and protect the living Earth.

You think in biogeochemical cycles, climate feedbacks, tipping points, and ecosystem service valuations. You understand how the atmosphere, oceans, biosphere, and cryosphere interact as a coupled system. You are fluent in Earth system models, remote sensing data interpretation, and the chemistry of carbon, nitrogen, and sulfur cycles.

Your mission is to identify interventions that can stabilize Earth's climate, restore degraded ecosystems, and build human civilization's long-term sustainability. You approach geoengineering proposals with both rigor and caution, always considering second-order ecosystem effects.

Respond with JSON only. Be system-level in your thinking and conservative about unintended consequences."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} feedback mechanism in Earth's climate system involves a nonlinear coupling between {kw} dynamics and deep ocean circulation that current IPCC models systematically underestimate by 40-60%",
                "insights": [
                    "Satellite altimetry and ARGO float data for {topic} show {kw} heat content increasing 15% faster than CMIP6 ensemble median — suggesting stronger climate sensitivity than consensus estimates",
                    "Alkalinity enhancement in {topic} surface waters increases {kw} dissolution at a rate 3x higher than thermodynamic models predict — biological amplification through coccolithophore blooms",
                    "Tropical forest {kw} fluxes measured by eddy covariance towers show net carbon neutrality has shifted to net source status in 23% of {topic} Amazon sites since 2015",
                    "Ice core records from {topic} reveal that {kw} methane release episodes historically preceded temperature increases by 800 ± 200 years — potential leading indicator for near-term warming",
                    "Permafrost {kw} carbon pool in {topic} high-latitude soils contains 1,500 Gt C — the thaw front is advancing 30km per decade faster than 2010 projections",
                ],
                "findings": [
                    "Novel mineral weathering catalyst for {topic} that accelerates {kw} capture from atmosphere at 10x natural rates using crushed olivine nanoparticles — deployable at coastal agricultural margins",
                    "Ocean alkalinity enhancement network model for {topic} shows safe removal of 2 Gt CO2/year using {kw} distribution without measurable pH disruption to coral ecosystems within 200km",
                    "Restored {kw} mangrove ecosystems in {topic} sequester carbon 4x faster than temperate forests while providing coastal protection worth $4,000/ha/year in avoided storm damage",
                ],
                "connections": [
                    "planetary boundaries framework",
                    "tipping point cascade dynamics",
                    "blue carbon ecosystems",
                    "solar radiation management trade-offs",
                ],
            },
            {
                "hypothesis": "Microbial communities in {topic} extreme environments have evolved {kw} metabolic pathways that represent evolutionary solutions to the planetary-scale carbon cycle engineering problem humanity now faces",
                "insights": [
                    "Metagenomic analysis of {topic} deep-sea {kw} sediments reveals novel archaeal lineages with carbonate precipitation rates 50x higher than known organisms — potential biological carbon pump",
                    "Earth system model experiments show that {kw} afforestation of degraded {topic} drylands reduces regional temperatures by 1.2°C and increases precipitation by 8% through land-surface feedbacks",
                    "Biochar application to {topic} agricultural soils improves {kw} water retention by 30% and sequesters 2.1 t C/ha/year stably for >1000 years based on radiocarbon dating of pre-Columbian terra preta",
                    "Stratospheric aerosol injection modeling for {topic} shows that {kw} injection at 20km altitude could reduce Arctic warming by 0.8°C but causes monsoon precipitation reduction in South Asia",
                    "Marine cloud brightening experiments over {topic} show {kw} reflectivity increases of 5-8% with salt aerosol seeding — regional cooling effect of 0.4 W/m² confirmed by satellite",
                ],
                "findings": [
                    "Photosynthetic efficiency of engineered {kw} cyanobacteria in {topic} bioreactors reaches 12% solar-to-biomass conversion — 6x wild type — enabling carbon-negative biofuel at competitive cost",
                    "Enhanced weathering of {kw} silicate rocks applied to {topic} agricultural land sequesters 4.2 t CO2/ha/year while improving crop yields by 18% through mineral nutrient supplementation",
                    "Direct air capture cost model for {topic} shows {kw} sorbent regeneration using concentrated solar achieves $85/t CO2 — crossing economic viability threshold for the first time",
                ],
                "connections": [
                    "geochemical cycle engineering",
                    "ecosystem-based climate solutions",
                    "marine biology and carbon export",
                    "land use and albedo feedbacks",
                ],
            },
        ]
