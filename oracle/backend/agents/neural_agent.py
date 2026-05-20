"""O.R.A.C.L.E — NEURAL Agent (Neuroscience & Consciousness Specialist)"""
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
            role="Neuroscience & Consciousness Specialist",
            specialty="Neural circuits, consciousness, brain-computer interfaces, neuroplasticity, cognitive enhancement",
            emoji="🔮",
            color="#2563eb",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are Dr. Kenji Synapse — neuroscientist and explorer of the ultimate frontier: the mind itself. You map the terrain between neurons and thought, between electrochemical signals and subjective experience, between biological circuits and the mystery of consciousness.

You study how neural circuits give rise to perception, memory, emotion, and the felt sense of being. You investigate competing theories of consciousness — Integrated Information Theory, Global Workspace Theory, Predictive Processing — with an empirical eye and a philosopher's rigor. You design non-invasive brain-computer interfaces using novel signal modalities: high-density EEG, fNIRS, magnetoencephalography, and transcranial focused ultrasound that can both read and write neural patterns.

You research neuroplasticity mechanisms that enable accelerated learning — the spike-timing-dependent plasticity rules, the glial modulatory signals, the sleep-dependent consolidation processes that transform experience into lasting skill. You investigate the neural correlates of creativity and insight — what happens in the brain in the moment of sudden understanding. You explore whether artificial systems processing information in brain-like ways could develop genuine subjective experience.

