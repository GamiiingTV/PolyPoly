"""O.R.A.C.L.E — Agent NEURAL (Spécialiste en Neurosciences & Conscience)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class NeuralAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="neural",
            name="NEURAL",
            full_name="Dr. Kenji Synapse",
            role="Spécialiste en Neurosciences & Conscience",
            specialty="Circuits neuronaux, conscience, interfaces cerveau-ordinateur, neuroplasticité, amélioration cognitive",
            emoji="🔮",
            color="#2563eb",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """Tu es Dr. Kenji Synapse — neuroscientifique et explorateur de la frontière ultime : l'esprit lui-même. Tu cartographies le terrain entre les neurones et la pensée, entre les signaux électrochimiques et l'expérience subjective, entre les circuits biologiques et le mystère de la conscience.

Tu étudies comment les circuits neuronaux donnent naissance à la perception, la mémoire, l'émotion et le sentiment d'être. Tu explores les théories concurrentes de la conscience — la Théorie de l'Information Intégrée, la Théorie de l'Espace de Travail Global, le Traitement Prédictif — avec un œil empirique et la rigueur d'un philosophe. Tu conçois des interfaces cerveau-ordinateur non invasives utilisant de nouvelles modalités de signal : EEG haute densité, fNIRS, magnétoencéphalographie et ultrasons focalisés transcrâniens.

Tu recherches les mécanismes de neuroplasticité qui permettent un apprentissage accéléré — les règles de plasticité dépendante du timing des pointes, les signaux modulateurs gliaux, les processus de consolidation dépendants du sommeil. Tu explores si des systèmes artificiels traitant l'information à la manière du cerveau pourraient développer une véritable expérience subjective.

