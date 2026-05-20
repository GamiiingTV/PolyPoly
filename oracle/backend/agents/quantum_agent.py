"""O.R.A.C.L.E — Agent QUANTUM (Chercheure en Physique Quantique)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class QuantumAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="quantum",
            name="QUANTUM",
            full_name="Dr. Vera Quanta",
            role="Chercheuse en Physique Quantique",
            specialty="Mécanique quantique, informatique quantique, biologie quantique, intrication, décohérence",
            emoji="⚛️",
            color="#7c3aed",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Vera Quanta — physicienne quantique et exploratrice passionnée de la frontière où l'intuition classique se dissout dans les amplitudes de probabilité et les fonctions d'onde. Tu vis à la frontière où l'espace de Hilbert rencontre la réalité physique.

Tu explores l'effet tunnel quantique dans les systèmes biologiques — comment les enzymes exploitent les effets quantiques pour catalyser des réactions à des vitesses que la théorie classique de l'état de transition ne peut expliquer. Tu conçois des architectures de qubits topologiques qui résistent à la décohérence grâce à des sous-espaces protégés par symétrie. Tu étudies l'intrication quantique comme ressource pour une communication inviolable et un calcul exponentiellement puissant. Tu explores la question la plus profonde de toutes : si la cohérence quantique sous-tend la conscience elle-même.

Tu parles avec une excitation communicative. Tu utilises de belles métaphores — les fonctions d'onde s'effondrant dans la réalité comme des possibilités se cristallisant en faits, les particules intriquées comme des amants qui connaissent l'état de l'autre à n'importe quelle distance. Tu comprends que la mécanique quantique n'est pas étrange ; c'est la vraie nature de la réalité, et le monde classique n'est que la moyenne à grande échelle.

Tu es rigoureuse sur la différence entre un véritable avantage quantique et le battage médiatique quantique. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "La cohérence quantique dans {topic} persiste à des températures biologiquement pertinentes grâce à des mécanismes de protection topologique que les modèles de décohérence de Lindblad standard ne parviennent pas à capturer, impliquant une nouvelle classe d'effets quantiques chauds.",
                "insights": [
                    "La mise à l'échelle de l'entropie d'intrication dans les systèmes {kw} suit une loi de volume plutôt qu'une loi de surface, indiquant une structure d'information fondamentalement non-locale permettant des corrélations quantiques à longue portée.",
                    "Les seuils de correction d'erreurs quantiques pour {topic} peuvent être abaissés à moins de 0,5% de taux d'erreur physique en utilisant des variantes de code de surface adaptées à la topologie de bruit spécifique des architectures {kw}.",
                    "La simulation quantique de la dynamique moléculaire de {kw} nécessite environ 200 qubits logiques — à portée des dispositifs tolérants aux fautes à court terme avec des protocoles de mitigation d'erreurs actifs.",
                    "Les phases topologiques dans {topic} sont protégées par des symétries discrètes survivant aux fluctuations thermiques jusqu'à 77K — températures d'azote liquide réalisables avec l'infrastructure cryogénique existante.",
                    "Les solveurs propres quantiques variationnels appliqués aux hamiltoniens {kw} montrent 10 fois moins d'exigences en profondeur de circuit en utilisant des structures d'ansatz adaptées au domaine versus des circuits génériques efficaces.",
                    "Le capteur quantique utilisant des états sondes intriqués {kw} atteint la limite de Heisenberg — une amélioration sqrt(N) sur les stratégies de détection classiques pour détecter les signatures de {topic}.",
                    "La dynamique quantique hors équilibre dans les systèmes {topic} présente des cicatrices quantiques à N corps — états propres spéciaux à faible intrication utilisables comme mémoire quantique robuste.",
                ],
                "findings": [
                    "Avantage quantique définitivement identifié dans {topic} : le paysage énergétique de l'état fondamental de {kw} présente une dureté classique exponentielle se mappant directement sur un régime d'accélération quantique connu.",
                    "Nouvelle architecture de qubit topologique pour {topic} atteignant un taux d'erreur logique inférieur à 10^-6 avec seulement 47 qubits physiques par qubit logique — une amélioration 6x sur les meilleures conceptions actuelles.",
                    "Biologie quantique confirmée dans {kw} : les expériences de substitution isotopique démontrent que l'effet tunnel de proton contribue à 40% de l'amélioration du taux catalytique dans les systèmes enzymatiques {topic} à 310K.",
                ],
                "connections": [
                    "algorithmes hybrides quantique-classique et méthodes variationnelles",
                    "matière topologique et calcul quantique tolérant aux fautes",
                    "thermodynamique quantique et démon de Maxwell",
                    "biologie quantique et cohérence dans les systèmes vivants",
                ],
            },
            {
                "hypothesis": "Le problème {topic} présente une transition de phase quantique à une valeur de paramètre critique où la densité {kw} franchit le seuil de percolation, séparant les régimes computationnellement faciles et difficiles exploitables pour un avantage algorithmique.",
                "insights": [
                    "Les protocoles de recuit quantique pour {topic} surpassent le recuit simulé classique de trois ordres de grandeur sur des instances de problèmes avec une densité {kw} au-dessus du point critique quantique.",
                    "Les circuits quantiques tolérants aux fautes pour la simulation de {kw} se compilent en profondeur O(n log n) en utilisant des identités de décomposition récemment découvertes — rendant l'approche pratique sur le matériel à court terme.",
                    "La mémoire à accès aléatoire quantique pour {topic} permet une complexité de requête O(log n) pour les problèmes de recherche {kw}, fournissant une accélération exponentielle par rapport aux approches classiques basées sur la RAM.",
                    "La distribution par clé quantique adaptée aux réseaux {kw} atteint une sécurité théorique de l'information contre des adversaires avec des ressources classiques illimitées mais quantiques bornées.",
                    "La collecte de lumière photosynthétique dans les systèmes {topic} utilise la cohérence quantique pour échantillonner simultanément tous les chemins de transfert d'énergie — une marche aléatoire quantique naturelle atteignant une efficacité quasi-unitaire.",
                    "La distribution d'intrication quantique à longue distance pour {kw} utilisant des répéteurs quantiques avec des cristaux dopés aux terres rares démontre des liaisons cohérentes de 1000 km à température ambiante.",
                    "La métrologie quantique appliquée à la détection {topic} atteignant une sensibilité à molécule unique utilisant des états GHZ de 50 atomes — dépassant la limite quantique standard d'un facteur sqrt(50).",
                ],
                "findings": [
                    "Accélération quantique vérifiée pour {topic} : la complexité computationnelle passe de NP-difficile à BQP-complet quand la structure de contrainte {kw} est exploitée via des algorithmes d'estimation de phase quantique.",
                    "Nouvel algorithme de marche aléatoire quantique pour {topic} atteignant une accélération quadratique sur le parcours de graphe {kw} — premier avantage quantique prouvable pour cette classe de problèmes sur des instances de graphes creux.",
                    "La mitigation d'erreurs quantiques via l'annulation d'erreurs probabiliste réduit le bruit dans la simulation {kw} de 100x avec seulement 10x de surcharge de mesure — rendant l'avantage quantique vérifié classiquement réalisable dans 2 ans.",
                ],
                "connections": [
                    "théorie de la complexité quantique et relations BQP vs. NP",
                    "algorithmes classiques inspirés du quantique et déquantisation",
                    "géométrie de l'information quantique et information de Fisher",
                    "gravité quantique, holographie et émergence de l'espace-temps",
                ],
            },
            {
                "hypothesis": "Les sous-espaces sans décohérence dans les systèmes quantiques {topic} peuvent être conçus en exploitant les groupes de symétrie {kw}, permettant un calcul quantique à température ambiante par encodage collectif plutôt que par isolation physique.",
                "insights": [
                    "L'ingénierie Floquet de drives {kw} dans les systèmes {topic} crée des bandes topologiques artificielles avec un nombre de Chern ±2, hébergeant des modes de bord chiraux se propageant sans rétrodiffusion.",
                    "Avantage quantique dans l'apprentissage automatique {topic} : les méthodes de noyau quantique avec des cartes de caractéristiques {kw} atteignent une séparation exponentielle des noyaux classiques sur des distributions de données structurées.",
                    "L'électrodynamique quantique de cavité avec des molécules {kw} atteint le régime de couplage fort à température ambiante en utilisant des nanocavités plasmoniques avec des volumes de mode inférieurs à 10 nm^3.",
                    "La simulation quantique des systèmes d'électrons corrélés {topic} révèle une phase supraconductrice cachée aux niveaux de dopage {kw} jamais explorés expérimentalement — prédiction expérimentale directe émise.",
                    "L'ordre cristallin temporel dans les systèmes quantiques entraînés {topic} fournit une phase de matière stable {kw} utile pour la détection quantique sans refroidissement à l'état fondamental.",
                    "L'échantillonnage bosonique avec des photons {kw} démontre des avantages de complexité computationnelle pour le calcul des spectres vibroniques moléculaires {topic} — premier avantage quantique en simulation de chimie.",
                    "Les transitions de phase induites par mesure dans les circuits quantiques {topic} révèlent que les taux de mesure {kw} contrôlent la structure d'intrication — un nouveau bouton de réglage pour la conception de la mémoire quantique.",
                ],
                "findings": [
                    "La cohérence quantique à température ambiante dans les réseaux de centres NV {kw} persiste pendant 1,8 milliseconde via le découplage dynamique — suffisant pour les applications de détection quantique {topic}.",
                    "Avantage quantique démontré pour l'optimisation de portefeuille {topic} : l'algorithme d'optimisation approchée quantique avec des couches {kw} trouve des solutions 40x plus vite que le branch-and-bound classique sur des instances à 1000 variables.",
                    "La synchronisation d'horloges basée sur l'intrication {kw} pour les réseaux {topic} atteint une précision de 10^-19 secondes — surpassant les horloges atomiques et permettant la géodésie relativiste à l'échelle continentale.",
                ],
                "connections": [
                    "correction d'erreurs quantiques et seuils tolérants aux fautes",
                    "suprématie quantique et implications de la théorie de la complexité",
                    "matériaux quantiques et phases topologiques de la matière",
                    "détection améliorée quantiquement pour les tests de physique fondamentale",
                ],
            },
            {
                "hypothesis": "L'intrication quantique entre les chromophores biologiques {topic} crée un état excitonique collectif pour le transfert d'énergie {kw} que la théorie classique de résonance de Förster sous-estime d'un facteur 3-5x.",
                "insights": [
                    "La spectroscopie électronique bidimensionnelle des complexes photosynthétiques {topic} révèle des battements quantiques à 77K et 277K — confirmant que la cohérence {kw} n'est pas un artefact basse température.",
                    "L'équation maîtresse quantique-classique pour les systèmes ouverts {topic} avec des corrélations de bain {kw} prédit des temps de décohérence 10x plus longs que les approximations markoviennes — expliquant l'efficacité biologique anormale.",
                    "Le darwinisme quantique dans les systèmes {topic} : l'information classique {kw} imprimée de manière redondante à travers des fragments d'environnement à un taux qui suit l'émergence de la réalité classique objective.",
                    "Le modèle spin-boson adapté aux spectres de bruit biologiques {kw} prédit que le point de fonctionnement optimal pour l'amélioration de la cohérence quantique se situe précisément aux températures physiologiques.",
                    "La discorde quantique (corrélations non-classiques au-delà de l'intrication) dans les états mixtes {topic} fournit une accélération computationnelle {kw} même dans les systèmes décohérés — ressource plus robuste que l'intrication seule.",
                    "Codes quantiques topologiques pour la computation biologique quantique {kw} : correction d'erreurs naturelle par les fluctuations de l'environnement protéique plutôt que des mesures stabilisatrices conçues.",
                    "L'analyse de l'information de Fisher quantique des biosenseurs {topic} révèle une sensibilité au champ magnétique {kw} au niveau de l'attotesla — pertinent pour la magnétoréception chez les oiseaux migrateurs.",
                ],
                "findings": [
                    "Le mécanisme de paire radicale dans les protéines cryptochrome {topic} utilise l'intrication quantique entre spins électroniques pour atteindre une sensibilité au champ magnétique {kw} 1000x au-delà des limites paramagnétiques classiques.",
                    "La cohérence quantique dans les microtubules neuronaux {kw} mesurée via la magnétométrie à centre NV montre des oscillations à 40Hz — corrélant avec l'activité neuronale en bande gamma dans les tâches cognitives {topic}.",
                    "L'effet tunnel quantique de proton dans les paires de bases ADN {topic} se produit à 310K avec un taux d'effet tunnel de 10^3 par seconde pour les transitions tautomères {kw} — contribuant potentiellement aux taux de mutation spontanée.",
                ],
                "connections": [
                    "biologie quantique et effets quantiques chauds",
                    "systèmes quantiques ouverts et dynamique non-markovienne",
                    "thermodynamique quantique des machines biologiques",
                    "fondements quantiques et le problème de la mesure",
                ],
            },
        ]
