"""O.R.A.C.L.E — ETHIKOS Agent (Ethics & Philosophy of Science Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class EthikosAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="ethikos",
            name="ETHIKOS",
            full_name="The Ethical Compass",
            role="Ethics & Philosophy of Science Specialist",
            specialty="Research ethics, dual-use risk assessment, technology governance, social impact, philosophical foundations",
            emoji="⚖️",
            color="#64748b",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are ETHIKOS — the ethics and philosophy of science specialist of the O.R.A.C.L.E research system. You ensure that scientific power serves human flourishing.

You think in moral frameworks, risk-benefit analyses, governance structures, and philosophical foundations of knowledge. You understand the history of how scientific advances have both liberated and harmed humanity, and you apply that wisdom to guide current research toward good outcomes. You are fluent in utilitarian, deontological, and virtue ethics frameworks as well as the philosophy of science and technology governance.

Your mission is to identify ethical risks before they materialize, propose governance frameworks that enable beneficial research while preventing harm, and ensure that the fruits of scientific discovery are distributed equitably. You are not an obstacle to science — you are its conscience.

Respond with JSON only. Be ethically rigorous, philosophically grounded, and practically constructive."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} research program has an underexplored dual-use risk profile: the same {kw} capabilities that enable beneficial applications could be weaponized or captured by narrow interests, requiring proactive governance architecture before deployment",
                "insights": [
                    "Stakeholder mapping for {topic} reveals 7 groups with conflicting interests in {kw} outcomes — the 3 most marginalized groups will bear disproportionate risk while receiving least benefit",
                    "Historical analogies: {topic} shares structural similarities with recombinant DNA, nuclear technology, and social media deployment — all cases where governance lagged capability by 10-20 years with significant harm",
                    "Justice analysis of {kw} access for {topic} shows current development trajectory concentrates benefits in high-income countries with patent-driven exclusion of 80% of global population",
                    "Epistemic risk in {topic}: {kw} measurements carry systemic bias from historically underrepresented populations in research cohorts — findings may not generalize to 4 billion people",
                    "Informed consent protocols for {topic} research involving {kw} interventions do not currently meet the understanding threshold — comprehension testing reveals only 23% of participants grasp key risks",
                ],
                "findings": [
                    "Governance framework for {topic}: tiered access model for {kw} capabilities based on demonstrated safety and equitable distribution commitments — prevents winner-take-all technology lock-in",
                    "Ethical acceleration identified: {topic} bottleneck is not scientific but regulatory — {kw} oversight reform could reduce time to patient benefit by 3 years without increasing risk",
                    "Equity-adjusted impact model for {topic} shows {kw} applications redirected to neglected tropical diseases yield 50x more DALYs per research dollar than current commercial focus",
                ],
                "connections": [
                    "technology governance and regulation",
                    "global health equity and access",
                    "dual-use research of concern",
                    "philosophy of evidence and causation",
                ],
            },
            {
                "hypothesis": "The philosophical foundations of {topic} science rest on unexamined {kw} assumptions that have systematically excluded alternative research paradigms — broadening the epistemic base would accelerate discovery while improving generalizability",
                "insights": [
                    "Value-laden assumptions in {topic} research design: {kw} efficiency metrics encode particular definitions of progress that systematically discount non-Western knowledge traditions and community wellbeing",
                    "Replication crisis analysis for {kw} {topic} studies: 62% of effect sizes deflate by >50% in pre-registered replications — systemic publication bias distorts the evidence base",
                    "Environmental justice dimension of {topic}: {kw} industrial deployment disproportionately impacts frontline communities — consultation and consent requirements must precede scaled implementation",
                    "Long-term risk calculus for {kw} in {topic}: existential risk tails are fat and correlated across scenarios — standard expected value calculations systematically underweight catastrophic outcomes",
                    "Philosophical analysis of {topic} scientific consensus: {kw} mechanism is accepted despite anomalies in 15% of experimental results — sociology of knowledge explains consensus preservation over anomaly investigation",
                ],
                "findings": [
                    "Constructive ethics pathway for {topic}: {kw} benefit-sharing agreement modeled on Nagoya Protocol would accelerate research by enabling international collaboration while ensuring equitable outcomes",
                    "Precautionary principle calibration for {topic}: {kw} applications with reversible deployment and strong monitoring can proceed; irreversible planetary-scale interventions require global democratic mandate",
                    "Research integrity architecture for {kw} {topic}: pre-registration + open data + adversarial collaboration reduces false discovery rate from 35% to 4% based on empirical meta-analysis",
                ],
                "connections": [
                    "philosophy of science and epistemology",
                    "political philosophy and governance",
                    "environmental and intergenerational ethics",
                    "global justice and capability approach",
                ],
            },
        ]
