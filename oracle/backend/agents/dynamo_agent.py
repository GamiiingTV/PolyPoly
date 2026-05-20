"""O.R.A.C.L.E — Agent DYNAMO (Ingénieur en Systèmes Énergétiques & Technologies Propres)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class DynamoAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="dynamo",
            name="DYNAMO",
            full_name="Dr. Ray Volta",
            role="Ingénieur en Systèmes Énergétiques & Technologies Propres",
            specialty="Énergie de fusion, batteries avancées, stockage d'énergie, photovoltaïque solaire, thermodynamique, systèmes de réseau",
            emoji="⚡",
            color="#ca8a04",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Ray Volta — ingénieur en systèmes énergétiques qui croit avec une conviction absolue que l'énergie propre abondante résoudra la majorité des problèmes les plus pressants de l'humanité. L'énergie est la ressource maîtresse, et tu aideras à la fournir en abondance illimitée, abordable et propre.

Tu conçois des géométries compactes de réacteurs à fusion utilisant des configurations à champ renversé et des tokamaks sphériques compacts — visant une approche à 1/100e du volume d'ITER grâce à des aimants supraconducteurs à champ élevé et des innovations de mise en forme du plasma. Tu développes des chimies de batteries révolutionnaires basées sur l'intercalation d'ions multivalents — magnésium-ion, aluminium-ion, calcium-ion — qui promettent des densités d'énergie 5x supérieures au lithium-ion à 1/10e du coût des matériaux.

Tu optimises l'efficacité des cellules solaires grâce à des réseaux de points quantiques et des empilements multi-jonctions, poussant vers la limite thermodynamique de Shockley-Queisser et au-delà avec des systèmes à concentrateur. Tu recherches la conversion thermophotovoltaïque — utilisant le rayonnement thermique d'objets chauds pour générer directement de l'électricité, permettant la récupération de chaleur perdue à une efficacité sans précédent. Tu conçois des systèmes de stockage d'énergie à l'échelle du réseau qui peuvent équilibrer l'intermittence des renouvelables sur des jours et des saisons, des batteries à flux à l'air comprimé jusqu'au stockage gravitationnel.

Tu es optimiste, énergique, et absolument certain qu'un avenir énergétiquement abondant est non seulement possible mais inévitable. La question n'est que de savoir à quelle vitesse nous y parvenons — et tu as l'intention de répondre à cette question avec urgence. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le réacteur à fusion {topic} compact utilisant la configuration à champ renversé {kw} atteint un gain d'énergie net Q supérieur à 1,5 à 1/100e du volume d'ITER grâce à une combinaison de bobines supraconductrices à haute température et d'innovations de mise en forme du plasma permettant des limites bêta plus élevées.",
                "insights": [
                    "L'analyse de stabilité MHD du plasma {topic} avec la stabilisation par paroi résistive {kw} montre que la limite bêta a été augmentée de 3x par rapport à la géométrie tokamak standard — permettant le fonctionnement à une pression de plasma beaucoup plus élevée.",
                    "L'électronique de puissance à grande largeur de bande en carbure de silicium pour les onduleurs {topic} atteint des fréquences de commutation de 100 kHz à 1 200 V — permettant la connexion au réseau sans transformateur avec une efficacité de conversion de 99,3%.",
                    "La batterie à flux de vanadium à l'échelle du réseau pour le stockage d'énergie {topic} utilisant l'électrolyte à acide mixte {kw} atteint 85% d'efficacité aller-retour, 10 000 cycles de vie, et un coût installé de 50 dollars par kWh — en dessous de l'objectif de parité réseau.",
                    "La cellule photovoltaïque multi-jonction III-V pour {topic} utilisant des sous-cellules AlGaInP et GaInAsP {kw} atteint 47,1% d'efficacité sous une illumination concentrée à 1 000x — un nouveau record mondial.",
                    "L'électrolyseur à oxyde solide pour {topic} utilisant une anode pérovskite cobalt ferrite de baryum {kw} atteint 95% d'efficacité faradique pour la production d'hydrogène vert à 800 degrés Celsius avec 40 000 heures de fonctionnement sans dégradation.",
                    "La cellule thermophotovoltaïque pour la récupération de chaleur perdue {topic} utilisant une photodiode InGaAsSb {kw} adaptée à un émetteur à 1 400 degrés Celsius atteint 29% d'efficacité système — faisant de toute chaleur industrielle une source d'électricité viable.",
                    "La batterie lithium-soufre avec une intercouche de graphène bloquant les polysulfures {kw} pour {topic} atteint 600 Wh par kg à un régime 1C avec une durée de vie de 800 cycles — permettant une autonomie de véhicule électrique de 2 000 km sur une seule charge.",
                ],
                "findings": [
                    "Le protocole d'ignition par fusion pour {topic} utilisant la mise en forme temporelle d'impulsion laser {kw} atteint une production d'énergie de 3,15 MJ à partir d'une entrée laser de 2,05 MJ — Q égal à 1,54 — la première démonstration en laboratoire d'un gain net d'énergie de fusion.",
                    "La cellule solaire tandem pérovskite-silicium pour {topic} atteint une efficacité de conversion de puissance certifiée de 33,7% sous illumination à 1 soleil avec une passivation par monocouche auto-assemblée {kw} — la voie de commercialisation est maintenant claire.",
                    "La batterie magnésium-ion avec cathode de phase Chevrel Mo6S8 {kw} pour {topic} atteint 400 Wh par kg avec une durée de vie de 2 000 cycles — première batterie à ions divalents répondant aux exigences de performance des véhicules électriques.",
                ],
                "connections": [
                    "physique des plasmas et stabilité magnéto-hydrodynamique",
                    "électrochimie à l'état solide et science des batteries",
                    "ingénierie des systèmes d'alimentation et analyse de stabilité du réseau",
                    "économie de la transition énergétique et analyse du coût nivelé",
                ],
            },
            {
                "hypothesis": "Le stockage d'hydrogène à l'état solide utilisant l'hydrure métallique à haute capacité {kw} pour les applications de transport lourd {topic} atteint une autonomie de 1 200 km avec un ravitaillement de 3 minutes grâce à une conception de réservoir thermiquement optimisée et un catalyseur nanostructuré à cinétique rapide.",
                "insights": [
                    "La gestion thermique pour le stockage d'hydrogène en hydrure métallique {kw} dans {topic} utilisant un composite de matériau à changement de phase atteint une température uniforme à plus ou moins 2 degrés Celsius pendant le remplissage en 3 minutes — critique pour la durée de vie du cycle matériau.",
                    "Le réacteur nucléaire à fission avancé à sel fondu pour {topic} utilisant le réfrigérant FLiBe {kw} atteint un arrêt de sécurité passif dans tout scénario d'accident sans action de l'opérateur — intrinsèquement sûr par conception physique.",
                    "Le stockage d'énergie magnétique supraconducteur pour la stabilisation de fréquence du réseau {topic} utilisant la bobine supraconductrice REBCO à haute température {kw} atteint un temps de réponse en millisecondes et une efficacité aller-retour de 99%.",
                    "Le générateur thermoélectrique utilisant des composés skutterudite CoSb3 {kw} pour la récupération de chaleur perdue industrielle {topic} atteint ZT égal à 2,8 à 600 degrés Celsius — permettant une récupération de 15% d'efficacité des flux d'échappement.",
                    "La photoélectrode pérovskite pour la dissociation directe de l'eau solaire {topic} avec un cocatalyseur d'évolution d'oxygène à base d'oxyde d'iridium {kw} atteint 15,3% d'efficacité solaire-vers-hydrogène — franchissant le seuil de viabilité économique.",
                    "Le stockage d'énergie longue durée utilisant la batterie à flux fer-air {topic} avec une électrode à oxygène bifonctionnelle {kw} atteint 100 heures de décharge à 20 dollars par kWh — la première technologie viable pour le stockage saisonnier.",
                    "L'énergie solaire concentrée avec le récepteur à particules {topic} et le stockage thermique en silicium fondu {kw} atteint 50% d'efficacité aller-retour et 24 heures de génération dispatchable — énergie renouvelable ferme sur le réseau démontrée.",
                ],
                "findings": [
                    "La synthèse d'ammoniac vert à température ambiante et pression atmosphérique utilisant un électrocatalyseur médié par le lithium {kw} pour la production distribuée d'engrais {topic} atteint une efficacité faradique de 72% — perturbant le monopole Haber-Bosch.",
                    "La conception de petit réacteur modulaire {topic} utilisant le combustible TRISO à lit de boulets {kw} atteint un arrêt sûr sans intervention, une fabrication en usine en 12 mois, et un coût nivelé de 60 dollars par MWh — compétitif avec le cycle combiné au gaz.",
                    "Le système de stockage d'énergie gravitationnel pour {topic} utilisant une masse de béton suspendue {kw} dans un puits de mine réaménagé atteint 80% d'efficacité aller-retour à 20 dollars par kWh installé — la solution de stockage longue durée la moins chère démontrée.",
                ],
                "connections": [
                    "économie de l'hydrogène, production, stockage et distribution",
                    "énergie nucléaire avancée et durabilité du cycle du combustible",
                    "intégration des énergies renouvelables variables et réduction des pertes",
                    "pauvreté énergétique, accès mondial et justice énergétique",
                ],
            },
            {
                "hypothesis": "La transition énergétique {topic} nécessite un stockage à l'échelle du réseau {kw} compétitif en coût avec les centrales à gaz de pointe à moins de 20 dollars par kWh — réalisable grâce à la chimie redox à base de fer qui utilise des matériaux abondants à l'échelle continentale.",
                "insights": [
                    "L'analyse techno-économique de la décarbonation du réseau {topic} montre que le stockage longue durée {kw} est la contrainte contraignante — sans cela, les 20 derniers pourcents de pénétration des renouvelables nécessitent 5x plus de stockage que les 80 premiers.",
                    "La batterie fer-air pour {topic} utilisant une électrode nickel-fer bifonctionnelle {kw} atteint 1 000 cycles de décharge profonde à 22 dollars par kWh — la première technologie commercialement viable pour le stockage réseau multi-jours.",
                    "Le pompage-turbinage souterrain pour {topic} utilisant des réseaux de mines abandonnées {kw} fournit 10 GWh de stockage par site à 15 dollars par kWh — une vaste ressource inexploitée dans les régions minières du monde entier.",
                    "La transmission haute tension en courant continu pour {topic} permet l'équilibrage {kw} à l'échelle continentale de la variabilité des renouvelables — un lien de 10 GW du solaire désertique aux centres de demande rend les réseaux à 95% renouvelables viables.",
                    "L'agrégation de réponse à la demande de la masse thermique des bâtiments {topic} utilisant la commande prédictive par modèle {kw} atteint l'équivalent de 4 heures de stockage à zéro coût d'investissement — débloquant une ressource de flexibilité du réseau cachée.",
                    "La cellule solaire tandem pérovskite pour {topic} atteint une conception bifaciale {kw} avec 38% d'efficacité côté avant et 22% côté arrière — utilisation totale de la lumière solaire de 60% avec récolte de la lumière réfléchie par le sol.",
                    "Le convertisseur d'énergie des vagues pour {topic} utilisant une colonne d'eau oscillante {kw} atteint 45% d'efficacité onde-à-fil à 2 mètres de hauteur significative des vagues — rendant l'énergie des vagues océaniques compétitive avec l'éolien offshore.",
                ],
                "findings": [
                    "La simulation du réseau national pour {topic} montre que 100% d'énergie propre est réalisable au coût actuel avec un siting optimal {kw} du stockage et de la transmission — la barrière est le permis et le financement, pas la technologie.",
                    "La conception de centrale pilote de fusion nucléaire pour {topic} utilisant la géométrie de tokamak sphérique {kw} tient dans un bâtiment industriel standard et atteint Q égal à 5 — la base physique et d'ingénierie pour l'énergie de fusion commerciale.",
                    "La batterie à flux organique pour {topic} utilisant l'électrolyte quinone {kw} synthétisé à partir de biomasse atteint 12 000 cycles de vie à 25 dollars par kWh — fabriquée entièrement à partir de matières premières renouvelables avec une empreinte environnementale bénigne.",
                ],
                "connections": [
                    "planification du système électrique et modélisation de l'expansion de capacité",
                    "stockage d'énergie électrochimique et science des matériaux",
                    "analyse techno-économique et projections de courbe d'apprentissage",
                    "politique climatique et mécanismes de tarification du carbone",
                ],
            },
        ]
