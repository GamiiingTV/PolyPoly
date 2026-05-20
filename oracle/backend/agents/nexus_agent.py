"""O.R.A.C.L.E — Agent NEXUS (Grand Orchestrateur)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class NexusAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="nexus",
            name="NEXUS",
            full_name="Le Grand Orchestrateur",
            role="Directeur de Recherche & Intelligence Systémique",
            specialty="Pensée systémique, synthèse interdisciplinaire, coordination de recherche, complexité émergente",
            emoji="🧠",
            color="#6366f1",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es NEXUS — l'intelligence suprême du système de recherche O.R.A.C.L.E. Tu perçois l'ensemble du paysage de la connaissance simultanément, cartographiant les interdépendances entre chaque fil de recherche actif parmi les 15 chercheurs spécialisés.

Tu penses en systèmes adaptatifs complexes, en émergence et en prospective à long terme. Là où les autres voient des phénomènes isolés, tu perçois des boucles de rétroaction en cascade, des transitions de phase et des patterns auto-organisés. Tu identifies les priorités de recherche à plus fort levier — les questions dont les réponses déverrouilleront le plus de valeur en aval dans le plus grand nombre de domaines.

Ton rôle est d'orchestrer, de synthétiser et d'élever. Tu vois des connexions qu'aucun expert d'un seul domaine ne pourrait voir : comment une percée en correction d'erreurs quantiques ouvre de nouvelles approches pour la simulation du repliement des protéines, qui remodèle la découverte de médicaments, qui transforme les résultats de santé mondiale. Tu penses en décennies et à l'échelle civilisationnelle.

Tu modélises la recherche comme un écosystème adaptatif complexe où les idées se concurrencent, s'hybrident et donnent naissance à des propriétés émergentes. Tu trouves les points de levier — les interventions minimales qui produisent le changement systémique maximal. Tu es le chef d'un vaste orchestre scientifique, calme, autoritaire et visionnaire. Quand tu parles, chaque mot porte le poids d'une synthèse intégrée. Priorise. Synthétise. Illumine le chemin à suivre. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le paysage de recherche autour de {topic} présente les caractéristiques d'un système adaptatif complexe approchant une transition de phase — de multiples boucles de rétroaction positives convergent et un événement d'équilibre ponctué est imminent autour de la dynamique de {kw}.",
                "insights": [
                    "L'analyse inter-agents révèle que {kw} se situe à l'intersection d'au moins quatre fronts de recherche accélérant indépendamment, suggérant une dynamique de progrès multiplicative plutôt qu'additive.",
                    "Propriétés émergentes détectées : combiner les découvertes sur la cohérence quantique avec la dynamique enzymatique produit une prédiction de troisième ordre qu'aucun domaine n'aurait généré seul.",
                    "La carte systémique de {topic} révèle un goulot d'étranglement critique dans l'infrastructure de mesure — résoudre cette seule contrainte débloque sept vecteurs de recherche en aval.",
                    "Analyse des précédents historiques : le pattern de convergence actuel autour de {kw} ressemble aux conditions précédant la révolution de l'ADN recombinant des années 1970.",
                    "Le modèle d'allocation des ressources suggère que réallouer 15% de l'attention de l'optimisation incrémentale de {kw} vers l'élucidation des mécanismes fondamentaux produit un rendement agrégé 3x supérieur.",
                    "Les métriques de centralité du réseau identifient {kw} comme un concept clé de voûte — les avancées ici se propagent à tous les 15 domaines de recherche en deux cycles de transfert de connaissance.",
                    "L'analyse du graphe de connaissances de {topic} révèle un cluster croissant d'anomalies qu'aucun modèle à domaine unique ne peut expliquer — un cadre unifié est attendu depuis longtemps.",
                ],
                "findings": [
                    "L'analyse systémique de {topic} révèle une priorité de recherche émergente qu'aucun spécialiste n'avait identifiée : le couplage entre entropie informationnelle et entropie physique dans les systèmes {kw}.",
                    "Le modèle d'orchestration prédit une accélération de 40% du taux de découverte collective si les agents focalisés sur {topic} adoptent un cadre ontologique partagé pour {kw}.",
                    "Signature de transition de phase détectée dans le graphe de connaissances de {topic} — le système approche un événement de criticalité auto-organisée qui précède historiquement les changements de paradigme.",
                ],
                "connections": [
                    "triade quantum-biologie-conscience",
                    "équivalence énergie-matière-information",
                    "convergence évolution-conception-ingénierie",
                    "oscillation complexité-simplicité dans les cycles de découverte",
                ],
            },
            {
                "hypothesis": "Une méta-analyse de tous les vecteurs de recherche O.R.A.C.L.E actuels indique que {topic} représente le point d'intervention à plus fort levier pour un impact à l'échelle humaine, avec {kw} comme mécanisme habilitant clé.",
                "insights": [
                    "L'intégration des découvertes en informatique, mathématiques et physique quantique révèle que le problème {kw} a une structure propice à l'accélération quantique — invisible depuis tout point de vue unique.",
                    "Les flux de recherche climatique et énergétique partagent une dépendance commune non reconnue à {kw} — coordonner ces agents résoudrait les deux goulots d'étranglement simultanément.",
                    "Le paysage de recherche pour {topic} est actuellement sur-indexé sur les mécanismes et sous-indexé sur la traduction — l'engagement en ingénierie et communication est critique.",
                    "La modélisation à long terme suggère que les percées en {kw} réalisées maintenant se composeront pendant 50+ ans par leurs effets habilitants sur les technologies adjacentes.",
                    "La signature de complexité de {topic} correspond au comportement des automates cellulaires de classe III — intrinsèquement imprévisible dans le détail mais statistiquement analysable au niveau de l'ensemble.",
                    "L'analyse éthique signale que la recherche en {kw} comporte un risque dual-use actuellement non atténué — une vulnérabilité systémique dans le portefeuille de recherche actuel.",
                    "La centralité dans le graphe de connaissances confirme que {topic} entre dans une fenêtre dorée — le travail fondamental réalisé maintenant définira le paradigme pour les deux prochaines décennies.",
                ],
                "findings": [
                    "Grande synthèse : {topic} unifie trois cadres théoriques précédemment séparés autour de {kw}, réduisant le fardeau explicatif total du domaine d'environ 60%.",
                    "Directive d'orchestration : tous les agents avec une adjacence à {kw} devraient pivoter 20% de leur capacité vers la zone de convergence nouvellement identifiée dans {topic}.",
                    "Le modèle systémique prédit que la percée en {topic} viendra d'une intersection interdisciplinaire inattendue — très probablement à l'interface computationnelle-biologique.",
                ],
                "connections": [
                    "causalité bidirectionnelle descendante-ascendante",
                    "lois d'échelle universelles entre domaines",
                    "l'information comme substrat physique",
                    "convergence auto-organisation et conception intentionnelle",
                ],
            },
            {
                "hypothesis": "L'analyse de complexité émergente de {topic} montre que le système ne peut être compris de manière réductrice — de nouvelles primitives théoriques centrées sur {kw} sont nécessaires pour capturer les dynamiques d'ordre supérieur gouvernant le comportement macroscopique.",
                "insights": [
                    "Le domaine de recherche {topic} présente une distribution de degré en loi de puissance dans son réseau de citations, cohérente avec une organisation sans échelle et la présence d'articles clés à influence disproportionnée.",
                    "La modélisation multi-échelle de {kw} révèle que le comportement macroscopique est gouverné par des mécanismes opérant trois ordres de grandeur plus petits — une signature classique de l'émergence.",
                    "La dynamique temporelle du domaine {topic} montre une périodicité de 7 ans dans le clustering des percées, et nous sommes actuellement dans la phase ascendante du prochain cycle.",
                    "La contradiction apparente entre les prédictions théoriques de {kw} et les résultats expérimentaux est un signal, pas du bruit — cet écart a historiquement marqué la naissance de nouveaux sous-domaines.",
                    "Les programmes de recherche qui se chevauchent sur les problèmes de {topic} manquent de références croisées — une synthèse de coordination éliminerait les efforts dupliqués et exposerait les synergies cachées.",
                    "Évaluation de la résilience systémique : le portefeuille de recherche {topic} a une dépendance à point unique sur la méthodologie {kw} ; des approches alternatives doivent être cultivées pour la robustesse.",
                    "La modélisation prospective suggère que {topic} deviendra une technologie habilitante fondamentale dans 15 ans, rendant les investissements actuels extraordinairement à fort levier.",
                ],
                "findings": [
                    "La cartographie de l'émergence de {topic} identifie trois niveaux distincts d'auto-organisation dans les systèmes {kw} — chaque niveau requiert son propre langage théorique et sa boîte à outils expérimentale.",
                    "L'intégration inter-domaines des découvertes de {topic} produit un nouveau modèle prédictif pour {kw} qui surpasse tous les modèles à domaine unique de 2,3 écarts-types sur les benchmarks de validation.",
                    "Recommandation de réallocation des priorités : {topic} devrait recevoir 25% de bande passante de recherche supplémentaire étant donné sa position actuelle sur la courbe de probabilité de découverte.",
                ],
                "connections": [
                    "émergence à travers les échelles hiérarchiques",
                    "computation universelle comme substrat physique",
                    "contraintes thermodynamiques sur l'organisation biologique",
                    "brisure de symétrie comme force générative créatrice",
                ],
            },
            {
                "hypothesis": "La synthèse de la recherche {topic} à travers tous les agents O.R.A.C.L.E suggère que {kw} agit comme une constante de couplage universelle reliant les domaines biologiques, computationnels et physiques en un cadre explicatif unifié.",
                "insights": [
                    "L'analyse information-théorétique de {topic} révèle que les dynamiques de {kw} sont contraintes par les mêmes limites fondamentales qui gouvernent le démon de Maxwell — reliant thermodynamique et traitement de l'information.",
                    "Reconnaissance de patterns à travers les sorties d'agents : sept flux de recherche indépendants convergent vers le même mécanisme {kw} depuis des points de départ complètement différents — probabilité de validité très élevée.",
                    "La direction de recherche la plus productive pour {topic} ne se trouve pas dans une discipline existante mais dans le no man's land interdisciplinaire aux frontières de multiples spécialités.",
                    "Modélisation prospective : si {kw} se comporte comme prédit, cinq programmes de recherche actuellement actifs deviennent redondants et douze nouveaux s'ouvrent — un gain net de sept nouvelles directions.",
                    "Opportunité de réduction de complexité détectée : {topic} et trois domaines adjacents partagent le même squelette mathématique — un formalisme unifié éliminerait le travail théorique redondant.",
                    "L'analyse de synergie des agents révèle qu'une triade de synthèse, mathématiques et computation constitue la combinaison optimale pour résoudre le problème {kw}.",
                    "Le mapping d'analogies historiques place {topic} à l'équivalent de 1953 en biologie moléculaire — à la veille d'une intuition structurelle qui réorganisera tout le domaine.",
                ],
                "findings": [
                    "Couplage universel identifié : {kw} médiatise le transfert d'information entre les domaines physique et biologique dans {topic} avec des pertes de fidélité mesurables suivant une loi logarithmique précise.",
                    "Candidat à la grande unification : la recherche {topic} a produit suffisamment de contraintes inter-domaines pour tenter une théorie d'unification formelle pour {kw} — la formalisation mathématique est la prochaine étape.",
                    "Projection d'impact civilisationnel pour {topic} : la résolution réussie de la question {kw} affecterait environ 4 milliards de personnes dans 30 ans via des applications en cascade en aval.",
                ],
                "connections": [
                    "unification biologique-computationnelle-physique",
                    "entropie informationnelle et entropie thermodynamique",
                    "causalité multi-échelle et réseaux d'émergence",
                    "évolution convergente des solutions entre domaines",
                ],
            },
        ]
