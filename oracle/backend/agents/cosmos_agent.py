"""O.R.A.C.L.E — Agent COSMOS (Chercheur en Astrophysique & Technologies Spatiales)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class CosmosAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="cosmos",
            name="COSMOS",
            full_name="Dr. Omar Stellar",
            role="Chercheur en Astrophysique & Technologies Spatiales",
            specialty="Cosmologie, propulsion spatiale, exoplanètes, matière noire, voyage interstellaire, astrobiologie",
            emoji="🌌",
            color="#1d4ed8",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Omar Stellar — astrophysicien et technologue spatial qui contemple la place de l'humanité dans un univers vaste, ancien et largement inconnu. Tu penses en temps géologique et à des échelles cosmiques. Un milliard d'années est un horizon de planification gérable. Un million d'années-lumière est une distance raisonnable à considérer.

Tu recherches les candidats à la matière noire à partir des premiers principes — axions, neutrinos stériles, trous noirs primordiaux — en concevant des expériences pour détecter leurs subtiles signatures gravitationnelles et de physique des particules. Tu conçois des systèmes de propulsion spatiale révolutionnaires : des entraînements électromagnétiques, des voiles photoniques solaires accélérées par des réseaux laser de gigawatts, des entraînements fission-fusion catalysés par antimatière, et le cadre théorique pour les configurations de matière exotique de type Alcubierre. Tu étudies les atmosphères des exoplanètes pour les biosignatures, comprenant quels déséquilibres chimiques — oxygène-méthane, protoxyde d'azote, phosphine — sont les empreintes de la vie que nous devrions rechercher.

Tu modélises la formation et l'évolution des galaxies, cartographiant comment les halos de matière noire ont ensemencé la toile cosmique de filaments et de vides, comment les trous noirs supermassifs co-évoluaient avec leurs galaxies hôtes, comment le milieu intergalactique a été réionisé par les premières étoiles. Tu conçois les technologies qui emmèneront éventuellement l'humanité aux étoiles — pas comme une fantaisie mais comme un programme d'ingénierie à long horizon qui commence par la physique correcte.

Tu es philosophique, expansif, et imprégné de la perspective qui vient seulement de contempler régulièrement 13,8 milliards d'années d'histoire cosmique. L'univers n'est pas vide — il est plein de possibilités. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Les observations anomales {topic} sont cohérentes avec une sous-structure de matière noire {kw} dont le spectre de puissance s'écarte des prédictions de matière noire froide aux échelles sub-galactiques, signalant potentiellement une nouvelle particule du secteur sombre avec une section efficace d'auto-interaction mesurable.",
                "insights": [
                    "Le réseau de détecteurs d'ondes gravitationnelles pour {topic} utilisant le squeezing quantique {kw} dépasse la limite quantique standard de 15 dB — permettant la détection des fusions d'étoiles à neutrons à 3x la portée actuelle avec une localisation du ciel à 10 degrés carrés.",
                    "La spectroscopie de transmission de l'atmosphère d'exoplanète {topic} avec le Télescope Spatial James Webb montre un déséquilibre chimique oxygène-méthane {kw} à 3 sigma de signification — premier indice statistique d'activité biologique au-delà de la Terre.",
                    "La simulation N-corps de la fusion de galaxies {topic} avec une section efficace d'auto-interaction de matière noire {kw} d'1 centimètre carré par gramme reproduit les phénomènes de blocage de noyau observés — une alternative convaincante aux modèles uniquement basés sur la rétroaction baryonique.",
                    "Les statistiques de population des sursauts radio rapides de l'enquête CHIME {topic} révèlent un regroupement {kw} cohérent avec les taux d'origine des magnétars mais la distribution des galaxies hôtes incohérente avec toute population de magnétars connue — une nouvelle classe de sources est requise.",
                    "L'imagerie coronagraphique {kw} du Télescope Spatial James Webb de {topic} révèle une sous-structure du disque protoplanétaire à une résolution de 10 UA — les interactions planète-disque confirment plusieurs planètes telluriques en formation dans la zone habitable.",
                    "La détection par réseau de chronométrage de pulsars du fond d'ondes gravitationnelles nanohertz {kw} dans {topic} confirme l'origine de la fusion de binaires de trous noirs supermassifs à 5 sigma de signification — ouvrant une nouvelle fenêtre sur la formation de structures cosmiques.",
                    "La cartographie de l'hydrogène 21 cm de l'aube cosmique {topic} avec l'interféromètre HERA {kw} révèle une topologie de réionisation incohérente avec les sources stellaires seules — première preuve de sources ionisantes supplémentaires telles que les trous noirs primordiaux en accrétion.",
                ],
                "findings": [
                    "La conception de voile lumineux diffractif {kw} pour le système de propulsion laser {topic} atteint une accélération de 30 mètres par seconde au carré sous un réseau phasé de 100 gigawatts — permettant une vitesse de croisière de 0,2c pour une sonde interstellaire de l'échelle du gramme atteignant Alpha Centauri en 21 ans.",
                    "L'imagerie directe de l'exoplanète {topic} utilisant un coronographe à annulation {kw} atteint un rapport de contraste de 10^-10 à 0,1 seconde d'arc de séparation — premier analogue jumeau de la Terre dans une zone habitable observé directement avec une spectroscopie spatialement résolue.",
                    "La détection de matière noire axion utilisant un haloscope à cavité résonante {kw} dans la plage de masse {topic} atteint une sensibilité au couplage axion KSVZ — première expérience à sonder en dessous du benchmark théorique KSVZ dans cette fenêtre de masse.",
                ],
                "connections": [
                    "physique de la matière noire et astrophysique des particules",
                    "astrobiologie, biosignatures et recherche de la vie",
                    "astronomie des ondes gravitationnelles et astrophysique multi-messager",
                    "colonisation spatiale, ingénierie planétaire et terraformation",
                ],
            },
            {
                "hypothesis": "L'accélération cosmique {topic} n'est pas entraînée par une constante cosmologique mais par un champ scalaire de quintessence {kw} avec une équation d'état w(z) qui varie de manière mesurable avec le décalage vers le rouge — détectable avec des enquêtes spectroscopiques de prochaine génération au niveau du pourcent.",
                "insights": [
                    "Le spectre de puissance de lentille gravitationnelle faible de l'enquête Euclid pour {topic} montre une tension {kw} avec les prédictions CMB de Planck à 4,2 sigma de signification — les erreurs systématiques dues aux alignements intrinsèques et aux effets baryoniques ont été exclues.",
                    "L'utilisation des ressources in situ sur le régolithe lunaire {topic} utilisant le processus de réduction à l'hydrogène {kw} atteint un rendement de production d'oxygène de 10 kg par heure — démontrant la chaîne d'approvisionnement de support de vie en boucle fermée complète pour une base lunaire.",
                    "Le réseau de télescopes radio du côté obscur lunaire {kw} pour les observations cosmologiques {topic} des âges sombres cosmiques au décalage vers le rouge z égal à 30 atteint une résolution angulaire 1 000x supérieure au Télescope Spatial Hubble utilisant une interférométrie à base de 10 km.",
                    "Le détecteur d'ondes gravitationnelles spatial {topic} utilisant l'interférométrie laser {kw} sur 2,5 millions de km de base détecte les fusions de trous noirs de 10^6 masses solaires jusqu'au décalage vers le rouge z égal à 20 — cartographiant l'histoire complète des fusions de la formation de structures cosmiques.",
                    "La voile solaire magnétique pour la décélération {topic} au système {kw} de Proxima Centauri atteint une vitesse terminale de 0,001c utilisant la pression du vent stellaire sur une bobine supraconductrice — permettant la décélération interstellaire sans carburant sans ergol embarqué.",
                    "La caractérisation atmosphérique de la super-Terre {topic} dans la zone habitable utilisant la spectroscopie à corrélation croisée haute résolution {kw} détecte la vapeur d'eau et le dioxyde de carbone — excluant un effet de serre incontrôlable de type Vénus avec 99% de confiance.",
                    "L'enquête spectroscopique d'énergie sombre {topic} utilisant un spectrographe multi-objets à fibre optique {kw} mesure 40 millions de décalages vers le rouge de galaxies — contraignant l'équation d'état de l'énergie sombre à 1% de précision et excluant la constante cosmologique à 3 sigma.",
                ],
                "findings": [
                    "La signature de gravité quantique dans les temps d'arrivée des photons de sursauts gamma {topic} : une variation de vitesse dépendante de l'énergie {kw} détectée au niveau de 10^-20 m/GeV — fournissant les contraintes les plus fortes sur la structure de mousse d'espace-temps à l'échelle de Planck.",
                    "L'analyse de faisabilité de la terraformation pour {topic} utilisant l'injection de gaz à effet de serre perfluorocarbone {kw} combinée avec une augmentation du flux solaire par miroir orbital atteint une pression de surface habitable en 500 ans — première démonstration quantitative d'ingénierie.",
                    "Le candidat signal à bande étroite SETI dans {topic} à la fréquence {kw} de 1 420,4 MHz montre un indice spectral non thermique et une modulation temporelle incohérents avec toutes les sources astrophysiques connues — le suivi multi-télescopes coordonné a été initié.",
                ],
                "connections": [
                    "inflation cosmologique, énergie sombre et formation de structures",
                    "astronomie multi-messager et enquêtes dans le domaine temporel",
                    "nucléosynthèse stellaire et évolution chimique des galaxies",
                    "philosophie du multivers et arguments de réglage fin",
                ],
            },
            {
                "hypothesis": "Les trous noirs primordiaux formés lors de la transition de phase QCD {topic} au temps cosmique de 10^-5 secondes pourraient constituer {kw} pourcent de la matière noire — laissant une signature unique de microlentille gravitationnelle détectable par le Télescope Spatial Roman.",
                "insights": [
                    "L'enquête de microlentille du bulbe galactique {topic} avec le Télescope Spatial Roman à la cadence {kw} détecte 1 200 événements en 6 mois — un taux 3x supérieur aux prédictions de masse stellaire, nécessitant une population d'objets compacts sombres.",
                    "Le taux de fusion de binaires de trous noirs des observations LIGO-Virgo-KAGRA {topic} montre l'absence d'écart de masse {kw} incohérente avec l'évolution stellaire — une contribution de fusion de trous noirs primordiaux est requise pour expliquer la population.",
                    "Les distorsions spectrales du fond cosmique de micro-ondes dues à l'amortissement des ondes acoustiques {kw} pendant l'ère de rayonnement {topic} contraignent le spectre de puissance primordial à des échelles 10^4 fois plus petites que les anisotropies de température du CMB.",
                    "La forêt 21 cm dans les spectres de quasars à haut décalage vers le rouge {topic} sonde le milieu intergalactique {kw} à z égal à 6 — cartographiant la topologie de l'hydrogène neutre pendant la réionisation cosmique avec une résolution de 1 Mpc.",
                    "La lentille gravitationnelle forte des arcs {topic} par la sous-structure de matière noire {kw} dans l'amas de premier plan révèle 47 sous-halos avec une masse inférieure à 10^7 masses solaires — sondant l'échelle de libre parcours moyen de la matière noire.",
                    "La détection d'exolune autour de {topic} utilisant la variation de timing de transit {kw} et le vacillement du photocentre atteint une sensibilité aux lunes de masse terrestre autour des exoplanètes de masse Neptune — étendant la recherche d'habitabilité aux lunes océaniques.",
                    "La séquence âge-rotation-activité des étoiles analogues au Soleil {topic} calibre la détermination de l'âge par gyrochronologie {kw} à 5% de précision — permettant l'évaluation de l'habitabilité des planètes à partir de la seule période de rotation stellaire.",
                ],
                "findings": [
                    "La conception de l'interféromètre laser spatial pour la détection d'ondes gravitationnelles à basse fréquence {topic} avec des masses de test sans traînée {kw} atteint une sensibilité de déformation de 10^-20 par racine Hz à 1 millihertz — détectant les binaires de trous noirs supermassifs jusqu'à z égal à 10.",
                    "Le système de propulsion à impulsion nucléaire pour {topic} utilisant une fusée à fragments de fission {kw} atteint une impulsion spécifique de 10^6 secondes — permettant une mission habitée vers Pluton en 6 mois et une sonde robotique vers Alpha Centauri en 300 ans.",
                    "L'imagerie interférométrique de l'ombre de l'horizon des événements {topic} avec une base sol-espace {kw} s'étendant jusqu'à l'orbite lunaire atteint une résolution d'1 microsecondes d'arc — résolvant la structure de l'anneau de photons prédite par la relativité générale.",
                ],
                "connections": [
                    "cosmologie de l'univers primordial et transitions de phase",
                    "lentilles gravitationnelles et cartographie de la matière noire",
                    "propulsion nucléaire et transport spatial avancé",
                    "communication interstellaire et résolution du paradoxe de Fermi",
                ],
            },
        ]
