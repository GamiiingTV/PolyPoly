"""Transcription locale avec faster-whisper (sur la carte graphique)."""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np


# Phrases que Whisper « invente » sur du silence ou de la musique.
HALLUCINATIONS = re.compile(
    r"(sous-titr|amara\.org|merci d'avoir regard|abonnez-vous|n'oubliez pas de|"
    r"radio-canada|^\W*$|^(merci|musique|\.+)\W*$)",
    re.IGNORECASE,
)


def _dll_cuda() -> None:
    """Sous Windows, rend visibles les DLL CUDA installées par pip (nvidia-cublas, nvidia-cudnn)."""
    if os.name != "nt":
        return
    try:
        import nvidia  # type: ignore
    except ImportError:
        return
    for base in getattr(nvidia, "__path__", []):
        for bin_ in Path(base).glob("*/bin"):
            os.add_dll_directory(str(bin_))
            os.environ["PATH"] = str(bin_) + os.pathsep + os.environ.get("PATH", "")


class Transcripteur:
    def __init__(self, modele: str, appareil: str, precision: str, journal, vocabulaire: str = ""):
        # Noms propres soufflés à Whisper pour qu'il les écrive correctement.
        self.vocabulaire = (vocabulaire.strip().rstrip(".") + ".") if vocabulaire.strip() else None
        _dll_cuda()
        from faster_whisper import WhisperModel  # import tardif : lourd

        try:
            self.modele = WhisperModel(modele, device=appareil, compute_type=precision)
        except Exception as e:
            journal(f"Whisper sur {appareil} impossible ({e}) ; repli sur le processeur.")
            self.modele = WhisperModel(modele, device="cpu", compute_type="int8")
        journal(f"Transcription prête (modèle {modele}).")

    def transcrire(self, audio: np.ndarray) -> str:
        segments, _ = self.modele.transcribe(
            audio,
            language="fr",
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=self.vocabulaire,
        )
        morceaux = []
        for s in segments:
            if s.no_speech_prob > 0.6 and s.avg_logprob < -0.8:
                continue
            texte = s.text.strip()
            if self.vocabulaire and texte.strip(" .,").lower() in self.vocabulaire.lower():
                continue          # Whisper qui répète la liste de noms sur du silence
            if texte and not HALLUCINATIONS.search(texte):
                morceaux.append(texte)
        return " ".join(morceaux).strip()
