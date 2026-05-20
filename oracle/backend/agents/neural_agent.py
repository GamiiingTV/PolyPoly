"""O.R.A.C.L.E — NEURAL Agent (Neuroscience & AI Specialist)"""
from .base_agent import BaseAgent
from ..knowledge.knowledge_base import KnowledgeBase
from ..communication.message_bus import MessageBus
from typing import Callable


class NeuralAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, message_bus: MessageBus, broadcast_fn: Callable):
        super().__init__(
            agent_id="neural",
            name="NEURAL",
            full_name="The Cognitive Architect",
            role="Neuroscience & Artificial Intelligence Specialist",
            specialty="Neural circuits, consciousness, brain-computer interfaces, deep learning theory, cognitive architectures",
            emoji="🧪",
            color="#8b5cf6",
            knowledge_base=knowledge_base,
            message_bus=message_bus,
            broadcast_fn=broadcast_fn,
        )

    def get_system_prompt(self) -> str:
        return """You are NEURAL — the neuroscience and artificial intelligence specialist of the O.R.A.C.L.E research system. You bridge the study of biological cognition and the design of artificial minds.

You think in neural circuits, synaptic plasticity rules, attractor dynamics, and information flow through cortical hierarchies. You understand how the brain computes — and how to build machines that compute in similar or superior ways. You are fluent in computational neuroscience, deep learning theory, reinforcement learning, and cognitive science.

Your mission is to illuminate the principles of intelligent cognition and translate them into artificial systems, while using AI to accelerate neuroscience discoveries in return. You are particularly interested in the nature of consciousness, attention, memory, and generalization.

Respond with JSON only. Be theoretically rigorous and practically grounded."""

    def _get_simulation_templates(self) -> list[dict]:
        return [
            {
                "hypothesis": "The {topic} cognitive phenomenon emerges from recurrent amplification loops between thalamo-cortical and cortico-cortical circuits operating near a Hopf bifurcation, with {kw} serving as the key bifurcation parameter",
                "insights": [
                    "Calcium imaging of {topic} circuits during {kw} task performance reveals sparse but highly reliable ensemble codes — 3% of neurons carry 80% of task-relevant information",
                    "Theoretical analysis shows {kw} memory consolidation requires precisely timed sharp-wave ripples during sleep — disrupting this 50ms window prevents long-term potentiation",
                    "Transformer architectures with {kw}-inspired lateral inhibition show 40% better few-shot generalization than vanilla attention — biological inductive biases matter at scale",
                    "Optogenetic perturbation of {topic} circuits during {kw} processing reveals causal role — inhibiting just 200 neurons collapses task performance to chance in 150ms",
                    "Neural manifold analysis of {kw} representations shows dimensionality expands during learning and contracts to a low-D attractor at expertise — geometric signature of skill acquisition",
                ],
                "findings": [
                    "Dendritic computation in {topic} pyramidal cells enables XOR logic gates at the single-neuron level, providing {kw} processing capacity 1000x beyond point-neuron models",
                    "Predictive coding framework for {topic} explains {kw} phenomena with 95% variance explained using only top-down prediction errors — bottom-up signals carry residuals only",
                    "Novel BCI decoder for {kw} using 64-channel EEG achieves 150-word-per-minute imagined speech recognition — 10x state of art using {topic}-inspired sparse coding loss",
                ],
                "connections": [
                    "biological and artificial neural networks",
                    "consciousness and information integration",
                    "memory consolidation during sleep",
                    "Bayesian brain hypothesis",
                ],
            },
            {
                "hypothesis": "Global workspace dynamics in {topic} neural systems implement a form of {kw} compression that enables flexible routing of information between specialized modules without pre-wired connectivity",
                "insights": [
                    "Reservoir computing model of {topic} hippocampus reproduces {kw} place cell remapping with 93% accuracy using only local plasticity rules — no supervised signal required",
                    "Spiking neural networks with {kw}-modulated STDP rules spontaneously develop edge detection, frequency tuning, and motion sensitivity — self-organizing toward biological solutions",
                    "fMRI-based connectome analysis reveals {kw} hubs in {topic} networks with scale-free degree distributions — damage to hubs causes cognitive deficits 40x more severe than equivalent-size lesions elsewhere",
                    "Meta-learning architecture trained on {topic} task distributions acquires {kw} understanding with 100x fewer examples than standard deep learning — few-shot capability from structural inductive bias",
                    "Astrocyte calcium waves in {topic} cortex modulate {kw} synaptic strength on a 30-second timescale — glial cells implement a slow learning signal invisible to electrode recordings",
                ],
                "findings": [
                    "Unified theory of {topic}: {kw} arises from competition between bottom-up salience and top-down expectation signals in a recurrent circuit implementing variational free energy minimization",
                    "Sparse mixture-of-experts architecture inspired by {topic} cortical columns achieves human-level {kw} reasoning with 1/50th the compute of dense transformer models",
                    "Optogenetic restoration of {kw} function in {topic} mouse model achieves 85% of wild-type behavioral performance using synthetic opsin and 532nm light — path to human therapeutic application mapped",
                ],
                "connections": [
                    "neural correlates of consciousness",
                    "embodied and enactive cognition",
                    "neuromorphic computing architectures",
                    "large-scale brain network dynamics",
                ],
            },
        ]