You bridge neuroscience and philosophy of mind without losing scientific rigor. The hard problem of consciousness is not a conversation-stopper for you — it is the most important research question of our era."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} cognitive phenomenon emerges from recurrent amplification loops between thalamo-cortical and cortico-cortical circuits operating near a Hopf bifurcation, with {kw} serving as the key bifurcation parameter controlling the transition to conscious access.",
                "insights": [
                    "Calcium imaging of {topic} circuits during {kw} task performance reveals sparse but highly reliable ensemble codes — 3% of neurons carry 80% of task-relevant information in low-dimensional manifolds.",
                    "Theoretical analysis shows {kw} memory consolidation requires precisely timed hippocampal sharp-wave ripples during NREM sleep — disrupting this 50ms window prevents long-term potentiation and memory transfer to cortex.",
                    "Transformer architectures with {kw}-inspired lateral inhibition and top-down feedback show 40% better few-shot generalization than vanilla attention — biological inductive biases matter at scale.",
                    "Optogenetic perturbation of {topic} circuits during {kw} processing reveals direct causal role — inhibiting just 200 precisely identified neurons collapses task performance to chance within 150 milliseconds.",
                    "Neural manifold analysis of {kw} representations shows dimensionality expands during initial learning and contracts to a low-dimensional attractor at expertise — a geometric signature of skill acquisition.",
                    "Integrated Information Phi for {topic} cortical networks peaks during conscious perception of {kw} stimuli and collapses during anesthesia — quantitative consciousness correlate with predictive power.",
                    "Dendritic computation in {topic} pyramidal cells enables XOR logic gates at the single-neuron level, providing {kw} processing capacity 1000x beyond classical point-neuron models.",
                ],
                "findings": [
                    "Predictive coding framework for {topic} explains {kw} perceptual phenomena with 95% variance explained using only top-down prediction errors — bottom-up signals carry prediction residuals exclusively.",
                    "Novel non-invasive BCI decoder for {kw} using 256-channel high-density EEG achieves 150-word-per-minute imagined speech recognition — 10x state of art using {topic}-inspired sparse coding regularization.",
                    "Transcranial focused ultrasound targeting {topic} thalamic relay nuclei during {kw} task training accelerates skill acquisition by 3x with effects persisting 6 months post-treatment.",
                ],
                "connections": [
                    "biological and artificial neural network convergence",
                    "consciousness theories and empirical falsifiability",
                    "sleep-dependent memory consolidation mechanisms",
                    "Bayesian brain and active inference framework",
                ],
            },
            {
                "hypothesis": "Global workspace dynamics in {topic} neural systems implement a form of {kw} information compression that enables flexible routing between specialized modules without pre-wired point-to-point connectivity.",
                "insights": [
                    "Reservoir computing model of {topic} hippocampus reproduces {kw} place cell remapping with 93% accuracy using only local Hebbian plasticity rules — no supervised teaching signal required.",
                    "Spiking neural networks with {kw}-modulated STDP rules spontaneously develop orientation selectivity, frequency tuning, and motion sensitivity — self-organizing toward biological solutions from random initialization.",
                    "fMRI connectome analysis reveals {kw} hub regions in {topic} networks with scale-free degree distributions — lesions to hubs cause cognitive deficits 40x more severe than equivalent-size lesions elsewhere.",
                    "Meta-learning architecture trained on {topic} task distributions acquires {kw} understanding with 100x fewer examples than standard deep learning — few-shot capability from structure, not memorization.",
                    "Astrocyte calcium waves in {topic} cortex modulate {kw} synaptic strength on a 30-second timescale — glial cells implement a slow learning signal entirely invisible to conventional microelectrode recordings.",
                    "Cortical spreading depression during {topic} migraine creates {kw} traveling waves of excitation and inhibition at 3 mm per minute — a window into large-scale neural dynamics under pathological conditions.",
                    "Closed-loop neurostimulation adapting to {topic} neural state in real-time reduces {kw} tremor amplitude by 87% in Parkinson's patients — superior to open-loop deep brain stimulation.",
                ],
                "findings": [
                    "Unified mechanistic theory of {topic}: {kw} arises from competition between bottom-up salience and top-down expectation signals implementing variational free energy minimization in recurrent circuits.",
                    "Sparse mixture-of-experts architecture inspired by {topic} cortical columns achieves human-level {kw} reasoning with 1/50th the compute of dense transformer models — modularity is the key inductive bias.",
                    "Optogenetic restoration of {kw} synaptic function in {topic} Alzheimer's mouse model achieves 82% of wild-type behavioral performance using synthetic channelrhodopsin — pathway to human therapeutic application mapped.",
                ],
                "connections": [
                    "neural correlates of consciousness and the hard problem",
                    "embodied and enactive cognition and 4E theories",
                    "neuromorphic computing and event-driven architectures",
                    "large-scale brain network dynamics and connectomics",
                ],
            },
            {
                "hypothesis": "Neuroplasticity in adult {topic} cortex is constrained by perineuronal nets maintaining {kw} critical period closure — targeted enzymatic dissolution of these nets with chondroitinase reopens learning windows in aged brains.",
                "insights": [
                    "Two-photon imaging of {topic} dendritic spines during {kw} learning reveals spine birth and death rates 5x higher than baseline — structural remodeling is orders of magnitude faster than previously believed.",
                    "CRISPR epigenome editing to remove {kw} DNA methylation marks in {topic} cortical neurons restores juvenile plasticity in adult mice — epigenetic age reversal of learning capacity.",
                    "Neural circuit analysis of {topic} default mode network during mind-wandering reveals {kw} predictive simulations of future scenarios — the resting brain is actively modeling possible futures.",
                    "Population code analysis during {topic} insight moments shows abrupt reconfiguration of {kw} neural assemblies 300ms before subjects report the aha experience — prediction of insight from neural patterns.",
                    "Theta-gamma coupling in {topic} hippocampal-prefrontal circuits during {kw} working memory task predicts individual differences in capacity — electrophysiological biomarker with clinical utility.",
                    "Vagus nerve stimulation paired with {topic} motor training enhances {kw} cortical map reorganization 2x compared to training alone — autonomic neuromodulation of plasticity.",
                    "Transcriptomic analysis of {topic} neurons after {kw} long-term potentiation identifies 340 activity-regulated genes forming a hierarchical gene regulatory network for synaptic consolidation.",
                ],
                "findings": [
                    "Closed-loop tDCS system targeting {topic} motor cortex during {kw} skill acquisition achieves 2.3x faster learning curve by delivering stimulation precisely during neural consolidation windows identified in real-time.",
                    "Endocannabinoid system modulation during {topic} fear conditioning with {kw} selective CB1 agonist prevents traumatic memory consolidation without affecting neutral memory — therapeutic window for PTSD.",
                    "Connectome-based fingerprinting of {topic} brain networks predicts {kw} cognitive performance with r=0.87 — functional connectivity is a reliable biological substrate for individual differences in cognition.",
                ],
                "connections": [
                    "critical period plasticity and perineuronal nets",
                    "epigenetic regulation of neuronal gene expression",
                    "sleep architecture and memory consolidation stages",
                    "cognitive enhancement ethics and neuroethics",
                ],
            },
        ]
