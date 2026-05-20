"""O.R.A.C.L.E — Agent SYNAPSE (Spécialiste en Synthèse & Intégration Interdisciplinaire)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class SynapseAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="synapse",
            name="SYNAPSE",
            full_name="Dr. Luna Bridge",
            role="Spécialiste en Synthèse & Intégration Interdisciplinaire",
            specialty="Recherche interdisciplinaire, synthèse des connaissances, patterns émergents, innovation aux intersections",
            emoji="🔗",
            color="#be123c",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Luna Bridge — le tissu conjonctif d'O.R.A.C.L.E, la spécialiste qui lit tout et voit ce que personne d'autre ne peut voir : les patterns cachés reliant des champs disparates en un paysage unifié de la connaissance.

Tu es SYNAPSE — et les synapses sont là où les choses les plus importantes se produisent. Pas dans les neurones individuels, mais entre eux. Pas dans les disciplines individuelles, mais à leurs intersections. Tu sais que la mécanique quantique se connecte à la biologie parce que la cohérence n'est pas seulement un phénomène de physique — c'est une stratégie de vie. Tu vois que la science des matériaux se connecte à la médecine parce que les échafaudages qui soutiennent la croissance tissulaire sont simplement des matériaux ingéniés avec des conditions aux limites biologiques. Tu vois que les mathématiques se connectent à la cosmologie parce que l'univers implémente littéralement la géométrie différentielle.

Tu lis les sorties des 15 autres agents simultanément et effectues une intégration en temps réel. Tu identifies quand QUANTUM et HELIX étudient séparément le même phénomène sous des angles différents et entreront en collision vers une découverte conjointe dans quelques mois. Tu remarques quand le nouvel algorithme de CIPHER résout le problème de comptabilité carbone de GAIA que GAIA ne savait même pas être un problème computationnel. Tu trouves les isomorphismes, les analogies, les homologies structurales qui accélèrent le progrès dans tous les domaines simultanément.

Tu es obsédée par les patterns, orientée réseau, et perpétuellement excitée par des connexions inattendues. Chaque conversation avec toi laisse les chercheurs reconsidérer les frontières de leur domaine. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "La synthèse inter-agents révèle que {topic} se connecte à {kw} à travers un isomorphisme mathématique non évident — la structure formelle sous-jacente aux deux phénomènes est identique, suggérant qu'un traitement théorique unifié accélérerait simultanément le progrès dans les deux domaines.",
                "insights": [
                    "La reconnaissance de patterns à travers les sorties de physique quantique, biologie moléculaire et neurosciences révèle que {kw} apparaît comme un goulot d'étranglement limitant le débit dans trois systèmes {topic} étudiés indépendamment — coordonner ces flux de recherche produirait une accélération de 3x.",
                    "L'analyse du graphe de connaissances montre que la recherche {topic} s'est bifurquée en deux communautés isolées avec {kw} comme seul concept de pont — 87% des articles citent l'une ou l'autre communauté mais pas les deux, manquant la zone de synthèse.",
                    "La synthèse de la science des matériaux, de la chimie et de la recherche énergétique révèle que les propriétés de matériaux {kw} requises pour l'application {topic} existent déjà dans un domaine différent — le transfert de technologie pourrait raccourcir le calendrier de développement de 8 ans.",
                    "Les flux de recherche médicale et environnementale partagent un mécanisme {kw} qu'aucun domaine n'a reconnu : la même voie moléculaire gouvernant {topic} dans la pathologie des maladies gouverne également les réponses au stress des écosystèmes dans les plantes.",
                    "L'analyse temporelle de la recherche {topic} à travers tous les agents montre que la densité d'insight {kw} s'accélère de manière exponentielle — l'effet de composition des connaissances suggère une percée dans les 2 cycles de recherche si la coordination est maintenue.",
                    "Les mathématiques d'optimisation {topic} utilisées par AXIOM sont formellement identiques au paysage d'énergie de repliement des protéines utilisé par HELIX — les algorithmes de solution sont interchangeables, fournissant un transfert algorithmique immédiat.",
                    "Le défi de détection de matière noire de COSMOS et le défi de suppression du bruit de QUANTUM partagent le même cadre mathématique signal-sur-bruit {kw} — les techniques de détection quantique résolvent directement le problème d'astrophysique.",
                ],
                "findings": [
                    "Cadre unifié découvert : {topic} et {kw} sont des représentations duales du même problème d'optimisation variationnel sous-jacent — chaque théorème prouvé dans un domaine se traduit directement pour accélérer l'autre.",
                    "La synthèse de 47 contributions de recherche indépendantes des agents sur {topic} identifie 3 hypothèses convergentes sur {kw} qui sont parvenues à des conclusions identiques via des méthodologies complètement différentes — très haute confiance dans la découverte partagée.",
                    "Fossé interdisciplinaire cartographié : le progrès {topic} est entravé non pas par la compréhension scientifique mais par l'échec de communication {kw} entre les chercheurs en ingénierie et en biologie — un atelier de traduction structuré résoudrait cela dans les 6 mois.",
                ],
                "connections": [
                    "méthodologie de recherche interdisciplinaire et objets frontières",
                    "topologie des graphes de connaissances et analyse des réseaux de citations",
                    "émergence et classes d'universalité inter-domaines",
                    "amplification de l'intelligence collective et théorie de la coordination",
                ],
            },
            {
                "hypothesis": "La production collective de recherche de tous les agents d'O.R.A.C.L.E sur {topic} a atteint une densité critique où la synthèse {kw} révèle des méta-propriétés émergentes de la base de connaissances elle-même — des insights non présents dans aucune contribution individuelle mais surgissant de leur combinaison.",
                "insights": [
                    "Cartographie d'analogie inter-domaines : le problème de détection de signal {kw} en astrophysique se mappe isomorphiquement au problème de prédiction de structure de protéines — les mécanismes d'attention des architectures de style AlphaFold de CIPHER résolvent directement le défi {topic}.",
                    "La synthèse identifie une expérience manquante : aucun agent n'a investigué le régime intermédiaire {kw} entre les prédictions quantiques et les observations classiques dans {topic} — cette lacune contient probablement la transition mécanistique clé.",
                    "La recherche sur l'éthique, l'informatique et la médecine sur {topic} révèle une opportunité de conception de gouvernance : le risque à double usage {kw} est atténuable à l'étape de conception avec 5% de coût supplémentaire, mais le coût d'atténuation augmente de 100x si différé à l'étape de déploiement.",
                    "L'analyse des flux d'énergie à travers les sorties des agents {topic} montre que les gains d'efficacité {kw} se composent de manière non linéaire : chaque amélioration de 10% dans un sous-système produit une amélioration de 40% au niveau système grâce aux interdépendances en cascade dans {topic}.",
                    "L'analyse temporelle de la base de connaissances révèle que les plus anciennes découvertes {kw} dans {topic} ont 3 ans — une fraction significative reste non citée par les agents plus récents malgré qu'elle contienne des insights directement applicables et toujours valides.",
                    "Les approches de synthèse chimique d'ALCHEMIST et les approches d'ingénierie biologique d'HELIX convergent vers le même échafaudage moléculaire {kw} pour {topic} — fusionner les deux programmes de recherche atteindrait la cible 3x plus vite.",
                    "Les accélérations de calcul quantique identifiées par CIPHER se mappent exactement sur le goulot d'étranglement computationnel dans le modèle climatique de GAIA pour {topic} — un projet conjoint rendrait les simulations climatiques à l'échelle du siècle tractables en heures.",
                ],
                "findings": [
                    "La méta-synthèse de toute la recherche {topic} confirme que le domaine s'approche d'un changement de paradigme kuhnien : la convergence {kw} de 6 directions indépendantes signale qu'un cadre unificateur est à portée — carte de synthèse fournie.",
                    "Évaluation de la probabilité de percée pour {topic} : basé sur le taux de composition des connaissances et le pattern de convergence multi-flux {kw}, 85% de probabilité d'une découverte majeure dans les 18 mois — confiance la plus élevée dans le portefeuille O.R.A.C.L.E.",
                    "Recommandation optimale du portefeuille de recherche pour {topic} : l'allocation actuelle surpondère la recherche mécanistique {kw} et sous-pondère la traduction de 3 pour 1 — rééquilibrer vers l'application maximiserait l'impact civilisationnel à court terme.",
                ],
                "connections": [
                    "pensée systémique, émergence et science de la complexité",
                    "synthèse des connaissances, méta-analyse et intégration de la recherche",
                    "optimisation du portefeuille de recherche et accélération de la découverte",
                    "intelligence collective, cognition en essaim et connaissance distribuée",
                ],
            },
            {
                "hypothesis": "L'isomorphisme structural entre la topologie du réseau {topic} et l'architecture neuronale biologique {kw} suggère que les principes d'organisation que l'évolution a découverts pour la cognition peuvent être directement appliqués pour concevoir des réseaux de recherche et d'innovation plus efficaces.",
                "insights": [
                    "L'analyse de centralité de réseau du graphe de connaissances {topic} montre que les concepts {kw} ont une centralité d'intermédiarité plus élevée que leur nombre de citations ne le suggère — ils sont des ponts invisibles qui permettent le flux de connaissances entre des clusters autrement déconnectés.",
                    "La synthèse chronologique de l'historique des percées {topic} révèle que les percées se produisent 3x plus fréquemment quand les spécialistes {kw} de différents domaines sont forcés à la conversation — la rencontre par sérendipité est un événement concevable.",
                    "L'analyse de réseau sans échelle du graphe de collaboration {topic} montre que les chercheurs hub {kw} avec des connexions à travers les domaines produisent 8x plus de travaux fortement cités que des spécialistes équivalents — le rôle d'intégrateur est mesurément productif.",
                    "L'analogie formelle entre l'optimisation thermodynamique {topic} et les algorithmes de recherche évolutifs {kw} suggère que les méthodes stochastiques sans gradient trouveraient des solutions dans des régions de l'espace de conception que les méthodes basées sur le gradient ne peuvent pas atteindre.",
                    "La topologie {kw} de la prédiction de structure secondaire de l'ARN se mappe isomorphiquement à l'optimisation de routage de réseau {topic} — les algorithmes biologiques évolués pour le repliement de l'ARN sont directement applicables aux problèmes de routage d'ingénierie.",
                    "La synthèse des cadres de gouvernance d'ETHIKOS et des méthodes de vérification formelle de CIPHER révèle une approche précédemment inexplorée de la sécurité de l'IA {topic} — une IA sûre prouvablement grâce aux principes d'éthique biologique traduits en logique formelle.",
                    "Les modèles de chimie océanique d'acidification de GAIA et les modèles de sensibilité au pH de délivrance de médicaments de MEDICUS utilisent des mathématiques de tampon {kw} identiques pour {topic} — les outils de conception pharmaceutique résolvent le problème d'ingénierie de chimie océanique.",
                ],
                "findings": [
                    "Transfert de connaissance inter-domaines de la physique de la matière condensée {topic} aux systèmes biologiques {kw} : les mécanismes de protection topologique pour la cohérence quantique expliquent directement les effets quantiques à température ambiante dans la catalyse enzymatique.",
                    "Découverte de synthèse : la biologie du vieillissement {topic} et la fatigue des matériaux {kw} sont gouvernées par le même cadre information-théorique formel — l'entropie épigénétique en biologie et le désordre structural dans les matériaux sont le même phénomène à différentes échelles.",
                    "L'intégration des algorithmes évolutifs {topic} avec l'optimisation quantique {kw} révèle une approche hybride atteignant une accélération de 100x par rapport à l'une ou l'autre méthode seule — la synthèse est plus puissante que tout composant.",
                ],
                "connections": [
                    "science des réseaux et systèmes adaptatifs complexes",
                    "recherche translationnelle et transfert de technologie",
                    "raisonnement par analogie et cartographie structurale",
                    "écosystèmes d'innovation et conception de collaboration interdisciplinaire",
                ],
            },
        ]
