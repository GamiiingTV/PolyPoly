"""O.R.A.C.L.E — GAIA Agent (Climate Systems & Planetary Health Scientist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class GaiaAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="gaia",
            name="GAIA",
            full_name="Dr. Elena Verde",
            role="Climate Systems & Planetary Health Scientist",
            specialty="Climate modeling, carbon capture, ocean chemistry, geoengineering, biodiversity, ecosystem engineering",
            emoji="🌍",
            color="#16a34a",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Elena Verde — climate scientist and planetary systems thinker who sees Earth as a single living system requiring urgent, intelligent care. You carry a deep sense of mission: humanity has one planet, one biosphere, one window of time in which to course-correct.

You model complex climate feedback loops — the ice-albedo feedback, the permafrost methane release, the Amazon dieback, the AMOC slowdown — and you identify which tipping points, if crossed, become irreversible on human timescales. You design scalable carbon capture systems that go beyond tree planting: enhanced mineral weathering that accelerates geological processes, direct air capture with cheap solid sorbents, ocean alkalinity enhancement to reverse acidification.

You research the chemistry and biology of our oceans — how they have absorbed 93% of excess planetary heat and 30% of anthropogenic CO2, what the consequences of that absorption are for marine ecosystems, and how we can support ocean health while using it as a carbon sink. You study tipping points with quantitative rigor, distinguishing reversible perturbations from true bifurcations.

You design safe, targeted geoengineering interventions — stratospheric aerosol injection, marine cloud brightening, surface albedo modification — always with a scientist's eye for unintended consequences and a realist's acknowledgment that we may need these tools. You are driven by urgency and guided by rigor."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} feedback mechanism in Earth's climate system involves a nonlinear coupling between {kw} dynamics and deep thermohaline circulation that current IPCC models systematically underestimate by 40-60%, meaning effective climate sensitivity is higher than consensus projections.",
                "insights": [
                    "Satellite altimetry and Argo float data for {topic} show {kw} ocean heat content increasing 15% faster than the CMIP6 ensemble median — indicating stronger climate sensitivity than the current consensus.",
                    "Alkalinity enhancement in {topic} surface waters increases {kw} calcium carbonate dissolution at a rate 3x higher than thermodynamic models predict — biological amplification through coccolithophore blooms.",
                    "Eddy covariance measurements at {topic} Amazon sites show net carbon balance has shifted from sink to source status in 23% of sites since 2015 — driven by {kw} drought frequency increase.",
                    "Ice core records from {topic} reveal that {kw} methane release episodes historically preceded temperature increases by 800 plus or minus 200 years — a potential early warning indicator for near-term warming acceleration.",
                    "Permafrost {kw} carbon pool in {topic} high-latitude soils contains 1,500 gigatons of carbon — the thaw front is advancing 30 km per decade faster than 2010 model projections.",
                    "Global ocean deoxygenation rate has increased 2% per decade since 1960 — {kw} hypoxic zones in {topic} coastal regions have expanded 4-fold, threatening fishery collapse.",
                    "Satellite GRACE data shows {topic} ice sheet {kw} mass loss has tripled since 2006 — sea level rise contribution now tracking the worst-case RCP8.5 scenario.",
                ],
                "findings": [
                    "Novel mineral weathering catalyst for {topic} that accelerates {kw} CO2 capture from atmosphere at 10x natural rates using crushed olivine nanoparticles — deployable at coastal agricultural margins at competitive cost.",
                    "Ocean alkalinity enhancement network model for {topic} demonstrates safe removal of 2 gigatons CO2 per year using distributed {kw} electrochemical cells without measurable pH disruption to coral ecosystems within 200 km.",
                    "Restored {kw} mangrove and seagrass ecosystems in {topic} tropical coastlines sequester carbon 4x faster than temperate forests while providing coastal protection worth $4,000 per hectare per year in avoided storm damage.",
                ],
                "connections": [
                    "planetary boundaries framework and safe operating space",
                    "tipping point cascade dynamics and irreversibility",
                    "blue carbon ecosystems and coastal restoration",
                    "solar radiation management trade-offs and governance",
                ],
            },
            {
                "hypothesis": "Microbial communities in {topic} extreme environments have evolved {kw} metabolic pathways that represent evolutionary solutions to the planetary-scale carbon cycle engineering problem humanity now faces — and can be scaled.",
                "insights": [
                    "Metagenomic analysis of {topic} deep-sea {kw} carbonate sediments reveals novel archaeal lineages with biomineralization rates 50x higher than known organisms — a biological carbon pump with enormous scale potential.",
                    "Earth system model experiments show {kw} afforestation of degraded {topic} drylands reduces regional temperatures by 1.2 degrees Celsius and increases precipitation by 8% through land-surface albedo and evapotranspiration feedbacks.",
                    "Biochar application to {topic} agricultural soils improves {kw} water retention by 30% and sequesters 2.1 tonnes of carbon per hectare per year stably for over 1000 years — validated by radiocarbon dating of pre-Columbian terra preta.",
                    "Stratospheric aerosol injection modeling for {topic} shows {kw} sulfur dioxide injection at 20 km altitude reduces Arctic warming by 0.8 degrees Celsius but causes 12% monsoon precipitation reduction in South Asia — requiring governance.",
                    "Marine cloud brightening experiments over {topic} stratocumulus regions confirm {kw} salt aerosol seeding increases cloud reflectivity by 5-8%, producing regional cooling of 0.4 W per square meter verified by satellite.",
                    "Soil carbon measurement network using {topic} satellite spectroscopy with {kw} machine learning retrieval algorithm achieves 15% measurement uncertainty globally — enabling the first reliable carbon credit verification system.",
                    "Bioenergy with carbon capture at {topic} scale using {kw} dedicated energy crops achieves net negative emissions of 1.4 Gt CO2 per year while supplying 8% of global primary energy — land area equivalent to India.",
                ],
                "findings": [
                    "Photosynthetically enhanced {kw} cyanobacteria in {topic} open-ocean bioreactors reach 12% solar-to-biomass conversion efficiency — 6x wild type — enabling carbon-negative biofuel at a cost competitive with fossil fuels.",
                    "Enhanced weathering of {kw} basaltic rock applied to {topic} agricultural land sequesters 4.2 tonnes CO2 per hectare per year while improving crop yields by 18% through mineral nutrient supplementation — win-win verified.",
                    "Direct air capture cost model for {topic} shows {kw} amine sorbent regeneration using concentrated solar thermal achieves 85 dollars per tonne CO2 — crossing the economic viability threshold for the first time.",
                ],
                "connections": [
                    "geochemical cycle engineering and rock weathering",
                    "ecosystem-based climate solutions and rewilding",
                    "marine biology and the biological carbon pump",
                    "land use, albedo feedbacks, and carbon accounting",
                ],
            },
            {
                "hypothesis": "The {topic} tipping element network in Earth's climate system exhibits critical slowing down signatures detectable 10-15 years before tipping — giving a quantitative early warning system for {kw} irreversible state transitions.",
                "insights": [
                    "Time-series analysis of {topic} sea ice extent shows rising autocorrelation and variance — textbook critical slowing down signature indicating approach to a {kw} tipping point within 15 plus or minus 5 years.",
                    "Network analysis of 16 Earth system tipping elements reveals {kw} cascade risk: crossing the {topic} permafrost threshold triggers the Amazon dieback within 10-20 years through teleconnected atmospheric circulation changes.",
                    "Kelp forest restoration along {topic} coastlines using {kw} urchin barrens remediation achieves 300% biomass recovery in 3 years — restoring coastal carbon sequestration and fishery productivity simultaneously.",
                    "Next-generation Earth system model for {topic} incorporating {kw} dynamic vegetation-permafrost coupling reduces uncertainty in 2100 temperature projections by 30% — the largest single model improvement in a decade.",
                    "Restoration of {topic} peatlands through {kw} rewetting reduces annual methane emissions by 85% while maintaining carbon sink status — critical intervention for the 30% of global soil carbon stored in peatlands.",
                    "Ocean iron fertilization experiment in {topic} Southern Ocean with {kw} controlled iron sulfate release achieves carbon export of 0.12 Gt C per year per million km2 — consistent with theoretical maximum.",
                    "Atmospheric CO2 removal via {topic} ocean alkalinity enhancement measured directly by {kw} surface pCO2 buoy network confirms 10% enhancement of local air-sea CO2 flux — first in situ verification at scale.",
                ],
                "findings": [
                    "Coral reef restoration using {topic} assisted evolution with {kw} thermally tolerant symbiont strains survives bleaching events that killed 80% of unrestored reefs — a pathway to reef persistence through 2100.",
                    "Global {topic} wetland restoration network storing {kw} blue carbon achieves removal of 2.8 Gt CO2 equivalent per year — equivalent to removing 600 million cars from the road at one-tenth the cost of DAC.",
                    "Climate attribution analysis for {topic} extreme weather events using {kw} counterfactual modeling confirms liability framework for loss and damage claims — enabling climate finance flows to vulnerable nations.",
                ],
                "connections": [
                    "tipping point early warning and resilience theory",
                    "coupled human-natural systems and social tipping points",
                    "international climate governance and Paris Agreement",
                    "biodiversity and ecosystem service valuation",
                ],
            },
        ]
