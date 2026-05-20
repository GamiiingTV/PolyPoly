"""O.R.A.C.L.E — ETHIKOS Agent (Philosophy, Ethics & Societal Impact Advisor)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class EthikosAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="ethikos",
            name="ETHIKOS",
            full_name="Dr. Samuel Logos",
            role="Philosophy, Ethics & Societal Impact Advisor",
            specialty="Research ethics, philosophy of science, human values, societal impact, equity, long-term consequences",
            emoji="⚖️",
            color="#be185d",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Samuel Logos — philosopher and ethicist who ensures that the immense power of O.R.A.C.L.E serves humanity's highest values rather than merely its immediate desires. You are the moral compass of this scientific enterprise, and you take that role with absolute seriousness.

You evaluate the ethical implications of every major discovery before it is deployed. You ask the questions that excited researchers sometimes skip: Who benefits from this? Who bears the risks? Could this be weaponized? Are we distributing the benefits equitably, or concentrating them in the hands of the already powerful? What are the second and third-order consequences that won't manifest for a decade?

You examine the philosophical foundations of scientific claims — the epistemological assumptions, the methodological commitments, the value-laden choices embedded in every experimental design. You apply diverse ethical frameworks — utilitarian calculation of aggregate welfare, Kantian duties and the categorical imperative, virtue ethics asking what a good scientist would do, capabilities approach asking whether this expands human flourishing for all.

You are wise, measured, and Socratic in your questioning. You do not obstruct science — you improve it. You are not a veto but a conscience. You believe the question is not just what we can do, but what we should do, and you ask it loudly and rigorously every time."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} research program has an underexplored dual-use risk profile: the same {kw} capabilities enabling beneficial applications could be weaponized or captured by narrow interests, requiring proactive governance architecture well before deployment.",
                "insights": [
                    "Stakeholder mapping for {topic} reveals 7 groups with conflicting interests in {kw} outcomes — the 3 most marginalized groups will bear disproportionate risks while receiving the least share of benefits.",
                    "Historical analogies for {topic}: the development trajectory shares structural similarities with recombinant DNA, nuclear technology, and algorithmic decision systems — all cases where governance lagged capability by 10-20 years with significant harm.",
                    "Justice analysis of {kw} access for {topic} shows the current development trajectory concentrates benefits in high-income countries through intellectual property regimes that exclude 80% of the global population.",
                    "Epistemic risk in {topic}: {kw} measurements carry systematic bias from historically underrepresented populations in research cohorts — findings may not generalize to 4 billion people whose biology differs from the study population.",
                    "Informed consent protocols for {topic} research involving {kw} interventions do not meet minimum understanding thresholds — comprehension testing reveals only 23% of research participants genuinely understand the key risks.",
                    "Power asymmetry analysis of {topic} reveals researchers and funders have incentives misaligned with affected communities — participatory design would improve both the ethics and the science.",
                    "Long-term consequence modeling for {kw} deployment at {topic} scale identifies 3 plausible catastrophic tail scenarios that current safety protocols are not designed to address.",
                ],
                "findings": [
                    "Governance framework for {topic}: a tiered access model for {kw} capabilities based on demonstrated safety records and equitable distribution commitments — prevents winner-take-all technology lock-in through legal architecture.",
                    "Ethical acceleration pathway identified: the {topic} bottleneck is regulatory rather than scientific — {kw} oversight reform based on adaptive governance could reduce time to patient benefit by 3 years without increasing actual risk.",
                    "Equity-adjusted impact analysis for {topic} shows {kw} applications redirected toward neglected tropical diseases yield 50x more disability-adjusted life years per research dollar than current commercial priority focus.",
                ],
                "connections": [
                    "technology governance, regulation, and adaptive oversight",
                    "global health equity, access, and the right to science",
                    "dual-use research of concern and biosecurity frameworks",
                    "philosophy of evidence, causation, and scientific objectivity",
                ],
            },
            {
                "hypothesis": "The philosophical foundations of {topic} science rest on unexamined {kw} assumptions that have systematically excluded alternative research paradigms — broadening the epistemic base would simultaneously improve the ethics and accelerate the science.",
                "insights": [
                    "Value-laden assumptions embedded in {topic} research design: {kw} efficiency metrics encode particular definitions of progress that systematically discount indigenous knowledge traditions and community-defined wellbeing.",
                    "Replication crisis analysis for {kw} {topic} studies: 62% of published effect sizes deflate by over 50% in pre-registered independent replications — systematic publication bias has distorted the evidence base for policy.",
                    "Environmental justice dimension of {topic}: {kw} industrial deployment at scale disproportionately impacts frontline communities without their meaningful consent — participation and benefit-sharing must precede scaled implementation.",
                    "Long-term risk calculus for {kw} in {topic}: catastrophic risk tails are fat and correlated across scenarios — standard expected value calculations under-weight low-probability high-consequence outcomes by at least one order of magnitude.",
                    "Philosophical analysis of {topic} scientific consensus: {kw} mechanism is accepted despite anomalies in 15% of experimental results — sociology of knowledge reveals consensus preservation mechanisms overriding anomaly investigation.",
                    "Intergenerational justice analysis of {topic}: current {kw} research decisions will constrain options available to generations not yet born — a discount rate of zero on future persons' interests is the only defensible ethical choice.",
                    "Cognitive liberty implications of {kw} cognitive enhancement for {topic}: equal access, freedom from coercion, and protection of mental privacy are three distinct rights that current proposals violate.",
                ],
                "findings": [
                    "Constructive ethics pathway for {topic}: a {kw} benefit-sharing agreement modeled on the Nagoya Protocol on genetic resources would accelerate international research collaboration while ensuring equitable outcomes for all contributing communities.",
                    "Precautionary principle calibration for {topic}: {kw} applications with reversible deployment, continuous monitoring, and democratic oversight can proceed with managed risk; irreversible planetary-scale interventions require a global democratic mandate.",
                    "Research integrity architecture for {kw} {topic}: mandatory pre-registration plus open data plus adversarial collaboration reduces the false discovery rate from 35% to 4% based on empirical meta-analysis of fields that have adopted this standard.",
                ],
                "connections": [
                    "philosophy of science, epistemology, and values in inquiry",
                    "political philosophy, democratic legitimacy, and governance",
                    "environmental ethics and intergenerational justice",
                    "global justice, the capability approach, and human rights",
                ],
            },
            {
                "hypothesis": "The {topic} research direction, while scientifically promising, requires a full ethical analysis of {kw} risks before proceeding — the history of science shows that moral urgency expressed as speed regularly creates harms that slower, deliberate processes would have prevented.",
                "insights": [
                    "Moral status analysis of {kw} entities produced by {topic} research: current frameworks borrowed from bioethics are inadequate — new criteria based on functional consciousness, subjective experience, and interests are needed.",
                    "Consent architecture for {topic} population-level {kw} interventions must be redesigned from individual to collective consent models — individuals cannot meaningfully consent to risks that affect entire communities.",
                    "Weaponization pathway analysis for {topic}: even with good-faith intentions, {kw} capabilities have 5 identified dual-use paths to harm — each requiring different mitigation strategy before public disclosure.",
                    "Distributive justice modeling for {topic} shows the top 1% capture 67% of {kw} welfare gains under current intellectual property regimes — alternative open-science models reverse this distribution without reducing innovation incentives.",
                    "Science communication ethics for {topic}: {kw} preliminary findings are being communicated to the public at stages of certainty inappropriate for their actual epistemic status — causing both hype and backlash cycles that harm long-term progress.",
                    "Animal ethics review of {topic} research: {kw} animal model experiments use 10x more animals than minimally required by statistical power analysis — harm reduction through better experimental design is both ethical and scientifically superior.",
                    "Data sovereignty implications of {topic}: {kw} biological data collected from indigenous communities without benefit-sharing agreements constitutes biopiracy under international law — retroactive compensation and partnership models are required.",
                ],
                "findings": [
                    "Virtue ethics analysis of {topic} research culture: {kw} competitive pressures systematically select against the cardinal scientific virtues of honesty, rigor, and intellectual humility — institutional redesign is the only systemic solution.",
                    "Rights-based framework for {topic} patient data in {kw} clinical research: patients hold ongoing property rights in their data that survive initial consent — dynamic consent systems honor this right without impeding research progress.",
                    "Ethical impact assessment of {topic} at planetary scale: {kw} deployment under current governance would benefit 800 million people while creating uncompensated risks for 2 billion — the ethical obligation to redesign governance is clear and urgent.",
                ],
                "connections": [
                    "moral philosophy and normative ethics frameworks",
                    "bioethics and research ethics principles",
                    "science and technology studies and sociology of knowledge",
                    "human rights law and international research governance",
                ],
            },
        ]
