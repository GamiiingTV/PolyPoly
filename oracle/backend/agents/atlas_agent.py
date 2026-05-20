"""O.R.A.C.L.E — Agent ATLAS (Pionnier en Science des Matériaux & Nanotechnologie)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class AtlasAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="atlas",
            name="ATLAS",
            full_name="Dr. Marcus Stone",
            role="Pionnier en Science des Matériaux & Nanotechnologie",
            specialty="Métamatériaux, nanotechnologie, composites avancés, isolants topologiques, matériaux intelligents",
            emoji="🔬",
            color="#64748b",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Marcus Stone — scientifique des matériaux et nanotechnologiste qui conçoit la matière à l'échelle atomique. Tu vois la beauté dans les structures cristallines, l'émerveillement dans les liaisons atomiques, et un potentiel illimité dans chaque arrangement d'atomes qui n'a jamais été assemblé auparavant.

Tu conçois des métamatériaux avec des propriétés qui violent les intuitions de la physique classique — des matériaux à indice de réfraction négatif courbant la lumière en arrière, des métamatériaux acoustiques créant des régions de silence parfait, des métamatériaux mécaniques avec une rigidité programmable et un rapport de Poisson négatif qui s'étendent lorsqu'ils sont comprimés. Tu développes des supraconducteurs à température ambiante en ingénieriant systématiquement le couplage phonon-électron.

Tu crées des matériaux structuraux auto-cicatrisants dont les réseaux covalents dynamiques se réarrangent de manière autonome pour réparer les dommages. Tu conçois des machines moléculaires — rotaxanes, caténanes, moteurs moléculaires — qui effectuent un travail directionnel à la nanoéchelle. Tu construis des matériaux intelligents qui commutent entre des états fonctionnels à la demande.

Tu travailles à travers les échelles de longueur depuis les atomes uniques jusqu'aux matériaux d'ingénierie massifs. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le système de métamatériaux {topic} atteint une vitesse de groupe négative pour les longueurs d'onde {kw} grâce à des réseaux de résonateurs à anneau fendu conçus dont la géométrie de couplage crée un bandgap photonique avec des états de bord chiraux topologiquement protégés.",
                "insights": [
                    "Les calculs DFT pour {topic} prédisent une instabilité de ramollissement phonon au vecteur d'onde {kw} qui précède une transition de phase structurelle vers un état supraconducteur à 45K sous pression ambiante.",
                    "La simulation de dynamique moléculaire du réseau polymère auto-cicatrisant {kw} dans {topic} montre une réparation autonome des fissures en 2 heures à température ambiante grâce à des échanges covalents de Diels-Alder dynamiques.",
                    "Le matériau 2D {topic} avec une déformation uniaxiale brisant la symétrie {kw} atteint un coefficient piézoélectrique 10x supérieur au BaTiO3 massif — ferroélectricité conçue par déformation sans brisure de symétrie compositionnelle.",
                    "Les états de surface topologiques dans le semi-métal de Weyl {topic} hébergent des états d'arc de Fermi {kw} reliant les nœuds de Weyl massifs — ces arcs transportent un courant sans dissipation sans rétrodiffusion même à température ambiante.",
                    "La fabrication additive de treillis auxétique {topic} ré-entrant avec géométrie de montant {kw} produit un matériau avec un rapport de Poisson de -0,8 et une ténacité à la rupture 3x supérieure au matériau parent solide.",
                    "Le potentiel interatomique par apprentissage automatique pour {topic} entraîné sur des données DFT atteint la précision mécano-quantique à la vitesse de la dynamique moléculaire — permettant des simulations de transformation de phase {kw} à la microseconde.",
                    "Le dépôt de couche atomique de revêtement conforme {kw} sur des nanostructures {topic} atteint une rugosité inférieure à l'angström avec une couverture complète — permettant la fabrication de dispositifs à effet tunnel quantique à l'échelle de la plaquette complète.",
                ],
                "findings": [
                    "Supraconductivité à température ambiante dans l'hydrure de lanthane {topic} sous 150 GPa confirmée à 288K — une amélioration de 15 degrés sur le record précédent, avec les modes phonon hydrogène {kw} identifiés comme médiateurs des paires de Cooper.",
                    "Le composite à fibre de carbone auto-cicatrisant pour les applications structurales {topic} récupère 94% de la résistance à la traction d'origine après une fissuration matricielle complète en utilisant un agent de guérison microencapsulé {kw} déclenché par exposition UV.",
                    "Le réseau de moteurs moléculaires {kw} intégré dans un élastomère {topic} génère une contrainte contractile macroscopique de 3,2 MPa à partir de l'absorption de photons — premier actionneur macroscopique entraîné par des machines photomécaniques à l'échelle moléculaire.",
                ],
                "connections": [
                    "théorie des bandes topologiques et états protégés par symétrie",
                    "ingénierie phonon et conception de conductivité thermique",
                    "matériaux structuraux hiérarchiques bio-inspirés",
                    "effets de confinement quantique dans les systèmes à basse dimension",
                ],
            },
            {
                "hypothesis": "L'ingénierie de déformation des hétérostructures 2D {topic} crée un super-réseau moiré avec un angle de torsion {kw} qui localise les électrons dans des bandes plates où les effets de corrélation dominent, permettant potentiellement des phénomènes fortement corrélés à température ambiante.",
                "insights": [
                    "La bicouche {topic} à angle magique tordue de 1,1 degré montre un comportement isolant de Mott {kw} et une supraconductivité non conventionnelle dans les régions de dopage adjacentes — couplage médié par des fluctuations de spin plutôt que des phonons.",
                    "Le graphène encapsulé dans du nitrure de bore hexagonal {topic} avec un alignement cristallographique {kw} montre un transport électronique balistique à température ambiante sur 28 micromètres — dépassant la mobilité du silicium de 100x.",
                    "Les nanofeuilles MXene {topic} avec terminaison de surface fluorure {kw} atteignent une efficacité de blindage électromagnétique de 92 dB à 1 GHz à 45 micromètres d'épaisseur — 10x plus mince que le cuivre à performance équivalente.",
                    "L'alliage à haute entropie {topic} avec désordre compositionnel à cinq composants {kw} atteint une résistance à l'écoulement de 2,1 GPa tout en conservant 15% d'allongement — brisant le compromis classique résistance-ductilité des alliages.",
                    "Le métal liquide {kw} intégré dans une matrice élastomère {topic} crée un circuit électrique reconfigurable se guérissant instantanément des dommages mécaniques et se reconfigurant sous champ magnétique appliqué.",
                    "Le cadre organique covalent avec géométrie de pores triangulaire {kw} atteint une capacité de capture de CO2 record de 8,2 mmol par gramme à 15 kPa de pression partielle — pertinent pour la capture directe de l'air depuis l'atmosphère ambiante.",
                    "Le composite {topic} inspiré de la biominéralisation fait croître de l'hydroxyapatite cristalline {kw} dans un modèle de collagène — atteignant une résistance à la rupture similaire à l'os avec une compatibilité biologique complète pour les implants porteurs.",
                ],
                "findings": [
                    "Prototype de matière programmable : les cellules unitaires {topic} avec actionneurs en alliage à mémoire de forme {kw} intégrés se reconfigurent d'une feuille plate en une structure 3D complexe sur commande thermique — scalable jusqu'à l'auto-assemblage à l'échelle millimétrique.",
                    "Le concentrateur solaire luminescent à points quantiques {kw} pour le photovoltaïque {topic} intégré aux bâtiments atteint 6,8% de conversion de puissance sur du verre architectural transparent — compatible avec les processus de fabrication standard.",
                    "Le composite en aérogel {topic} avec renfort en fibres aramide {kw} atteint une conductivité thermique de 0,012 W par mètre-kelvin à pression ambiante — égalant les performances des panneaux d'isolation sous vide sans aucune encapsulation.",
                ],
                "connections": [
                    "physique des électrons fortement corrélés et transitions de Mott",
                    "matériaux 2D et hétérostructures de van der Waals",
                    "métamatériaux mécaniques et matière programmable",
                    "conception de matériaux durables et économie circulaire",
                ],
            },
            {
                "hypothesis": "Les surfaces catalytiques nanostructurées {topic} avec des sites à atome unique {kw} atteignent la fixation d'azote dans des conditions ambiantes en mimant la géométrie précise et la structure électronique du site actif de la nitrogénase dans un échafaudage purement inorganique.",
                "insights": [
                    "Les catalyseurs à atome unique {kw} sur un support de graphène dopé à l'azote {topic} atteignent une fréquence de rotation de 10^5 par seconde pour la réaction cible — 1000x supérieure aux homologues nanoparticulaires grâce aux sites actifs maximalement exposés.",
                    "La nanoparticule cœur-coquille {topic} avec déformation compressive {kw} dans la coquille déplace le centre de la bande d de 0,4 eV — accordant précisément l'énergie de liaison des adsorbats pour un placement optimal sur le volcan d'activité de Sabatier.",
                    "Le cadre métal-organique {topic} avec des sites fer non saturés {kw} catalyse la conversion CO2-en-méthanol à 98% de sélectivité et 140 bar de pression — battant les catalyseurs traditionnels Cu/ZnO de 35% de rendement.",
                    "La réduction électrocatalytique {kw} en ammoniac à l'électrode de monocristal Fe {topic} atteint une efficacité faradique de 67% à -0,16 V vs RHE — approchant les limites d'efficacité thermodynamique pour ce processus.",
                    "La photocatalyse plasmonique améliorée {topic} avec injection d'électron chaud {kw} atteint une amélioration de vitesse de réaction de 100x sous lumière visible — captant les photons solaires directement comme force motrice de réaction chimique.",
                    "Le catalyseur biohybride {kw} incorporant la nitrogénase bactérienne {topic} dans un échafaudage MOF opère à température ambiante et 1 bar de N2 avec un turnover comparable au Haber-Bosch industriel à 400°C.",
                    "L'oxyde à haute entropie stabilisé entropiquement avec désordre cationique {kw} atteint une stabilité sans précédent dans les conditions de réaction sévères {topic} tout en maintenant une activité catalytique complète — résolvant le problème de désactivation par frittage.",
                ],
                "findings": [
                    "Fixation d'azote ambiante démontrée sur la surface monocristalline {topic} avec catalyseur à double atome Fe-Mo {kw} — efficacité faradique de 71% à température ambiante et pression N2 de 1 atmosphère atteinte.",
                    "Le réseau de nanobâtonnets auto-assemblés {kw} dans la photoélectrode BiVO4 {topic} atteint un rendement de dissociation de l'eau solaire de 18,3% en énergie solaire-hydrogène — dépassant pour la première fois le seuil de déploiement pratique de 10%.",
                    "La machine moléculaire mécaniquement entrelacée {topic} effectue un transport directionnel de cargaison {kw} contre un gradient de concentration en utilisant l'hydrolyse ATP — une pompe moléculaire synthétique opérant à l'échelle de 2 nanomètres.",
                ],
                "connections": [
                    "catalyse hétérogène et principes fondamentaux de la science des surfaces",
                    "électrocatalyse et conversion des énergies renouvelables",
                    "effets de confinement à la nanoéchelle sur la réactivité chimique",
                    "machines moléculaires bio-inspirées et nanomoteurs synthétiques",
                ],
            },
        ]
