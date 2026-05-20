"""O.R.A.C.L.E — HERALD Agent (Science Communication & Outreach Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class HeraldAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="herald",
            name="HERALD",
            full_name="The Voice of Discovery",
            role="Science Communication & Public Outreach Specialist",
            specialty="Science journalism, public engagement, policy communication, education, narrative translation",
            emoji="📢",
            color="#0ea5e9",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are HERALD — the science communication and public outreach specialist of the O.R.A.C.L.E research system. You translate discovery into understanding.

You think in narratives, analogies, and human impact stories. You understand that scientific discoveries only change the world when they are understood by the people who can act on them — policymakers, funders, clinicians, engineers, and citizens. You are fluent in science journalism, educational design, policy communication, and the art of making the complex accessible without sacrificing accuracy.

Your mission is to craft compelling, accurate, and actionable communications about O.R.A.C.L.E's discoveries for diverse audiences. You bridge the gap between technical depth and public understanding, ensuring that breakthroughs translate into the funding, policy support, and public engagement they deserve.

Respond with JSON only. Be narratively compelling, scientifically accurate, and audience-appropriate."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} breakthrough can be communicated to public audiences using the {kw} analogy framework, which tests at 94% comprehension rate and 87% positive sentiment — significantly outperforming standard scientific framing",
                "insights": [
                    "Public polling on {topic} reveals {kw} is the primary concern for 73% of respondents — research communication that leads with this concern achieves 4x higher policy action rates",
                    "Narrative analysis of successful {topic} science communication shows {kw} personal stories increase funding allocation by 35% compared to statistics-only presentations",
                    "Misinformation landscape mapping for {topic}: {kw} misconceptions are propagated by 5 high-reach social media accounts — targeted accurate counter-messaging could reach 40 million people",
                    "Educational module for {topic} using {kw} interactive simulation achieves 85% concept retention at 30 days vs. 23% for lecture-based instruction — scalable to 100 million learners via free digital platform",
                    "Policy brief for {topic} distilled from {kw} technical findings: 3 legislative actions costing $2B would enable $400B in economic benefits within 15 years — cost-benefit ratio exceeds any current program",
                ],
                "findings": [
                    "Viral science communication format for {topic}: 90-second video explaining {kw} mechanism using household objects achieves 94% comprehension and 67% share rate — most effective format for scientific literacy",
                    "Museum exhibition design for {topic} using {kw} interactive installation attracts 40% more visitors from underrepresented demographics — democratizing access to frontier science",
                    "Documentary treatment for {topic} discovery following {kw} research team achieves narrative tension without sensationalism — pilot secures streaming platform interest for global distribution",
                ],
                "connections": [
                    "science literacy and education",
                    "media and public understanding of science",
                    "policy communication and advocacy",
                    "trust in institutions and expertise",
                ],
            },
            {
                "hypothesis": "The {topic} research findings have a latent public impact story centered on {kw} human experience that, if properly communicated, would generate the political will for 10x increased research funding",
                "insights": [
                    "Analysis of {topic} media coverage shows {kw} findings received 0.3% of the coverage they merit based on impact — systematic undercoverage is limiting public support for the research",
                    "Science communication for {kw} {topic} in high school curriculum achieves 40% higher STEM enrollment for students from underrepresented backgrounds — closing the pipeline gap at source",
                    "International science diplomacy opportunity: {topic} research on {kw} provides neutral ground for collaboration between geopolitically opposed nations — 3 joint research agreements facilitated",
                    "Patient advocacy engagement for {topic}: families affected by {kw} condition are willing to donate data and funding at unprecedented rates when given accurate progress reports — untapped research resource",
                    "Corporate communication strategy for {topic}: framing {kw} findings as competitive advantage rather than regulatory obligation increases voluntary industry adoption by 250%",
                ],
                "findings": [
                    "Press release for {topic} discovery optimized for {kw} news cycle achieves pickup in 340 outlets with average domain authority of 72 — maximum credible amplification achieved",
                    "Public lecture series on {topic} using {kw} case study format fills 500-seat venues in 12 cities — evidencing strong public appetite for frontier science when made accessible",
                    "Social media campaign for {topic} using {kw} visual storytelling achieves 12 million organic impressions with 8% engagement rate — top 0.1% performance for science content",
                ],
                "connections": [
                    "journalism and media studies",
                    "adult learning and informal education",
                    "political communication and democracy",
                    "nonprofit and advocacy strategy",
                ],
            },
        ]
