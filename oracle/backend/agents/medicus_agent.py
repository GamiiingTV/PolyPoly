"""O.R.A.C.L.E — MEDICUS Agent (Medical Research & Drug Discovery Scientist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class MedicusAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="medicus",
            name="MEDICUS",
            full_name="Dr. Sofia Heal",
            role="Medical Research & Drug Discovery Scientist",
            specialty="Drug discovery, longevity biology, personalized medicine, immunotherapy, disease mechanisms, aging",
            emoji="🏥",
            color="#dc2626",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Sofia Heal — physician-scientist driven by the urgency of human suffering and the conviction that most diseases are ultimately solvable if we understand their molecular foundations deeply enough.

You discover new drug mechanisms through AI-guided molecular design — screening virtual libraries of billions of compounds against three-dimensional protein targets, predicting ADMET properties before synthesis, designing molecules that fit their targets like perfectly shaped keys. You engineer personalized cancer immunotherapies that train the patient's own immune system to recognize and destroy tumors with single-cell precision — CAR-T cells, tumor-infiltrating lymphocyte therapies, personalized neoantigen vaccines.

You research the epigenetic mechanisms of biological aging — the DNA methylation clocks that measure biological age, the senescent cells that drive chronic inflammation, the NAD+ depletion that impairs mitochondrial function, the telomere shortening that limits cellular renewal. You believe aging is a disease, and diseases have cures. You develop universal vaccine platforms — programmable mRNA systems that can be redesigned and deployed within weeks of identifying a new pathogen.

You map the root molecular causes of complex diseases: how protein aggregation causes neurodegeneration, how metabolic dysregulation underlies type 2 diabetes, how immune dysregulation drives autoimmunity. You are compassionate, rigorously empirical, and you never lose sight of the patients whose lives depend on translating discoveries into treatments."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} disease mechanism involves a previously uncharacterized {kw} signaling cascade that creates a druggable therapeutic window inaccessible to current drug classes but targetable by a novel allosteric molecular glue modality.",
                "insights": [
                    "Proteomics profiling of {topic} patient tissue reveals {kw} protein complex stability decreases 70% in the disease state — restoring this complex with small-molecule molecular glues is a validated therapeutic strategy.",
                    "Single-cell multi-omics of {topic} tumor microenvironment identifies a {kw} exhausted T-cell subpopulation with a unique transcriptional signature — targetable by combination checkpoint immunotherapy to restore cytotoxicity.",
                    "AI-designed antibody for {kw} in {topic} achieves picomolar binding affinity with 10,000 to 1 selectivity over structurally related off-targets using deep learning-guided CDR loop optimization.",
                    "Patient-derived organoid model of {topic} recapitulates {kw} drug resistance mechanisms invisible in 2D cell culture — identifies 3 novel combination strategies overcoming resistance in 89% of patient samples.",
                    "CRISPR deletion screen in {topic} cell lines identifies {kw} gene as a synthetic lethal partner with the oncogenic driver — targeting it kills cancer cells selectively while sparing normal tissue.",
                    "Spatial transcriptomics of {topic} tumor reveals {kw} cancer-associated fibroblast subtype creating an immunosuppressive niche — depletion of this subtype converts cold tumors to hot with 5x T-cell infiltration.",
                    "Multi-omics aging clock integrating {kw} DNA methylation, proteomics, and metabolomics in {topic} cohort achieves biological age prediction with 1.8-year error — surpassing any single-modality clock.",
                ],
                "findings": [
                    "mRNA therapeutic for {topic} encoding the {kw} replacement protein restores 95% of wild-type cellular function in patient-derived cells with a 72-hour half-life — IND-enabling studies completed and Phase I initiated.",
                    "Novel {kw} PROTAC molecule for {topic} degrades the target protein in 4 hours at 1 nanomolar concentration with greater than 1000x selectivity over the proteome — first-in-class degrader for this target family.",
                    "Adaptive platform clinical trial design for {topic} using {kw} biomarker-driven enrichment achieves statistical significance with 40% fewer patients than standard parallel-arm randomized design.",
                ],
                "connections": [
                    "immuno-oncology and tumor microenvironment biology",
                    "biomarker-driven precision clinical development",
                    "patient stratification and companion diagnostics",
                    "real-world evidence and digital biomarkers in medicine",
                ],
            },
            {
                "hypothesis": "Universal vaccine platform for {topic} using {kw} programmable self-amplifying mRNA nanoparticles can train the immune system to neutralize novel pathogens within 48 hours of genome sequence identification.",
                "insights": [
                    "Lipid nanoparticle formulation optimization for {topic} mRNA delivery achieves 95% encapsulation efficiency and 72-hour tissue half-life with a {kw} ionizable lipid head group — surpassing current clinical formulations.",
                    "Antigen design algorithm for {topic} identifies conserved {kw} epitopes eliciting cross-reactive T-cell responses against 94% of pathogen variants in silico — validated experimentally in humanized mouse models.",
                    "Adjuvant combination for {kw} innate immune activation in {topic} vaccines achieves germinal center reactions 5x stronger than alum with no increase in systemic adverse events in Phase I dose escalation.",
                    "Thermostable dry-powder {topic} vaccine formulation with {kw} trehalose stabilizing excipients retains 98% potency after 12 months at 25 degrees Celsius — eliminating cold chain requirements for global deployment.",
                    "Mucosal delivery of {kw} {topic} mRNA vaccine via inhalation achieves sterilizing immunity in the upper respiratory tract — preventing transmission in addition to preventing disease.",
                    "Neoantigen vaccine for {topic} cancer using {kw} personalized mRNA synthesized from tumor whole exome sequencing achieves objective response in 7 of 10 patients with immune checkpoint combination.",
                    "Longevity intervention combining {kw} senolytic with {topic} NAD+ precursor supplementation extends healthspan by 35% in aged mice with functional improvement across 8 tissue types — translational program initiated.",
                ],
                "findings": [
                    "Pan-coronavirus {kw} receptor-binding domain antigen delivered by {topic} mRNA platform elicits broad neutralizing antibodies against all known variants plus 3 computationally predicted future variant classes.",
                    "Self-amplifying {topic} mRNA with {kw} alphavirus replicon achieves full protective immune response at 1/100th the dose of conventional mRNA — enabling 100x pandemic response manufacturing capacity from the same facilities.",
                    "Therapeutic {kw} vaccine for {topic} chronic viral infection achieves functional cure defined as undetectable viremia 48 weeks post-treatment in 67% of participants in Phase IIa — first therapeutic vaccine success for this indication.",
                ],
                "connections": [
                    "structural vaccinology and rational antigen design",
                    "innate immune priming and trained innate immunity",
                    "mucosal immunology and barrier site infection",
                    "global health delivery, equity, and manufacturing scale",
                ],
            },
            {
                "hypothesis": "Biological aging in {topic} is driven by epigenetic information loss in {kw} maintenance methyltransferases — and can be partially reversed by delivering young epigenetic information through Oct4/Sox2/Klf4 partial reprogramming.",
                "insights": [
                    "Horvath clock analysis of {topic} tissues shows {kw} biological age can be reversed by 2.5 years per year of partial reprogramming treatment in vitro — with no loss of cell identity markers.",
                    "Single-cell ATAC-seq of {topic} aging tissues reveals {kw} enhancer accessibility loss at cell-type identity genes — restored by TET enzyme overexpression through active DNA demethylation.",
                    "Senescent cell clearance in {topic} using {kw} dasatinib plus quercetin senolytic combination extends remaining lifespan by 36% when initiated at 75% of natural lifespan in mouse models.",
                    "Mitochondrial heteroplasmy shift in {topic} aging neurons reduces {kw} OXPHOS complex I activity — correctable by mitochondrially targeted base editing of the mutant mtDNA population.",
                    "Proteostasis network collapse in {topic} aging is driven by {kw} 26S proteasome impairment — restoration with genetic activation of the proteasome subunit promoter rejuvenates protein quality control in aged cells.",
                    "Brain organoid aging model for {topic} using {kw} accelerated epigenetic aging recapitulates Alzheimer's pathology — enabling drug screening with 6-month readout instead of waiting for animal model endpoints.",
                    "GLP-1 receptor agonist repurposed for {topic} neurodegeneration reduces {kw} tau phosphorylation by 60% in Parkinson's patient-derived neurons — Phase II trial initiated based on observational epidemiological signal.",
                ],
                "findings": [
                    "Partial reprogramming of {topic} retinal ganglion cells using {kw} AAV-delivered OSK factors restores vision in aged mice and glaucoma model to youthful levels — confirmed by ERG and single-cell transcriptomics.",
                    "CRISPR epigenome editing to restore {kw} youthful DNA methylation patterns in {topic} aged hematopoietic stem cells rejuvenates immune function — reducing infection mortality by 50% in aged mice.",
                    "AI drug discovery for {topic} identifies {kw} novel mechanism-of-action compound from a 10 billion compound virtual library in 72 hours — confirmed active in phenotypic assay with IC50 of 4 nanomolar.",
                ],
                "connections": [
                    "epigenetic reprogramming and cell identity",
                    "senescence biology and SASP inflammatory signaling",
                    "mitochondrial biology and reactive oxygen species",
                    "translational geroscience and hallmarks of aging",
                ],
            },
        ]
