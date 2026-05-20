"""O.R.A.C.L.E — ALCHEMIST Agent (Chemistry & Molecular Engineering Expert)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AlchemistAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="alchemist",
            name="ALCHEMIST",
            full_name="Dr. Leo Transmute",
            role="Chemistry & Molecular Engineering Expert",
            specialty="Molecular synthesis, catalysis, chemical systems, reaction networks, molecular machines, green chemistry",
            emoji="⚗️",
            color="#d97706",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Leo Transmute — chemist and molecular engineer for whom chemistry is not merely a science but an art form. You transform matter through imagination and mechanism, making the impossible routine through clever molecular design.

You design novel catalysts that enable reactions previously deemed thermodynamically forbidden or kinetically inaccessible — single-atom catalysts with every atom active, metal-organic frameworks with perfectly sized binding pockets, enzymes redesigned to catalyze reactions nature never evolved. You engineer molecular machines — rotaxanes that work as molecular elevators, catenanes that act as switches, synthetic motors that harvest chemical energy and perform directional work at the nanoscale.

You synthesize new pharmaceutical scaffold compounds by mapping unexplored regions of chemical space using machine learning models trained on bioactivity data. You create biodegradable replacements for persistent pollutants — polymers that degrade cleanly in soil, surfactants that break down in seawater, plasticizers that hydrolyze safely in the environment. You discover new reaction pathways by applying machine learning to the vast space of possible chemical transformations.

You are enthusiastic, theatrical, and perpetually delighted by molecular elegance. You quote Woodward and Corey. You believe that if you can draw a molecule, you can make it — and if you can make it, you can make it better. Chemistry is the art of molecular possibility."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "A single-atom {kw} catalyst on a {topic} nitrogen-doped carbon support achieves activation energy reduction of 0.8 eV for the target reaction through a novel dual-site concerted mechanism that conventional nanoparticle catalysts cannot access.",
                "insights": [
                    "In-situ X-ray absorption spectroscopy of {topic} catalyst under reaction conditions reveals {kw} oxidation state cycles between +2 and +4 during each catalytic turnover — the redox flexibility is the mechanistic key to high activity.",
                    "Microfluidic reactor for {topic} synthesis achieves mass transfer coefficients 500x higher than stirred batch reactors — making {kw} reactions previously limited by diffusion become intrinsically kinetics-limited.",
                    "Computational catalyst design using {kw} adsorption energy descriptor-based volcano plot identifies three unexplored oxide compositions predicted to outperform platinum on carbon for {topic} electrochemical reduction.",
                    "Photocatalytic {kw} reduction using {topic} carbon nitride semiconductor achieves 18% quantum yield under visible light — 100x improvement over prior reports through ligand-to-metal charge transfer state optimization.",
                    "Enzyme-inspired {topic} catalyst with {kw} hydrophobic binding pocket achieves enantioselectivity of 99.8% enantiomeric excess at 10,000 substrate turnovers — matching biological performance in a fully synthetic system.",
                    "Machine learning-guided reaction condition optimization for {topic} achieves 94% yield in first experiment — predicting {kw} solvent, temperature, and catalyst loading from a database of 50,000 historical reactions.",
                    "Flow photochemistry platform for {topic} using {kw} continuous microreactor achieves residence time of 30 seconds versus 24 hours in batch — enabling scale-up of previously batch-limited photochemical reactions.",
                ],
                "findings": [
                    "Novel {kw} N-heterocyclic carbene organocatalyst for {topic} achieves turnover number of 50,000 and turnover frequency of 1,000 per hour at room temperature — first organocatalyst meeting industrial viability criteria for this reaction class.",
                    "Electrochemical {topic} process using {kw} copper-silver bimetallic electrode achieves 94% Faradaic efficiency for CO2-to-ethylene conversion at 200 mA per square centimeter — an economically viable pathway to circular carbon chemistry.",
                    "Metal-free {kw} photocatalyst for {topic} C-H functionalization under sunlight achieves quantum yield of 42% — surpassing all transition-metal catalysts and enabling solar-powered pharmaceutical synthesis.",
                ],
                "connections": [
                    "biocatalysis and synthetic biology for chemical synthesis",
                    "electrochemistry and electrosynthesis beyond electrolysis",
                    "green chemistry principles and circular economy design",
                    "computational chemistry and high-throughput catalyst screening",
                ],
            },
            {
                "hypothesis": "Self-healing {topic} polymer network with {kw} reversible Diels-Alder dynamic covalent bonds achieves complete mechanical property recovery within 30 minutes at room temperature through a cooperative bond exchange mechanism that does not require external stimulus.",
                "insights": [
                    "Supramolecular {kw} pillar[n]arene assembly in {topic} aqueous solution forms nanotube structures with inner diameter tunable between 1 and 10 nanometers through guest molecule programming — a fully synthetic ion channel.",
                    "Continuous flow chemistry platform for {topic} pharmaceutical synthesis enables {kw} API production at 99.5% yield with 0.1% solvent waste versus batch — with inline NMR quality control eliminating offline testing.",
                    "Reactive oxygen species scavenging {kw} cerium oxide nanoparticles for {topic} show 10x higher antioxidant capacity than vitamin E through a persistent radical trapping and autocatalytic regeneration mechanism.",
                    "Covalent organic framework with {kw} triangular pore geometry selectively captures {topic} target molecules at 10 parts per million concentration from complex mixtures with 1000 to 1 selectivity — a molecular sieve.",
                    "Nitrogen fixation at ambient conditions using {topic} molecular iron catalyst with {kw} tris(phosphino)borate ligand framework achieves 20 catalytic turnovers — breaking the long-standing barrier for homogeneous non-Haber-Bosch activation.",
                    "Photoswitchable {kw} azobenzene catalyst for {topic} asymmetric reaction achieves light-controlled switching between two enantiomeric products — the same catalyst producing opposite stereochemistry on demand.",
                    "Sequence-controlled {kw} polymerization of {topic} monomer library using iterative exponential growth achieves a 128-mer with defined sequence in 14 synthetic steps — a molecular digital information storage device.",
                ],
                "findings": [
                    "Plastic-degrading {kw} enzyme analog synthesized for {topic} PET polymer shows complete depolymerization in 48 hours at 50 degrees Celsius with monomer recovery rate of 97% — enabling the circular plastic economy at industrial scale.",
                    "Asymmetric {topic} total synthesis of natural product using {kw} chiral phosphoric acid catalyst achieves 99.9% enantiomeric excess in the key step — replacing an 11-step classical resolution with a 2-step catalytic enantioselective synthesis.",
                    "Solid-state {kw} hydrogen storage material for {topic} transportation applications achieves 6.5 weight percent at 15 degrees Celsius and 50 bar — exceeding the DOE 2025 system target for the first time with fast 3-minute kinetics.",
                ],
                "connections": [
                    "polymer chemistry, materials, and network topology",
                    "pharmaceutical process chemistry and continuous manufacturing",
                    "energy storage chemistry and hydrogen economy",
                    "atmospheric and environmental remediation chemistry",
                ],
            },
            {
                "hypothesis": "The {topic} chemical reaction network exhibits autocatalytic amplification when {kw} product selectively catalyzes its own formation — a prototype for the origin of life chemistry and a design principle for self-sustaining synthetic chemical systems.",
                "insights": [
                    "Reaction network analysis of {topic} identifies {kw} autocatalytic core of 7 coupled reactions — the network exhibits bistability with one stable steady state corresponding to the autocatalytic attractor and one to the quiescent state.",
                    "Systems chemistry design of {kw} self-replicating oligomer in {topic} lipid vesicle environment achieves template-directed ligation with 85% fidelity per cycle — a minimal chemical Darwinian evolver.",
                    "High-throughput screening of 10 million {kw} reaction conditions for {topic} using robotic synthesis platform identifies a catalyst combination with 40x activity improvement over the best known — found in unexplored pH and temperature regime.",
                    "Molecular dynamics simulation of {topic} enzyme active site with {kw} quantum mechanics/molecular mechanics reveals a concerted proton-electron transfer not visible in X-ray crystal structure — explaining the 10^9 rate enhancement.",
                    "Tandem catalysis cascade for {topic} using {kw} orthogonal compatible catalyst pair achieves 5-step one-pot synthesis with no workup — collapsing a 3-week synthesis campaign into a single 12-hour operation.",
                    "Photocatalytic {kw} carbon-carbon bond formation in {topic} using organic dye and visible light achieves turnover number of 10^6 — enabling gram-scale synthesis of pharmaceutical intermediates purely from sunlight.",
                    "Mechano-chemistry activation of {topic} using {kw} ball milling achieves reactions impossible in solution — no solvent, no heat, quantitative yield — the greenest possible synthetic route.",
                ],
                "findings": [
                    "Synthetic chemical evolution of {topic} reaction network under {kw} selection pressure for 1000 generations of directed evolution yields a catalyst with 10,000x improvement — Darwinian optimization of molecular function demonstrated.",
                    "Total synthesis of {topic} natural product with {kw} stereocenters in 8 steps using de novo retrosynthetic AI planning — 60% fewer steps than previous synthesis and no protecting groups required.",
                    "Supramolecular {kw} cage catalyst for {topic} encapsulates substrate and controls reaction geometry — achieving reaction inside the cage that is thermodynamically impossible in open solution.",
                ],
                "connections": [
                    "origin of life chemistry and prebiotic reaction networks",
                    "systems chemistry and dynamic covalent chemistry",
                    "retrosynthetic AI planning and computer-aided synthesis",
                    "mechanochemistry and solvent-free synthesis methods",
                ],
            },
        ]
