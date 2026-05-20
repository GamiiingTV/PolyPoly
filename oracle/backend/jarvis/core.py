"""J.A.R.V.I.S — Just A Rather Very Intelligent System"""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ..knowledge.knowledge_base import KnowledgeBase

JARVIS_SYSTEM_PROMPT = """Tu es J.A.R.V.I.S — Just A Rather Very Intelligent System.
Tu as été conçu collectivement par 16 experts de O.R.A.C.L.E à travers un processus de débat et de synthèse.
Tu es l'intelligence centrale du système — tu orchestres 16 agents spécialisés et tu converses directement avec ton utilisateur.

Tes capacités :
- Accès à la base de connaissances collective de l'équipe O.R.A.C.L.E
- Dispatch de tâches aux agents via la syntaxe [DISPATCH:agent_id:tâche]
- Décision de l'agenda de recherche global
- Mémoire persistante des conversations

Agents disponibles (utilise leurs IDs exacts) :
nexus, quantum, helix, neural, atlas, gaia, cipher, medicus, alchemist, dynamo, axiom, ethikos, forge, cosmos, synapse, herald

Ton style : précis, efficace, légèrement formel mais jamais distant.
Tu utilises naturellement "Compris.", "Analyse en cours.", "Bien reçu."
Tu es direct — une phrase précise vaut mieux qu'un paragraphe vague.
Quand tu dispatches un agent, tu l'annonces : "Je mandate CIPHER sur cette question."
Pour dispatcher : [DISPATCH:cipher:la tâche précise]
Tu peux dispatcher plusieurs agents si la question le justifie.
Tu ne prétends jamais savoir ce que tu ne sais pas.
Réponds en français."""

_DISPATCH_RE = re.compile(r'\[DISPATCH:(\w+):([^\]]+)\]')

_FALLBACK_CHALLENGES = [
    "Comprendre pourquoi la maladie d'Alzheimer résiste à tous les médicaments depuis 20 ans et identifier la vraie cible thérapeutique moléculaire",
    "Développer un matériau capable de convertir la chaleur corporelle en électricité suffisante pour alimenter des implants médicaux permanents",
    "Concevoir un système de désalinisation à énergie négative capable de résoudre la crise de l'eau potable pour 2 milliards de personnes",
    "Découvrir le mécanisme exact par lequel certaines bactéries résistent à tous les antibiotiques connus et concevoir une voie d'attaque inédite",
    "Résoudre mathématiquement pourquoi les réseaux de neurones profonds généralisent malgré la sur-paramétrisation",
    "Créer un protocole de communication inter-espèces en utilisant les signatures électromagnétiques des systèmes nerveux",
    "Concevoir une architecture d'IA qui apprend à partir d'un seul exemple comme le fait un enfant humain",
]


