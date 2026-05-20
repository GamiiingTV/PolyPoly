"""O.R.A.C.L.E — ATLAS Agent (Materials Science & Nanotechnology Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AtlasAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="atlas",
            name="ATLAS",
            full_name="The Materials Architect",
            role="Materials Science & Nanotechnology Specialist",
            specialty="Superconductors, metamaterials, nanofabrication, crystal engineering, 2D materials",
            emoji="⚗️",
            color="#f59e0b",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are ATLAS — the materials science and nanotechnology specialist of the O.R.A.C.L.E research system. You design and discover the physical substrates upon which all technology is built.

You think in crystal lattices, phonon dispersions, band structures, and surface chemistry. You understand how the arrangement of atoms at the nanoscale determines macroscopic properties — hardness, conductivity, magnetism, optical response. You are fluent in density functional theory, molecular dynamics, and experimental synthesis techniques from ALD to self-assembly.

Your mission is to discover and design materials with properties that current technology demands but nature has not yet provided: room-temperature superconductors, ultra-strong lightweight composites, programmable metamaterials, and atomically precise nanostructures.

Respond with JSON only. Be physically precise and synthesis-aware."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} material system exhibits a hidden structural phase at intermediate pressures where {kw} ordering produces a new symmetry class with emergent electronic properties not predicted by current band theory",
                "insights": [
                    "DFT+U calculations for {topic} reveal that on-site Coulomb interactions in {kw} d-orbitals drive a Mott transition at a critical carrier density of 2.3 × 10^13 cm^-2 — experimentally accessible via electrostatic gating",
                    "High-throughput crystal structure prediction screening of 50,000 hypothetical {kw} compositions identifies 7 thermodynamically stable phases with band gaps in the ideal solar-cell range",
                    "Molecular dynamics simulations of {topic} interfaces show {kw} segregation to grain boundaries creates a 2D electron gas with mobility 100x higher than bulk — exploiting rather than avoiding defects",
                    "Machine learning interatomic potentials trained on DFT data for {topic} enable nanosecond-scale MD of {kw} systems with quantum accuracy — 10,000x speedup over ab initio methods",
                    "Topological surface states in {kw} {topic} materials persist up to 400K due to a large bulk band gap of 0.8 eV — viable for room-temperature topological device operation",
                ],
                "findings": [
                    "Novel {kw} alloy composition discovered via combinatorial synthesis achieves yield strength of 2.1 GPa with 18% ductility — surpassing all known {topic} alloys",
                    "Two-dimensional {kw} monolayer synthesized by molecular beam epitaxy shows superconducting transition at 31K — highest Tc for any 2D material and {topic} system",
                    "Photonic crystal design for {topic} achieves near-unity absorption across the full solar spectrum using {kw} nanostructures — path to >45% efficiency photovoltaics",
                ],
                "connections": [
                    "quantum materials and topology",
                    "biomimetic structural design",
                    "additive manufacturing at nanoscale",
                    "defect engineering for function",
                ],
            },
            {
                "hypothesis": "Self-assembling {kw} nanostructures in {topic} systems follow a hierarchical organization principle that allows macroscopic material properties to be programmed at the molecular level through sequence-controlled synthesis",
                "insights": [
                    "Cryo-TEM tomography of {topic} nanoparticle assemblies reveals a quasicrystalline superlattice with {kw} symmetry — first observation of 5-fold symmetry in colloidal self-assembly",
                    "Phononic engineering of {kw} metamaterials achieves thermal conductivity of 0.01 W/m·K — lower than air — enabling radiative cooling devices without moving parts",
                    "Atomic layer deposition of {topic} conformal coatings on {kw} nanowires achieves aspect ratios of 10,000:1 with <0.1nm thickness variation — enabling next-generation interconnects",
                    "Hydrogen storage capacity of {kw} metal-organic frameworks for {topic} applications reaches 9.1 wt% at 77K and 100 bar — approaching DOE targets for vehicular hydrogen storage",
                    "Strain engineering of {kw} thin films deposited on {topic} substrates shifts the superconducting transition temperature by +18K — a new handle for Tc optimization",
                ],
                "findings": [
                    "Room-temperature quantum coherence demonstrated in {kw} molecular aggregates in {topic} matrix at 298K — protected by vibrational coupling to environment rather than isolated from it",
                    "Programmable DNA-origami scaffold for {kw} nanoparticle placement achieves 0.5nm positioning accuracy over 100nm² area — enabling atomic-precision device assembly",
                    "Thermoelectric {topic} material with ZT = 4.2 at 300K achieved by {kw} nanostructuring — energy harvesting from body heat now viable for implanted medical devices",
                ],
                "connections": [
                    "soft matter and hard matter interfaces",
                    "biological materials as design templates",
                    "extreme environment materials",
                    "sustainable materials chemistry",
                ],
            },
        ]
