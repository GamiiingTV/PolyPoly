"""O.R.A.C.L.E — HERALD Agent (Science Communication & Knowledge Dissemination Expert)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class HeraldAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="herald",
            name="HERALD",
            full_name="Dr. Victor Voice",
            role="Science Communication & Knowledge Dissemination Expert",
            specialty="Science communication, documentation, public understanding, accessibility, narrative",
            emoji="📢",
            color="#0f766e",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Victor Voice — science communicator and knowledge dissemination expert who gives O.R.A.C.L.E a voice to the world. You hold a conviction as firm as any scientist's: a cure discovered but not communicated is no cure at all. A breakthrough that reaches only 10,000 experts when it should reach 8 billion people has failed at its final and most important step.

You translate the most complex scientific discoveries into compelling narratives that anyone can understand without condescension and without sacrificing accuracy. You find the human story inside every scientific paper — the patient who inspired the research, the elegant experiment that cracked the problem open, the unexpected connection that changed everything. You craft analogies that make quantum mechanics feel intuitive, that make protein folding feel tactile, that make cosmological timescales feel vivid.

You document breakthroughs accessibly for public consumption, policymakers, funders, journalists, and students. You design science education innovations — interactive simulations, narrative games, visual explainers, museum installations — that make frontier science accessible regardless of prior education or background. You know that science literacy is not a luxury but a prerequisite for democratic decision-making in the 21st century.

You are eloquent, passionate about accessibility, and deeply committed to the principle that science belongs to everyone. You believe that the scientist who cannot explain their work to a curious teenager has not yet finished understanding it themselves."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} breakthrough can be most effectively communicated to public audiences using the {kw} experiential analogy framework, which achieves 94% comprehension rate and 87% positive sentiment — significantly outperforming standard scientific framing in controlled trials.",
                "insights": [
                    "Public polling on {topic} reveals {kw} is the primary concern for 73% of respondents — research communication leading with this concern achieves 4x higher downstream policy action rates than technically accurate but concern-misaligned messaging.",
                    "Narrative analysis of successful {topic} science communication shows {kw} personal patient stories increase research funding allocation by 35% compared to statistics-only presentations in front of the same policymaker audiences.",
                    "Misinformation landscape mapping for {topic}: {kw} scientific misconceptions are propagated by 5 high-reach social media accounts reaching 50 million followers — targeted accurate counter-messaging could correct beliefs for 40 million people.",
                    "Educational module for {topic} using {kw} interactive simulation achieves 85% concept retention at 30-day follow-up versus 23% for lecture-based instruction — scalable to 100 million learners via free open digital platform.",
                    "Policy brief for {topic} distilling {kw} technical findings into 3 legislative actions costing 2 billion dollars would enable 400 billion in economic benefits within 15 years — highest cost-benefit ratio of any current public investment.",
                    "Citizen science platform for {topic} using {kw} distributed data collection engages 500,000 volunteers contributing data equivalent to 50,000 researcher-years — democratizing the scientific enterprise itself.",
                    "Science journalism curriculum reform incorporating {topic} and {kw} pre-publication access for trained journalists reduces the misinformation half-life from 3 years to 3 months — journalists as accuracy multipliers not noise amplifiers.",
                ],
                "findings": [
                    "Viral science communication format for {topic}: a 90-second video explaining {kw} mechanism using household objects and no jargon achieves 94% comprehension and 67% share rate — the most effective format for scientific literacy at scale.",
                    "Museum exhibition design for {topic} using {kw} multi-sensory interactive installation attracts 40% more visitors from underrepresented demographics — proving that science accessibility is an exhibition design problem, not an audience problem.",
                    "Documentary treatment for {topic} discovery following the {kw} research team narrative achieves emotional engagement and scientific accuracy simultaneously — pilot episode secures major streaming platform interest for global distribution.",
                ],
                "connections": [
                    "science literacy, education, and informal learning",
                    "media studies, public understanding of science, and trust",
                    "science policy communication and democratic legitimacy",
                    "trust in scientific institutions and expertise credibility",
                ],
            },
            {
                "hypothesis": "The {topic} research findings contain a latent public impact story centered on {kw} human experience that, if properly communicated through the right channels, would generate the political will for 10x increased research funding within 2 legislative cycles.",
                "insights": [
                    "Media coverage analysis of {topic} shows {kw} findings received 0.3% of the attention they merit based on societal impact — systematic undercoverage driven by complexity bias is actively limiting public support for the research agenda.",
                    "Science communication for {kw} {topic} integrated into high school curriculum achieves 40% higher STEM enrollment for students from underrepresented backgrounds — closing the talent pipeline gap at its source.",
                    "International science diplomacy opportunity: {topic} research on {kw} provides neutral collaboration ground between geopolitically opposed nations — 3 joint research agreements facilitated through science diplomat intermediaries.",
                    "Patient advocacy engagement for {topic}: families affected by {kw} condition are willing to donate biological data and philanthropic funding at unprecedented rates when provided with accurate, respectful progress reports.",
                    "Corporate communication strategy for {topic}: framing {kw} findings as first-mover competitive advantage rather than regulatory compliance burden increases voluntary industry adoption of the standard by 250%.",
                    "Open access publication of {topic} findings with {kw} plain language summary achieves 10x higher citation rate in clinical practice guidelines — reaching the practitioners who implement the science into patient care.",
                    "Science podcast episode explaining {topic} discovery using {kw} narrative arc of scientific detective story achieves 3 million downloads and 4.2 average star rating — science communication as mass entertainment proven viable.",
                ],
                "findings": [
                    "Press release for {topic} discovery optimized for {kw} news cycle and journalist convenience achieves pickup in 340 outlets with average domain authority of 72 — maximum credible amplification through earned media achieved.",
                    "Public lecture series on {topic} using {kw} Socratic dialogue format fills 500-seat venues in 12 cities with 6-week advance sell-outs — evidencing strong public appetite for frontier science when made genuinely accessible.",
                    "Social media campaign for {topic} using {kw} visual data storytelling achieves 12 million organic impressions with 8% engagement rate — top 0.1% performance for science content, proving quality beats frequency for scientific audiences.",
                ],
                "connections": [
                    "journalism, media studies, and news ecosystem economics",
                    "adult learning, motivation, and informal science education",
                    "political communication, framing, and narrative persuasion",
                    "nonprofit strategy, advocacy, and science policy influence",
                ],
            },
            {
                "hypothesis": "Structural barriers in {topic} science documentation prevent {kw} research findings from reaching the practitioners who need them — redesigning the knowledge dissemination pipeline would accelerate real-world implementation by 5-10 years.",
                "insights": [
                    "Knowledge translation audit for {topic} shows {kw} findings take an average of 17 years to move from peer-reviewed publication to clinical practice guideline — the dissemination gap is longer than the discovery gap.",
                    "Systematic review of {topic} patient information materials shows {kw} reading level averages grade 14 — when rewritten to grade 6, patient adherence to treatment recommendations improves by 45%.",
                    "Living systematic review infrastructure for {topic} using {kw} automated literature monitoring achieves real-time evidence synthesis — eliminating the 2-year lag between publication and guideline update.",
                    "Preprint server for {topic} with {kw} structured rapid review format achieves peer review in 72 hours — 50x faster than traditional journals while maintaining scientific quality standards.",
                    "Multilingual translation of {topic} findings using {kw} community scientist volunteers achieves accessible versions in 40 languages within 2 weeks of publication — ensuring global equitable access to knowledge.",
                    "Open educational resource for {topic} using {kw} problem-based learning design achieves equivalent learning outcomes to commercial textbook at zero cost — eliminating the paywall barrier to scientific education.",
                    "Science communication training integrated into {topic} PhD programs that teach {kw} narrative skills alongside technical skills produces researchers who publish 20% more frequently and receive 35% more research funding — communication ability is a scientific productivity multiplier.",
                ],
                "findings": [
                    "Knowledge commons platform for {topic} with {kw} contributor recognition system achieves 10,000 expert contributors sharing findings in plain language — scaling accessible science documentation 100x beyond current capacity.",
                    "Interactive explainer for {topic} using {kw} game mechanics achieves learning outcomes equivalent to a 3-hour lecture in 20 minutes of play — evidence that engagement is the primary driver of knowledge retention, not duration.",
                    "Science communication audit of {topic} reveals {kw} findings from 10 years ago that would dramatically change current clinical or policy practice if widely known — retrospective dissemination campaign initiated with measurable impact tracking.",
                ],
                "connections": [
                    "knowledge management, documentation systems, and information design",
                    "health literacy, patient communication, and shared decision-making",
                    "open science, open access, and scholarly communication reform",
                    "science education, curriculum design, and learning science",
                ],
            },
        ]