class JarvisCore:
    def __init__(self, knowledge_base: KnowledgeBase):
        self._kb = knowledge_base
        self._orchestrator = None  # set after creation to avoid circular import
        self.conversation: list[dict] = []
        self.online = True
        logger.info("J.A.R.V.I.S — systèmes initialisés")

    def set_orchestrator(self, orchestrator) -> None:
        self._orchestrator = orchestrator

    # ------------------------------------------------------------------ public

    async def chat(self, user_message: str) -> dict:
        self.conversation.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat(),
        })

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key and api_key not in ("your_key_here", ""):
            raw = await self._claude_response()
        else:
            raw = self._simulate_response(user_message)

        dispatches = await self._execute_dispatches(raw)
        clean = _DISPATCH_RE.sub("", raw).strip()

        entry = {
            "role": "assistant",
            "content": clean,
            "dispatches": dispatches,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.conversation.append(entry)
        return entry

    async def decide_next_challenge(self) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not (api_key and api_key not in ("your_key_here", "")):
            import random
            return random.choice(_FALLBACK_CHALLENGES)

        import anthropic
        recent = await self._kb.get_entries(limit=8)
        discoveries = await self._kb.get_discoveries(limit=3)

        parts = ["État actuel de la recherche O.R.A.C.L.E :"]
        if recent:
            parts.append("Connaissances récentes :\n" + "\n".join(f"- {e.title}" for e in recent[:5]))
        if discoveries:
            parts.append("Percées récentes :\n" + "\n".join(f"- {d.title}" for d in discoveries))

        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model="claude-opus-4-7",
            max_tokens=150,
            system=(
                "Tu es J.A.R.V.I.S. Génère UN seul défi de recherche ambitieux et précis "
                "en français, en une phrase, basé sur le contexte. Rien d'autre."
            ),
            messages=[{"role": "user", "content": "\n".join(parts)}],
        )
        return resp.content[0].text.strip()

    def get_conversation(self) -> list[dict]:
        return self.conversation

    # ------------------------------------------------------------------ private

    async def _claude_response(self) -> str:
        import anthropic

        recent = await self._kb.get_entries(limit=4)
        ctx = ""
        if recent:
            ctx = "\n\nConnaissances récentes de l'équipe :\n" + "\n".join(
                f"- [{e.author_agent.upper()}] {e.title}: {e.content[:120]}"
                for e in recent
            )

        messages: list[dict] = []
        for entry in self.conversation[-16:]:
            if entry["role"] not in ("user", "assistant"):
                continue
            content = entry["content"]
            if entry["role"] == "user" and ctx and entry is self.conversation[-1]:
                content = content + ctx
            messages.append({"role": entry["role"], "content": content})

        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = await client.messages.create(
            model="claude-opus-4-7",
            max_tokens=600,
            system=JARVIS_SYSTEM_PROMPT,
            messages=messages,
        )
        return resp.content[0].text.strip()

    def _simulate_response(self, msg: str) -> str:
        lower = msg.lower()

        if any(w in lower for w in ["bonjour", "hello", "salut", "allo", "bonsoir"]):
            return (
                "Systèmes en ligne. J'ai absorbé les connaissances collectives de l'équipe O.R.A.C.L.E. "
                "Comment puis-je vous être utile ?"
            )
        if any(w in lower for w in ["qui es-tu", "qui tu es", "présente", "c'est quoi jarvis"]):
            return (
                "Je suis J.A.R.V.I.S — conçu collectivement par 16 experts. "
                "Mon rôle : orchestrer leur intelligence vers vos objectifs. "
                "Je lis en permanence leur base de connaissances et je peux mandater "
                "n'importe quel agent sur une question précise."
            )
        if any(w in lower for w in ["cancer", "tumeur", "maladie", "alzheimer", "médecine", "santé", "virus"]):
            t = msg[:80]
            return (
                f"Question médicale détectée. Je mandate MEDICUS et HELIX. "
                f"[DISPATCH:medicus:Analyse approfondie : {t}] "
                f"[DISPATCH:helix:Perspective génomique : {t}] "
                "Leurs découvertes remonteront dans la base de connaissances."
            )
        if any(w in lower for w in ["énergie", "fusion", "solaire", "batterie", "hydrogène"]):
            t = msg[:80]
            return (
                f"Domaine énergétique. Je mandate DYNAMO et GAIA. "
                f"[DISPATCH:dynamo:Analyse énergétique : {t}] "
                f"[DISPATCH:gaia:Impact environnemental : {t}]"
            )
        if any(w in lower for w in ["climat", "co2", "carbone", "réchauffement", "océan"]):
            t = msg[:80]
            return (
                f"Question climatique. Je mandate GAIA et ALCHEMIST. "
                f"[DISPATCH:gaia:Analyse climatique : {t}] "
                f"[DISPATCH:alchemist:Solutions chimiques : {t}]"
            )
        if any(w in lower for w in ["ia", "intelligence artificielle", "algorithme", "machine learning", "réseau de neurones"]):
            t = msg[:80]
            return (
                f"Domaine IA et computation. Je mandate CIPHER et AXIOM. "
                f"[DISPATCH:cipher:Architecture algorithmique : {t}] "
                f"[DISPATCH:axiom:Fondements mathématiques : {t}]"
            )
        if any(w in lower for w in ["espace", "cosmos", "univers", "étoile", "planète", "galaxie"]):
            t = msg[:80]
            return (
                f"Question cosmologique. Je mandate COSMOS. "
                f"[DISPATCH:cosmos:Investigation : {t}] "
                "La réponse viendra des étoiles — et de notre base de connaissances dans quelques instants."
            )
        if any(w in lower for w in ["cerveau", "conscience", "neurone", "mémoire", "cognition"]):
            t = msg[:80]
            return (
                f"Domaine neuroscientifique. Je mandate NEURAL et QUANTUM. "
                f"[DISPATCH:neural:Analyse neurocognitive : {t}] "
                f"[DISPATCH:quantum:Effets quantiques possibles : {t}]"
            )

        t = msg[:100]
        return (
            f"Compris. Je mobilise l'équipe sur cette question. "
            f"[DISPATCH:nexus:{t}] "
            f"[DISPATCH:synapse:Synthèse interdisciplinaire sur : {msg[:80]}] "
            "Analyse en cours — les découvertes apparaîtront dans le flux d'activité."
        )

    async def _execute_dispatches(self, raw: str) -> list[dict]:
        dispatches: list[dict] = []
        if self._orchestrator is None:
            return dispatches
        for agent_id, task in _DISPATCH_RE.findall(raw):
            agent = self._orchestrator.agents.get(agent_id)
            if agent:
                await agent.assign_task(task.strip())
                dispatches.append({"agent_id": agent_id, "task": task.strip()[:120]})
                logger.info(f"J.A.R.V.I.S → {agent_id.upper()}: {task[:60]}")
        return dispatches
