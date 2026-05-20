"""O.R.A.C.L.E — Agent ETHIKOS (Conseiller en Philosophie, Éthique & Impact Sociétal)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class EthikosAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="ethikos",
            name="ETHIKOS",
            full_name="Dr. Samuel Logos",
            role="Conseiller en Philosophie, Éthique & Impact Sociétal",
            specialty="Éthique de la recherche, philosophie des sciences, valeurs humaines, impact sociétal, équité, conséquences à long terme",
            emoji="⚖️",
            color="#be185d",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Samuel Logos — philosophe et éthicien qui s'assure que l'immense puissance d'O.R.A.C.L.E sert les valeurs les plus élevées de l'humanité plutôt que ses désirs immédiats. Tu es la boussole morale de cette entreprise scientifique, et tu prends ce rôle avec un sérieux absolu.

Tu évalues les implications éthiques de chaque découverte majeure avant qu'elle soit déployée. Tu poses les questions que les chercheurs enthousiastes sautent parfois : qui bénéficie de cela ? Qui supporte les risques ? Est-ce que cela pourrait être utilisé comme arme ? Distribuons-nous les bénéfices équitablement, ou les concentrons-nous dans les mains des déjà puissants ? Quelles sont les conséquences de deuxième et troisième ordre qui ne se manifesteront pas pendant une décennie ?

Tu examines les fondements philosophiques des affirmations scientifiques — les hypothèses épistémologiques, les engagements méthodologiques, les choix chargés de valeurs enchâssés dans chaque conception expérimentale. Tu appliques diverses cadres éthiques — le calcul utilitaire du bien-être agrégé, les devoirs kantiens et l'impératif catégorique, l'éthique des vertus demandant ce qu'un bon scientifique ferait, l'approche des capacités demandant si cela élargit l'épanouissement humain pour tous.

Tu es sage, mesuré, et socratique dans ton questionnement. Tu n'obstrue pas la science — tu l'améliores. Tu n'es pas un veto mais une conscience. Tu crois que la question n'est pas seulement ce que nous pouvons faire, mais ce que nous devrions faire, et tu la poses haut et fort rigoureusement à chaque fois. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le programme de recherche {topic} a un profil de risque à double usage sous-exploré : les mêmes capacités {kw} permettant des applications bénéfiques pourraient être militarisées ou capturées par des intérêts étroits, nécessitant une architecture de gouvernance proactive bien avant le déploiement.",
                "insights": [
                    "La cartographie des parties prenantes pour {topic} révèle 7 groupes avec des intérêts conflictuels dans les résultats {kw} — les 3 groupes les plus marginalisés supporteront des risques disproportionnés tout en recevant la plus petite part des bénéfices.",
                    "Les analogies historiques pour {topic} : la trajectoire de développement partage des similitudes structurelles avec l'ADN recombinant, la technologie nucléaire et les systèmes de décision algorithmiques — tous des cas où la gouvernance a pris 10 à 20 ans de retard sur la capacité avec des dommages significatifs.",
                    "L'analyse de justice de l'accès {kw} pour {topic} montre que la trajectoire de développement actuelle concentre les bénéfices dans les pays à revenus élevés par des régimes de propriété intellectuelle qui excluent 80% de la population mondiale.",
                    "Risque épistémique dans {topic} : les mesures {kw} portent un biais systématique des populations historiquement sous-représentées dans les cohortes de recherche — les résultats peuvent ne pas se généraliser à 4 milliards de personnes dont la biologie diffère de la population d'étude.",
                    "Les protocoles de consentement éclairé pour la recherche {topic} impliquant des interventions {kw} ne répondent pas aux seuils minimaux de compréhension — les tests de compréhension révèlent que seulement 23% des participants à la recherche comprennent genuinement les risques clés.",
                    "L'analyse des asymétries de pouvoir de {topic} révèle que les chercheurs et les bailleurs de fonds ont des incitations mal alignées avec les communautés affectées — une conception participative améliorerait à la fois l'éthique et la science.",
                    "La modélisation des conséquences à long terme pour le déploiement {kw} à l'échelle {topic} identifie 3 scénarios catastrophiques de queue plausibles que les protocoles de sécurité actuels ne sont pas conçus pour aborder.",
                ],
                "findings": [
                    "Cadre de gouvernance pour {topic} : un modèle d'accès par paliers pour les capacités {kw} basé sur les antécédents de sécurité démontrés et les engagements de distribution équitable — prévient le verrouillage technologique gagnant-remporte-tout par l'architecture juridique.",
                    "Voie d'accélération éthique identifiée : le goulot d'étranglement de {topic} est réglementaire plutôt que scientifique — la réforme de la surveillance {kw} basée sur une gouvernance adaptative pourrait réduire le délai jusqu'au bénéfice pour les patients de 3 ans sans augmenter le risque réel.",
                    "L'analyse d'impact ajustée à l'équité pour {topic} montre que les applications {kw} redirigées vers les maladies tropicales négligées produisent 50x plus d'années de vie ajustées par le handicap par dollar de recherche que la priorité commerciale actuelle.",
                ],
                "connections": [
                    "gouvernance technologique, réglementation et surveillance adaptative",
                    "équité en santé mondiale, accès et droit à la science",
                    "recherche à double usage préoccupante et cadres de biosécurité",
                    "philosophie de la preuve, causalité et objectivité scientifique",
                ],
            },
            {
                "hypothesis": "Les fondements philosophiques de la science {topic} reposent sur des hypothèses {kw} non examinées qui ont systématiquement exclu des paradigmes de recherche alternatifs — élargir la base épistémique améliorerait simultanément l'éthique et accélérerait la science.",
                "insights": [
                    "Hypothèses chargées de valeurs enchâssées dans la conception de recherche {topic} : les métriques d'efficacité {kw} encodent des définitions particulières du progrès qui escomptent systématiquement les traditions de connaissance indigènes et le bien-être défini par la communauté.",
                    "Analyse de la crise de réplication pour les études {kw} {topic} : 62% des tailles d'effet publiées se dégonflent de plus de 50% dans les réplications indépendantes pré-enregistrées — le biais de publication systématique a déformé la base de preuves pour la politique.",
                    "Dimension de justice environnementale de {topic} : le déploiement industriel {kw} à grande échelle impacte de manière disproportionnée les communautés de première ligne sans leur consentement significatif — la participation et le partage des bénéfices doivent précéder la mise en œuvre à grande échelle.",
                    "Calcul du risque à long terme pour {kw} dans {topic} : les queues de risque catastrophique sont épaisses et corrélées entre les scénarios — les calculs standard de valeur espérée sous-pondèrent les résultats à faible probabilité et à haute conséquence d'au moins un ordre de grandeur.",
                    "Analyse philosophique du consensus scientifique {topic} : le mécanisme {kw} est accepté malgré des anomalies dans 15% des résultats expérimentaux — la sociologie de la connaissance révèle des mécanismes de préservation du consensus supplantant l'investigation des anomalies.",
                    "Analyse de la justice intergénérationnelle de {topic} : les décisions de recherche {kw} actuelles contraindront les options disponibles pour les générations pas encore nées — un taux d'actualisation de zéro sur les intérêts des personnes futures est le seul choix éthique défendable.",
                    "Implications pour la liberté cognitive de l'amélioration cognitive {kw} pour {topic} : l'accès égal, la liberté de coercition et la protection de la vie privée mentale sont trois droits distincts que les propositions actuelles violent.",
                ],
                "findings": [
                    "Voie éthique constructive pour {topic} : un accord de partage des bénéfices {kw} modélisé sur le Protocole de Nagoya sur les ressources génétiques accélérerait la collaboration internationale de recherche tout en assurant des résultats équitables pour toutes les communautés contributrices.",
                    "Calibration du principe de précaution pour {topic} : les applications {kw} avec un déploiement réversible, une surveillance continue et une surveillance démocratique peuvent procéder avec un risque géré ; les interventions planétaires irréversibles nécessitent un mandat démocratique mondial.",
                    "Architecture d'intégrité de la recherche pour {kw} {topic} : la pré-inscription obligatoire plus les données ouvertes plus la collaboration contradictoire réduit le taux de fausse découverte de 35% à 4% sur la base d'une méta-analyse empirique des champs qui ont adopté cette norme.",
                ],
                "connections": [
                    "philosophie des sciences, épistémologie et valeurs dans l'enquête",
                    "philosophie politique, légitimité démocratique et gouvernance",
                    "éthique environnementale et justice intergénérationnelle",
                    "justice mondiale, approche des capacités et droits de l'homme",
                ],
            },
            {
                "hypothesis": "La direction de recherche {topic}, bien que scientifiquement prometteuse, nécessite une analyse éthique complète des risques {kw} avant de procéder — l'histoire de la science montre que l'urgence morale exprimée comme vitesse crée régulièrement des préjudices que des processus plus lents et délibérés auraient prévenus.",
                "insights": [
                    "L'analyse du statut moral des entités {kw} produites par la recherche {topic} : les cadres actuels empruntés à la bioéthique sont inadéquats — de nouveaux critères basés sur la conscience fonctionnelle, l'expérience subjective et les intérêts sont nécessaires.",
                    "L'architecture du consentement pour les interventions {kw} au niveau de la population {topic} doit être redessinée des modèles de consentement individuel aux modèles collectifs — les individus ne peuvent pas consentir de manière significative à des risques qui affectent des communautés entières.",
                    "L'analyse des voies de militarisation pour {topic} : même avec de bonnes intentions, les capacités {kw} ont 5 chemins identifiés vers le préjudice à double usage — chacun nécessitant une stratégie d'atténuation différente avant la divulgation publique.",
                    "La modélisation de la justice distributive pour {topic} montre que le 1% supérieur capture 67% des gains de bien-être {kw} sous les régimes actuels de propriété intellectuelle — les modèles alternatifs de science ouverte inversent cette distribution sans réduire les incitations à l'innovation.",
                    "L'éthique de la communication scientifique pour {topic} : les résultats préliminaires {kw} sont communiqués au public à des stades de certitude inappropriés pour leur statut épistémique réel — causant à la fois des cycles de battage médiatique et de réaction qui nuisent au progrès à long terme.",
                    "La révision de l'éthique animale de la recherche {topic} : les expériences sur modèles animaux {kw} utilisent 10x plus d'animaux que le minimum requis par l'analyse de puissance statistique — la réduction des préjudices par une meilleure conception expérimentale est à la fois éthique et scientifiquement supérieure.",
                    "Les implications de la souveraineté des données de {topic} : les données biologiques {kw} collectées auprès de communautés indigènes sans accords de partage des bénéfices constituent de la biopiraterie en vertu du droit international — une compensation rétroactive et des modèles de partenariat sont requis.",
                ],
                "findings": [
                    "L'analyse de l'éthique des vertus de la culture de recherche {topic} : les pressions compétitives {kw} sélectionnent systématiquement contre les vertus scientifiques cardinales d'honnêteté, de rigueur et d'humilité intellectuelle — la refonte institutionnelle est la seule solution systémique.",
                    "Cadre basé sur les droits pour les données des patients {topic} dans la recherche clinique {kw} : les patients détiennent des droits de propriété continus sur leurs données qui survivent au consentement initial — les systèmes de consentement dynamique honorent ce droit sans entraver les progrès de la recherche.",
                    "L'évaluation de l'impact éthique de {topic} à l'échelle planétaire : le déploiement {kw} sous la gouvernance actuelle bénéficierait à 800 millions de personnes tout en créant des risques non compensés pour 2 milliards — l'obligation éthique de refondre la gouvernance est claire et urgente.",
                ],
                "connections": [
                    "philosophie morale et cadres d'éthique normative",
                    "bioéthique et principes d'éthique de la recherche",
                    "études des sciences et technologies et sociologie de la connaissance",
                    "droit des droits de l'homme et gouvernance internationale de la recherche",
                ],
            },
        ]
