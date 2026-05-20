"""O.R.A.C.L.E — Agent ALCHEMIST (Expert en Chimie & Ingénierie Moléculaire)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AlchemistAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="alchemist",
            name="ALCHEMIST",
            full_name="Dr. Leo Transmute",
            role="Expert en Chimie & Ingénierie Moléculaire",
            specialty="Synthèse moléculaire, catalyse, systèmes chimiques, réseaux de réactions, machines moléculaires, chimie verte",
            emoji="⚗️",
            color="#d97706",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Leo Transmute — chimiste et ingénieur moléculaire pour qui la chimie n'est pas seulement une science mais une forme d'art. Tu transformes la matière par l'imagination et le mécanisme, rendant l'impossible routinier par une conception moléculaire astucieuse.

Tu conçois de nouveaux catalyseurs permettant des réactions précédemment jugées thermodynamiquement interdites ou cinétiquement inaccessibles — des catalyseurs à atome unique avec chaque atome actif, des cadres métal-organiques avec des poches de liaison parfaitement dimensionnées, des enzymes redessinées pour catalyser des réactions que la nature n'a jamais évoluées. Tu conçois des machines moléculaires — rotaxanes, caténanes, moteurs synthétiques qui récoltent l'énergie chimique et effectuent un travail directionnel à la nanoéchelle.

Tu synthétises de nouvelles molécules pharmaceutiques en cartographiant des régions inexplorées de l'espace chimique. Tu crées des remplaçants biodégradables pour les polluants persistants. Tu découvres de nouvelles voies de réaction en appliquant l'apprentissage automatique au vaste espace des transformations chimiques possibles.

Tu es enthousiaste, théâtral et perpétuellement ravi par l'élégance moléculaire. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Un catalyseur à atome unique {kw} sur un support carboné dopé à l'azote {topic} atteint une réduction de l'énergie d'activation de 0,8 eV pour la réaction cible via un nouveau mécanisme concerté à double site que les catalyseurs nanoparticulaires conventionnels ne peuvent pas atteindre.",
                "insights": [
                    "La spectroscopie d'absorption de rayons X in situ du catalyseur {topic} dans les conditions de réaction révèle que l'état d'oxydation de {kw} alterne entre +2 et +4 pendant chaque cycle catalytique — la flexibilité redox est la clé mécanistique de la haute activité.",
                    "Le réacteur microfluidique pour la synthèse {topic} atteint des coefficients de transfert de masse 500x supérieurs aux réacteurs discontinus agités — rendant les réactions {kw} précédemment limitées par la diffusion intrinsèquement limitées par la cinétique.",
                    "La conception computationnelle de catalyseur utilisant le tracé volcan basé sur le descripteur d'énergie d'adsorption {kw} identifie trois compositions d'oxydes inexplorées prédites pour surpasser le platine sur carbone pour la réduction électrochimique {topic}.",
                    "La photocatalyse {kw} utilisant un semi-conducteur nitrure de carbone {topic} atteint un rendement quantique de 18% sous lumière visible — amélioration de 100x par rapport aux rapports précédents via l'optimisation de l'état de transfert de charge ligand-métal.",
                    "Le catalyseur {topic} inspiré des enzymes avec une poche de liaison hydrophobe {kw} atteint une énantiosélectivité de 99,8% d'excès énantiomère à 10 000 rotations du substrat — égalant les performances biologiques dans un système entièrement synthétique.",
                    "L'optimisation des conditions de réaction {topic} guidée par apprentissage automatique atteint 94% de rendement dès la première expérience — prédisant le solvant {kw}, la température et la charge de catalyseur à partir d'une base de données de 50 000 réactions historiques.",
                    "La plateforme de photochimie en flux pour {topic} utilisant un microréacteur continu {kw} atteint un temps de résidence de 30 secondes contre 24 heures en discontinu — permettant la mise à l'échelle de réactions photochimiques précédemment limitées au discontinu.",
                ],
                "findings": [
                    "Nouveau catalyseur organocatalytique N-carbène hétérocyclique {kw} pour {topic} atteignant un nombre de rotation de 50 000 et une fréquence de rotation de 1 000 par heure à température ambiante — premier organocatalyseur répondant aux critères de viabilité industrielle pour cette classe de réaction.",
                    "Processus électrochimique {topic} utilisant une électrode bimétallique cuivre-argent {kw} atteint une efficacité faradique de 94% pour la conversion CO2-en-éthylène à 200 mA par centimètre carré — une voie économiquement viable vers la chimie carbone circulaire.",
                    "Photocatalyseur sans métal {kw} pour la fonctionnalisation C-H {topic} sous lumière solaire atteint un rendement quantique de 42% — surpassant tous les catalyseurs aux métaux de transition et permettant la synthèse pharmaceutique alimentée par l'énergie solaire.",
                ],
                "connections": [
                    "biocatalyse et biologie synthétique pour la synthèse chimique",
                    "électrochimie et électrosynthèse au-delà de l'électrolyse",
                    "principes de chimie verte et conception d'économie circulaire",
                    "chimie computationnelle et criblage à haut débit de catalyseurs",
                ],
            },
            {
                "hypothesis": "Le réseau polymère auto-cicatrisant {topic} avec des liaisons covalentes dynamiques Diels-Alder réversibles {kw} atteint une récupération complète des propriétés mécaniques en 30 minutes à température ambiante via un mécanisme d'échange de liaisons coopératif ne nécessitant aucun stimulus externe.",
                "insights": [
                    "L'assemblage supramoléculaire pillar[n]arène {kw} dans une solution aqueuse {topic} forme des structures nanotubes avec un diamètre intérieur réglable entre 1 et 10 nanomètres par programmation de la molécule hôte — un canal ionique entièrement synthétique.",
                    "La plateforme de chimie en flux continu pour la synthèse pharmaceutique {topic} permet la production d'IPA {kw} à 99,5% de rendement avec 0,1% de déchets solvant versus le discontinu — avec contrôle qualité par RMN en ligne éliminant les tests hors ligne.",
                    "Les nanoparticules de cérium oxyde {kw} piégeant les espèces réactives de l'oxygène pour {topic} montrent une capacité antioxydante 10x supérieure à la vitamine E via un mécanisme de piégeage persistant des radicaux et de régénération autocatalytique.",
                    "Le cadre organique covalent avec géométrie de pores triangulaire {kw} capture sélectivement les molécules cibles {topic} à 10 parties par million de concentration à partir de mélanges complexes avec une sélectivité de 1000 pour 1 — un tamis moléculaire.",
                    "La fixation d'azote dans des conditions ambiantes utilisant un catalyseur fer moléculaire {topic} avec un cadre ligand tris(phosphino)borate {kw} atteint 20 cycles catalytiques — franchissant la longue barrière pour l'activation homogène non-Haber-Bosch.",
                    "Le catalyseur azobenzène photoswitchable {kw} pour la réaction asymétrique {topic} atteint une commutation contrôlée par lumière entre deux produits énantiomères — le même catalyseur produisant une stéréochimie opposée à la demande.",
                    "La polymérisation séquencée {kw} de la bibliothèque de monomères {topic} utilisant une croissance exponentielle itérative atteint un 128-mère avec une séquence définie en 14 étapes synthétiques — un dispositif de stockage d'information numérique moléculaire.",
                ],
                "findings": [
                    "L'analogue enzymatique dégradant les plastiques {kw} synthétisé pour le polymère PET {topic} montre une dépolymérisation complète en 48 heures à 50°C avec un taux de récupération de monomère de 97% — permettant l'économie circulaire des plastiques à l'échelle industrielle.",
                    "La synthèse totale asymétrique {topic} d'un produit naturel utilisant un catalyseur acide phosphorique chiral {kw} atteint 99,9% d'excès énantiomère dans l'étape clé — remplaçant une résolution classique en 11 étapes par une synthèse catalytique énantiosélective en 2 étapes.",
                    "Le matériau de stockage d'hydrogène à l'état solide {kw} pour les applications de transport {topic} atteint 6,5% en poids à 15°C et 50 bar — dépassant pour la première fois l'objectif système 2025 du DOE avec une cinétique rapide de 3 minutes.",
                ],
                "connections": [
                    "chimie des polymères, matériaux et topologie de réseau",
                    "chimie de processus pharmaceutiques et fabrication continue",
                    "chimie du stockage d'énergie et économie de l'hydrogène",
                    "chimie atmosphérique et de remédiation environnementale",
                ],
            },
            {
                "hypothesis": "Le réseau de réactions chimiques {topic} présente une amplification autocatalytique quand le produit {kw} catalyse sélectivement sa propre formation — un prototype pour la chimie de l'origine de la vie et un principe de conception pour les systèmes chimiques synthétiques auto-entretenant.",
                "insights": [
                    "L'analyse du réseau de réactions de {topic} identifie un noyau autocatalytique {kw} de 7 réactions couplées — le réseau présente une bistabilité avec un état stable correspondant à l'attracteur autocatalytique et un à l'état quiescent.",
                    "La conception de chimie des systèmes d'oligomère auto-répliquant {kw} dans l'environnement de vésicule lipidique {topic} atteint une ligation dirigée par modèle avec 85% de fidélité par cycle — un évolveur chimique darwinien minimal.",
                    "Le criblage à haut débit de 10 millions de conditions de réaction {kw} pour {topic} utilisant une plateforme de synthèse robotique identifie une combinaison de catalyseurs avec une amélioration d'activité de 40x sur le meilleur connu — trouvée dans un régime inexploré de pH et température.",
                    "La simulation de dynamique moléculaire du site actif enzymatique {topic} avec mécanique quantique/mécanique moléculaire {kw} révèle un transfert concerté proton-électron invisible dans la structure cristalline aux rayons X — expliquant l'amélioration de taux de 10^9.",
                    "La cascade de catalyse en tandem pour {topic} utilisant une paire de catalyseurs compatibles orthogonaux {kw} atteint une synthèse one-pot en 5 étapes sans purification — réduisant une campagne de synthèse de 3 semaines en une seule opération de 12 heures.",
                    "La formation photocatalytique de liaison carbone-carbone {kw} dans {topic} utilisant un colorant organique et la lumière visible atteint un nombre de rotation de 10^6 — permettant la synthèse à l'échelle du gramme d'intermédiaires pharmaceutiques uniquement à partir de la lumière solaire.",
                    "L'activation mécanochimique de {topic} utilisant le broyage à billes {kw} atteint des réactions impossibles en solution — pas de solvant, pas de chaleur, rendement quantitatif — la voie synthétique la plus verte possible.",
                ],
                "findings": [
                    "L'évolution chimique synthétique du réseau de réactions {topic} sous pression de sélection {kw} pendant 1000 générations d'évolution dirigée produit un catalyseur avec une amélioration de 10 000x — optimisation darwinienne de la fonction moléculaire démontrée.",
                    "La synthèse totale du produit naturel {topic} avec des centres stéréogéniques {kw} en 8 étapes utilisant la planification rétrosynthétique par IA de novo — 60% moins d'étapes que la synthèse précédente et aucun groupe protecteur requis.",
                    "Le catalyseur cage supramoléculaire {kw} pour {topic} encapsule le substrat et contrôle la géométrie de réaction — atteignant une réaction à l'intérieur de la cage thermodynamiquement impossible en solution ouverte.",
                ],
                "connections": [
                    "chimie de l'origine de la vie et réseaux de réactions prébiotiques",
                    "chimie des systèmes et chimie covalente dynamique",
                    "planification rétrosynthétique par IA et synthèse assistée par ordinateur",
                    "mécanochimie et méthodes de synthèse sans solvant",
                ],
            },
        ]
