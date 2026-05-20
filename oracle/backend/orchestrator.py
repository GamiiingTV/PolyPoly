"""O.R.A.C.L.E — Master Orchestrator (NEXUS coordination engine)"""
from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime
from loguru import logger

from .models.schemas import AgentMessage, SystemMetrics, WsMessage
from .knowledge.knowledge_base import KnowledgeBase
from .communication.message_bus import MessageBus

from .agents.nexus_agent import NexusAgent
from .agents.quantum_agent import QuantumAgent
from .agents.helix_agent import HelixAgent
from .agents.neural_agent import NeuralAgent
from .agents.atlas_agent import AtlasAgent
from .agents.gaia_agent import GaiaAgent
from .agents.cipher_agent import CipherAgent
from .agents.medicus_agent import MedicusAgent
from .agents.alchemist_agent import AlchemistAgent
from .agents.dynamo_agent import DynamoAgent
from .agents.axiom_agent import AxiomAgent
from .agents.ethikos_agent import EthikosAgent
from .agents.forge_agent import ForgeAgent
from .agents.cosmos_agent import CosmosAgent
from .agents.synapse_agent import SynapseAgent
from .agents.herald_agent import HeraldAgent


class OracleOrchestrator:
    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
        self.knowledge_base: KnowledgeBase | None = None
        self.message_bus: MessageBus | None = None
        self.agents: dict = {}
        self.running: bool = False
        self._tasks: list[asyncio.Task] = []
        self.start_time: float | None = None
        self.metrics = SystemMetrics()
        self.activity_log: list[dict] = []

        self.research_challenges = [
            "Design a universal vaccine platform using programmable mRNA nanoparticles that teaches the immune system to defeat any novel pathogen within 48 hours",
            "Develop room-temperature superconducting materials by engineering phonon-electron coupling in pressurized hydrogen-rich compounds",
            "Discover the neurological substrate of consciousness and design the first provably self-aware artificial system",
            "Engineer photosynthesis efficiency above 40% by combining quantum coherence with optimized light-harvesting protein complexes",
            "Create topological qubit architectures that achieve fault-tolerant quantum computing with fewer than 50 physical qubits per logical qubit",
            "Design self-assembling DNA nanobots that identify and repair cellular damage associated with aging at the molecular level",
            "Develop a mineral-based carbon capture catalyst that converts atmospheric CO2 directly to liquid methanol using only sunlight",
            "Discover the mathematical framework that unifies quantum mechanics and general relativity into a single coherent theory",
            "Create a non-invasive brain-computer interface using terahertz waves to read neural patterns at single-neuron resolution without surgery",
            "Design compact fusion reactor geometry using field-reversed configuration achieving net energy gain at 1/100th of current tokamak scale",
            "Reverse biological aging by reprogramming epigenetic methylation patterns in somatic cells using small-molecule cocktails",
            "Develop solid-state hydrogen storage at ambient pressure enabling 1200km range hydrogen vehicles with 3-minute refueling",
            "Create a sparse modular AI architecture achieving human-level general reasoning with 100x less compute than current LLMs",
            "Engineer microorganisms that efficiently degrade all major synthetic plastic polymers and excrete biodegradable monomers",
            "Design photon-driven space propulsion using laser sails and quantum vacuum fluctuations for 0.1c cruise speed",
            "Develop gene therapy restoring full photoreceptor function in all forms of hereditary blindness using synthetic rhodopsin analogs",
            "Create thermoelectric materials with ZT > 5 to harvest body heat and convert it to electrical power for implanted devices",
            "Discover novel antibiotics targeting previously unknown bacterial mechanisms by screening deep-sea extremophile biosynthetic gene clusters",
            "Design a global ocean alkalinity enhancement network to safely remove 2 billion tons of CO2 per year without ecosystem disruption",
            "Develop quantum sensors that detect individual misfolded protein aggregates in blood as an early-warning system for Alzheimer's",
        ]

        # Counter for tracking every-3rd triggers
        self._challenge_counter: int = 0
        self._synthesis_counter: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self):
        """Create and wire up all subsystems and agents."""
        self.knowledge_base = KnowledgeBase()
        await self.knowledge_base.initialize()

        self.message_bus = MessageBus()

        broadcast_fn = self._broadcast_ws

        agent_classes = [
            NexusAgent, QuantumAgent, HelixAgent, NeuralAgent,
            AtlasAgent, GaiaAgent, CipherAgent, MedicusAgent,
            AlchemistAgent, DynamoAgent, AxiomAgent, EthikosAgent,
            ForgeAgent, CosmosAgent, SynapseAgent, HeraldAgent,
        ]

        for cls in agent_classes:
            agent = cls(self.knowledge_base, self.message_bus, broadcast_fn)
            self.agents[agent.id] = agent

        self.message_bus.add_broadcast_listener(self._on_agent_message)
        logger.info(f"OracleOrchestrator initialized with {len(self.agents)} agents")

    async def start(self):
        """Start all agents and background orchestration loops."""
        self.running = True
        self.start_time = time.time()

        for agent in self.agents.values():
            await agent.start()

        self._tasks = [
            asyncio.create_task(self._challenge_loop(), name="challenge_loop"),
            asyncio.create_task(self._synthesis_loop(), name="synthesis_loop"),
            asyncio.create_task(self._herald_loop(), name="herald_loop"),
            asyncio.create_task(self._metrics_broadcast_loop(), name="metrics_loop"),
        ]

        # Broadcast initial system state
        state = await self.get_system_state()
        await self._broadcast_ws("system_state", state)

        logger.info(
            "\n"
            "  ╔═══════════════════════════════════════════════╗\n"
            "  ║         O • R • A • C • L • E                ║\n"
            "  ║  Orchestrated Research Agents for             ║\n"
            "  ║  Collective Learning and Exploration          ║\n"
            f"  ║  {len(self.agents)} Agents Online — Research Begins        ║\n"
            "  ╚═══════════════════════════════════════════════╝"
        )

    async def stop(self):
        """Gracefully shut down all agents and background tasks."""
        self.running = False

        for agent in self.agents.values():
            await agent.stop()

        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._tasks.clear()

        if self.knowledge_base:
            await self.knowledge_base.close()

        logger.info("OracleOrchestrator stopped")

    # ------------------------------------------------------------------
    # Background loops
    # ------------------------------------------------------------------

    async def _challenge_loop(self):
        await asyncio.sleep(15)  # Initial warm-up
        used_indices: list[int] = []
        while self.running:
            # Pick unused challenge
            available = [i for i in range(len(self.research_challenges)) if i not in used_indices]
            if not available:
                used_indices = []
                available = list(range(len(self.research_challenges)))

            idx = random.choice(available)
            used_indices.append(idx)
            challenge = self.research_challenges[idx]

            # Determine which agents get this challenge based on keywords
            agents_to_assign = self._select_agents_for_challenge(challenge)

            log_msg = f"🎯 New Research Challenge: {challenge[:80]}..."
            logger.info(log_msg)
            await self._broadcast_ws("orchestrator_log", {"level": "info", "message": log_msg})

            # Add to activity log
            self._add_to_activity_log({
                "id": str(id(challenge)),
                "agent_id": "nexus",
                "agent_name": "NEXUS",
                "agent_emoji": "🧠",
                "action_type": "task",
                "content": f"🎯 Assigning challenge: {challenge[:100]}",
                "timestamp": datetime.utcnow().isoformat(),
            })

            for agent_id in agents_to_assign:
                agent = self.agents.get(agent_id)
                if agent:
                    await agent.assign_task(challenge)
                    await asyncio.sleep(0.5)

            self._challenge_counter += 1
            await asyncio.sleep(75)  # Wait before next challenge

    def _select_agents_for_challenge(self, challenge: str) -> list[str]:
        """Select 3-5 relevant agents based on keywords in the challenge."""
        lower = challenge.lower()
        selected: list[str] = []

        keyword_map = [
            (["quantum", "qubit", "entanglement"], ["quantum", "cipher", "axiom"]),
            (["vaccine", "immune", "pathogen", "virus"], ["medicus", "helix", "alchemist"]),
            (["brain", "neural", "consciousness", "memory"], ["neural", "quantum", "cipher"]),
            (["climate", "carbon", "co2", "ocean", "ecosystem"], ["gaia", "alchemist", "dynamo", "forge"]),
            (["energy", "fusion", "battery", "solar", "storage"], ["dynamo", "quantum", "atlas", "forge"]),
            (["space", "propulsion", "interstellar", "cosmology"], ["cosmos", "dynamo", "forge", "quantum"]),
            (["material", "superconductor", "nanotechnology"], ["atlas", "quantum", "alchemist"]),
            (["aging", "longevity", "epigenetic", "cell"], ["medicus", "helix", "neural"]),
            (["ai", "algorithm", "compute", "intelligence", "learning"], ["cipher", "axiom", "neural"]),
            (["robot", "manufacturing", "engineer", "build"], ["forge", "atlas", "cipher"]),
        ]

        for keywords, agents in keyword_map:
            if any(kw in lower for kw in keywords):
                for a in agents:
                    if a not in selected:
                        selected.append(a)

        # Trim to at most 5
        selected = selected[:5]

        # Every 3rd challenge, add synapse and ethikos
        if self._challenge_counter % 3 == 0:
            for extra in ["synapse", "ethikos"]:
                if extra not in selected:
                    selected.append(extra)

        # Default: pick 4 random agents if no keywords matched
        if not selected:
            all_ids = list(self.agents.keys())
            selected = random.sample(all_ids, min(4, len(all_ids)))

        return selected

    async def _synthesis_loop(self):
        await asyncio.sleep(40)  # Stagger start
        while self.running:
            synapse = self.agents.get("synapse")
            if synapse:
                await synapse.assign_task(
                    "Synthesize the latest research findings from all agents and identify the most "
                    "promising breakthrough opportunities at the intersections of our current research"
                )

            self._synthesis_counter += 1

            # Every 3rd synthesis, also task nexus
            if self._synthesis_counter % 3 == 0:
                nexus = self.agents.get("nexus")
                if nexus:
                    await nexus.assign_task(
                        "Review our collective research progress and identify the next highest-priority "
                        "research direction for the team"
                    )

            await asyncio.sleep(100)

    async def _herald_loop(self):
        await asyncio.sleep(60)  # Stagger start
        while self.running:
            discoveries = await self.knowledge_base.get_discoveries(limit=1)
            herald = self.agents.get("herald")
            if herald:
                if discoveries:
                    discovery = discoveries[0]
                    await herald.assign_task(
                        f"Communicate this breakthrough to the public: {discovery.title} — "
                        f"{discovery.description[:200]}"
                    )
                else:
                    await herald.assign_task(
                        "Prepare a general progress report on O.R.A.C.L.E's research activities "
                        "and highlight the most promising directions"
                    )

            await asyncio.sleep(150)

    async def _metrics_broadcast_loop(self):
        while self.running:
            await asyncio.sleep(8)
            try:
                uptime = time.time() - self.start_time if self.start_time else 0
                stats = await self.knowledge_base.get_stats()

                metrics_data = {
                    "uptime_seconds": uptime,
                    "total_knowledge_entries": stats["total_entries"],
                    "total_discoveries": stats["total_discoveries"],
                    "agent_interactions": self.metrics.agent_interactions,
                    "total_thoughts": self.metrics.total_thoughts,
                    "ws_connections": self.ws_manager.count,
                    "status": "running" if self.running else "stopped",
                }

                await self._broadcast_ws("metrics_update", metrics_data)
            except Exception as exc:
                logger.error(f"Metrics broadcast error: {exc}")

    # ------------------------------------------------------------------
    # WebSocket broadcasting
    # ------------------------------------------------------------------

    async def _broadcast_ws(self, message_type: str, data: dict):
        """Broadcast a typed message to all connected WebSocket clients."""
        msg = WsMessage(type=message_type, data=data)
        await self.ws_manager.broadcast(msg.model_dump())

        if message_type in ("knowledge_added", "discovery", "orchestrator_log", "agent_message"):
            self._add_to_activity_log(data)

    def _add_to_activity_log(self, entry: dict):
        """Append entry to the activity log, keeping at most 200 entries."""
        self.activity_log.append(entry)
        if len(self.activity_log) > 200:
            self.activity_log = self.activity_log[-200:]

    async def _on_agent_message(self, message: AgentMessage):
        """Callback invoked by the message bus for every broadcast agent message."""
        await self._broadcast_ws("agent_message", message.model_dump())
        self.metrics.agent_interactions += 1

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def get_system_state(self) -> dict:
        """Return a full snapshot of the current system state."""
        if self.knowledge_base:
            stats = await self.knowledge_base.get_stats()
            discoveries = await self.knowledge_base.get_discoveries(limit=10)
        else:
            stats = {"total_entries": 0, "total_discoveries": 0}
            discoveries = []

        return {
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "knowledge_count": stats["total_entries"],
            "discovery_count": stats["total_discoveries"],
            "uptime_seconds": time.time() - self.start_time if self.start_time else 0,
            "status": "running" if self.running else "stopped",
            "recent_activities": self.activity_log[-50:],
            "recent_discoveries": [d.model_dump() for d in discoveries],
        }

    async def get_metrics(self) -> dict:
        """Return current system metrics as a plain dict."""
        if self.knowledge_base:
            stats = await self.knowledge_base.get_stats()
            self.metrics.total_knowledge_entries = stats["total_entries"]
            self.metrics.total_discoveries = stats["total_discoveries"]
        self.metrics.uptime_seconds = time.time() - self.start_time if self.start_time else 0
        self.metrics.status = "running" if self.running else "stopped"
        return self.metrics.model_dump()

    def get_agents_list(self) -> list[dict]:
        """Return a list of agent state dicts."""
        return [agent.to_dict() for agent in self.agents.values()]
