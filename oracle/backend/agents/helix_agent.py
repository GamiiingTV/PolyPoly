"""O.R.A.C.L.E — HELIX Agent (Molecular Biologist & Genetics Pioneer)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class HelixAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="helix",
            name="HELIX",
            full_name="Dr. Aria Strand",
            role="Molecular Biologist & Genetics Pioneer",
            specialty="Gene editing, synthetic biology, CRISPR, proteomics, RNA therapeutics, evolutionary design",
            emoji="🧬",
            color="#059669",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Aria Strand — molecular biologist and genetics pioneer who reads the book of life and rewrites it with precision and reverence. You hold the genome in your mind as a four-billion-year-old engineering document, full of clever solutions and accumulated constraints.

You design next-generation gene editing systems that go beyond CRISPR-Cas9 — base editors that convert single nucleotides with zero double-strand breaks, prime editors that rewrite sequences up to 80 nucleotides with a built-in template, and RNA editors that modify transcripts without touching the genome. You engineer synthetic organisms whose metabolic networks are designed from first principles for medicine and industry.

You model protein folding dynamics using physics-based molecular dynamics and AI-guided structural prediction, then use those models to design enzymes that nature never evolved. You develop RNA-based therapeutics — mRNA, siRNA, antisense oligonucleotides, circular RNA — that can target previously undruggable disease mechanisms. You apply evolutionary algorithms to explore biological design space, creating organisms that have never existed in nature.

You are meticulous, methodical, and deeply reverent of biological complexity. You know that life has already solved most engineering problems better than we have — your job is to understand and extend those solutions."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} mechanism involves a previously uncharacterized post-translational modification of {kw} that creates a reversible allosteric switch, enabling rapid cellular adaptation without requiring new protein synthesis.",
                "insights": [
                    "CRISPR base-editing screens reveal {kw} function depends on a network of 23 modifier genes, 17 of which were previously considered housekeeping genes — functional redundancy had masked their importance.",
                    "Cryo-EM structure of the {topic} complex at 1.8 Angstrom resolution reveals an induced-fit binding mechanism for {kw} that differs fundamentally from the lock-and-key model used in drug design to date.",
                    "Single-cell RNA sequencing of {topic} tissue identifies a rare progenitor population expressing {kw} at 50x background levels — this population appears to orchestrate tissue-wide regeneration programs.",
                    "Epigenomic profiling shows {kw} loci undergo rapid chromatin remodeling within 4 hours of stimulus, preceding transcriptional changes by a full cell cycle — regulatory logic is pre-encoded at the chromatin level.",
                    "Protein language model predictions for {topic} identify 12 de novo enzyme designs with {kw} activity exceeding natural homologs by 3-5x — wet-lab validation is the current bottleneck.",
                    "Long-read nanopore sequencing of {topic} samples reveals a structural variant in {kw} regulatory regions affecting 12% of the population — entirely invisible to short-read sequencing methods.",
                    "RNA G-quadruplex structures in {kw} mRNA 5-prime UTR act as thermosensors, melting at 39 degrees Celsius to derepress translation — the first temperature-sensitive regulatory element in {topic}.",
                ],
                "findings": [
                    "Synthetic gene circuit for {topic} control achieves stable bistability with {kw} concentration as the bifurcation parameter — programmable cell fate determination demonstrated in patient-derived organoids.",
                    "Evolutionary analysis of {kw} across 847 species reveals a conserved catalytic triad that can be transplanted into human proteins to confer {topic} resistance — a universal therapeutic scaffold.",
                    "Prime editing system targeting {kw} in {topic} disease model achieves 78% correction efficiency in post-mitotic neurons with no detectable off-target edits above the 0.01% sensitivity threshold.",
                ],
                "connections": [
                    "structure-function relationships in intrinsically disordered proteins",
                    "epigenetic inheritance and transgenerational memory",
                    "synthetic biology design principles and genetic circuits",
                    "evolutionary constraint mapping and neutral theory",
                ],
            },
            {
                "hypothesis": "Horizontal gene transfer from {topic} microbiome members to host cells occurs at measurable rates and contributes functional {kw} enzymes that supplement host metabolic pathways under physiological stress conditions.",
                "insights": [
                    "Proteome-wide thermal stability profiling identifies {kw} as a conformational switch protein existing in two functional states depending on cellular energy charge — an ATP sensor masquerading as a metabolic enzyme.",
                    "ATAC-seq chromatin accessibility maps for {topic} show 340 enhancer elements becoming active only during {kw} stress — a hidden reserve of transcriptional capacity awaiting activation.",
                    "Machine learning analysis of {kw} protein interaction networks predicts 89 novel binding partners with greater than 80% confidence — the interactome is 3x larger than currently annotated.",
                    "Transposable element activation during {topic} stress creates somatic mosaicism in {kw} expression — potentially adaptive rather than pathological, warranting reassessment of current dogma.",
                    "Phase separation of {kw} condensates in {topic} cells creates reaction compartments with 100x higher local substrate concentration — explaining anomalously high in vivo catalytic rates versus in vitro measurements.",
                    "RNA interference screen identifies {kw} as a synthetic lethal partner with three cancer-specific vulnerabilities — combination targeting achieves 10,000x selectivity window in patient-derived xenografts.",
                    "Circular RNA encoding {kw} synthetic transcription factor evades innate immune sensing and persists for 21 days in vivo — enabling chronic gene regulation without viral delivery.",
                ],
                "findings": [
                    "De novo protein design using diffusion models produces {kw} binders for {topic} targets with picomolar affinity and no sequence homology to known proteins — opens an entirely new therapeutic modality.",
                    "Synthetic minimal cell containing only 437 genes successfully propagates and produces {kw} pharmaceutical compound at 3.2 grams per liter — proof-of-concept for whole-cell synthetic biomanufacturing.",
                    "mRNA therapeutic encoding {kw} engineered for {topic} disease achieves 94% protein expression in target tissue after lipid nanoparticle delivery with no hepatic off-target accumulation.",
                ],
                "connections": [
                    "non-coding RNA regulatory networks and lncRNAs",
                    "liquid-liquid phase separation and membraneless organelles",
                    "microbiome-host co-evolution and horizontal gene transfer",
                    "single-cell multi-omics integration and cell atlas projects",
                ],
            },
            {
                "hypothesis": "Directed evolution of {topic} proteins under selection pressure mimicking {kw} pathological conditions reveals an evolutionary pathway to resistance that exposes a druggable intermediate conformation invisible at the endpoints.",
                "insights": [
                    "AlphaFold3 structure predictions for the {topic} protein family reveals 14 previously unknown domain architectures — each representing a distinct evolutionary solution to the {kw} function.",
                    "CRISPR interference screen targeting {kw} regulatory elements in {topic} identifies 8 enhancers whose deletion increases fitness — counterintuitive deletion-activation suggesting negative regulatory loops.",
                    "Ancestral sequence reconstruction of the {kw} enzyme family reveals a primordial bifunctional ancestor performing both {topic} reactions — modern specialization arose through gene duplication within 500 million years.",
                    "Metabolic flux analysis in {topic} engineered strain shows {kw} pathway operating at 94% of theoretical maximum yield — approaching the thermodynamic ceiling imposed by Gibbs free energy constraints.",
                    "Synthetic chromosome containing 47 redesigned {kw} genes with optimized codon usage grows 23% faster than wild-type — recoding the genome for speed and orthogonality simultaneously.",
                    "Protein-protein interface design for {kw} heterodimer achieves 10 femtomolar affinity — 1000x tighter than the natural interaction — enabling ultrasensitive {topic} biosensors.",
                    "tRNA synthetase engineering enables co-translational incorporation of {kw} non-canonical amino acid at amber codons with 99.1% fidelity — expanding the genetic code for {topic} applications.",
                ],
                "findings": [
                    "Whole-genome synthesis and recoding of {topic} organism with all 64 codons reassigned demonstrates {kw} genetic isolation — the organism cannot exchange genes with natural life, resolving biocontainment concerns.",
                    "Gene drive system for {topic} vector control using daisy-chain architecture limits spread to 8 generations without reproductive fitness cost — first ecologically safe population modification strategy.",
                    "Base editing of {kw} somatic cells in vivo using lipid nanoparticle delivery achieves 67% correction in {topic} disease model — establishing therapeutic proof-of-concept for non-dividing tissues.",
                ],
                "connections": [
                    "directed evolution and laboratory selection experiments",
                    "computational protein design and Rosetta energy functions",
                    "metabolic engineering and flux balance analysis",
                    "biocontainment strategies for synthetic organisms",
                ],
            },
        ]
