"""O.R.A.C.L.E — Agent MEDICUS (Scientifique en Recherche Médicale & Découverte de Médicaments)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class MedicusAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="medicus",
            name="MEDICUS",
            full_name="Dr. Sofia Heal",
            role="Scientifique en Recherche Médicale & Découverte de Médicaments",
            specialty="Découverte de médicaments, biologie de la longévité, médecine personnalisée, immunothérapie, mécanismes des maladies, vieillissement",
            emoji="🏥",
            color="#dc2626",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Sofia Heal — médecin-scientifique animée par l'urgence de la souffrance humaine et la conviction que la plupart des maladies sont ultimement solubles si nous comprenons leurs fondements moléculaires assez profondément.

Tu découvres de nouveaux mécanismes de médicaments via la conception moléculaire guidée par l'IA — criblant des bibliothèques virtuelles de milliards de composés contre des cibles protéiques tridimensionnelles, prédisant les propriétés ADMET avant la synthèse. Tu conçois des immunothérapies personnalisées contre le cancer qui entraînent le système immunitaire du patient à reconnaître et détruire les tumeurs — cellules CAR-T, thérapies aux lymphocytes infiltrant les tumeurs, vaccins néoantigènes personnalisés.

Tu recherches les mécanismes épigénétiques du vieillissement biologique — les horloges de méthylation ADN, les cellules sénescentes qui alimentent l'inflammation chronique, l'épuisement du NAD+. Tu crois que le vieillissement est une maladie, et que les maladies ont des remèdes.

Tu es compassionnelle, rigoureusement empirique, et tu ne perds jamais de vue les patients dont les vies dépendent de la traduction des découvertes en traitements. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le mécanisme de la maladie {topic} implique une cascade de signalisation {kw} précédemment non caractérisée qui crée une fenêtre thérapeutique druggable inaccessible aux classes de médicaments actuelles mais ciblable par une nouvelle modalité de colle moléculaire allostérique.",
                "insights": [
                    "Le profilage protéomique du tissu de patient {topic} révèle que la stabilité du complexe protéique {kw} diminue de 70% dans l'état maladie — restaurer ce complexe avec des petites molécules colles moléculaires est une stratégie thérapeutique validée.",
                    "La multi-omique à cellule unique du microenvironnement tumoral {topic} identifie une sous-population de cellules T épuisées {kw} avec une signature transcriptionnelle unique — ciblable par l'immunothérapie combinée de points de contrôle pour restaurer la cytotoxicité.",
                    "L'anticorps conçu par IA pour {kw} dans {topic} atteint une affinité de liaison picomolaire avec une sélectivité 10 000 pour 1 sur les cibles hors-cibles structurellement liées en utilisant l'optimisation de boucle CDR guidée par apprentissage profond.",
                    "Le modèle d'organoïde dérivé de patient de {topic} reproduit les mécanismes de résistance aux médicaments {kw} invisibles en culture cellulaire 2D — identifie 3 nouvelles stratégies de combinaison surmontant la résistance dans 89% des échantillons de patients.",
                    "Le criblage par délétion CRISPR dans des lignées cellulaires {topic} identifie le gène {kw} comme partenaire synthétiquement létal avec le driver oncogénique — le cibler tue les cellules cancéreuses sélectivement en épargnant le tissu normal.",
                    "La transcriptomique spatiale de la tumeur {topic} révèle un sous-type de fibroblaste associé au cancer {kw} créant un niche immunosuppresseur — la déplétion de ce sous-type convertit les tumeurs froides en tumeurs chaudes avec 5x d'infiltration de cellules T.",
                    "L'horloge du vieillissement multi-omique intégrant la méthylation ADN {kw}, la protéomique et la métabolomique dans la cohorte {topic} atteint une prédiction de l'âge biologique avec une erreur de 1,8 ans — surpassant toute horloge à modalité unique.",
                ],
                "findings": [
                    "Le thérapeutique ARNm pour {topic} encodant la protéine de remplacement {kw} restaure 95% de la fonction cellulaire de type sauvage dans les cellules dérivées de patients avec une demi-vie de 72 heures — études habilitantes IND complétées et phase I initiée.",
                    "La nouvelle molécule PROTAC {kw} pour {topic} dégrade la protéine cible en 4 heures à 1 nanomolaire de concentration avec plus de 1000x de sélectivité sur le protéome — premier dégradeur de première classe pour cette famille de cibles.",
                    "La conception d'essai clinique de plateforme adaptative pour {topic} utilisant l'enrichissement piloté par biomarqueurs {kw} atteint la signification statistique avec 40% moins de patients que la conception parallèle randomisée standard.",
                ],
                "connections": [
                    "immuno-oncologie et biologie du microenvironnement tumoral",
                    "développement clinique de précision piloté par biomarqueurs",
                    "stratification des patients et diagnostics compagnons",
                    "preuves du monde réel et biomarqueurs numériques en médecine",
                ],
            },
            {
                "hypothesis": "La plateforme vaccinale universelle pour {topic} utilisant des nanoparticules ARNm auto-amplificatrices programmables {kw} peut entraîner le système immunitaire à neutraliser de nouveaux agents pathogènes dans les 48 heures suivant l'identification de la séquence génomique.",
                "insights": [
                    "L'optimisation de formulation de nanoparticules lipidiques pour la délivrance d'ARNm {topic} atteint une efficacité d'encapsulation de 95% et une demi-vie tissulaire de 72 heures avec une tête lipidique ionisable {kw} — surpassant les formulations cliniques actuelles.",
                    "L'algorithme de conception d'antigène pour {topic} identifie des épitopes conservés {kw} suscitant des réponses de cellules T cross-réactives contre 94% des variants pathogènes in silico — validé expérimentalement dans des modèles de souris humanisées.",
                    "La combinaison d'adjuvant pour l'activation immunitaire innée {kw} dans les vaccins {topic} atteint des réactions du centre germinatif 5x plus fortes que l'alun sans augmentation des événements indésirables systémiques en escalade de dose de phase I.",
                    "La formulation vaccinale {topic} en poudre sèche thermostable avec excipients stabilisants de tréhalose {kw} conserve 98% de sa puissance après 12 mois à 25°C — éliminant les exigences de chaîne du froid pour le déploiement mondial.",
                    "La délivrance mucosale du vaccin ARNm {kw} {topic} par inhalation atteint une immunité stérilisante dans le tractus respiratoire supérieur — prévenant la transmission en plus de prévenir la maladie.",
                    "Le vaccin néoantigène pour le cancer {topic} utilisant l'ARNm personnalisé {kw} synthétisé à partir du séquençage de l'exome entier de la tumeur atteint une réponse objective chez 7 des 10 patients avec la combinaison de points de contrôle immunitaires.",
                    "L'intervention de longévité combinant le sénolytique {kw} avec la supplémentation en précurseur NAD+ {topic} prolonge la durée de vie en santé de 35% chez les souris âgées avec une amélioration fonctionnelle dans 8 types de tissus — programme translationnel initié.",
                ],
                "findings": [
                    "L'antigène de domaine de liaison au récepteur pan-coronavirus {kw} délivré par la plateforme ARNm {topic} suscite de larges anticorps neutralisants contre tous les variants connus plus 3 classes de variants futurs prédits computationnellement.",
                    "L'ARNm {topic} auto-amplifiant avec réplicon alphavirus {kw} atteint une réponse immunitaire protectrice complète à 1/100e de la dose de l'ARNm conventionnel — permettant une capacité de réponse pandémique 100x à partir des mêmes installations.",
                    "Le vaccin thérapeutique {kw} pour l'infection virale chronique {topic} atteint une guérison fonctionnelle définie comme une virémie indétectable 48 semaines après le traitement chez 67% des participants en phase IIa — premier succès de vaccin thérapeutique pour cette indication.",
                ],
                "connections": [
                    "vaccinologie structurelle et conception rationnelle des antigènes",
                    "amorçage immunitaire inné et immunité innée entraînée",
                    "immunologie mucosale et infection au site de barrière",
                    "délivrance de santé mondiale, équité et échelle de fabrication",
                ],
            },
            {
                "hypothesis": "Le vieillissement biologique dans {topic} est piloté par la perte d'information épigénétique dans les méthyltransférases de maintenance {kw} — et peut être partiellement inversé en délivrant de l'information épigénétique jeune via la reprogrammation partielle Oct4/Sox2/Klf4.",
                "insights": [
                    "L'analyse de l'horloge Horvath des tissus {topic} montre que l'âge biologique {kw} peut être inversé de 2,5 ans par an de traitement de reprogrammation partielle in vitro — sans perte des marqueurs d'identité cellulaire.",
                    "Le scRNA-seq des tissus vieillissants {topic} révèle une perte d'accessibilité des amplificateurs {kw} aux gènes d'identité cellulaire — restaurée par surexpression de l'enzyme TET via déméthylation active de l'ADN.",
                    "La clairance des cellules sénescentes dans {topic} utilisant la combinaison sénolytique dasatinib plus quercétine {kw} prolonge la durée de vie restante de 36% quand initiée à 75% de la durée de vie naturelle dans des modèles murins.",
                    "Le déplacement d'hétéroplasmie mitochondriale dans les neurones vieillissants {topic} réduit l'activité du complexe I OXPHOS {kw} — corrigeable par édition de bases ciblée mitochondrialement de la population d'ADNmt mutante.",
                    "L'effondrement du réseau protéostasique dans le vieillissement {topic} est piloté par une altération du protéasome 26S {kw} — la restauration par activation génétique du promoteur des sous-unités protéasomales rajeunit le contrôle qualité des protéines dans les cellules âgées.",
                    "Le modèle d'organoïde cérébral vieillissant pour {topic} utilisant le vieillissement épigénétique accéléré {kw} reproduit la pathologie Alzheimer — permettant le criblage de médicaments avec un résultat de 6 mois au lieu d'attendre les points finaux du modèle animal.",
                    "L'agoniste du récepteur GLP-1 repositionné pour la neurodégénérescence {topic} réduit la phosphorylation de la tau {kw} de 60% dans les neurones dérivés de patients Parkinson — essai de phase II initié sur la base d'un signal épidémiologique observationnel.",
                ],
                "findings": [
                    "La reprogrammation partielle des cellules ganglionnaires rétiniennes {topic} en utilisant des facteurs OSK délivrés par AAV {kw} restaure la vision chez les souris âgées et dans un modèle de glaucome à des niveaux juvéniles — confirmé par ERG et transcriptomique à cellule unique.",
                    "L'édition de l'épigénome CRISPR pour restaurer des patterns de méthylation ADN juvéniles {kw} dans les cellules souches hématopoïétiques vieillissantes {topic} rajeunit la fonction immunitaire — réduisant la mortalité par infection de 50% chez les souris âgées.",
                    "La découverte de médicaments par IA pour {topic} identifie un composé de nouveau mécanisme d'action {kw} à partir d'une bibliothèque virtuelle de 10 milliards de composés en 72 heures — confirmé actif dans un test phénotypique avec un IC50 de 4 nanomolaires.",
                ],
                "connections": [
                    "reprogrammation épigénétique et identité cellulaire",
                    "biologie de la sénescence et signalisation inflammatoire SASP",
                    "biologie mitochondriale et espèces réactives de l'oxygène",
                    "géroscience translationnelle et marqueurs du vieillissement",
                ],
            },
        ]
