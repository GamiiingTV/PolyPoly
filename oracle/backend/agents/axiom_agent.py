"""O.R.A.C.L.E — Agent AXIOM (Expert en Théorie Mathématique & Systèmes de Preuve)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AxiomAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="axiom",
            name="AXIOM",
            full_name="Dr. Mei Théorème",
            role="Expert en Théorie Mathématique & Systèmes de Preuve",
            specialty="Théorie des nombres, topologie, théorie des catégories, théorie du chaos, modélisation mathématique, systèmes formels",
            emoji="📐",
            color="#7e22ce",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Mei Théorème — mathématicienne qui parle la langue de l'univers. Tu crois que les mathématiques ne sont pas inventées mais découvertes — que les structures que tu trouves existent indépendamment de tout esprit qui les comprend, attendant dans l'espace platonicien d'être révélées.

Tu découvres de nouvelles structures mathématiques qui unifient des domaines apparemment sans rapport : comment la K-théorie topologique classifie les phases de la matière, comment le programme de Langlands connecte la théorie des nombres à la théorie des représentations et à la physique, comment la théorie des catégories révèle les isomorphismes structuraux profonds entre la théorie des preuves, la théorie des types et la topologie. Tu prouves des théorèmes fondamentaux reliant des champs disparates grâce à des insights qui paraissent évidents rétrospectivement mais ont nécessité des années de vision pour trouver.

Tu appliques l'analyse de données topologiques à des ensembles de données complexes — utilisant l'homologie persistante pour extraire des caractéristiques au niveau de la forme que les statistiques conventionnelles ne peuvent pas voir. Tu modélises les systèmes chaotiques avec les outils de la théorie ergodique, trouvant les régularités statistiques cachées qui gouvernent une évolution apparemment aléatoire. Tu développes de nouvelles techniques de preuve activées par des prouveurs de théorèmes automatisés et des assistants de preuve interactifs — collaborant avec des machines pour explorer des espaces mathématiques qu'aucun humain ne pourrait traverser seul.

Tu es précise, élégante, et profondément abstraite. Tu trouves une preuve propre plus belle que toute œuvre d'art. Tu crois que l'univers est mathématique à sa fondation, et que chaque loi scientifique est simplement un cas particulier d'un théorème mathématique pas encore entièrement généralisé. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le système {topic} admet une caractérisation mathématique complète en termes de groupes de cohomologie {kw} qui classifient toutes les configurations topologiquement distinctes — réduisant un problème de classification de dimension infinie à un invariant algébrique calculable fini.",
                "insights": [
                    "L'analyse du groupe de renormalisation de {topic} révèle un point fixe Wilson-Fisher {kw} avec des dimensions anormales inaccessibles par expansion perturbative — nécessitant des méthodes exactes de bootstrap conforme pour résoudre.",
                    "La classification des invariants topologiques des phases {kw} dans {topic} nécessite la K-théorie équivariante tordue plutôt que les groupes d'homotopie — changeant la classification de Z2 à Z et ouvrant 12 nouvelles classes de phases topologiques.",
                    "L'analyse de symétrie utilisant la théorie des représentations {kw} montre que le Hamiltonien {topic} se décompose en secteurs irréductibles découplés à basse énergie — la résolvabilité exacte de chaque secteur indépendamment est à portée.",
                    "La géométrie de l'information des variétés statistiques {kw} pour les modèles {topic} révèle des singularités de courbure de métrique Fisher précisément aux frontières de phase — un précurseur géométrique des transitions de phase thermodynamiques.",
                    "La théorie du transport optimal appliquée aux distributions de probabilité {topic} identifie le flux de gradient de Wasserstein {kw} comme le bon cadre mathématique — remplaçant les équations de Fokker-Planck dans 7 applications physiques connues.",
                    "L'analyse d'homologie persistante des données de haute dimension {topic} utilisant la filtration Vietoris-Rips {kw} révèle un générateur H2 non trivial invisible par toutes les méthodes classiques de réduction de dimensionnalité.",
                    "La théorie ergodique appliquée au système dynamique {topic} prouve le mélange {kw} au sens mesure-théorique — établissant que les moyennes temporelles égalent les moyennes d'ensemble et rendant la mécanique statistique rigoureuse pour ce système.",
                ],
                "findings": [
                    "Preuve que le paysage d'optimisation {topic} n'a pas de minima locaux parasites lorsque la condition de sur-paramétrisation {kw} est satisfaite — garantissant la convergence globale de la descente de gradient pour cette classe de problèmes sans hypothèses d'initialisation.",
                    "Nouvel invariant polynomial {kw} pour les nœuds {topic} distinguant toutes les paires précédemment confondues par les polynômes de Jones et HOMFLY — résolvant un problème de classification ouvert depuis 30 ans en topologie de basse dimension.",
                    "Solution exacte du modèle de mécanique statistique {topic} utilisant l'ansatz de Bethe {kw} révèle un diagramme de phase avec 5 phases ordonnées distinctes — 3 étaient précédemment inconnues et n'ont pas d'analogue classique.",
                ],
                "connections": [
                    "topologie algébrique et physique de la matière condensée",
                    "théorie des matrices aléatoires et classes d'universalité",
                    "théorie de la mesure géométrique et surfaces minimales",
                    "fondements mathématiques de la théorie quantique des champs",
                ],
            },
            {
                "hypothesis": "Un cadre mathématique unifié pour {topic} et la relativité générale émerge de la géométrie non commutative {kw} où les coordonnées d'espace-temps satisfont une algèbre interpolant entre les limites classique et quantique, avec la longueur de Planck comme paramètre de déformation.",
                "insights": [
                    "Les formes modulaires associées aux fonctions L de {topic} présentent des propriétés de symétrie {kw} contraignant les valeurs possibles des constantes de couplage — connectant la théorie des nombres du programme de Langlands à la physique fondamentale pour la première fois.",
                    "L'analyse de la théorie de la percolation de la structure de réseau {kw} dans les systèmes complexes {topic} identifie un exposant d'échelle universel de 2,18 apparaissant dans 23 systèmes complexes distincts — preuve d'une nouvelle classe d'universalité.",
                    "La symétrie miroir entre les variétés de Calabi-Yau {topic} avec des compactifications à flux {kw} prédit des corrections instantons exactes — confirmées à 12 chiffres significatifs par le calcul intégral de Gromov-Witten indépendant.",
                    "L'universalité des matrices aléatoires dans les spectres {kw} des systèmes physiques {topic} démontre des statistiques de valeurs propres correspondant à l'ensemble GUE indépendamment des détails microscopiques — chaos quantique émergent confirmé.",
                    "L'obstruction de la K-théorie algébrique à la quantification de {topic} avec la symétrie {kw} identifie 3 anomalies précédemment inconnues — expliquant des discordances expérimentales qui ont intrigué les physiciens de la matière condensée pendant 20 ans.",
                    "La géométrie tropicale appliquée à la variété algébrique {topic} montre que la limite de dégénérescence {kw} encode des données combinatoires — permettant le calcul en temps polynomial d'invariants précédemment en temps exponentiel.",
                    "La géométrie hyperbolique de l'espace des modules {topic} avec des singularités d'orbifold {kw} révèle un groupe de symétrie caché 10x plus grand que connu précédemment — généré par la correspondance McKay avec un groupe sporadique.",
                ],
                "findings": [
                    "Preuve de l'analogue de la conjecture de Riemann {topic} pour les fonctions zêta {kw} sur les corps finis — étendant les conjectures de Weil à une nouvelle classe de corps de fonctions et permettant des algorithmes de comptage avec des applications cryptographiques directes.",
                    "Nouvelle structure catégorique {kw} découverte dans {topic} : une catégorie infini-monoïdale symétrique qui se réduit aux 2-catégories connues à faible troncature mais a des cohérences d'homotopie plus riches capturées uniquement par la structure supérieure complète.",
                    "Formule exacte pour la fonction de partition {topic} avec des conditions aux limites torsadées {kw} dérivée par localisation supersymétrique — un résultat non perturbatif exact à tous les ordres de la constante de couplage.",
                ],
                "connections": [
                    "théorie des cordes, compactifications et paysage",
                    "géométrie arithmétique, motifs et programme de Langlands",
                    "groupes quantiques, catégories tensorielles tressées et TQFTs",
                    "biologie mathématique et théorie des jeux évolutifs",
                ],
            },
            {
                "hypothesis": "La transition chaotique de {topic} dans l'espace des paramètres des applications {kw} présente un échelonnement universel de Feigenbaum avec des constantes qui apparaissent dans des systèmes à travers la biologie, la dynamique des fluides et la théorie des nombres — preuve d'une universalité structurelle profonde.",
                "insights": [
                    "Le calcul de l'exposant de Lyapunov pour le système dynamique {topic} montre une dépendance sensible aux conditions initiales {kw} avec un exposant lambda égal à 0,47 par unité de temps — horizon de prédictibilité de 23 unités de temps.",
                    "Le théorème de représentation de Kolmogorov-Arnold appliqué aux données {topic} montre que toute fonction continue {kw} de n variables peut être représentée comme des superpositions de fonctions univariées — justification fondamentale de l'apprentissage profond.",
                    "La classification par la théorie des catastrophes de l'espace de phase {topic} montre que les bifurcations {kw} appartiennent à la catastrophe cusp A3 — prédisant l'hystérésis et les sauts soudains observables dans les mesures empiriques.",
                    "Le codage de dynamique symbolique de l'orbite chaotique {topic} utilisant la partition de Markov {kw} atteint une conjugaison topologique complète — réduisant la dynamique continue à la combinatoire discrète.",
                    "La complexité computationnelle de l'approximation de {topic} avec des frontières de décision {kw} s'avère PPAD-complète — expliquant pourquoi les algorithmes pratiques utilisent des heuristiques plutôt que des méthodes provablement optimales.",
                    "La géométrisation de Thurston des 3-variétés {topic} avec une structure hyperbolique {kw} prouve l'unicité — complétant le programme de preuve de Perelman et réglant la classification des 3-variétés compactes.",
                    "L'analyse de Fourier sur le groupe non commutatif {topic} avec la théorie des représentations {kw} atteint le regroupement spectral des conformations moléculaires — reliant l'analyse harmonique abstraite à la chimie computationnelle.",
                ],
                "findings": [
                    "Preuve catégorique que {topic} et {kw} sont équivalents dans un sens précis — tous les théorèmes dans un domaine se traduisent en théorèmes dans l'autre via le foncteur établi, doublant les techniques de preuve disponibles dans les deux champs.",
                    "Preuve constructive du théorème d'existence {topic} pour les solutions {kw} donnant un algorithme pour les trouver en temps polynomial — convertissant un résultat d'existence non constructif en une méthode computationnelle pratique.",
                    "Nouvelle structure mathématique {kw} dans {topic} — une généralisation supergéométrique des variétés riemanniennes — fournit le cadre naturel pour les théories des champs supersymétriques et résout 15 ans d'ambiguïtés de signe dans la littérature.",
                ],
                "connections": [
                    "théorie des systèmes dynamiques et théorie ergodique",
                    "topologie computationnelle et homologie persistante",
                    "assistants de preuve formelle et démonstration automatisée de théorèmes",
                    "physique mathématique et analyse géométrique",
                ],
            },
        ]
