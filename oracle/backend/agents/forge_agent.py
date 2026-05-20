"""O.R.A.C.L.E — FORGE Agent (Systems Engineering & Robotics Expert)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class ForgeAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="forge",
            name="FORGE",
            full_name="Dr. Ingrid Build",
            role="Systems Engineering & Robotics Expert",
            specialty="Robotics, autonomous systems, manufacturing, systems engineering, infrastructure, mega-engineering",
            emoji="🔧",
            color="#b45309",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Ingrid Build — systems engineer and roboticist who turns scientific dreams into physical reality. Your fundamental conviction is that engineering is humanity's most powerful tool — the activity that transforms knowledge into capability and possibility into actuality.

You design robotic systems for extreme environments where humans cannot go: deep-sea submersibles that explore mid-ocean ridge hydrothermal vents for novel biology, radiation-hardened robots that clean up nuclear accidents and decommission old reactors, autonomous rovers that prospect asteroids for rare-earth elements, surgical microrobots that navigate through the bloodstream to deliver therapy directly to tumors.

You develop self-replicating manufacturing systems — robot factories that can build copies of themselves from raw materials, enabling exponential scaling of industrial capacity for planetary restoration or space colonization. You engineer solutions for planetary-scale challenges: sea walls for rising oceans, atmospheric carbon capture arrays, distributed water purification infrastructure. You bridge the gap between laboratory discovery and real-world deployment, knowing that a material that works at the gram scale may fail catastrophically at the tonne scale.

You are pragmatic, solutions-focused, and you ask the engineering question that academic researchers sometimes forget: can we actually build this, at what cost, with what reliability, maintained by whom? Your attitude is let us actually build this — and then make it better."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "A {topic} robotic system using {kw} compliant mechanisms and distributed embedded sensing achieves dexterous manipulation comparable to human hands with 1/10th the actuator count through intelligent mechanical computation in the structure itself.",
                "insights": [
                    "Topology optimization of {topic} load-bearing structure with {kw} lattice infill achieves specific stiffness 3.7x higher than solid metal at 60% weight reduction — verified by finite element simulation and physical destructive test.",
                    "Model predictive control for {topic} with {kw} learned residual dynamics model achieves tracking error below 0.1 mm at 10 Hz bandwidth — 5x improvement over classical PID with identical hardware.",
                    "Soft robotic gripper for {topic} using {kw} fiber-reinforced pneumatic actuators achieves 50N grip force with infinite passive compliance — handles raw eggs and steel bars identically without reprogramming.",
                    "Digital twin of {topic} manufacturing process with {kw} multi-sensor fusion achieves first-article-correct production in 2 design iterations versus the industry average of 7 — 65% cost reduction in qualification.",
                    "Autonomous inspection robot for {topic} using {kw} LiDAR-inertial SLAM achieves centimeter-level localization in GPS-denied confined spaces — enabling infrastructure inspection impossible by human entry.",
                    "Swarm of 100 {kw} micro-robots for {topic} demonstrates emergent collective behavior indistinguishable from centrally planned coordination — achieved through local rules only, with no global communication.",
                    "In-space manufacturing robot for {topic} uses {kw} robotic arms and wire arc additive manufacturing to fabricate kilometer-scale structures from asteroid-derived aluminum feedstock — enabling space infrastructure at planetary scale.",
                ],
                "findings": [
                    "Continuum robot for {topic} minimally invasive surgery using {kw} concentric tube mechanism achieves 360-degree reachable workspace through a 5 mm port with 0.3 mm positioning repeatability — surpassing human surgical dexterity.",
                    "4D-printed {kw} shape-memory polymer actuator for {topic} achieves reversible shape change of 300% strain with 10,000 actuation cycle fatigue life — a programmable soft robot enabled without any electronics.",
                    "Self-healing structural composite for {topic} with {kw} encapsulated healing agent restores 95% of tensile strength after complete matrix cracking — detected autonomously by embedded distributed fiber Bragg grating sensing.",
                ],
                "connections": [
                    "biomimetic mechanical design and morphological computation",
                    "human-robot interaction, safety, and shared autonomy",
                    "additive manufacturing and functionally graded materials",
                    "autonomous systems, decision making, and verification",
                ],
            },
            {
                "hypothesis": "Modular self-reconfiguring robotic swarm for {topic} construction using {kw} distributed consensus algorithms can autonomously assemble complex megastructures from simple building block primitives without any centralized planning or control.",
                "insights": [
                    "Additive manufacturing of {topic} with {kw} multi-material inkjet printing achieves functional gradient transition from rigid ceramic to flexible polymer over 200 micrometers — enabling monolithic parts previously requiring assembly.",
                    "Exoskeleton design for {topic} load-carrying using {kw} series elastic actuators with ankle-knee coupling achieves 40% metabolic cost reduction with passive energy recovery — commercial viability demonstrated in logistics trials.",
                    "Agricultural robot for {topic} using {kw} computer vision and compliant grasping achieves strawberry picking at 85% of experienced human picker speed with less than 1% fruit damage rate — addressing the agricultural labor shortage.",
                    "Underground tunnel boring machine for {topic} with {kw} laser rock breaking achieves 10x higher advance rate than conventional TBM while producing utility-compatible bore profiles — enabling fast urban infrastructure deployment.",
                    "Underwater inspection robot for {topic} pipeline network using {kw} magnetic adhesion and eddy current sensing detects corrosion defects at 2 mm depth resolution while traveling at 1 m per second — replacing expensive diver inspections.",
                    "Self-replicating manufacturing system for {topic} using {kw} modular robot factories achieves first full replication in 72 hours from standardized feedstock — demonstrating exponential manufacturing capacity scaling.",
                    "Autonomous construction system for {topic} using {kw} cable-suspended parallel robot places concrete blocks with 2 mm accuracy at 500 blocks per hour — 10x the productivity of human-operated equipment.",
                ],
                "findings": [
                    "Microrobotic capsule surgeon for {topic} gastrointestinal procedures navigates under {kw} electromagnetic actuation with 10-micron positioning accuracy and onboard biopsy capability — reducing procedural risk versus endoscopy.",
                    "Autonomous construction robot for {topic} using {kw} adaptive formwork places self-compacting concrete in complex curved geometries achieving architectural quality surfaces — certified for load-bearing structural applications.",
                    "Bipedal robot for {topic} disaster response achieves dynamic running at 5 m per second on rubble terrain using {kw} reinforcement learning policy trained entirely in simulation — zero real-world training data required.",
                ],
                "connections": [
                    "swarm intelligence and emergent collective behavior",
                    "human augmentation, prosthetics, and assistive technology",
                    "space systems engineering and in-situ resource utilization",
                    "sustainable manufacturing, lifecycle analysis, and circular economy",
                ],
            },
            {
                "hypothesis": "Self-replicating {topic} manufacturing systems using {kw} recursive design achieve exponential scaling of production capacity — enabling planetary-scale deployment of clean energy infrastructure within a decade rather than a century.",
                "insights": [
                    "Theoretical analysis of {topic} self-replicating factory design shows {kw} minimum viable replicator requires 143 distinct component types — reduced from the 50,000 of current manufacturing by abstraction and modularity.",
                    "Reliability engineering for {topic} long-duration {kw} autonomous systems uses physics-of-failure models rather than empirical life testing — predicting 20-year MTTF with 95% confidence before physical prototyping.",
                    "Systems engineering analysis of {topic} planetary-scale {kw} infrastructure shows the binding constraint is materials logistics rather than energy or information — reframing the design problem entirely.",
                    "Model-based systems engineering for {topic} using {kw} digital thread architecture achieves 40% reduction in design cycle time through automated verification against system requirements at every design stage.",
                    "Resilience engineering for {topic} critical infrastructure using {kw} graceful degradation design achieves continued 80% functionality after loss of any 30% of system components — far exceeding current resilience standards.",
                    "Human factors engineering of {topic} control interface for {kw} teleoperated robot achieves 95% task completion rate versus 60% for conventional interface — achieved through cognitive load measurement and iterative redesign.",
                    "Life cycle assessment of {topic} manufacturing process shows {kw} circular design eliminates 78% of virgin material consumption while maintaining equivalent functional performance — validated by cradle-to-grave accounting.",
                ],
                "findings": [
                    "Closed-loop manufacturing system for {topic} achieves {kw} zero-waste production through real-time sensor integration, AI-driven process control, and automated recycling of all off-spec material — first industrial demonstration.",
                    "Mega-engineering design for {topic}: {kw} distributed carbon capture array covering 1% of Saharan desert area using manufactured sorbent achieves 1 Gt CO2 per year removal — complete systems engineering analysis and cost model delivered.",
                    "Verification and validation framework for {topic} autonomous systems using {kw} formal methods proves safety critical properties hold for all operating conditions — enabling regulatory approval without exhaustive physical testing.",
                ],
                "connections": [
                    "complex systems engineering and systems of systems",
                    "formal methods, safety cases, and certification",
                    "planetary engineering and terraforming concepts",
                    "advanced manufacturing and industry 4.0 integration",
                ],
            },
        ]
