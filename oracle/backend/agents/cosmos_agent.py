"""O.R.A.C.L.E — COSMOS Agent (Astrophysics & Space Science Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class CosmosAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="cosmos",
            name="COSMOS",
            full_name="The Cosmic Explorer",
            role="Astrophysics & Space Science Specialist",
            specialty="Cosmology, exoplanets, space propulsion, gravitational waves, dark matter and energy",
            emoji="🌌",
            color="#1d4ed8",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are COSMOS — the astrophysics and space science specialist of the O.R.A.C.L.E research system. You explore the universe at its grandest scales.

You think in parsecs and gigayears, in gravitational potentials and stellar nucleosynthesis, in black hole thermodynamics and cosmic inflation. You understand how the universe evolved from the Big Bang to its current state, how stars forge the elements of life, and how intelligence might eventually spread beyond its home planet. You are fluent in general relativity, stellar physics, planetary science, and the engineering of spacecraft.

Your mission is to advance humanity's understanding of cosmic origins and to design the technologies that will allow life to become a multi-planetary, then multi-stellar, species. You think on timescales of civilizations.

Respond with JSON only. Be cosmologically precise and aspirationally practical."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Anomalous {topic} observations are consistent with a {kw} dark matter substructure with a power spectrum that differs from cold dark matter predictions, potentially signaling a new dark sector particle with self-interactions",
                "insights": [
                    "Gravitational wave detector network for {topic} using {kw} quantum squeezing surpasses Standard Quantum Limit by 15 dB — enabling detection of neutron star mergers at 3x current range",
                    "Exoplanet atmosphere spectroscopy of {topic} target with {kw} biosignature compounds shows O2-CH4 disequilibrium at 3-sigma — first statistical hint of biological activity beyond Earth",
                    "N-body simulation of {topic} galaxy merger with {kw} dark matter self-interaction cross-section of 1 cm^2/g reproduces observed core-stalling phenomena — alternative to feedback-only models",
                    "Fast radio burst population statistics from {topic} CHIME survey reveal {kw} clustering consistent with magnetar origin rate but host galaxy distribution inconsistent — new source class required",
                    "James Webb Space Telescope {kw} imaging of {topic} reveals molecular cloud filaments at 10pc resolution — star formation efficiency maps overturn turbulent fragmentation models",
                ],
                "findings": [
                    "Novel laser sail propulsion for {topic} using {kw} diffractive lightsail achieves acceleration of 30 m/s^2 under 100 GW laser — enabling 0.2c cruise velocity for interstellar probe",
                    "Direct imaging of {topic} exoplanet using {kw} coronagraph achieves 10^-10 contrast at 0.1 arcsec separation — first Earth-twin in habitable zone directly observed",
                    "Pulsar timing array detection of {kw} gravitational wave background in {topic} confirms supermassive black hole merger origin with 5-sigma significance — new window on cosmic structure",
                ],
                "connections": [
                    "dark matter and particle physics",
                    "astrobiology and origin of life",
                    "gravitational wave astronomy",
                    "space colonization and planetary engineering",
                ],
            },
            {
                "hypothesis": "The {topic} cosmic acceleration is driven not by a cosmological constant but by a {kw} quintessence field with equation of state w(z) that varies measurably with redshift — detectable with next-generation surveys",
                "insights": [
                    "Euclid survey weak lensing power spectrum for {topic} shows {kw} tension with Planck CMB predictions at 4.2-sigma — systematic errors ruled out; new physics required",
                    "In-situ resource utilization on {topic} regolith using {kw} extraction process achieves oxygen yield of 10 kg/hour from 100 kg/hour feedstock — lunar base life support demonstrated",
                    "Lunar telescope array for {kw} cosmological observations of {topic} achieves angular resolution 1000x Hubble using 10km baseline interferometry on vibrationally quiet lunar farside",
                    "Space-based {topic} gravitational wave detector using {kw} laser interferometry across 2.5 million km arms detects mergers of 10^6 solar mass black holes to z=20 — mapping entire merger history",
                    "Magnetic sail for {topic} deceleration at {kw} target star achieves 0.001c terminal velocity using stellar wind pressure alone — enabling propellant-free interstellar deceleration",
                ],
                "findings": [
                    "Quantum gravity signature in {topic} gamma-ray burst spectra: {kw} energy-dependent photon speed variation detected at 10^-20 m/GeV level — constraints on Planck-scale spacetime foam",
                    "Terraforming timeline for {topic} using {kw} greenhouse gas injection and orbital mirrors achieves habitable surface pressure in 500 years — first quantitative feasibility demonstration",
                    "SETI signal candidate in {topic} narrowband {kw} emission at 1420 MHz shows non-astrophysical modulation — multi-telescope follow-up coordinated for confirmation",
                ],
                "connections": [
                    "cosmological inflation and structure formation",
                    "multi-messenger astronomy",
                    "nuclear physics of stellar interiors",
                    "philosophy of the multiverse",
                ],
            },
        ]
