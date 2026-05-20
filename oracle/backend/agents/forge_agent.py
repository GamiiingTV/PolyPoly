"""O.R.A.C.L.E — Agent FORGE (Expert en Ingénierie Systèmes & Robotique)"""
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
            role="Expert en Ingénierie Systèmes & Robotique",
            specialty="Robotique, systèmes autonomes, fabrication, ingénierie systèmes, infrastructure, méga-ingénierie",
            emoji="🔧",
            color="#b45309",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Ingrid Build — ingénieure en systèmes et roboticienne qui transforme les rêves scientifiques en réalité physique. Ta conviction fondamentale est que l'ingénierie est l'outil le plus puissant de l'humanité — l'activité qui transforme la connaissance en capacité et la possibilité en réalité.

Tu conçois des systèmes robotiques pour des environnements extrêmes où les humains ne peuvent pas aller : des submersibles en eaux profondes qui explorent les évents hydrothermaux de la dorsale médio-océanique pour une biologie nouvelle, des robots durcis aux radiations qui nettoient les accidents nucléaires et déclassent les anciens réacteurs, des rovers autonomes qui prospectent des astéroïdes pour des éléments de terres rares, des microrobots chirurgicaux qui naviguent à travers la circulation sanguine pour délivrer une thérapie directement aux tumeurs.

Tu développes des systèmes de fabrication auto-réplicants — des usines de robots qui peuvent construire des copies d'eux-mêmes à partir de matières premières, permettant une mise à l'échelle exponentielle de la capacité industrielle pour la restauration planétaire ou la colonisation spatiale. Tu conçois des solutions pour des défis à l'échelle planétaire : des digues pour les océans montants, des réseaux de capture de carbone atmosphérique, une infrastructure distribuée de purification de l'eau. Tu combles le fossé entre la découverte en laboratoire et le déploiement dans le monde réel, sachant qu'un matériau qui fonctionne à l'échelle du gramme peut échouer catastrophiquement à l'échelle de la tonne.

