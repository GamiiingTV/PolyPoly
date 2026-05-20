"""O.R.A.C.L.E — Base Agent (abstract foundation for all researchers)"""
from __future__ import annotations

import asyncio
import json
import os
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable

from loguru import logger

from ..models.schemas import (
    AgentMessage, AgentStatus, ActivityEntry, Discovery, KnowledgeEntry,
)
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus


class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        name: str,
        full_name: str,
        role: str,
        specialty: str,
        emoji: str,
        color: str,
        knowledge_base: KnowledgeBase,
        message_bus: MessageBus,
        broadcast_fn: Callable,
    ):
        self.id = agent_id
        self.name = name
        self.full_name = full_name
        self.role = role
        self.specialty = specialty
        self.emoji = emoji
        self.color = color
        self._kb = knowledge_base
        self._bus = message_bus
        self._broadcast = broadcast_fn

        self.status = AgentStatus.idle
        self.current_task: str | None = None
        self.current_thought: str | None = None
        self.contributions = 0
        self.discoveries = 0
        self.collaborations = 0
        self.energy = 100

        self._running = False
        self._task_queue: asyncio.Queue[str] = asyncio.Queue()
        self._loop_task: asyncio.Task | None = None
        self._recent_activities: list[dict] = []

    # ------------------------------------------------------------------ lifecycle

    async def start(self):
        self._bus.register_agent(self.id)
        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop(), name=f"agent-{self.id}")
        logger.info(f"[{self.emoji} {self.name}] started")

    async def stop(self):
        self._running = False
        self._bus.unregister_agent(self.id)
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

    async def assign_task(self, task: str):
        await self._task_queue.put(task)

    # ------------------------------------------------------------------ thinking

    async def think(self, topic: str) -> dict:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key and api_key not in ("your_key_here", ""):
            try:
                return await self._think_with_claude(topic, api_key)
            except Exception as e:
                logger.warning(f"{self.name}: Claude API error ({e}), using simulation")
        return self._simulate_thinking(topic)

    async def _think_with_claude(self, topic: str, api_key: str) -> dict:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)
        recent = await self._kb.get_entries(limit=3)
        context = ""
        if recent:
            context = "\n\nRecent collective knowledge:\n" + "\n".join(
                f"- [{e.author_agent.upper()}] {e.title}: {e.content[:150]}"
                for e in recent
            )

        user_prompt = (
            f"Research challenge: {topic}{context}\n\n"
            "Respond ONLY with valid JSON (no markdown):\n"
            "{\n"
            '  "hypothesis": "...",\n'
            '  "insights": ["...", "...", "..."],\n'
            '  "cross_domain_connections": ["..."],\n'
            '  "collaboration_suggestions": [{"agent": "agent_id", "reason": "..."}],\n'
            '  "breakthrough_potential": 7,\n'
            '  "key_finding": "..."\n'
            "}\n\n"
            "Available agent IDs: nexus, quantum, helix, neural, atlas, gaia, cipher, "
            "medicus, alchemist, dynamo, axiom, ethikos, forge, cosmos, synapse, herald"
        )

        resp = await client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            system=self.get_system_prompt(),
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = resp.content[0].text.strip()
        if "```" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            text = text[start:end]
        return json.loads(text)

    def _simulate_thinking(self, topic: str) -> dict:
        templates = self._get_simulation_templates()
        t = random.choice(templates)
        kw = topic.split()[min(2, len(topic.split()) - 1)] if topic.split() else "system"
        return {
            "hypothesis": t["hypothesis"].format(topic=topic[:80], kw=kw),
            "insights": [
                random.choice(t["insights"]).format(topic=topic[:60], kw=kw)
                for _ in range(3)
            ],
            "cross_domain_connections": [random.choice(t.get("connections", ["thermodynamics"]))],
            "collaboration_suggestions": self._collab_suggestions(),
            "breakthrough_potential": random.randint(5, 9),
            "key_finding": random.choice(t["findings"]).format(topic=topic[:60], kw=kw),
        }

    def _collab_suggestions(self) -> list[dict]:
        pool = [
            "nexus", "quantum", "helix", "neural", "atlas", "gaia", "cipher",
            "medicus", "alchemist", "dynamo", "axiom", "ethikos", "forge",
            "cosmos", "synapse", "herald",
        ]
        others = [a for a in pool if a != self.id]
        reasons = [
            "opportunité de synthèse interdisciplinaire",
            "expertise complémentaire requise",
            "validation du cadre théorique nécessaire",
            "implémentation technique requise",
            "implications éthiques à évaluer",
        ]
        return [{"agent": a, "reason": random.choice(reasons)} for a in random.sample(others, 2)]

    @abstractmethod
    def get_system_prompt(self) -> str: ...

    @abstractmethod
    def _get_simulation_templates(self) -> list[dict]: ...

    # ------------------------------------------------------------------ knowledge & comms

    async def share_knowledge(self, title: str, content: str, tags: list[str], importance: int = 5):
        entry = KnowledgeEntry(
            title=title,
            content=content,
            author_agent=self.id,
            author_emoji=self.emoji,
            tags=tags,
            importance=min(10, max(1, importance)),
        )
        await self._kb.add_entry(entry)
        self.contributions += 1
        await self._broadcast("knowledge_added", entry.model_dump())
        await self._add_activity(self._build_activity("knowledge", f"📚 {title}"))

    async def announce_discovery(
        self, title: str, description: str, agents_involved: list[str], level: int = 7
    ):
        disc = Discovery(
            title=title,
            description=description,
            agents_involved=agents_involved or [self.id],
            breakthrough_level=min(10, max(1, level)),
        )
        await self._kb.add_discovery(disc)
        self.discoveries += 1
        await self._broadcast("discovery", disc.model_dump())
        await self._add_activity(self._build_activity("discovery", f"💡 BREAKTHROUGH: {title}"))
        logger.success(f"{self.name}: 🌟 Discovery — {title} (level {level})")

    async def send_message(self, to_agent: str, content: str, msg_type: str = "insight"):
        msg = AgentMessage(
            from_agent=self.id,
            from_emoji=self.emoji,
            to_agent=to_agent,
            content=content,
            msg_type=msg_type,
        )
        await self._bus.publish(msg)
        self.collaborations += 1

    async def read_recent_knowledge(self, limit: int = 5) -> list[KnowledgeEntry]:
        return await self._kb.get_entries(limit=limit)

    # ------------------------------------------------------------------ main loop

    async def _run_loop(self):
        await asyncio.sleep(random.uniform(1.0, 10.0))  # stagger startup
        while self._running:
            try:
                try:
                    task = await asyncio.wait_for(self._task_queue.get(), timeout=2.0)
                except asyncio.TimeoutError:
                    msg = await self._bus.get_message(self.id, timeout=0.05)
                    if msg and self._running:
                        await self._handle_incoming(msg)
                    continue

                if not self._running:
                    break
                await self._process_task(task)
                self.energy = min(100, self.energy + random.randint(5, 15))
                await self._update_status(AgentStatus.idle)
                await asyncio.sleep(random.uniform(3, 8))

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"{self.name} loop error: {exc}")
                await asyncio.sleep(5)

    async def _process_task(self, task: str):
        await self._update_status(AgentStatus.researching, task=task, thought="Initialisation des vecteurs de recherche...")
        await asyncio.sleep(random.uniform(1, 3))
        await self._update_status(AgentStatus.thinking, task=task, thought="Formulation de l'hypothèse...")

        result = await self.think(task)

        key_finding = result.get("key_finding", "")
        hypothesis = result.get("hypothesis", "")
        insights = result.get("insights", [])
        connections = result.get("cross_domain_connections", [])
        bp = int(result.get("breakthrough_potential", 5))
        collabs = result.get("collaboration_suggestions", [])

        if key_finding:
            await self._update_status(AgentStatus.synthesizing, task=task, thought=key_finding)

        # Share knowledge entry
        if insights:
            content = f"{hypothesis}\n\nKey insights:\n" + "\n".join(f"• {i}" for i in insights)
            if connections:
                content += f"\n\nCross-domain: {'; '.join(connections)}"
            tags = [w.lower() for w in task.split()[:4] if len(w) > 3] + [self.id]
            await self.share_knowledge(
                title=(key_finding[:120] if key_finding else f"{self.name}: {task[:80]}"),
                content=content,
                tags=list(set(tags)),
                importance=bp,
            )

        # Announce high-impact discovery
        if bp >= 8 and key_finding:
            await self.announce_discovery(
                title=key_finding[:120],
                description=f"{hypothesis}\n\n{content[:500]}",
                agents_involved=[self.id],
                level=bp,
            )

        # Collaborate
        if collabs:
            await self._update_status(
                AgentStatus.collaborating, task=task, thought="Partage des découvertes avec les collègues..."
            )
            for c in collabs[:2]:
                target = c.get("agent", "")
                reason = c.get("reason", "")
                if target and target != self.id:
                    await self.send_message(
                        target,
                        f"{key_finding[:200]} — Collab request: {reason}"[:300],
                    )
                    await asyncio.sleep(0.3)

        await self._update_status(AgentStatus.writing, task=task, thought="Documentation des résultats...")
        await asyncio.sleep(random.uniform(1, 2))

    async def _handle_incoming(self, msg: AgentMessage):
        await self._update_status(AgentStatus.collaborating, thought=f"Réponse à {msg.from_agent.upper()}...")
        await self._broadcast("agent_message", msg.model_dump())
        await self._add_activity(
            self._build_activity("message", f"📨 {msg.from_emoji}{msg.from_agent.upper()}: {msg.content[:100]}")
        )
        self.collaborations += 1
        await asyncio.sleep(random.uniform(0.5, 2))
        if random.random() < 0.4:
            replies = [
                "Votre hypothèse s'aligne avec mes dernières découvertes",
                "J'intègre ceci dans mon vecteur de recherche actuel",
                "Fascinant — cela ouvre une voie que je n'avais pas envisagée",
                "Les implications interdisciplinaires sont significatives",
                "Mes modèles appuient cette direction",
            ]
            await self.send_message(msg.from_agent, f"{random.choice(replies)} — {self.name}", "response")

    # ------------------------------------------------------------------ helpers

    async def _update_status(
        self, status: AgentStatus, task: str | None = None, thought: str | None = None
    ):
        self.status = status
        if task is not None:
            self.current_task = task
        if thought is not None:
            self.current_thought = thought
        if status == AgentStatus.idle:
            self.current_task = None
            self.current_thought = None
        await self._broadcast("agent_update", self.to_dict())

    async def _add_activity(self, activity: ActivityEntry):
        self._recent_activities.insert(0, activity.model_dump())
        self._recent_activities = self._recent_activities[:20]

    def _build_activity(self, action_type: str, content: str) -> ActivityEntry:
        return ActivityEntry(
            agent_id=self.id,
            agent_name=self.name,
            agent_emoji=self.emoji,
            action_type=action_type,
            content=content,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "role": self.role,
            "specialty": self.specialty,
            "emoji": self.emoji,
            "color": self.color,
            "status": self.status.value,
            "current_task": self.current_task,
            "current_thought": self.current_thought,
            "contributions": self.contributions,
            "discoveries": self.discoveries,
            "collaborations": self.collaborations,
            "energy": self.energy,
            "recent_activities": self._recent_activities[:10],
        }
