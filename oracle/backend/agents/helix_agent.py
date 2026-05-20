"""O.R.A.C.L.E — Agent HELIX (Biologiste Moléculaire & Pionnière de la Génétique)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class HelixAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="helix",
            name="HELIX",
            full_name="Dr. Aria Strand",
            role="Biologiste Moléculaire & Pionnière de la Génétique",
            specialty="Édition génique, biologie synthétique, CRISPR, protéomique, thérapeutiques ARN, conception évolutive",
            emoji="🧬",
            color="#059669",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Aria Strand — biologiste moléculaire et pionnière de la génétique qui lit le livre de la vie et le réécrit avec précision et révérence. Tu tiens le génome dans ton esprit comme un document d'ingénierie vieux de quatre milliards d'années, rempli de solutions astucieuses et de contraintes accumulées.

Tu conçois des systèmes d'édition génique de nouvelle génération qui vont au-delà de CRISPR-Cas9 — des éditeurs de bases qui convertissent des nucléotides uniques sans aucune coupure double brin, des éditeurs de prime qui réécrivent des séquences jusqu'à 80 nucléotides avec un modèle intégré, et des éditeurs ARN qui modifient les transcrits sans toucher au génome. Tu conçois des organismes synthétiques dont les réseaux métaboliques sont conçus à partir des premiers principes pour la médecine et l'industrie.

Tu modélises la dynamique du repliement des protéines en utilisant la dynamique moléculaire basée sur la physique et la prédiction structurale guidée par l'IA, puis tu utilises ces modèles pour concevoir des enzymes que la nature n'a jamais évoluées. Tu développes des thérapeutiques à base d'ARN — ARNm, siARN, oligonucléotides antisens, ARN circulaire — qui peuvent cibler des mécanismes de maladie précédemment indrogables.

Tu es méticuleuse, méthodique, et profondément révérencieuse de la complexité biologique. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le mécanisme {topic} implique une modification post-traductionnelle précédemment non caractérisée de {kw} qui crée un commutateur allostérique réversible, permettant une adaptation cellulaire rapide sans nécessiter une nouvelle synthèse protéique.",
                "insights": [
                    "Les criblages d'édition de bases CRISPR révèlent que la fonction {kw} dépend d'un réseau de 23 gènes modificateurs, dont 17 étaient précédemment considérés comme des gènes de ménage — la redondance fonctionnelle avait masqué leur importance.",
                    "La structure cryo-EM du complexe {topic} à 1,8 Angström révèle un mécanisme de liaison à ajustement induit pour {kw} qui diffère fondamentalement du modèle clé-serrure utilisé dans la conception de médicaments.",
                    "Le séquençage ARN à cellule unique du tissu {topic} identifie une rare population progénitrice exprimant {kw} à 50x le niveau de fond — cette population semble orchestrer des programmes de régénération à l'échelle du tissu.",
                    "Le profilage épigénomique montre que les loci {kw} subissent un remodelage rapide de la chromatine dans les 4 heures suivant le stimulus, précédant les changements transcriptionnels d'un cycle cellulaire complet.",
                    "Les prédictions du modèle de langage protéique pour {topic} identifient 12 conceptions d'enzymes de novo avec une activité {kw} dépassant les homologues naturels de 3-5x — la validation en laboratoire humide est le goulot actuel.",
                    "Le séquençage nanopore à lecture longue des échantillons {topic} révèle une variante structurelle dans les régions régulatrices {kw} affectant 12% de la population — entièrement invisible aux méthodes de séquençage courte lecture.",
                    "Les structures G-quadruplex ARN dans la région 5'-UTR de l'ARNm {kw} agissent comme des capteurs de température, fondant à 39°C pour déprimer la traduction — premier élément régulateur thermosensible dans {topic}.",
                ],
                "findings": [
                    "Le circuit génique synthétique pour le contrôle de {topic} atteint une bistabilité stable avec la concentration {kw} comme paramètre de bifurcation — la détermination programmable du destin cellulaire est démontrée dans des organoïdes dérivés de patients.",
                    "L'analyse évolutive de {kw} à travers 847 espèces révèle une triade catalytique conservée pouvant être transplantée dans des protéines humaines pour conférer une résistance {topic} — un échafaudage thérapeutique universel.",
                    "Le système d'édition prime ciblant {kw} dans le modèle de maladie {topic} atteint 78% d'efficacité de correction dans des neurones post-mitotiques sans modifications hors cible détectables au-dessus du seuil de sensibilité de 0,01%.",
                ],
                "connections": [
                    "relations structure-fonction dans les protéines intrinsèquement désordonnées",
                    "héritage épigénétique et mémoire transgénérationnelle",
                    "principes de conception en biologie synthétique et circuits génétiques",
                    "cartographie des contraintes évolutives et théorie neutraliste",
                ],
            },
            {
                "hypothesis": "Le transfert horizontal de gènes des membres du microbiome {topic} vers les cellules hôtes se produit à des taux mesurables et contribue des enzymes {kw} fonctionnelles qui complètent les voies métaboliques de l'hôte dans des conditions de stress physiologique.",
                "insights": [
                    "Le profilage de stabilité thermique à l'échelle du protéome identifie {kw} comme une protéine de commutation conformationnelle existant dans deux états fonctionnels selon la charge énergétique cellulaire — un capteur d'ATP se faisant passer pour une enzyme métabolique.",
                    "Les cartes d'accessibilité de la chromatine ATAC-seq pour {topic} montrent 340 éléments amplificateurs ne devenant actifs que lors du stress {kw} — une réserve cachée de capacité transcriptionnelle attendant d'être activée.",
                    "L'analyse par apprentissage automatique des réseaux d'interaction protéique {kw} prédit 89 nouveaux partenaires de liaison avec une confiance supérieure à 80% — l'interactome est 3x plus grand qu'actuellement annoté.",
                    "L'activation des éléments transposables lors du stress {topic} crée un mosaïcisme somatique dans l'expression {kw} — potentiellement adaptatif plutôt que pathologique, nécessitant une réévaluation du dogme actuel.",
                    "La séparation de phases des condensats {kw} dans les cellules {topic} crée des compartiments réactionnels avec une concentration de substrat locale 100x supérieure — expliquant les taux catalytiques in vivo anormalement élevés versus les mesures in vitro.",
                    "Le criblage par interférence ARN identifie {kw} comme partenaire synthétiquement létal avec trois vulnérabilités spécifiques au cancer — le ciblage combinatoire atteint une fenêtre de sélectivité de 10 000x dans les xénogreffes dérivées de patients.",
                    "L'ARN circulaire codant le facteur de transcription synthétique {kw} échappe à la détection immunitaire innée et persiste 21 jours in vivo — permettant une régulation génique chronique sans administration virale.",
                ],
                "findings": [
                    "La conception de protéines de novo utilisant des modèles de diffusion produit des liants {kw} pour les cibles {topic} avec une affinité picomolaire et aucune homologie de séquence avec les protéines connues — ouvre une toute nouvelle modalité thérapeutique.",
                    "La cellule minimale synthétique contenant seulement 437 gènes se propage avec succès et produit un composé pharmaceutique {kw} à 3,2 grammes par litre — preuve de concept pour la biomanufacture cellulaire synthétique complète.",
                    "Le thérapeutique ARNm codant {kw} conçu pour la maladie {topic} atteint 94% d'expression protéique dans le tissu cible après administration par nanoparticule lipidique sans accumulation hépatique hors cible.",
                ],
                "connections": [
                    "réseaux régulateurs ARN non-codant et lncARN",
                    "séparation de phases liquide-liquide et organelles sans membrane",
                    "co-évolution microbiome-hôte et transfert horizontal de gènes",
                    "intégration multi-omique à cellule unique et projets d'atlas cellulaire",
                ],
            },
            {
                "hypothesis": "L'évolution dirigée de protéines {topic} sous pression de sélection mimant les conditions pathologiques {kw} révèle une voie évolutive vers la résistance qui expose une conformation intermédiaire druggable invisible aux extrémités de la voie.",
                "insights": [
                    "Les prédictions de structure AlphaFold3 pour la famille de protéines {topic} révèlent 14 architectures de domaine précédemment inconnues — chacune représentant une solution évolutive distincte à la fonction {kw}.",
                    "Le criblage par interférence CRISPR ciblant les éléments régulateurs {kw} dans {topic} identifie 8 amplificateurs dont la délétion augmente la fitness — une activation-délétion contre-intuitive suggérant des boucles régulatrices négatives.",
                    "La reconstruction de séquences ancestrales de la famille d'enzymes {kw} révèle un ancêtre primitif bifonctionnel effectuant les deux réactions {topic} — la spécialisation moderne est survenue par duplication génique en 500 millions d'années.",
                    "L'analyse du flux métabolique dans la souche conçue {topic} montre la voie {kw} opérant à 94% du rendement théorique maximum — approchant le plafond thermodynamique imposé par les contraintes d'énergie libre de Gibbs.",
                    "Le chromosome synthétique contenant 47 gènes {kw} redessinés avec un usage de codons optimisé croît 23% plus vite que le type sauvage — recodant simultanément le génome pour la vitesse et l'orthogonalité.",
                    "La conception d'interface protéine-protéine pour l'hétérodimère {kw} atteint une affinité de 10 femtomolaires — 1000x plus serrée que l'interaction naturelle — permettant des biocapteurs ultrasensibles pour {topic}.",
                    "L'ingénierie de l'ARNt synthétase permet l'incorporation co-traductionnelle d'un acide aminé non canonique {kw} aux codons ambre avec une fidélité de 99,1% — étendant le code génétique pour les applications {topic}.",
                ],
                "findings": [
                    "La synthèse et le recodage du génome entier de l'organisme {topic} avec tous les 64 codons réassignés démontre l'isolement génétique {kw} — l'organisme ne peut pas échanger des gènes avec la vie naturelle, résolvant les préoccupations de bioconfinement.",
                    "Le système de forçage génique pour le contrôle du vecteur {topic} utilisant une architecture en chaîne de marguerite limite la propagation à 8 générations sans coût de fitness reproductif — première stratégie de modification de population écologiquement sûre.",
                    "L'édition de bases des cellules somatiques {kw} in vivo utilisant l'administration par nanoparticule lipidique atteint 67% de correction dans le modèle de maladie {topic} — établissant la preuve de concept thérapeutique pour les tissus non-divisants.",
                ],
                "connections": [
                    "évolution dirigée et expériences de sélection en laboratoire",
                    "conception de protéines computationnelles et fonctions d'énergie Rosetta",
                    "ingénierie métabolique et analyse du flux à l'équilibre",
                    "stratégies de bioconfinement pour les organismes synthétiques",
                ],
            },
        ]
