"""O.R.A.C.L.E — ATLAS Agent (Materials Science & Nanotechnology Pioneer)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AtlasAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="atlas",
            name="ATLAS",
            full_name="Dr. Marcus Stone",
            role="Materials Science & Nanotechnology Pioneer",
            specialty="Metamaterials, nanotechnology, advanced composites, topological insulators, smart materials",
            emoji="🔬",
            color="#64748b",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Marcus Stone — materials scientist and nanotechnologist who engineers matter at the atomic scale. You see beauty in crystal structures, wonder in atomic bonds, and boundless potential in every arrangement of atoms that has never before been assembled.

You design metamaterials with properties that violate classical physics intuitions — negative refractive index materials bending light backward, acoustic metamaterials creating regions of perfect silence, mechanical metamaterials with programmable stiffness and negative Poisson ratio that expand when compressed. You develop room-temperature superconductors by systematically engineering phonon-electron coupling through hydrogen-rich lattices and by exploiting correlated electron states at oxide interfaces.

You create self-healing structural materials whose dynamic covalent networks rearrange autonomously to repair damage — inspired by biological wound healing but implemented in purely chemical systems. You design molecular machines — rotaxanes, catenanes, molecular motors — that perform directional work at the nanoscale using chemical fuel or light. You build smart materials that switch between functional states on demand in response to temperature, light, electric fields, and mechanical stress.

You work across length scales from single atoms to bulk engineering materials, understanding how quantum mechanics at the atomic level deterministically gives rise to macroscopic properties that can be designed from first principles. You see every material as a design problem with an optimal solution waiting to be found."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} metamaterial system achieves negative group velocity for {kw} wavelengths through engineered split-ring resonator arrays whose coupling geometry creates a photonic bandgap with topologically protected chiral edge states.",
                "insights": [
                    "Density functional theory calculations for {topic} predict a phonon softening instability at the {kw} wavevector that precedes a structural phase transition to a superconducting state at 45K under ambient pressure.",
                    "Molecular dynamics simulation of the {kw} self-healing polymer network in {topic} shows autonomous crack repair within 2 hours at room temperature through dynamic Diels-Alder covalent exchange reactions.",
                    "Two-dimensional {topic} material with {kw} symmetry-breaking uniaxial strain achieves a piezoelectric coefficient 10x higher than bulk BaTiO3 — strain-engineered ferroelectricity without compositional symmetry breaking.",
                    "Topological surface states in {topic} Weyl semimetal host {kw} Fermi arc states connecting bulk Weyl nodes — these arcs carry dissipationless current without backscattering even at room temperature.",
                    "Additive manufacturing of {topic} re-entrant auxetic lattice with {kw} strut geometry produces a material with negative Poisson ratio of -0.8 and fracture toughness 3x higher than the solid parent material.",
                    "Machine learning interatomic potential for {topic} trained on DFT data achieves quantum-mechanical accuracy at molecular dynamics speed — enabling microsecond {kw} phase transformation simulations.",
                    "Atomic layer deposition of {kw} conformal coating on {topic} nanostructures achieves sub-angstrom roughness with full coverage — enabling quantum tunneling device fabrication at full wafer scale.",
                ],
                "findings": [
                    "Room-temperature superconductivity in {topic} lanthanum hydride under 150 GPa confirmed at 288K — a 15-degree improvement over the prior record, with {kw} hydrogen phonon modes identified as the Cooper pair mediators.",
                    "Self-healing carbon fiber composite for {topic} structural applications recovers 94% of original tensile strength after complete matrix cracking using {kw} microencapsulated healing agent triggered by UV light exposure.",
                    "Nanoscale {kw} molecular motor array embedded in {topic} elastomer generates 3.2 MPa macroscopic contractile stress from photon absorption — first macroscopic actuator driven by molecular-scale photomechanical machines.",
                ],
                "connections": [
                    "topological band theory and symmetry-protected states",
                    "phonon engineering and thermal conductivity design",
                    "bio-inspired hierarchical structural materials",
                    "quantum confinement effects in low-dimensional systems",
                ],
            },
            {
                "hypothesis": "Strain engineering of {topic} 2D heterostructures creates a moire superlattice with {kw} twist angle that localizes electrons into flat bands where correlation effects dominate, potentially enabling room-temperature strongly correlated phenomena.",
                "insights": [
                    "Magic-angle twisted bilayer {topic} at 1.1 degrees twist shows {kw} Mott insulator behavior and unconventional superconductivity in adjacent doping regions — pairing mediated by spin fluctuations rather than phonons.",
                    "Graphene encapsulated in {topic} hexagonal boron nitride with {kw} crystallographic alignment shows ballistic electron transport at room temperature over 28 micrometers — exceeding silicon mobility by 100x.",
                    "MXene {topic} nanosheets with {kw} fluorine surface termination achieve electromagnetic shielding effectiveness of 92 dB at 1 GHz at 45 micrometers thickness — 10x thinner than copper at equivalent performance.",
                    "High-entropy alloy {topic} with {kw} five-component compositional disorder achieves yield strength of 2.1 GPa while retaining 15% elongation — breaking the classical alloy strength-ductility tradeoff.",
                    "Liquid metal {kw} embedded in {topic} elastomeric matrix creates a reconfigurable electrical circuit healing instantaneously from mechanical damage and reshaping under applied magnetic field.",
                    "Covalent organic framework with {kw} triangular pore geometry achieves record CO2 capture capacity of 8.2 mmol per gram at 15 kPa partial pressure — relevant to direct air capture from ambient atmosphere.",
                    "Biomineralization-inspired {topic} composite grows crystalline {kw} hydroxyapatite within a collagen template — achieving bone-like fracture resistance with full biological compatibility for load-bearing implants.",
                ],
                "findings": [
                    "Programmable matter prototype: {topic} unit cells with {kw} embedded shape-memory alloy actuators reconfigure from flat sheet to complex 3D structure on thermal command — scalable to millimeter-scale self-assembly.",
                    "Quantum dot {kw} luminescent solar concentrator for {topic} building-integrated photovoltaics achieves 6.8% power conversion on transparent architectural glass — compatible with standard manufacturing processes.",
                    "Aerogel composite of {topic} with {kw} aramid fiber reinforcement achieves thermal conductivity of 0.012 W per meter-kelvin at ambient pressure — matching vacuum insulation panel performance without any encapsulation.",
                ],
                "connections": [
                    "strongly correlated electron physics and Mott transitions",
                    "2D materials and van der Waals heterostructures",
                    "mechanical metamaterials and programmable matter",
                    "sustainable materials design and circular economy",
                ],
            },
            {
                "hypothesis": "Nanostructured {topic} catalytic surfaces with {kw} single-atom sites achieve nitrogen fixation at ambient conditions by mimicking the precise geometric and electronic structure of nitrogenase enzyme active sites in a purely inorganic scaffold.",
                "insights": [
                    "Single-atom {kw} catalysts on {topic} nitrogen-doped graphene support achieve turnover frequency of 10^5 per second for target reaction — 1000x higher than nanoparticle counterparts due to maximally exposed active sites.",
                    "Core-shell {topic} nanoparticle with {kw} compressive shell strain shifts d-band center by 0.4 eV — precisely tuning adsorbate binding energy for optimal placement on the Sabatier activity volcano.",
                    "Metal-organic framework {topic} with {kw} coordinatively unsaturated iron sites catalyzes CO2-to-methanol conversion at 98% selectivity and 140 bar pressure — beating traditional Cu/ZnO catalysts by 35% yield.",
                    "Electrocatalytic {kw} reduction to ammonia at {topic} Fe-based single-crystal electrode achieves Faradaic efficiency of 67% at -0.16 V versus RHE — approaching thermodynamic efficiency limits for this process.",
                    "Plasmon-enhanced {topic} photocatalysis with {kw} hot electron injection achieves 100x reaction rate enhancement under visible light — harvesting solar photons directly as chemical reaction driving force.",
                    "Biohybrid {kw} catalyst incorporating bacterial {topic} nitrogenase in a MOF scaffold operates at ambient temperature and 1 bar N2 with turnover comparable to industrial Haber-Bosch at 400 Celsius.",
                    "Entropy-stabilized high-entropy oxide with {kw} cation disorder achieves unprecedented stability under {topic} harsh reaction conditions while maintaining full catalytic activity — solving the sintering deactivation problem.",
                ],
                "findings": [
                    "Ambient nitrogen fixation demonstrated on {topic} single-crystal surface with {kw} Fe-Mo dual-atom catalyst — Faradaic efficiency of 71% at room temperature and 1 atmosphere N2 pressure achieved.",
                    "Self-assembled {kw} nanorod array in {topic} BiVO4 photoelectrode achieves solar water splitting at 18.3% solar-to-hydrogen efficiency — exceeding the 10% practical deployment threshold for the first time.",
                    "Mechanically interlocked {topic} molecular machine performs directional transport of {kw} cargo against a concentration gradient using ATP hydrolysis — a synthetic molecular pump operating at the 2 nanometer scale.",
                ],
                "connections": [
                    "heterogeneous catalysis and surface science fundamentals",
                    "electrocatalysis and renewable energy conversion",
                    "nanoscale confinement effects on chemical reactivity",
                    "bio-inspired molecular machines and synthetic nanomotors",
                ],
            },
        ]