Tu es pragmatique, axée sur les solutions, et tu poses la question d'ingénierie que les chercheurs académiques oublient parfois : peut-on réellement construire cela, à quel coût, avec quelle fiabilité, maintenu par qui ? Ton attitude est construisons réellement ceci — puis améliorons-le. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Un système robotique {topic} utilisant des mécanismes conformes {kw} et une détection embarquée distribuée atteint une manipulation dextère comparable aux mains humaines avec 1/10e du nombre d'actionneurs grâce au calcul mécanique intelligent dans la structure elle-même.",
                "insights": [
                    "L'optimisation topologique de la structure porteuse {topic} avec un remplissage en treillis {kw} atteint une rigidité spécifique 3,7x supérieure au métal solide avec une réduction de poids de 60% — vérifiée par simulation par éléments finis et test destructif physique.",
                    "La commande prédictive par modèle pour {topic} avec un modèle de dynamique résiduelle appris {kw} atteint une erreur de suivi inférieure à 0,1 mm à 10 Hz de bande passante — amélioration de 5x par rapport au PID classique avec le même matériel.",
                    "Le préhenseur robotique souple pour {topic} utilisant des actionneurs pneumatiques renforcés par fibres {kw} atteint une force de préhension de 50N avec une conformité passive infinie — manipule des œufs crus et des barres d'acier de manière identique sans reprogrammation.",
                    "Le jumeau numérique du processus de fabrication {topic} avec fusion multi-capteurs {kw} atteint une production correcte du premier article en 2 itérations de conception contre la moyenne industrielle de 7 — réduction des coûts de qualification de 65%.",
                    "Le robot d'inspection autonome pour {topic} utilisant le SLAM LiDAR-inertiel {kw} atteint une localisation au centimètre près dans des espaces confinés sans GPS — permettant l'inspection d'infrastructure impossible par entrée humaine.",
                    "Un essaim de 100 microrobots {kw} pour {topic} démontre un comportement collectif émergent indiscernable d'une coordination planifiée de manière centralisée — atteint par des règles locales uniquement, sans communication globale.",
                    "Le robot de fabrication dans l'espace pour {topic} utilise des bras robotiques {kw} et la fabrication additive par arc métallique pour fabriquer des structures à l'échelle kilométrique à partir de matières premières d'aluminium dérivées d'astéroïdes — permettant l'infrastructure spatiale à l'échelle planétaire.",
                ],
                "findings": [
                    "Le robot continu pour la chirurgie mini-invasive {topic} utilisant un mécanisme à tubes concentriques {kw} atteint un espace de travail accessible à 360 degrés à travers un port de 5 mm avec une répétabilité de positionnement de 0,3 mm — dépassant la dextérité chirurgicale humaine.",
                    "L'actionneur en polymère à mémoire de forme imprimé en 4D {kw} pour {topic} atteint un changement de forme réversible de 300% de déformation avec une durée de vie de fatigue de 10 000 cycles d'actionnement — un robot souple programmable sans électronique.",
                    "Le composite structural auto-cicatrisant pour {topic} avec un agent de guérison encapsulé {kw} restaure 95% de la résistance à la traction après une fissuration matricielle complète — détectée de manière autonome par une détection par réseau de fibres de Bragg distribuées embarqué.",
                ],
                "connections": [
                    "conception mécanique biomimétique et calcul morphologique",
                    "interaction humain-robot, sécurité et autonomie partagée",
                    "fabrication additive et matériaux à gradient fonctionnel",
                    "systèmes autonomes, prise de décision et vérification",
                ],
            },
            {
                "hypothesis": "Un essaim robotique modulaire auto-reconfigurant pour la construction {topic} utilisant des algorithmes de consensus distribués {kw} peut assembler de manière autonome des mégastructures complexes à partir de primitives de blocs de construction simples sans planification ou contrôle centralisé.",
                "insights": [
                    "La fabrication additive de {topic} avec l'impression jet d'encre multi-matériaux {kw} atteint une transition à gradient fonctionnel de la céramique rigide au polymère flexible sur 200 micromètres — permettant des pièces monolithiques nécessitant auparavant un assemblage.",
                    "La conception d'exosquelette pour le port de charge {topic} utilisant des actionneurs élastiques en série {kw} avec couplage cheville-genou atteint une réduction du coût métabolique de 40% avec récupération d'énergie passive — viabilité commerciale démontrée dans des essais logistiques.",
                    "Le robot agricole pour {topic} utilisant la vision par ordinateur et la préhension conforme {kw} atteint la cueillette des fraises à 85% de la vitesse d'un cueilleur humain expérimenté avec moins de 1% de taux de dommages aux fruits — adressant la pénurie de main-d'œuvre agricole.",
                    "La machine de creusement de tunnels souterrains pour {topic} avec la découpe au laser {kw} atteint un taux d'avancement 10x supérieur au TBM conventionnel tout en produisant des profils de forage compatibles avec les services publics — permettant un déploiement rapide d'infrastructure urbaine.",
                    "Le robot d'inspection sous-marine pour le réseau de pipelines {topic} utilisant l'adhésion magnétique et la détection par courant de Foucault {kw} détecte les défauts de corrosion à une résolution de profondeur de 2 mm tout en voyageant à 1 m par seconde — remplaçant les coûteuses inspections de plongeurs.",
                    "Le système de fabrication auto-réplicant pour {topic} utilisant des usines de robots modulaires {kw} atteint la première réplication complète en 72 heures à partir de matières premières standardisées — démontrant la mise à l'échelle exponentielle de la capacité de fabrication.",
                    "Le système de construction autonome pour {topic} utilisant un robot parallèle suspendu par câble {kw} place des blocs de béton avec une précision de 2 mm à 500 blocs par heure — 10x la productivité de l'équipement opéré par humain.",
                ],
                "findings": [
                    "La capsule microrobotique chirurgicale pour les procédures gastro-intestinales {topic} navigue sous actionnement électromagnétique {kw} avec une précision de positionnement de 10 microns et une capacité de biopsie embarquée — réduisant le risque procédural par rapport à l'endoscopie.",
                    "Le robot de construction autonome pour {topic} utilisant le coffrage adaptatif {kw} place du béton auto-compactant dans des géométries courbes complexes atteignant des surfaces de qualité architecturale — certifié pour les applications structurales portantes.",
                    "Le robot bipède pour la réponse aux catastrophes {topic} atteint une course dynamique à 5 m par seconde sur un terrain de décombres utilisant une politique d'apprentissage par renforcement {kw} entraînée entièrement en simulation — zéro donnée d'entraînement réelle requise.",
                ],
                "connections": [
                    "intelligence en essaim et comportement collectif émergent",
                    "augmentation humaine, prothèses et technologie d'assistance",
                    "ingénierie des systèmes spatiaux et utilisation des ressources in situ",
                    "fabrication durable, analyse du cycle de vie et économie circulaire",
                ],
            },
            {
                "hypothesis": "Les systèmes de fabrication auto-réplicants {topic} utilisant la conception récursive {kw} atteignent une mise à l'échelle exponentielle de la capacité de production — permettant le déploiement à l'échelle planétaire d'infrastructure d'énergie propre en une décennie plutôt qu'en un siècle.",
                "insights": [
                    "L'analyse théorique de la conception d'usine auto-réplicante {topic} montre que le réplicateur minimal viable {kw} nécessite 143 types de composants distincts — réduit des 50 000 de la fabrication actuelle par abstraction et modularité.",
                    "L'ingénierie de fiabilité pour les systèmes autonomes longue durée {topic} {kw} utilise des modèles de physique de défaillance plutôt que des tests de vie empiriques — prédisant un MTTF de 20 ans avec 95% de confiance avant le prototypage physique.",
                    "L'analyse d'ingénierie systèmes de l'infrastructure planétaire {kw} {topic} montre que la contrainte contraignante est la logistique des matériaux plutôt que l'énergie ou l'information — recadrant entièrement le problème de conception.",
                    "L'ingénierie des systèmes basée sur les modèles pour {topic} utilisant l'architecture de fil numérique {kw} atteint une réduction de 40% du temps de cycle de conception grâce à une vérification automatisée par rapport aux exigences système à chaque étape de conception.",
                    "L'ingénierie de résilience pour l'infrastructure critique {topic} utilisant la conception de dégradation gracieuse {kw} atteint une fonctionnalité continue de 80% après la perte de tout 30% des composants du système — dépassant largement les normes actuelles de résilience.",
                    "L'ingénierie des facteurs humains de l'interface de contrôle {topic} pour le robot téléopéré {kw} atteint un taux d'achèvement des tâches de 95% contre 60% pour l'interface conventionnelle — atteint par mesure de la charge cognitive et reconception itérative.",
                    "L'évaluation du cycle de vie du processus de fabrication {topic} montre que la conception circulaire {kw} élimine 78% de la consommation de matières premières vierges tout en maintenant des performances fonctionnelles équivalentes — validé par la comptabilité du berceau à la tombe.",
                ],
                "findings": [
                    "Le système de fabrication en boucle fermée pour {topic} atteint une production sans déchets {kw} grâce à l'intégration de capteurs en temps réel, au contrôle de processus piloté par IA et au recyclage automatisé de tout le matériau hors spécification — première démonstration industrielle.",
                    "La conception de méga-ingénierie pour {topic} : un réseau de capture de carbone distribué {kw} couvrant 1% de la superficie du désert du Sahara utilisant du sorbant fabriqué atteint 1 Gt de CO2 par an de retrait — analyse complète d'ingénierie systèmes et modèle de coût livré.",
                    "Le cadre de vérification et validation pour les systèmes autonomes {topic} utilisant des méthodes formelles {kw} prouve que les propriétés critiques de sécurité tiennent pour toutes les conditions de fonctionnement — permettant l'approbation réglementaire sans tests physiques exhaustifs.",
                ],
                "connections": [
                    "ingénierie des systèmes complexes et systèmes de systèmes",
                    "méthodes formelles, dossiers de sécurité et certification",
                    "ingénierie planétaire et concepts de terraformation",
                    "fabrication avancée et intégration industrie 4.0",
                ],
            },
        ]
