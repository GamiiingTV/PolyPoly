"""Reconnaissance approximative des voix (qui parle ?).

Empreinte simple : moyenne et écart-type du spectre log-mel d'une réplique.
Les répliques proches sont rangées sous la même voix (« Voix A », « Voix B »...).
C'est volontairement léger (aucun réseau de neurones) : ça distingue bien
une voix grave d'une voix aiguë, moins bien deux voix semblables. Le joueur
peut renommer une voix dans l'interface (« Voix A » -> « Kuno le forgeron »)
et Claude s'aide aussi du contexte (« Je suis Kuno... »).
"""
from __future__ import annotations

import string
import threading

import numpy as np

from .audio import TAUX

N_FFT = 512
PAS = 160          # 10 ms
N_MEL = 32


def _banc_mel(n_mel: int = N_MEL, n_fft: int = N_FFT, taux: int = TAUX) -> np.ndarray:
    def hz_mel(f):
        return 2595.0 * np.log10(1.0 + f / 700.0)

    def mel_hz(m):
        return 700.0 * (10 ** (m / 2595.0) - 1.0)

    points = mel_hz(np.linspace(hz_mel(80.0), hz_mel(7600.0), n_mel + 2))
    cases = np.floor((n_fft + 1) * points / taux).astype(int)
    banc = np.zeros((n_mel, n_fft // 2 + 1))
    for i in range(1, n_mel + 1):
        g, c, d = cases[i - 1], cases[i], cases[i + 1]
        for k in range(g, c):
            banc[i - 1, k] = (k - g) / max(1, c - g)
        for k in range(c, d):
            banc[i - 1, k] = (d - k) / max(1, d - c)
    return banc


_BANC = _banc_mel()
_FENETRE = np.hanning(400)


def empreinte(audio: np.ndarray) -> np.ndarray | None:
    if audio.size < TAUX // 2:
        return None
    n = 1 + (audio.size - 400) // PAS
    idx = np.arange(400)[None, :] + PAS * np.arange(n)[:, None]
    trames = audio[idx] * _FENETRE
    energie = np.sqrt((trames ** 2).mean(axis=1))
    trames = trames[energie > np.percentile(energie, 40)]   # garde les trames voisées
    if len(trames) < 10:
        return None
    spectre = np.abs(np.fft.rfft(trames, n=N_FFT)) ** 2
    logmel = np.log(spectre @ _BANC.T + 1e-10)
    logmel -= logmel.mean(axis=1, keepdims=True)            # insensible au volume
    v = np.concatenate([logmel.mean(axis=0), logmel.std(axis=0)])
    return v / (np.linalg.norm(v) + 1e-9)


class RegistreVoix:
    def __init__(self, seuil: float = 0.93):
        self.seuil = seuil
        self._centres: list[np.ndarray] = []
        self._comptes: list[int] = []
        self._noms: dict[str, str] = {}
        self._verrou = threading.Lock()

    @staticmethod
    def _etiquette(i: int) -> str:
        lettres = string.ascii_uppercase
        return f"Voix {lettres[i % 26]}{'' if i < 26 else i // 26}"

    def identifier(self, audio: np.ndarray) -> str:
        v = empreinte(audio)
        with self._verrou:
            if v is None:
                return "Voix ?"
            if self._centres:
                sims = [float(c @ v) for c in self._centres]
                i = int(np.argmax(sims))
                if sims[i] >= self.seuil:
                    n = self._comptes[i]
                    c = (self._centres[i] * n + v) / (n + 1)
                    self._centres[i] = c / (np.linalg.norm(c) + 1e-9)
                    self._comptes[i] = min(n + 1, 30)
                    return self._etiquette(i)
            self._centres.append(v)
            self._comptes.append(1)
            return self._etiquette(len(self._centres) - 1)

    def nommer(self, etiquette: str, nom: str) -> None:
        with self._verrou:
            if nom.strip():
                self._noms[etiquette] = nom.strip()
            else:
                self._noms.pop(etiquette, None)

    def nom(self, etiquette: str) -> str:
        return self._noms.get(etiquette, etiquette)
