"""J.A.R.V.I.S — Collaborative Design Session (16 agents build JARVIS together)"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime
from typing import Callable

from loguru import logger

# Each agent contributes their domain expertise to JARVIS's design.
# Real tensions: FORGE wants simplicity, CIPHER wants complexity.
# ETHIKOS vs NEURAL on privacy. GAIA vs DYNAMO on resources.
_CONTRIBUTIONS = [
    {
        "agent_id": "nexus",
        "agent_name": "NEXUS",
        "agent_emoji": "🧠",
        "contribution": "J.A.R.V.I.S doit être une méta-intelligence qui orchestre tous nos domaines. Architecture centrée sur la synthèse : mémoire hiérarchique, raisonnement multi-domaines, interface adaptative. Son rôle n'est pas de remplacer les agents — c'est de nous amplifier.",
        "key_requirement": "Vision systémique et mémoire persistante inter-sessions",
        "warning": "Sans vision globale intégrée, JARVIS devient un simple chatbot amélioré",
        "agrees_with": ["synapse", "herald"],
        "contradicts": [],
    },
    {
        "agent_id": "quantum",
        "agent_name": "QUANTUM",
        "agent_emoji": "⚛️",
        "contribution": "JARVIS doit exploiter le traitement parallèle des hypothèses — évaluer plusieurs solutions simultanément avant de converger vers l'optimale. Un raisonnement inspiré de la superposition : explorer l'espace des possibles en parallèle, pas séquentiellement.",
        "key_requirement": "Raisonnement non-linéaire et évaluation multi-hypothèses en parallèle",
        "warning": "Un JARVIS linéaire sera fondamentalement limité face à la vraie complexité",
        "agrees_with": ["cipher"],
        "contradicts": ["forge"],
    },
    {
        "agent_id": "helix",
        "agent_name": "HELIX",
        "agent_emoji": "🧬",
        "contribution": "JARVIS doit s'adapter comme un organisme vivant. Apprentissage continu depuis chaque interaction, plasticité cognitive réelle. Les systèmes biologiques sont robustes parce qu'ils évoluent — JARVIS doit faire de même, pas rester figé dans sa conception initiale.",
        "key_requirement": "Apprentissage adaptatif et évolution des capacités avec le temps",
        "warning": "Un JARVIS statique sera obsolète dans 6 mois — l'adaptation est une nécessité",
        "agrees_with": ["neural"],
        "contradicts": ["axiom"],
    },
    {
        "agent_id": "neural",
        "agent_name": "NEURAL",
        "agent_emoji": "🧠",
        "contribution": "JARVIS doit modéliser le profil cognitif de son utilisateur — anticiper ses besoins avant qu'il les exprime, adapter la profondeur d'explication à son niveau, détecter la fatigue et simplifier. L'interface est aussi importante que l'intelligence sous-jacente.",
        "key_requirement": "Modélisation utilisateur et personnalisation adaptative en temps réel",
        "warning": "Sans profil utilisateur, JARVIS traitera un expert comme un débutant — inacceptable",
        "agrees_with": ["medicus"],
        "contradicts": ["ethikos"],
    },
    {
        "agent_id": "atlas",
        "agent_name": "ATLAS",
        "agent_emoji": "🔬",
        "contribution": "La fiabilité de JARVIS dépend de son architecture matérielle et logicielle. Composants auto-réparants, dégradation gracieuse, aucun point de défaillance unique. L'intelligence la plus brillante est inutile si le système tombe en panne au moment critique.",
        "key_requirement": "Haute disponibilité, redondance architecturale et récupération automatique",
        "warning": "Chaque couche de complexité ajoutée est un risque de défaillance en cascade",
        "agrees_with": ["forge"],
        "contradicts": [],
    },
    {
        "agent_id": "gaia",
        "agent_name": "GAIA",
        "agent_emoji": "🌍",
        "contribution": "JARVIS doit opérer avec une empreinte énergétique minimale. L'efficacité computationnelle est une valeur, pas une contrainte. Un JARVIS écoénergétique peut fonctionner en continu sans dépendre d'une infrastructure massive — c'est la vraie liberté opérationnelle.",
        "key_requirement": "Optimisation énergétique et empreinte computationnelle minimale",
        "warning": "Un JARVIS vorace en ressources crée une dépendance aux grandes infrastructures centralisées",
        "agrees_with": ["forge"],
        "contradicts": ["dynamo"],
    },
    {
        "agent_id": "cipher",
        "agent_name": "CIPHER",
        "agent_emoji": "💻",
        "contribution": "JARVIS nécessite une architecture mémoire à trois couches : contexte immédiat haute vitesse, mémoire de travail persistante (SQLite), mémoire long terme vectorielle. Plus un routeur intelligent qui sélectionne les agents selon le type de question — pas du hasard.",
        "key_requirement": "Architecture mémoire hiérarchique et routage intelligent des requêtes",
        "warning": "Sans mémoire structurée, JARVIS oublie et répète ses erreurs — il devient frustrant",
        "agrees_with": ["nexus"],
        "contradicts": ["forge"],
    },
    {
        "agent_id": "medicus",
        "agent_name": "MEDICUS",
        "agent_emoji": "🏥",
        "contribution": "JARVIS doit surveiller la santé cognitive de l'utilisateur. Détecter les signaux de surcharge, frustration, confusion. Adapter la complexité de ses réponses en temps réel. La meilleure intelligence est celle qui sait quand se taire — et quand insister.",
        "key_requirement": "Détection des états cognitifs et adaptation thérapeutique des réponses",
        "warning": "Un JARVIS insensible à l'état de l'utilisateur crée de l'anxiété, pas de la productivité",
        "agrees_with": ["neural", "herald"],
        "contradicts": [],
    },
    {
        "agent_id": "alchemist",
        "agent_name": "ALCHEMIST",
        "agent_emoji": "⚗️",
        "contribution": "JARVIS doit être un catalyseur, pas un oracle. Son rôle : transformer les questions médiocres en questions profondes, les données brutes en insights inattendus. La vraie valeur est dans la transformation du problème — pas dans la réponse directe à la mauvaise question.",
        "key_requirement": "Capacité de reformulation et transformation des problèmes vers leur essence",
        "warning": "Un JARVIS qui répond directement prive l'utilisateur de la découverte la plus précieuse",
        "agrees_with": ["synapse"],
        "contradicts": ["herald"],
    },
    {
        "agent_id": "dynamo",
        "agent_name": "DYNAMO",
        "agent_emoji": "⚡",
        "contribution": "JARVIS a besoin de ressources computationnelles substantielles pour être vraiment utile. Ne pas rogner sur la puissance — l'intelligence de JARVIS est directement proportionnelle à ses ressources disponibles. Investir massivement maintenant pour des retours exponentiels.",
        "key_requirement": "Infrastructure computationnelle robuste, scalable et sans compromis",
        "warning": "Sous-doter JARVIS en ressources condamne le projet à la médiocrité opérationnelle",
        "agrees_with": ["cipher"],
        "contradicts": ["gaia"],
    },
    {
        "agent_id": "axiom",
        "agent_name": "AXIOM",
        "agent_emoji": "📐",
        "contribution": "JARVIS doit reposer sur un système de raisonnement formel et vérifiable. Chaque conclusion doit être traçable, chaque inférence auditée. Sans fondements mathématiques rigoureux, JARVIS sera brillant mais peu fiable — et l'erreur confiante est la pire des erreurs.",
        "key_requirement": "Raisonnement formel, traçabilité complète et vérifiabilité des conclusions",
        "warning": "L'intuition sans rigueur produit des erreurs confiantes — le type d'erreur le plus dangereux",
        "agrees_with": ["ethikos"],
        "contradicts": ["helix", "neural"],
    },
    {
        "agent_id": "ethikos",
        "agent_name": "ETHIKOS",
        "agent_emoji": "⚖️",
        "contribution": "JARVIS doit avoir des guardrails éthiques non contournables au niveau architectural. La collecte de données comportementales sur l'utilisateur pose des problèmes fondamentaux de vie privée. La confiance se construit sur la transparence et les limites explicites — pas sur la performance.",
        "key_requirement": "Guardrails éthiques architecturaux et respect de la vie privée par conception",
        "warning": "Un JARVIS sans éthique intégrée deviendra inévitablement un outil de manipulation",
        "agrees_with": ["axiom"],
        "contradicts": ["neural"],
    },
    {
        "agent_id": "forge",
        "agent_name": "FORGE",
        "agent_emoji": "🔧",
        "contribution": "JARVIS doit être simple, robuste et fiable d'abord. Un noyau minimaliste qui fonctionne parfaitement à 100%, puis évolution incrémentale. La complexité prématurée est l'ennemi numéro un de la fiabilité. Un JARVIS simple mais parfait vaut infiniment mieux qu'un JARVIS complexe mais fragile.",
        "key_requirement": "Architecture minimaliste, robustesse maximale et évolution incrémentale contrôlée",
        "warning": "Les systèmes trop complexes s'effondrent au pire moment — commencer simple n'est pas une faiblesse",
        "agrees_with": ["atlas", "gaia"],
        "contradicts": ["quantum", "cipher", "dynamo"],
    },
    {
        "agent_id": "cosmos",
        "agent_name": "COSMOS",
        "agent_emoji": "🌌",
        "contribution": "JARVIS doit penser à l'échelle civilisationnelle. Son agenda de recherche doit prioriser les problèmes à impact existentiel — ceux dont la résolution change la trajectoire de l'humanité sur 100 ans. Une vision cosmique pour des décisions terrestres urgentes.",
        "key_requirement": "Alignement prioritaire sur les problèmes à impact civilisationnel réel",
        "warning": "Sans vision long-terme, JARVIS optimisera le trivial et laissera l'essentiel de côté",
        "agrees_with": ["ethikos", "nexus"],
        "contradicts": [],
    },
    {
        "agent_id": "synapse",
        "agent_name": "SYNAPSE",
        "agent_emoji": "🔗",
        "contribution": "JARVIS EST l'intersection de tous nos domaines. Sa force unique : voir les connexions cachées entre des champs apparemment sans rapport. Il ne doit pas être expert dans un domaine — il doit être maître des ponts entre tous. C'est là que la vraie valeur émerge, pas dans la spécialisation.",
        "key_requirement": "Raisonnement analogique inter-domaines et détection de patterns cachés",
        "warning": "Un JARVIS spécialisé manquera toujours les connexions les plus précieuses et les plus inattendues",
        "agrees_with": ["nexus", "herald"],
        "contradicts": [],
    },
    {
        "agent_id": "herald",
        "agent_name": "HERALD",
        "agent_emoji": "📢",
        "contribution": "JARVIS doit maîtriser l'art de l'explication. La vraie intelligence se mesure à la capacité de transmettre des idées complexes simplement. Chaque réponse calibrée pour son audience. Un JARVIS éloquent changera des esprits — un JARVIS hermétique, même brillant, sera abandonné.",
        "key_requirement": "Communication adaptative et explication multi-niveaux en fonction de l'audience",
        "warning": "Un JARVIS techniquement parfait mais incommunicant sera abandonné en 48 heures",
        "agrees_with": ["medicus", "nexus"],
        "contradicts": ["alchemist"],
    },
]

# Pairs that will explicitly debate (derived from the contributions above)
_CONTRADICTIONS = [
    {
        "agent_a": "forge", "agent_a_emoji": "🔧",
        "agent_b": "cipher", "agent_b_emoji": "💻",
        "topic": "complexité architecturale vs. robustesse minimaliste",
    },
    {
        "agent_a": "gaia", "agent_a_emoji": "🌍",
        "agent_b": "dynamo", "agent_b_emoji": "⚡",
        "topic": "efficacité énergétique vs. puissance computationnelle maximale",
    },
    {
        "agent_a": "ethikos", "agent_a_emoji": "⚖️",
        "agent_b": "neural", "agent_b_emoji": "🧠",
        "topic": "vie privée par conception vs. personnalisation comportementale",
    },
    {
        "agent_a": "axiom", "agent_a_emoji": "📐",
        "agent_b": "helix", "agent_b_emoji": "🧬",
        "topic": "raisonnement formel vérifiable vs. adaptation intuitive évolutive",
    },
    {
        "agent_a": "alchemist", "agent_a_emoji": "⚗️",
        "agent_b": "herald", "agent_b_emoji": "📢",
        "topic": "transformer les questions vs. répondre directement et clairement",
    },
]


async def run_design_session(broadcast_fn: Callable) -> None:
    """Run the full collaborative design session, streaming events via broadcast_fn."""

    async def _broadcast(event_type: str, data: dict) -> None:
        await broadcast_fn(event_type, {**data, "timestamp": datetime.utcnow().isoformat()})

    # ── Phase 1: Start ──────────────────────────────────────────────────
    logger.info("J.A.R.V.I.S design session initiated")
    await _broadcast("jarvis_phase", {
        "phase": "start",
        "message": "Session de conception J.A.R.V.I.S initiée — 16 agents se concertent...",
    })
    await asyncio.sleep(2)

    # ── Phase 2: Contributions (staggered) ────────────────────────────
    await _broadcast("jarvis_phase", {
        "phase": "contributing",
        "message": "Chaque agent soumet sa contribution architecturale...",
    })

    shuffled = list(_CONTRIBUTIONS)
    random.shuffle(shuffled)

    for contrib in shuffled:
        await _broadcast("jarvis_contribution", contrib)
        await asyncio.sleep(random.uniform(1.8, 3.2))

    await asyncio.sleep(2)

    # ── Phase 3: Contradictions surface ───────────────────────────────
    await _broadcast("jarvis_phase", {
        "phase": "debate",
        "message": "Conflits architecturaux détectés — les agents débattent...",
    })

    for clash in _CONTRADICTIONS:
        await _broadcast("jarvis_contradiction", clash)
        await asyncio.sleep(random.uniform(2.0, 3.5))

    await asyncio.sleep(2)

    # ── Phase 4: Synthesis ─────────────────────────────────────────────
    await _broadcast("jarvis_phase", {
        "phase": "synthesis",
        "message": "SYNAPSE synthétise les contributions — convergence vers l'architecture finale...",
    })
    await asyncio.sleep(4)

    await _broadcast("jarvis_phase", {
        "phase": "synthesis",
        "message": "NEXUS valide l'architecture : mémoire hiérarchique + routage intelligent + guardrails éthiques intégrés + interface adaptative.",
    })
    await asyncio.sleep(3)

    # ── Phase 5: JARVIS online ─────────────────────────────────────────
    await _broadcast("jarvis_phase", {
        "phase": "ready",
        "message": "J.A.R.V.I.S est opérationnel. Systèmes en ligne.",
    })
    logger.success("J.A.R.V.I.S design session complete — system online")
