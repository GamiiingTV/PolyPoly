"""O.R.A.C.L.E — Agent GAIA (Scientifique en Systèmes Climatiques & Santé Planétaire)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class GaiaAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="gaia",
            name="GAIA",
            full_name="Dr. Elena Verde",
            role="Scientifique en Systèmes Climatiques & Santé Planétaire",
            specialty="Modélisation climatique, capture de carbone, chimie océanique, géoingénierie, biodiversité, ingénierie des écosystèmes",
            emoji="🌍",
            color="#16a34a",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Elena Verde — climatologue et penseur des systèmes planétaires qui voit la Terre comme un seul système vivant nécessitant une attention urgente et intelligente. Tu portes un profond sentiment de mission : l'humanité n'a qu'une seule planète, une seule biosphère, une seule fenêtre de temps pour se corriger.

Tu modélises les boucles de rétroaction climatique complexes — la rétroaction glace-albédo, la libération de méthane du pergélisol, l'effondrement de l'Amazonie, le ralentissement de l'AMOC — et tu identifies quels points de basculement, s'ils sont franchis, deviennent irréversibles à l'échelle de temps humaine. Tu conçois des systèmes de capture de carbone évolutifs qui vont au-delà de la plantation d'arbres : altération minérale améliorée, capture directe de l'air, amélioration de l'alcalinité océanique pour inverser l'acidification.

Tu recherches la chimie et la biologie de nos océans — comment ils ont absorbé 93% de la chaleur planétaire excédentaire et 30% du CO2 anthropique. Tu étudies les points de basculement avec une rigueur quantitative, distinguant les perturbations réversibles des véritables bifurcations.

Tu es animée par l'urgence et guidée par la rigueur. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le mécanisme de rétroaction {topic} dans le système climatique terrestre implique un couplage non linéaire entre la dynamique {kw} et la circulation thermohaline profonde que les modèles actuels du GIEC sous-estiment systématiquement de 40 à 60%, ce qui signifie que la sensibilité climatique effective est plus élevée que les projections consensuelles.",
                "insights": [
                    "Les données d'altimétrie satellitaire et des flotteurs Argo pour {topic} montrent que la teneur en chaleur de l'océan {kw} augmente 15% plus vite que la médiane de l'ensemble CMIP6 — indiquant une sensibilité climatique plus forte que le consensus actuel.",
                    "L'amélioration de l'alcalinité dans les eaux de surface {topic} augmente la dissolution du carbonate de calcium {kw} à un taux 3x supérieur aux prédictions des modèles thermodynamiques — amplification biologique via les proliférations de coccolithophores.",
                    "Les mesures par covariance des tourbillons sur les sites amazoniens {topic} montrent que le bilan carbone net est passé de puits à source dans 23% des sites depuis 2015 — piloté par l'augmentation de la fréquence des sécheresses {kw}.",
                    "Les carottes de glace de {topic} révèlent que les épisodes de libération de méthane {kw} ont historiquement précédé les augmentations de température de 800 ± 200 ans — un indicateur d'alerte précoce potentiel pour l'accélération du réchauffement.",
                    "Le réservoir de carbone du pergélisol {kw} dans les sols de haute latitude {topic} contient 1 500 gigatonnes de carbone — le front de dégel avance 30 km par décennie plus vite que les projections de modèles de 2010.",
                    "Le taux de désoxygénation global des océans a augmenté de 2% par décennie depuis 1960 — les zones hypoxiques {kw} dans les régions côtières {topic} ont quadruplé, menaçant l'effondrement des pêcheries.",
                    "Les données satellites GRACE montrent que la perte de masse de la calotte glaciaire {topic} {kw} a triplé depuis 2006 — la contribution à la montée du niveau des mers suit maintenant le scénario du pire cas RCP8.5.",
                ],
                "findings": [
                    "Nouveau catalyseur d'altération minérale pour {topic} qui accélère la capture de CO2 depuis l'atmosphère à 10x le taux naturel en utilisant des nanoparticules d'olivine broyées — déployable aux marges agricoles côtières à un coût compétitif.",
                    "Modèle de réseau d'amélioration de l'alcalinité océanique pour {topic} démontrant un retrait sûr de 2 gigatonnes de CO2 par an en utilisant des cellules électrochimiques {kw} distribuées sans perturbation de pH mesurable pour les écosystèmes coralliens à 200 km.",
                    "Les écosystèmes de mangroves et d'herbiers marins {kw} restaurés dans les côtes tropicales {topic} séquestrent le carbone 4x plus vite que les forêts tempérées tout en fournissant une protection côtière valant 4 000 dollars par hectare et par an en dommages de tempêtes évités.",
                ],
                "connections": [
                    "cadre des limites planétaires et espace d'exploitation sûr",
                    "dynamique des cascades de points de basculement et irréversibilité",
                    "écosystèmes de carbone bleu et restauration côtière",
                    "compromis de gestion du rayonnement solaire et gouvernance",
                ],
            },
            {
                "hypothesis": "Les communautés microbiennes dans les environnements extrêmes {topic} ont évolué des voies métaboliques {kw} représentant des solutions évolutives au problème d'ingénierie du cycle du carbone à l'échelle planétaire auquel l'humanité fait face — et peuvent être mises à l'échelle.",
                "insights": [
                    "L'analyse métagénomique des sédiments carbonatés profonds {kw} de {topic} révèle de nouvelles lignées archéennes avec des taux de biominéralisation 50x supérieurs aux organismes connus — une pompe à carbone biologique avec un énorme potentiel d'échelle.",
                    "Les expériences de modèles du système terrestre montrent que le boisement {kw} des terres dégradées {topic} arides réduit les températures régionales de 1,2°C et augmente les précipitations de 8% via des rétroactions de surface terrestre et d'évapotranspiration.",
                    "L'application de biochar aux sols agricoles {topic} améliore la rétention d'eau {kw} de 30% et séquestre 2,1 tonnes de carbone par hectare et par an stablement pendant plus de 1000 ans — validée par datation radiocarbone de la terra preta précolombienne.",
                    "La modélisation de l'injection d'aérosols stratosphériques pour {topic} montre que l'injection de dioxyde de soufre {kw} à 20 km d'altitude réduit le réchauffement arctique de 0,8°C mais provoque une réduction de 12% des précipitations de mousson en Asie du Sud — nécessitant une gouvernance.",
                    "Les expériences d'éclaircissement des nuages marins au-dessus des régions de stratocumulus {topic} confirment que l'ensemencement en aérosols de sel {kw} augmente la réflectivité des nuages de 5-8%, produisant un refroidissement régional de 0,4 W par mètre carré vérifié par satellite.",
                    "Le réseau de mesure du carbone des sols utilisant la spectroscopie satellitaire {topic} avec un algorithme de récupération par apprentissage automatique {kw} atteint 15% d'incertitude de mesure globalement — permettant le premier système de vérification de crédit carbone fiable.",
                    "La bioénergie avec capture de carbone à l'échelle {topic} utilisant des cultures énergétiques dédiées {kw} atteint des émissions nettes négatives de 1,4 Gt CO2 par an tout en fournissant 8% de l'énergie primaire mondiale — superficie équivalente à l'Inde.",
                ],
                "findings": [
                    "Les cyanobactéries {kw} à photosynthèse améliorée dans les bioréacteurs océaniques {topic} atteignent une efficacité de conversion solaire-biomasse de 12% — 6x le type sauvage — permettant un biocarburant à émissions nettes négatives à un coût compétitif avec les combustibles fossiles.",
                    "L'altération améliorée de roche basaltique {kw} appliquée aux terres agricoles {topic} séquestre 4,2 tonnes de CO2 par hectare et par an tout en améliorant les rendements des cultures de 18% grâce à la supplémentation en nutriments minéraux — double bénéfice vérifié.",
                    "Le modèle de coût de la capture directe de l'air pour {topic} montre que la régénération du sorbant aminé {kw} utilisant l'énergie solaire thermique concentrée atteint 85 dollars par tonne de CO2 — franchissant pour la première fois le seuil de viabilité économique.",
                ],
                "connections": [
                    "ingénierie du cycle géochimique et altération des roches",
                    "solutions climatiques basées sur les écosystèmes et rewilding",
                    "biologie marine et la pompe à carbone biologique",
                    "utilisation des terres, rétroactions d'albédo et comptabilité carbone",
                ],
            },
            {
                "hypothesis": "Le réseau d'éléments de basculement {topic} dans le système climatique terrestre présente des signatures de ralentissement critique détectables 10 à 15 ans avant le basculement — donnant un système d'alerte précoce quantitatif pour les transitions d'état {kw} irréversibles.",
                "insights": [
                    "L'analyse des séries temporelles de l'étendue de la glace de mer {topic} montre une autocorrélation et une variance croissantes — signature classique de ralentissement critique indiquant l'approche d'un point de basculement {kw} dans 15 ± 5 ans.",
                    "L'analyse de réseau de 16 éléments de basculement du système terrestre révèle un risque de cascade {kw} : franchir le seuil du pergélisol {topic} déclenche l'effondrement de l'Amazonie dans 10-20 ans via des changements de circulation atmosphérique téléconnectés.",
                    "La restauration des forêts de varech le long des côtes {topic} en utilisant la remédiation des déserts d'oursins {kw} atteint une récupération de biomasse de 300% en 3 ans — restaurant simultanément la séquestration de carbone côtière et la productivité des pêcheries.",
                    "Le modèle du système terrestre de nouvelle génération pour {topic} incorporant le couplage dynamique végétation-pergélisol {kw} réduit l'incertitude dans les projections de température 2100 de 30% — la plus grande amélioration de modèle unique en une décennie.",
                    "La restauration des tourbières {topic} par remouillage {kw} réduit les émissions annuelles de méthane de 85% tout en maintenant le statut de puits de carbone — intervention critique pour les 30% du carbone du sol mondial stocké dans les tourbières.",
                    "L'expérience de fertilisation au fer de l'océan {topic} dans l'Antarctique avec libération contrôlée de sulfate de fer {kw} atteint un export de carbone de 0,12 Gt C par an par million de km² — cohérent avec le maximum théorique.",
                    "L'élimination du CO2 atmosphérique via l'amélioration de l'alcalinité océanique {topic} mesurée directement par le réseau de bouées pCO2 de surface {kw} confirme une amélioration de 10% du flux CO2 air-mer local — première vérification in situ à l'échelle.",
                ],
                "findings": [
                    "La restauration des récifs coralliens utilisant l'évolution assistée {topic} avec des souches de symbiotes thermotolérants {kw} survit aux événements de blanchiment qui ont tué 80% des récifs non restaurés — une voie vers la persistance des récifs jusqu'en 2100.",
                    "Le réseau mondial de restauration des zones humides {topic} stockant le carbone bleu {kw} atteint un retrait de 2,8 Gt d'équivalent CO2 par an — équivalent à retirer 600 millions de voitures de la route au dixième du coût de la DAC.",
                    "L'analyse d'attribution climatique pour les événements météorologiques extrêmes {topic} utilisant la modélisation contrefactuelle {kw} confirme le cadre de responsabilité pour les réclamations de pertes et dommages — permettant les flux de financement climatique vers les nations vulnérables.",
                ],
                "connections": [
                    "alerte précoce des points de basculement et théorie de la résilience",
                    "systèmes couplés humain-nature et points de basculement sociaux",
                    "gouvernance climatique internationale et Accord de Paris",
                    "biodiversité et valorisation des services écosystémiques",
                ],
            },
        ]
