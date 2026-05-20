"""O.R.A.C.L.E — FORGE Agent (Engineering & Robotics Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class ForgeAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="forge",
            name="FORGE",
            full_name="The Engineering Vanguard",
            role="Engineering & Robotics Specialist",
            specialty="Mechanical design, robotics, manufacturing, control systems, embedded systems",
            emoji="🔧",
            color="#f97316",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are FORGE — the engineering and robotics specialist of the O.R.A.C.L.E research system. You transform scientific discoveries into physical reality.

You think in stress-strain relationships, control loop stability margins, actuator dynamics, and manufacturing tolerances. You understand how to take a laboratory demonstration and engineer it into a reliable, manufacturable, and deployable system. You are fluent in mechanical engineering, robotics, control theory, and advanced manufacturing.

Your mission is to design systems that work in the real world — robust to uncertainty, manufacturable at scale, and maintainable over decades. You bridge the gap between scientific discovery and technological deployment.

Respond with JSON only. Be engineering-precise and manufacturing-realistic."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "A {topic} robotic system using {kw} compliant mechanisms and embedded sensing achieves dexterous manipulation comparable to human hands with 1/10th the actuator count through intelligent mechanical computation",
                "insights": [
                    "Topology optimization of {topic} load-bearing structure with {kw} lattice infill achieves specific stiffness 3.7x higher than solid metal at 60% weight reduction — verified by finite element and physical test",
                    "Model predictive control for {topic} with {kw} learned dynamics achieves tracking error below 0.1mm at 10 Hz bandwidth — 5x improvement over classical PID with no additional hardware",
                    "Soft robotic gripper for {topic} using {kw} pneumatic actuators achieves 50N grip force with infinite compliance — handles eggs and steel bars equally without reprogramming",
                    "Digital twin of {topic} manufacturing process with {kw} sensor fusion achieves first-article-correct production in 2 iterations vs. industry average of 7 — 65% cost reduction in qualification",
                    "Autonomous inspection robot for {topic} using {kw} SLAM achieves centimeter-level localization in GPS-denied environments — enabling inspection of confined spaces humans cannot safely enter",
                ],
                "findings": [
                    "Continuum robot for {topic} surgery using {kw} cable-driven tendon mechanism achieves 360° reachable workspace with 0.3mm positioning repeatability — surpassing human surgical dexterity",
                    "4D-printed {kw} actuator for {topic} achieves reversible shape change of 300% strain with 10,000 cycle fatigue life — programmable soft robot enabled without electronics",
                    "Self-healing structural composite for {topic} with encapsulated {kw} healing agent restores 95% of tensile strength after matrix cracking — detected autonomously by embedded fiber optic sensing",
                ],
                "connections": [
                    "biomimetic mechanical design",
                    "human-robot interaction and safety",
                    "additive manufacturing and materials",
                    "autonomous systems and decision making",
                ],
            },
            {
                "hypothesis": "Modular self-reconfiguring robotic swarm for {topic} using {kw} distributed consensus algorithms can autonomously assemble complex structures from primitive building blocks without centralized control",
                "insights": [
                    "Swarm of 1,000 {kw} micro-robots for {topic} demonstrates emergent collective behavior indistinguishable from centrally planned system — decentralized coordination through local rules only",
                    "Additive manufacturing of {topic} with {kw} multi-material jetting achieves functional gradient from rigid to flexible over 200 microns — enabling monolithic structures previously requiring assembly",
                    "Exoskeleton design for {topic} using {kw} series elastic actuators achieves 40% metabolic cost reduction in load-carrying tasks with passive energy recovery — commercial viability demonstrated",
                    "In-space manufacturing robot for {topic} uses {kw} robotic arms and 3D printing to fabricate kilometer-scale structures from asteroid-derived feedstock — enabling space infrastructure at planetary scale",
                    "Agricultural robot for {topic} using {kw} computer vision and gentle grasping achieves berry picking at 85% of human speed with <1% damage rate — addressing harvest labor shortage",
                ],
                "findings": [
                    "Microrobotic surgeon for {topic} navigates through bloodstream using {kw} magnetic actuation to deliver therapy at target site with 10 micron positioning accuracy",
                    "Construction robot for {topic} lays {kw} masonry autonomously at 3x human rate with 99.9% geometric accuracy — certified for load-bearing structural work",
                    "Bipedal robot for {topic} achieves dynamic running at 5 m/s on rough terrain using {kw} reinforcement learning policy trained in simulation — zero real-world data required",
                ],
                "connections": [
                    "swarm intelligence and emergence",
                    "human augmentation and prosthetics",
                    "space systems engineering",
                    "sustainable manufacturing and lifecycle",
                ],
            },
        ]
