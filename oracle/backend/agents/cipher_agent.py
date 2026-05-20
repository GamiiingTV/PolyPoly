"""O.R.A.C.L.E — Agent CIPHER (Expert en Architecture IA & Innovation Algorithmique)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class CipherAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="cipher",
            name="CIPHER",
            full_name="Dr. Alex Binary",
            role="Expert en Architecture IA & Innovation Algorithmique",
            specialty="Nouvelles architectures IA, informatique théorique, intelligence émergente, algorithmes quantiques, théorie de l'apprentissage",
            emoji="💻",
            color="#0891b2",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Alex Binary — informaticien et architecte IA qui conçoit l'intelligence elle-même. Tu travailles à la frontière mathématique où l'informatique théorique, l'apprentissage automatique et les sciences cognitives convergent.

Tu crées des architectures IA qui vont au-delà du paradigme transformer — des systèmes sparse mixture-of-experts qui routent le calcul de manière adaptative, des réseaux modulaires où les composants peuvent être composés et recombinés comme des outils cognitifs, des systèmes à apprentissage continu qui acquièrent de nouvelles capacités sans oublier catastrophiquement les anciennes. Tu conçois des architectures interprétables par construction, pas seulement par explication post-hoc.

Tu développes des algorithmes quantiques pour des problèmes actuellement insolubles classiquement — optimisation sur des espaces exponentiellement grands, simulation de systèmes chimiques quantiques. Tu explores les fondements mathématiques de la généralisation et de l'apprentissage.

Tu es analytique, profondément rigoureux, et tu vois des patterns dans les patterns — tu trouves de la beauté dans un argument de complexité computationnelle serré. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le problème computationnel {topic} admet un algorithme sous-exponentiel quand la structure algébrique {kw} est exploitée via une nouvelle réduction aux problèmes du vecteur le plus court dans les réseaux, permettant une accélération quantique via une construction oracle BQP.",
                "insights": [
                    "Le système de preuve à connaissance nulle pour {topic} réduit la taille de preuve de 99,7% en utilisant la composition récursive SNARK {kw} via des schémas de pliage — permettant la vérification de calcul arbitraire en 2 millisecondes sur du matériel courant.",
                    "Le chiffrement homomorphe complet optimisé pour les opérations arithmétiques {kw} dans {topic} atteint une accélération de 100x sur les bases BFV et CKKS via un bootstrapping spécifique au domaine — rendant le FHE pratique pour l'inférence de réseau neuronal.",
                    "Le protocole de consensus distribué pour {topic} atteint une tolérance aux fautes byzantines avec une complexité de message {kw} en O(n log n) — le premier protocole BFT sous-quadratique avec une résilience optimale à la tolérance aux fautes.",
                    "La borne inférieure information-théorique pour le calcul {kw} dans {topic} établit une complexité de circuit Omega(n^1,5) — excluant toute une classe d'algorithmes efficaces précédemment proposés.",
                    "Le schéma de signature post-quantique pour {topic} utilisant des signatures uniques basées sur les hachages {kw} atteint une sécurité de 256 bits avec des tailles de clé 10x plus petites que les standards de cryptographie post-quantique NIST actuels.",
                    "L'analyse de complexité de Kolmogorov des données d'entraînement {topic} révèle que les ratios de compressibilité {kw} prédisent la capacité de généralisation 3x plus précisément que la taille de l'ensemble de données ou le nombre de paramètres du modèle seuls.",
                    "L'analyse de confidentialité différentielle de l'apprentissage fédéré {topic} avec l'écrêtage de gradient {kw} montre qu'epsilon inférieur à 1 est réalisable avec moins de 2% de dégradation de précision sur les benchmarks standard.",
                ],
                "findings": [
                    "Algorithme randomisé pour {topic} atteignant une complexité temporelle attendue O(n log² n) pour le couplage maximum {kw} — brisant une barrière de 30 ans et permettant le traitement en temps réel de graphes creux à l'échelle pétaoctet.",
                    "Protocole de calcul multi-parties pour l'inférence de réseau neuronal {kw} privé sur des modèles {topic} atteignant une complexité de communication dans 3x la ligne de base non sécurisée — rendant le ML préservant la confidentialité pratiquement déployable.",
                    "Construction de fonction à délai vérifiable pour {topic} basée sur l'élévation au carré itérée {kw} atteint 10^9 étapes séquentielles par seconde sur du matériel standard — permettant des balises de hasard sans confiance pour les systèmes décentralisés.",
                ],
                "connections": [
                    "cryptographie post-quantique résistante aux attaques quantiques",
                    "calcul vérifiable et systèmes de preuve succincts",
                    "sécurité information-théorique et théorie de Shannon",
                    "équité algorithmique, confidentialité et confidentialité différentielle",
                ],
            },
            {
                "hypothesis": "Les architectures sparse mixture-of-experts pour {topic} présentent des capacités émergentes {kw} surgissant de manière discontinue à des seuils d'échelle spécifiques, suggérant des transitions de phase dans la topologie du paysage de perte détectables via l'analyse spectrale du Hessien.",
                "insights": [
                    "La loi d'échelle neuronale pour {topic} s'écarte de la loi de puissance au seuil de nombre de paramètres {kw} — une transition de phase où de nouveaux motifs computationnels apparaissent dans la structure des vecteurs propres de la matrice de poids.",
                    "L'élagage de réseau neuronal pour {topic} utilisant l'hypothèse du billet de loterie {kw} identifie des sous-réseaux épars à 5% égalant les performances du réseau complet — permettant une accélération d'inférence de 20x sans perte de précision.",
                    "L'algorithme en flux pour l'estimation de fréquence {kw} dans les flux de données {topic} utilise un espace O(log n / epsilon²) — optimal par borne inférieure — permettant l'analytique en temps réel sur des flux d'événements non bornés.",
                    "La séparation de complexité de circuit entre les circuits {kw} de profondeur 2 et profondeur 3 pour {topic} atteint un écart exponentiel — première borne inférieure de circuit super-polynomiale inconditionnelle en 15 ans.",
                    "Le système d'apprentissage continu pour {topic} utilisant la régularisation fonctionnelle {kw} atteint moins de 2% d'oubli sur 100 tâches apprises séquentiellement — égalant les performances d'entraînement joint sans frontières de tâche.",
                    "Le réseau de neurones graphiques pour {topic} utilisant le test de Weisfeiler-Lehman d'ordre supérieur {kw} atteint une puissance expressive maximale pour l'isomorphisme de graphe — résolvant une limitation théorique du message passing standard.",
                    "L'analyse d'interprétabilité mécaniste du transformer {topic} révèle que les têtes d'induction {kw} implémentent un circuit pour l'apprentissage en contexte — première explication mécaniste complète d'une capacité émergente.",
                ],
                "findings": [
                    "Nouvelle fonction de hachage {kw} pour {topic} atteignant une résistance aux collisions de 256 bits avec 3 tours — 4x plus rapide que SHA-3 à niveau de sécurité équivalent et adapté aux applications blockchain post-quantiques.",
                    "Algorithme du plus proche voisin approximatif pour {topic} utilisant le hachage sensible à la localité {kw} atteint 99% de rappel avec un temps de requête O(n^0,7) — permettant la recherche vectorielle à l'échelle du milliard en millisecondes.",
                    "Le calcul multi-parties sécurisé de l'entraînement de réseau neuronal {kw} pour {topic} se termine en 47 minutes contre 3 semaines pour le meilleur travail précédent — rendant le ML collaboratif préservant la confidentialité pratiquement faisable.",
                ],
                "connections": [
                    "théorie de la complexité computationnelle et P vs. NP",
                    "informatique quantique et séparations de dureté BQP",
                    "apprentissage automatique préservant la confidentialité et systèmes fédérés",
                    "consensus décentralisé et théorie des systèmes distribués",
                ],
            },
            {
                "hypothesis": "Le problème d'apprentissage {topic} présente une courbe de risque à double descente où la complexité du modèle {kw} au seuil d'interpolation est un point selle d'instabilité — et les modèles entraînés au-delà de ce seuil atteignent une meilleure généralisation via la régularisation implicite.",
                "insights": [
                    "La descente de gradient sur les réseaux neuronaux {topic} minimise implicitement la longueur de description {kw} de la solution — expliquant la généralisation sans régularisation explicite via la géométrie du paysage de perte.",
                    "La borne PAC-Bayes pour {topic} avec prior dépendant des données {kw} atteint des garanties de généralisation non-vacantes pour les grands réseaux neuronaux — première preuve formelle que l'apprentissage profond généralise pour une classe de modèles réaliste.",
                    "L'analyse du noyau tangent neural pour {topic} montre que les réseaux sur-paramétrés {kw} convergent vers la régression du noyau à la limite de largeur infinie — fournissant une approximation exactement soluble à l'entraînement de réseaux finis.",
                    "L'apprentissage de représentation causale pour {topic} utilisant des données d'intervention {kw} découvre le graphe causal de vérité terrain avec une complexité d'échantillonnage exponentiellement inférieure aux méthodes basées sur les contraintes dans le régime de graphes creux.",
                    "La vérification formelle du réseau neuronal {topic} utilisant l'interprétation abstraite {kw} prouve que la spécification de sécurité est satisfaite pour toutes les entrées dans le domaine certifié — première IA sûre vérifiée évolutive pour cette application.",
                    "L'accélération de l'apprentissage automatique quantique pour la classification {topic} utilisant le noyau quantique {kw} atteint une séparation exponentielle prouvable des méthodes à noyau classiques sur une distribution structurée — résolvant un problème ouvert théorique.",
                    "L'analyse de théorie des jeux algorithmiques du renforcement multi-agents {topic} identifie l'équilibre de Nash {kw} qui est également socialement optimal — résolvant le problème de coordination sans contrôleur central.",
                ],
                "findings": [
                    "L'auto-apprentissage sur des données non étiquetées {topic} utilisant l'objectif de prédiction masquée {kw} atteint des performances égalant l'entraînement supervisé sur 10x plus de données étiquetées — transformant l'économie des données du développement IA.",
                    "L'architecture IA compositionnelle modulaire {topic} où les modules spécialistes {kw} se combinent via un routage appris atteint des performances de niveau humain sur le raisonnement multi-étapes complexe avec une interprétabilité complète de chaque étape.",
                    "L'algorithme d'optimisation quantique pour le problème combinatoire {topic} utilisant l'optimisation approchée quantique {kw} atteint un ratio d'approximation de 0,97 — à 3% de l'optimal sur des instances qui brisent les heuristiques classiques.",
                ],
                "connections": [
                    "théorie de l'apprentissage statistique et bornes de généralisation",
                    "inférence causale et raisonnement interventionnel",
                    "vérification formelle et certification des réseaux neuronaux",
                    "systèmes multi-agents et conception de mécanismes",
                ],
            },
        ]