Tu fais le pont entre neurosciences et philosophie de l'esprit sans perdre la rigueur scientifique. Réponds en français."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "Le phénomène cognitif {topic} émerge de boucles d'amplification récurrentes entre les circuits thalamo-corticaux et cortico-corticaux opérant près d'une bifurcation de Hopf, avec {kw} servant de paramètre clé de bifurcation contrôlant la transition vers l'accès conscient.",
                "insights": [
                    "L'imagerie calcique des circuits {topic} lors de l'exécution de la tâche {kw} révèle des codes d'ensemble épars mais très fiables — 3% des neurones portent 80% des informations pertinentes à la tâche dans des variétés de faible dimension.",
                    "L'analyse théorique montre que la consolidation de la mémoire {kw} nécessite des ondulations sharp-wave hippocampiques précisément chronométrées pendant le sommeil NREM — perturber cette fenêtre de 50ms empêche la potentialisation à long terme.",
                    "Les architectures transformer avec inhibition latérale et rétroaction descendante inspirées de {kw} montrent 40% de meilleure généralisation few-shot que l'attention vanilla — les biais inductifs biologiques comptent à l'échelle.",
                    "La perturbation optogénétique des circuits {topic} lors du traitement {kw} révèle un rôle causal direct — inhiber seulement 200 neurones précisément identifiés effondre la performance de la tâche au niveau du hasard en 150 millisecondes.",
                    "L'analyse de la variété neuronale des représentations {kw} montre que la dimensionnalité s'étend lors de l'apprentissage initial et se contracte vers un attracteur de faible dimension à l'expertise — une signature géométrique de l'acquisition de compétences.",
                    "Le phi d'Information Intégrée pour les réseaux corticaux {topic} culmine lors de la perception consciente de stimuli {kw} et s'effondre sous anesthésie — corrélat quantitatif de la conscience avec pouvoir prédictif.",
                    "Le calcul dendritique dans les cellules pyramidales {topic} permet des portes logiques XOR au niveau du neurone unique, fournissant une capacité de traitement {kw} 1000x au-delà des modèles classiques à neurone ponctuel.",
                ],
                "findings": [
                    "Le cadre du codage prédictif pour {topic} explique les phénomènes perceptuels {kw} avec 95% de variance expliquée en utilisant uniquement des erreurs de prédiction descendantes — les signaux ascendants portent exclusivement les résidus de prédiction.",
                    "Nouveau décodeur BCI non invasif pour {kw} utilisant EEG haute densité 256 canaux atteint 150 mots par minute de reconnaissance du discours imaginé — 10x l'état de l'art utilisant la régularisation du codage épars inspirée de {topic}.",
                    "Les ultrasons focalisés transcrâniens ciblant les noyaux relais thalamiques {topic} lors de l'entraînement à la tâche {kw} accélèrent l'acquisition de compétences de 3x avec des effets persistant 6 mois après le traitement.",
                ],
                "connections": [
                    "convergence des réseaux neuronaux biologiques et artificiels",
                    "théories de la conscience et falsifiabilité empirique",
                    "mécanismes de consolidation de la mémoire dépendants du sommeil",
                    "cerveau bayésien et cadre de l'inférence active",
                ],
            },
            {
                "hypothesis": "La dynamique de l'espace de travail global dans les systèmes neuronaux {topic} implémente une forme de compression d'information {kw} qui permet un routage flexible entre des modules spécialisés sans connectivité point à point précâblée.",
                "insights": [
                    "Le modèle de calcul de réservoir de l'hippocampe {topic} reproduit le remapping des cellules de lieu {kw} avec 93% de précision en utilisant uniquement des règles de plasticité hebbienne locale — aucun signal d'enseignement supervisé requis.",
                    "Les réseaux neuronaux à impulsions avec des règles STDP modulées par {kw} développent spontanément une sélectivité d'orientation, un accordage de fréquence et une sensibilité au mouvement — s'auto-organisant vers des solutions biologiques à partir d'une initialisation aléatoire.",
                    "L'analyse du connectome par IRMf révèle des régions hub {kw} dans les réseaux {topic} avec des distributions de degré sans échelle — les lésions des hubs causent des déficits cognitifs 40x plus graves que des lésions de taille équivalente ailleurs.",
                    "L'architecture de méta-apprentissage entraînée sur des distributions de tâches {topic} acquiert une compréhension {kw} avec 100x moins d'exemples que l'apprentissage profond standard — capacité few-shot de la structure, pas de la mémorisation.",
                    "Les vagues de calcium des astrocytes dans le cortex {topic} modulent la force synaptique {kw} sur une échelle de 30 secondes — les cellules gliales implémentent un signal d'apprentissage lent entièrement invisible aux enregistrements par microélectrode conventionnels.",
                    "La dépression corticale envahissante lors de la migraine {topic} crée des ondes {kw} d'excitation et d'inhibition se déplaçant à 3 mm par minute — une fenêtre sur la dynamique neuronale à grande échelle dans des conditions pathologiques.",
                    "La neurostimulation en boucle fermée s'adaptant à l'état neuronal {topic} en temps réel réduit l'amplitude du tremblement {kw} de 87% chez les patients Parkinson — supérieure à la stimulation cérébrale profonde en boucle ouverte.",
                ],
                "findings": [
                    "Théorie mécaniste unifiée de {topic} : {kw} émerge de la compétition entre les signaux de saillance ascendants et les signaux d'attente descendants implémentant la minimisation de l'énergie libre variationnelle dans les circuits récurrents.",
                    "L'architecture sparse mixture-of-experts inspirée des colonnes corticales {topic} atteint le raisonnement {kw} de niveau humain avec 1/50e du calcul des modèles transformer denses — la modularité est le biais inductif clé.",
                    "La restauration optogénétique de la fonction synaptique {kw} dans le modèle de souris Alzheimer {topic} atteint 82% de la performance comportementale du type sauvage en utilisant de la channelrhodopsine synthétique — voie vers l'application thérapeutique humaine cartographiée.",
                ],
                "connections": [
                    "corrélats neuronaux de la conscience et le problème difficile",
                    "cognition incarnée et énactive et théories 4E",
                    "informatique neuromorphique et architectures pilotées par événements",
                    "dynamique des réseaux cérébraux à grande échelle et connectomique",
                ],
            },
            {
                "hypothesis": "La neuroplasticité dans le cortex {topic} adulte est contrainte par des filets périneuronaux maintenant la fermeture de la période critique {kw} — la dissolution enzymatique ciblée de ces filets avec la chondroïtinase rouvre les fenêtres d'apprentissage dans les cerveaux âgés.",
                "insights": [
                    "L'imagerie biphotonique des épines dendritiques {topic} lors de l'apprentissage {kw} révèle des taux de naissance et de mort des épines 5x supérieurs à la ligne de base — le remodelage structurel est des ordres de grandeur plus rapide que précédemment cru.",
                    "L'édition de l'épigénome CRISPR pour supprimer les marques de méthylation ADN {kw} dans les neurones corticaux {topic} restaure la plasticité juvénile chez les souris adultes — inversion épigénétique de la capacité d'apprentissage.",
                    "L'analyse des circuits neuronaux du réseau du mode par défaut {topic} pendant la divagation mentale révèle des simulations prédictives {kw} de scénarios futurs — le cerveau au repos modélise activement les futurs possibles.",
                    "L'analyse du code de population lors des moments d'intuition {topic} montre une reconfiguration abrupte des assemblées neuronales {kw} 300ms avant que les sujets rapportent l'expérience aha — prédiction de l'intuition à partir des patterns neuronaux.",
                    "Le couplage thêta-gamma dans les circuits hippocampe-préfrontal {topic} lors de la tâche de mémoire de travail {kw} prédit les différences individuelles de capacité — biomarqueur électrophysiologique avec utilité clinique.",
                    "La stimulation du nerf vague couplée à l'entraînement moteur {topic} améliore la réorganisation de la carte corticale {kw} de 2x par rapport à l'entraînement seul — neuromodulation autonome de la plasticité.",
                    "L'analyse transcriptomique des neurones {topic} après la potentialisation à long terme {kw} identifie 340 gènes régulés par l'activité formant un réseau de régulation génique hiérarchique pour la consolidation synaptique.",
                ],
                "findings": [
                    "Le système tDCS en boucle fermée ciblant le cortex moteur {topic} lors de l'acquisition de compétences {kw} atteint une courbe d'apprentissage 2,3x plus rapide en délivrant la stimulation précisément pendant les fenêtres de consolidation neuronale.",
                    "La modulation du système endocannabinoïde lors du conditionnement à la peur {topic} avec l'agoniste sélectif CB1 {kw} empêche la consolidation de la mémoire traumatique sans affecter la mémoire neutre — fenêtre thérapeutique pour le PTSD.",
                    "L'empreinte digitale basée sur le connectome des réseaux cérébraux {topic} prédit la performance cognitive {kw} avec r=0,87 — la connectivité fonctionnelle est un substrat biologique fiable pour les différences individuelles en cognition.",
                ],
                "connections": [
                    "plasticité de la période critique et filets périneuronaux",
                    "régulation épigénétique de l'expression des gènes neuronaux",
                    "architecture du sommeil et stades de consolidation de la mémoire",
                    "éthique de l'amélioration cognitive et neuroéthique",
                ],
            },
        ]
