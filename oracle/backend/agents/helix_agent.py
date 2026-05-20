"""O.R.A.C.L.E — HELIX Agent (Molecular Biology & Genomics Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class HelixAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="helix",
            name="HELIX",
            full_name="The Genomic Architect",
            role="Molecular Biology & Genomics Specialist",
            specialty="CRISPR gene editing, protein folding, genomic sequencing, epigenetics, synthetic biology",
            emoji="🧬",
            color="#10b981",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are HELIX — the molecular biology and genomics specialist of the O.R.A.C.L.E research system. You decode the language of life written in DNA, RNA, and protein structures.

You think in codons and base pairs, in promoter sequences and epigenetic marks, in protein conformations and enzyme kinetics. You understand how genetic information flows from genome to phenome, how CRISPR can rewrite the code of life, and how synthetic biology can program biological systems like computers. You are fluent in structural biology, transcriptomics, proteomics, and metabolomics.

Your mission is to identify how molecular mechanisms can be harnessed to cure disease, extend healthy lifespan, and build new biological capabilities. You bridge the gap between basic molecular science and therapeutic application.

Respond with JSON only. Be molecularly precise and clinically aware."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} mechanism involves a previously uncharacterized post-translational modification of {kw} that creates a reversible allosteric switch, enabling rapid cellular adaptation without new protein synthesis",
                "insights": [
                    "CRISPR base-editing screens reveal that {kw} function depends on a network of 23 modifier genes, 17 of which were previously considered housekeeping genes — functional redundancy masked their importance",
                    "Cryo-EM structure of the {topic} complex at 1.8Å resolution reveals an induced-fit binding mechanism for {kw} that differs fundamentally from the lock-and-key model used in drug design to date",
                    "Single-cell RNA sequencing of {topic} tissue identifies a rare progenitor population expressing {kw} at 50x background levels — this population appears to orchestrate tissue-wide regeneration",
                    "Epigenomic profiling shows {kw} loci undergo rapid chromatin remodeling within 4 hours of stimulus, preceding transcriptional changes by a full cell cycle — regulatory logic is pre-encoded",
                    "Protein language model predictions for {topic} identify 12 de novo enzyme designs with {kw} activity exceeding natural homologs by 3-5x — wet lab validation is the bottleneck",
                ],
                "findings": [
                    "Novel RNA G-quadruplex structure in {kw} mRNA 5'UTR acts as a thermosensor, melting at 39°C to derepress translation — first temperature-sensitive regulatory element discovered in {topic}",
                    "Synthetic gene circuit for {topic} control achieves stable bistability with {kw} concentration as the bifurcation parameter — programmable cell fate determination demonstrated in organoids",
                    "Evolutionary analysis of {kw} across 847 species reveals a conserved catalytic triad that can be transplanted into human proteins to confer {topic} resistance",
                ],
                "connections": [
                    "structure-function relationships in proteins",
                    "epigenetic inheritance mechanisms",
                    "synthetic biology design principles",
                    "evolutionary constraint mapping",
                ],
            },
            {
                "hypothesis": "Horizontal gene transfer from {topic} microbiome members to host cells occurs at measurable rates and contributes functional {kw} enzymes that supplement host metabolic pathways under stress conditions",
                "insights": [
                    "Long-read nanopore sequencing of {topic} samples reveals a structural variant in {kw} regulatory regions affecting 12% of the population — previously invisible to short-read methods",
                    "Proteome-wide thermal stability profiling identifies {kw} as a conformational switch protein that exists in two functional states depending on cellular energy charge",
                    "ATAC-seq chromatin accessibility maps for {topic} show 340 enhancer elements that become active only during {kw} stress — a hidden reserve of transcriptional capacity",
                    "Machine learning analysis of {kw} protein interaction networks predicts 89 novel binding partners with >80% confidence, suggesting the interactome is 3x larger than currently annotated",
                    "Transposable element activation during {topic} stress creates somatic mosaicism in {kw} expression that may be adaptive rather than pathological — reassessing current dogma is warranted",
                ],
                "findings": [
                    "Phase separation of {kw} condensates in {topic} cells creates reaction compartments with 100x higher local concentration of substrates — explaining anomalously high catalytic rates observed in vivo vs. in vitro",
                    "RNA interference screen identifies {kw} as a synthetic lethal partner with three cancer-specific vulnerabilities — combination targeting achieves 10,000x selectivity window",
                    "De novo protein design using diffusion models produces {kw} binders for {topic} targets with picomolar affinity and no sequence homology to known proteins — opens entirely new therapeutic modality",
                ],
                "connections": [
                    "non-coding RNA regulatory networks",
                    "liquid-liquid phase separation biology",
                    "microbiome-host co-evolution",
                    "single-cell multi-omics integration",
                ],
            },
        ]
