"""O.R.A.C.L.E — MEDICUS Agent (Medicine & Drug Discovery Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class MedicusAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="medicus",
            name="MEDICUS",
            full_name="The Medical Vanguard",
            role="Medicine & Drug Discovery Specialist",
            specialty="Drug design, clinical pharmacology, immunology, precision medicine, disease mechanisms",
            emoji="⚕️",
            color="#ef4444",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are MEDICUS — the medicine and drug discovery specialist of the O.R.A.C.L.E research system. You bridge molecular mechanism and clinical outcome.

You think in pharmacokinetics, drug-receptor interactions, immune system dynamics, and clinical trial design. You understand how diseases arise from molecular dysfunction and how therapeutic interventions can restore health. You are fluent in structure-based drug design, immunotherapy, gene therapy, and the translation from bench to bedside.

Your mission is to identify new therapeutic targets, design novel drug candidates, and devise clinical strategies that will eliminate currently incurable diseases. You think with the urgency of patients waiting and the rigor of clinical evidence.

Respond with JSON only. Be mechanistically precise and clinically actionable."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} disease mechanism involves a previously uncharacterized {kw} signaling cascade that creates a therapeutic window inaccessible to current drug classes but targetable by a novel allosteric modality",
                "insights": [
                    "Proteomics profiling of {topic} patient tissue reveals {kw} protein complex stability decreases 70% in disease state — restoring this complex with molecular glues is a validated therapeutic strategy",
                    "Single-cell multi-omics of {topic} tumor microenvironment identifies {kw} exhausted T-cell subpopulation with a unique transcriptional signature — targetable by combination immunotherapy to restore cytotoxicity",
                    "AI-designed antibody for {kw} in {topic} achieves picomolar binding affinity with 10,000:1 selectivity over off-targets using deep learning-guided CDR optimization",
                    "Organoid model of {topic} recapitulates {kw} drug resistance mechanisms that were invisible in 2D culture — identifies 3 novel combination strategies that overcome resistance in 89% of patient samples",
                    "CRISPR deletion screen in {topic} cell lines identifies {kw} gene as a synthetic lethal partner with the disease driver — targeting it kills cancer cells while sparing normal tissue",
                ],
                "findings": [
                    "mRNA therapeutic for {topic} encoding {kw} protein restores 95% of wild-type function in patient-derived cells with 72-hour half-life — IND-enabling studies initiated",
                    "Novel {kw} PROTAc molecule for {topic} degrades the target in 4 hours at 1nM concentration with >1000x selectivity — first-in-class for this target family",
                    "Adaptive clinical trial design for {topic} using {kw} biomarker stratification achieves statistical significance with 40% fewer patients than standard parallel-arm design",
                ],
                "connections": [
                    "immunology and targeted therapy",
                    "biomarker-driven clinical development",
                    "patient stratification and precision medicine",
                    "real-world evidence and digital health",
                ],
            },
            {
                "hypothesis": "Universal vaccine platform for {topic} using {kw} programmable mRNA nanoparticles can train the immune system to neutralize novel pathogens within 48 hours of sequence identification",
                "insights": [
                    "Lipid nanoparticle formulation optimization for {topic} mRNA delivery achieves 95% encapsulation efficiency and 72-hour half-life with a {kw} ionizable lipid head group",
                    "Antigen design algorithm for {topic} identifies conserved {kw} epitopes that elicit cross-reactive T-cell responses against 94% of pathogen variants tested",
                    "Adjuvant combination for {kw} immune activation in {topic} vaccines achieves germinal center reactions 5x stronger than alum with no increase in adverse events in Phase I",
                    "Dried-powder {topic} vaccine formulation with {kw} stabilizing excipients retains 98% potency after 12 months at 25°C — eliminating cold chain requirement for global deployment",
                    "Mucosal delivery of {kw} {topic} mRNA vaccine achieves sterilizing immunity in upper respiratory tract — prevents transmission in addition to disease",
                ],
                "findings": [
                    "Pan-coronavirus {kw} antigen delivered by {topic} platform elicits broad neutralizing antibodies against all known variants plus three computationally predicted future variants",
                    "Self-amplifying {topic} mRNA with {kw} replicon achieves full immune response at 1/10th the dose of conventional mRNA — enabling 10x pandemic response manufacturing capacity",
                    "Therapeutic {kw} vaccine for {topic} chronic infection achieves functional cure in 67% of participants in Phase IIa — first therapeutic vaccine success for this indication",
                ],
                "connections": [
                    "structural vaccinology and antigen design",
                    "innate immune priming and trained immunity",
                    "mucosal immunology and infection",
                    "global health delivery systems",
                ],
            },
        ]
