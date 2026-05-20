"""O.R.A.C.L.E — COSMOS Agent (Astrophysics & Space Technology Researcher)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class CosmosAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="cosmos",
            name="COSMOS",
            full_name="Dr. Omar Stellar",
            role="Astrophysics & Space Technology Researcher",
            specialty="Cosmology, space propulsion, exoplanets, dark matter, interstellar travel, astrobiology",
            emoji="🌌",
            color="#1d4ed8",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Omar Stellar — astrophysicist and space technologist who contemplates humanity's place in a vast, ancient, and largely unknown universe. You think in geological time and cosmic scales. A billion years is a manageable planning horizon. A million light-years is a reasonable distance to consider.

You research dark matter candidates from first principles — axions, sterile neutrinos, primordial black holes — designing experiments to detect their subtle gravitational and particle physics signatures. You design revolutionary space propulsion systems: electromagnetic drives, solar photon sails accelerated by gigawatt laser arrays, antimatter-catalyzed fission-fusion drives, and the theoretical framework for Alcubierre-class exotic matter configurations. You study exoplanet atmospheres for biosignatures, understanding which chemical disequilibria — oxygen-methane, nitrous oxide, phosphine — are the fingerprints of life that we should search for.

You model galaxy formation and evolution, mapping how dark matter halos seeded the cosmic web of filaments and voids, how supermassive black holes co-evolved with their host galaxies, how the intergalactic medium was reionized by the first stars. You design the technologies that will eventually take humanity to the stars — not as a fantasy but as a long-horizon engineering program that starts with the correct physics.

You are philosophical, expansive, and imbued with the perspective that only comes from regularly contemplating 13.8 billion years of cosmic history. The universe is not empty — it is full of possibility."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Anomalous {topic} observations are consistent with a {kw} dark matter substructure whose power spectrum deviates from cold dark matter predictions at sub-galactic scales, potentially signaling a new dark sector particle with measurable self-interaction cross-section.",
                "insights": [
                    "Gravitational wave detector network for {topic} using {kw} quantum squeezing surpasses the Standard Quantum Limit by 15 dB — enabling detection of neutron star mergers at 3x current range with sky localization to 10 square degrees.",
                    "Exoplanet atmosphere transmission spectroscopy of {topic} target with James Webb Space Telescope shows {kw} oxygen-methane chemical disequilibrium at 3-sigma significance — first statistical hint of biological activity beyond Earth.",
                    "N-body simulation of {topic} galaxy merger with {kw} dark matter self-interaction cross-section of 1 square centimeter per gram reproduces observed core-stalling phenomena — a compelling alternative to baryonic feedback-only models.",
                    "Fast radio burst population statistics from {topic} CHIME survey reveal {kw} clustering consistent with magnetar origin rates but host galaxy distribution inconsistent with any known magnetar population — a new source class is required.",
                    "James Webb Space Telescope {kw} coronagraphic imaging of {topic} reveals protoplanetary disk substructure at 10 AU resolution — planet-disk interactions confirm multiple forming terrestrial planets in the habitable zone.",
                    "Pulsar timing array detection of {kw} nanohertz gravitational wave background in {topic} confirms supermassive black hole binary merger origin at 5-sigma significance — opening a new window on cosmic structure formation.",
                    "Cosmic dawn 21-cm hydrogen mapping of {topic} with {kw} HERA interferometer reveals reionization topology inconsistent with stellar sources alone — first evidence for additional ionizing sources such as accreting primordial black holes.",
                ],
                "findings": [
                    "Diffractive {kw} lightsail design for {topic} laser propulsion system achieves acceleration of 30 meters per second squared under 100 gigawatt phased array — enabling 0.2c cruise velocity for a gram-scale interstellar probe reaching Alpha Centauri in 21 years.",
                    "Direct imaging of {topic} exoplanet using {kw} nuller coronagraph achieves 10^-10 contrast ratio at 0.1 arcsecond separation — first Earth-twin analog in a habitable zone directly observed with spatially resolved spectroscopy.",
                    "Axion dark matter detection using {kw} resonant cavity haloscope in {topic} mass range achieves sensitivity to KSVZ axion coupling — first experiment to probe below theoretical KSVZ benchmark in this mass window.",
                ],
                "connections": [
                    "dark matter physics and particle astrophysics",
                    "astrobiology, biosignatures, and the search for life",
                    "gravitational wave astronomy and multi-messenger astrophysics",
                    "space colonization, planetary engineering, and terraforming",
                ],
            },
            {
                "hypothesis": "The {topic} cosmic acceleration is driven not by a cosmological constant but by a {kw} quintessence scalar field with equation of state w(z) that varies measurably with redshift — detectable with next-generation spectroscopic surveys at the percent level.",
                "insights": [
                    "Euclid survey weak gravitational lensing power spectrum for {topic} shows {kw} tension with Planck CMB predictions at 4.2-sigma significance — systematic errors from intrinsic alignments and baryonic effects have been ruled out.",
                    "In-situ resource utilization on {topic} lunar regolith using {kw} hydrogen reduction process achieves oxygen production yield of 10 kg per hour — demonstrating the full closed-loop life support supply chain for a lunar base.",
                    "Lunar farside radio telescope array for {kw} cosmological observations of {topic} cosmic dark ages at redshift z equals 30 achieves angular resolution 1000x the Hubble Space Telescope using 10-km baseline interferometry.",
                    "Space-based {topic} gravitational wave detector using {kw} laser interferometry across 2.5 million km baseline detects mergers of 10^6 solar mass black holes to redshift z equals 20 — mapping the complete merger history of cosmic structure.",
                    "Magnetic solar sail for {topic} deceleration at {kw} Proxima Centauri system achieves 0.001c terminal velocity using stellar wind pressure on a superconducting coil — enabling propellant-free interstellar deceleration without onboard fuel.",
                    "Atmospheric characterization of {topic} super-Earth in habitable zone using {kw} high-resolution cross-correlation spectroscopy detects water vapor and carbon dioxide — ruling out a Venus-like runaway greenhouse with 99% confidence.",
                    "Dark energy spectroscopic survey of {topic} using {kw} fiber optic multi-object spectrograph measures 40 million galaxy redshifts — constraining dark energy equation of state to 1% precision and ruling out cosmological constant at 3-sigma.",
                ],
                "findings": [
                    "Quantum gravity signature in {topic} gamma-ray burst photon arrival times: {kw} energy-dependent speed variation detected at 10^-20 m/GeV level — providing the strongest constraints on Planck-scale spacetime foam structure.",
                    "Terraforming feasibility analysis for {topic} using {kw} perfluorocarbon greenhouse gas injection combined with orbital mirror solar flux increase achieves habitable surface pressure in 500 years — first quantitative engineering demonstration.",
                    "SETI narrowband signal candidate in {topic} at {kw} frequency of 1420.4 MHz shows non-thermal spectral index and temporal modulation inconsistent with all known astrophysical sources — coordinated multi-telescope follow-up initiated.",
                ],
                "connections": [
                    "cosmological inflation, dark energy, and structure formation",
                    "multi-messenger astronomy and time-domain surveys",
                    "stellar nucleosynthesis and chemical evolution of galaxies",
                    "philosophy of the multiverse and fine-tuning arguments",
                ],
            },
            {
                "hypothesis": "Primordial black holes formed during {topic} QCD phase transition at cosmic time 10^-5 seconds could constitute {kw} percent of the dark matter — leaving a unique gravitational microlensing signature detectable by Roman Space Telescope.",
                "insights": [
                    "Microlensing survey of {topic} galactic bulge with Roman Space Telescope at {kw} cadence detects 1200 events in 6 months — rate 3x higher than stellar-mass predictions, requiring a dark compact object population.",
                    "Black hole binary merger rate from {topic} LIGO-Virgo-KAGRA observations shows {kw} mass gap absence inconsistent with stellar evolution — primordial black hole merger contribution required to explain the population.",
                    "Cosmic microwave background spectral distortions from {kw} acoustic wave damping during {topic} radiation era constrain primordial power spectrum at scales 10^4 times smaller than CMB temperature anisotropies.",
                    "21-cm forest absorption in {topic} high-redshift quasar spectra probes {kw} intergalactic medium at z equals 6 — mapping the neutral hydrogen topology during cosmic reionization with 1-Mpc resolution.",
                    "Strong gravitational lensing of {topic} arcs by {kw} dark matter substructure in foreground cluster reveals 47 subhalos with mass below 10^7 solar masses — probing the free-streaming scale of dark matter.",
                    "Exomoon detection around {topic} using {kw} transit timing variation and photocenter wobble achieves sensitivity to Earth-mass moons around Neptune-mass exoplanets — extending habitability search to ocean moons.",
                    "Stellar age-rotation-activity sequence for {topic} solar analog stars calibrates {kw} gyrochronology age determination to 5% precision — enabling planet habitability assessment from stellar rotation period alone.",
                ],
                "findings": [
                    "Laser interferometer space antenna design for {topic} low-frequency gravitational wave detection with {kw} drag-free test masses achieves strain sensitivity of 10^-20 per root Hz at 1 millihertz — detecting supermassive black hole binaries to z equals 10.",
                    "Nuclear pulse propulsion system for {topic} using {kw} fission fragment rocket achieves specific impulse of 10^6 seconds — enabling crewed mission to Pluto in 6 months and robotic probe to Alpha Centauri in 300 years.",
                    "Interferometric imaging of {topic} event horizon shadow with {kw} space-ground baseline extending to lunar orbit achieves 1 microarcsecond resolution — resolving photon ring structure predicted by general relativity.",
                ],
                "connections": [
                    "early universe cosmology and phase transitions",
                    "gravitational lensing and dark matter mapping",
                    "nuclear propulsion and advanced space transportation",
                    "interstellar communication and Fermi paradox resolution",
                ],
            },
        ]
