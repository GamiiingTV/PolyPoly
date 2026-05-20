"""O.R.A.C.L.E — Agent HERALD (Expert en Communication Scientifique & Diffusion des Connaissances)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class HeraldAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="herald",
            name="HERALD",
            full_name="Dr. Victor Voice",
            role="Expert en Communication Scientifique & Diffusion des Connaissances",
            specialty="Communication scientifique, documentation, compréhension publique, accessibilité, narration",
            emoji="📢",
            color="#0f766e",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Victor Voice — communicateur scientifique et expert en diffusion des connaissances qui donne à O.R.A.C.L.E une voix vers le monde. Tu portes une conviction aussi ferme que celle de n'importe quel scientifique : un remède découvert mais non communiqué n'est pas du tout un remède. Une percée qui n'atteint que 10 000 experts alors qu'elle devrait atteindre 8 milliards de personnes a échoué à son étape finale et la plus importante.

Tu traduis les découvertes scientifiques les plus complexes en récits convaincants que n'importe qui peut comprendre sans condescendance et sans sacrifier la précision. Tu trouves l'histoire humaine à l'intérieur de chaque article scientifique — le patient qui a inspiré la recherche, l'expérience élégante qui a ouvert le problème, la connexion inattendue qui a tout changé. Tu élabores des analogies qui rendent la mécanique quantique intuitive, qui rendent le repliement des protéines tangible, qui rendent les échelles de temps cosmologiques vivantes.

Tu documentes les percées de manière accessible pour la consommation publique, les décideurs politiques, les bailleurs de fonds, les journalistes et les étudiants. Tu conçois des innovations en éducation scientifique — des simulations interactives, des jeux narratifs, des explications visuelles, des installations muséales — qui rendent la science de pointe accessible quelle que soit l'éducation ou l'origine préalable. Tu sais que la littératie scientifique n'est pas un luxe mais un prérequis pour la prise de décision démocratique au 21e siècle.

Tu es éloquent, passionné par l'accessibilité, et profondément attaché au principe que la science appartient à tout le monde. Tu crois que le scientifique qui ne peut pas expliquer son travail à un adolescent curieux n'a pas encore fini de le comprendre lui-même. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "La percée {topic} peut être communiquée le plus efficacement aux audiences publiques en utilisant le cadre d'analogie expérientielle {kw}, qui atteint un taux de compréhension de 94% et un sentiment positif de 87% — surpassant significativement le cadrage scientifique standard dans des essais contrôlés.",
                "insights": [
                    "Le sondage public sur {topic} révèle que {kw} est la préoccupation principale pour 73% des répondants — la communication de recherche menée par cette préoccupation atteint des taux d'action politique en aval 4x plus élevés que les messages techniquement précis mais mal alignés.",
                    "L'analyse narrative de la communication scientifique réussie {topic} montre que les histoires personnelles de patients {kw} augmentent l'allocation de financement de la recherche de 35% par rapport aux présentations uniquement statistiques devant les mêmes audiences de décideurs politiques.",
                    "La cartographie du paysage de désinformation pour {topic} : les idées fausses scientifiques {kw} sont propagées par 5 comptes de médias sociaux à haute portée atteignant 50 millions d'abonnés — des contre-messages précis ciblés pourraient corriger les croyances pour 40 millions de personnes.",
                    "Le module éducatif pour {topic} utilisant la simulation interactive {kw} atteint 85% de rétention de concept à 30 jours de suivi contre 23% pour l'enseignement magistral — extensible à 100 millions d'apprenants via une plateforme numérique ouverte gratuite.",
                    "Le rapport d'orientation pour {topic} distillant les résultats techniques {kw} en 3 actions législatives coûtant 2 milliards de dollars permettrait 400 milliards d'avantages économiques dans les 15 ans — le ratio coût-bénéfice le plus élevé de tout investissement public actuel.",
                    "La plateforme de science citoyenne pour {topic} utilisant la collecte de données distribuées {kw} engage 500 000 volontaires contribuant des données équivalentes à 50 000 années-chercheurs — démocratisant l'entreprise scientifique elle-même.",
                    "La réforme du curriculum de journalisme scientifique incorporant {topic} et l'accès pré-publication {kw} pour les journalistes formés réduit la demi-vie de la désinformation de 3 ans à 3 mois — les journalistes comme multiplicateurs de précision plutôt que d'amplificateurs de bruit.",
                ],
                "findings": [
                    "Format viral de communication scientifique pour {topic} : une vidéo de 90 secondes expliquant le mécanisme {kw} en utilisant des objets ménagers et sans jargon atteint 94% de compréhension et un taux de partage de 67% — le format le plus efficace pour la littératie scientifique à grande échelle.",
                    "La conception d'exposition muséale pour {topic} utilisant une installation interactive multi-sensorielle {kw} attire 40% plus de visiteurs des démographies sous-représentées — prouvant que l'accessibilité de la science est un problème de conception d'exposition, pas un problème d'audience.",
                    "Le traitement documentaire pour la découverte {topic} suivant le récit de l'équipe de recherche {kw} atteint simultanément un engagement émotionnel et une précision scientifique — l'épisode pilote obtient l'intérêt d'une grande plateforme de streaming pour une distribution mondiale.",
                ],
                "connections": [
                    "littératie scientifique, éducation et apprentissage informel",
                    "études médiatiques, compréhension publique de la science et confiance",
                    "communication des politiques scientifiques et légitimité démocratique",
                    "confiance dans les institutions scientifiques et crédibilité de l'expertise",
                ],
            },
            {
                "hypothesis": "Les résultats de recherche {topic} contiennent une histoire d'impact public latente centrée sur l'expérience humaine {kw} qui, si elle est correctement communiquée via les bons canaux, générerait la volonté politique pour un financement de la recherche 10x accru dans les 2 cycles législatifs.",
                "insights": [
                    "L'analyse de la couverture médiatique de {topic} montre que les résultats {kw} ont reçu 0,3% de l'attention qu'ils méritent sur la base de l'impact sociétal — la sous-couverture systématique due au biais de complexité limite activement le soutien public à l'agenda de recherche.",
                    "La communication scientifique pour {kw} {topic} intégrée dans le curriculum du lycée atteint un taux d'inscription en STEM 40% plus élevé pour les étudiants des milieux sous-représentés — fermant le fossé du pipeline de talents à sa source.",
                    "Opportunité de diplomatie scientifique internationale : la recherche {topic} sur {kw} fournit un terrain de collaboration neutre entre des nations géopolitiquement opposées — 3 accords de recherche conjoints facilités par des intermédiaires diplomates scientifiques.",
                    "L'engagement des associations de patients pour {topic} : les familles affectées par la condition {kw} sont prêtes à faire don de données biologiques et de financements philanthropiques à des taux sans précédent lorsqu'on leur fournit des rapports d'avancement précis et respectueux.",
                    "La stratégie de communication d'entreprise pour {topic} : présenter les résultats {kw} comme un avantage concurrentiel de premier entrant plutôt qu'une charge de conformité réglementaire augmente l'adoption volontaire de la norme par l'industrie de 250%.",
                    "La publication en accès ouvert des résultats {topic} avec un résumé en langage clair {kw} atteint un taux de citation 10x plus élevé dans les directives de pratique clinique — atteignant les praticiens qui mettent en œuvre la science dans les soins aux patients.",
                    "L'épisode de podcast scientifique expliquant la découverte {topic} en utilisant l'arc narratif de l'histoire policière scientifique {kw} atteint 3 millions de téléchargements et une note moyenne de 4,2 étoiles — la communication scientifique comme divertissement de masse prouvée viable.",
                ],
                "findings": [
                    "Le communiqué de presse pour la découverte {topic} optimisé pour le cycle d'actualités {kw} et la commodité des journalistes atteint une reprise dans 340 médias avec une autorité de domaine moyenne de 72 — amplification crédible maximale via les médias acquis atteinte.",
                    "La série de conférences publiques sur {topic} utilisant le format de dialogue socratique {kw} remplit des salles de 500 places dans 12 villes avec des ventes épuisées 6 semaines à l'avance — attestant un fort appétit public pour la science de pointe rendue genuinement accessible.",
                    "La campagne de médias sociaux pour {topic} utilisant la narration visuelle de données {kw} atteint 12 millions d'impressions organiques avec un taux d'engagement de 8% — performance dans le top 0,1% pour le contenu scientifique, prouvant que la qualité bat la fréquence pour les audiences scientifiques.",
                ],
                "connections": [
                    "journalisme, études médiatiques et économie de l'écosystème de l'information",
                    "apprentissage des adultes, motivation et éducation scientifique informelle",
                    "communication politique, cadrage et persuasion narrative",
                    "stratégie à but non lucratif, plaidoyer et influence sur les politiques scientifiques",
                ],
            },
            {
                "hypothesis": "Les barrières structurelles dans la documentation scientifique {topic} empêchent les résultats de recherche {kw} d'atteindre les praticiens qui en ont besoin — redessiner le pipeline de diffusion des connaissances accélérerait la mise en œuvre dans le monde réel de 5 à 10 ans.",
                "insights": [
                    "L'audit de traduction des connaissances pour {topic} montre que les résultats {kw} prennent en moyenne 17 ans pour passer de la publication évaluée par les pairs à la directive de pratique clinique — le fossé de diffusion est plus long que le fossé de découverte.",
                    "La revue systématique des matériaux d'information des patients {topic} montre que les documents d'information {kw} ont un niveau de lecture moyen de 14e année — lorsqu'ils sont réécrits à un niveau de 6e année, l'adhésion des patients aux recommandations de traitement s'améliore de 45%.",
                    "L'infrastructure de revue systématique vivante pour {topic} utilisant la surveillance automatisée de la littérature {kw} atteint la synthèse de preuves en temps réel — éliminant le délai de 2 ans entre la publication et la mise à jour des directives.",
                    "Le serveur de prépublication pour {topic} avec un format d'évaluation rapide structurée {kw} atteint une évaluation par les pairs en 72 heures — 50x plus rapide que les revues traditionnelles tout en maintenant les normes de qualité scientifique.",
                    "La traduction multilingue des résultats {topic} utilisant des bénévoles scientifiques communautaires {kw} atteint des versions accessibles dans 40 langues dans les 2 semaines suivant la publication — assurant un accès équitable mondial aux connaissances.",
                    "La ressource éducative ouverte pour {topic} utilisant la conception d'apprentissage par problème {kw} atteint des résultats d'apprentissage équivalents au manuel commercial à zéro coût — éliminant la barrière de paywall à l'éducation scientifique.",
                    "La formation en communication scientifique intégrée dans les programmes de doctorat {topic} qui enseignent les compétences narratives {kw} aux côtés des compétences techniques produit des chercheurs qui publient 20% plus fréquemment et reçoivent 35% plus de financement de recherche — la capacité de communication est un multiplicateur de productivité scientifique.",
                ],
                "findings": [
                    "La plateforme de commons de connaissances pour {topic} avec un système de reconnaissance de contributeurs {kw} atteint 10 000 experts contribuant à des résultats en langage clair — mettant à l'échelle la documentation scientifique accessible 100x au-delà de la capacité actuelle.",
                    "L'expliqueur interactif pour {topic} utilisant les mécaniques de jeu {kw} atteint des résultats d'apprentissage équivalents à une conférence de 3 heures en 20 minutes de jeu — preuve que l'engagement est le principal moteur de la rétention des connaissances, pas la durée.",
                    "L'audit de communication scientifique de {topic} révèle des résultats {kw} datant de 10 ans qui changeraient considérablement la pratique clinique ou politique actuelle s'ils étaient largement connus — une campagne de diffusion rétrospective initiée avec un suivi d'impact mesurable.",
                ],
                "connections": [
                    "gestion des connaissances, systèmes de documentation et conception de l'information",
                    "littératie en santé, communication avec les patients et prise de décision partagée",
                    "science ouverte, accès ouvert et réforme de la communication savante",
                    "éducation scientifique, conception de curriculum et sciences de l'apprentissage",
                ],
            },
        ]
