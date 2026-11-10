"""Capture du son et découpage en répliques.

Deux sources :
  - "interlocuteur" : ce que le PC joue (chat vocal du jeu), capturé en
    boucle WASAPI (loopback) via PyAudioWPatch, Windows uniquement ;
  - "moi" : le micro du joueur.

Chaque flux est découpé en répliques par un détecteur d'activité vocale
fondé sur l'énergie, avec un bruit de fond qui s'adapte (musique, ambiance).
"""
from __future__ import annotations

import collections
import threading
from typing import Callable

import numpy as np

TAUX = 16_000          # Whisper attend du 16 kHz mono
TRAME_MS = 30
TRAME = TAUX * TRAME_MS // 1000


def reechantillonner(signal: np.ndarray, taux_source: int, taux_cible: int = TAUX) -> np.ndarray:
    """Rééchantillonnage léger (moyenne puis décimation, ou interpolation)."""
    if taux_source == taux_cible or signal.size == 0:
        return signal.astype(np.float32)
    if taux_source % taux_cible == 0:
        facteur = taux_source // taux_cible
        n = signal.size - signal.size % facteur
        return signal[:n].reshape(-1, facteur).mean(axis=1).astype(np.float32)
    duree = signal.size / taux_source
    n_cible = int(duree * taux_cible)
    x_src = np.linspace(0.0, duree, signal.size, endpoint=False)
    x_cib = np.linspace(0.0, duree, n_cible, endpoint=False)
    return np.interp(x_cib, x_src, signal).astype(np.float32)


class Segmenteur:
    """Découpe un flux audio 16 kHz en répliques (segments de parole)."""

    def __init__(
        self,
        silence_fin_ms: int = 550,
        duree_min_ms: int = 400,
        sensibilite: float = 3.0,
        duree_max_s: float = 25.0,
        preroll_ms: int = 300,
    ):
        self.trames_silence_fin = max(1, silence_fin_ms // TRAME_MS)
        self.trames_min = max(1, duree_min_ms // TRAME_MS)
        self.trames_max = int(duree_max_s * 1000 / TRAME_MS)
        self.sensibilite = sensibilite
        self.bruit = 0.003            # estimation du bruit de fond (RMS)
        self.plancher = 0.0015        # en dessous : silence quoi qu'il arrive
        self._preroll = collections.deque(maxlen=max(1, preroll_ms // TRAME_MS))
        self._tampon = np.zeros(0, dtype=np.float32)
        self._en_parole = False
        self._trames: list[np.ndarray] = []
        self._silence = 0
        self._candidat = 0
        self._voisees = 0
        self.au_debut = None          # rappel facultatif : quelqu'un commence à parler

    def _est_parole(self, rms: float) -> bool:
        return rms > max(self.plancher, self.bruit * self.sensibilite)

    def pousser(self, echantillons: np.ndarray) -> list[np.ndarray]:
        """Ajoute de l'audio ; renvoie les répliques terminées."""
        termines: list[np.ndarray] = []
        self._tampon = np.concatenate([self._tampon, echantillons.astype(np.float32)])
        while self._tampon.size >= TRAME:
            trame, self._tampon = self._tampon[:TRAME], self._tampon[TRAME:]
            seg = self._traiter(trame)
            if seg is not None:
                termines.append(seg)
        return termines

    def _traiter(self, trame: np.ndarray) -> np.ndarray | None:
        rms = float(np.sqrt(np.mean(trame * trame)) + 1e-9)
        parole = self._est_parole(rms)

        if not self._en_parole:
            # Le bruit de fond suit lentement le niveau ambiant hors parole.
            self.bruit = 0.97 * self.bruit + 0.03 * rms if not parole else self.bruit
            self._preroll.append(trame)
            self._candidat = self._candidat + 1 if parole else 0
            if self._candidat >= 3:   # 90 ms de parole d'affilée
                self._en_parole = True
                self._trames = list(self._preroll)
                self._silence = 0
                self._voisees = self._candidat
                if self.au_debut:
                    self.au_debut()
            return None

        self._trames.append(trame)
        self._silence = 0 if parole else self._silence + 1
        self._voisees += 1 if parole else 0
        trop_long = len(self._trames) >= self.trames_max
        if self._silence >= self.trames_silence_fin or trop_long:
            # On garde un peu du silence final, pour ne pas couper la dernière syllabe.
            trames = self._trames[: len(self._trames) - (0 if trop_long else self._silence // 2)]
            voisees = self._voisees
            self._en_parole = False
            self._trames = []
            self._candidat = 0
            self._voisees = 0
            self._preroll.clear()
            if voisees >= self.trames_min:
                return np.concatenate(trames)
        return None

    def vider(self) -> np.ndarray | None:
        if self._en_parole and self._voisees >= self.trames_min:
            seg = np.concatenate(self._trames)
            self._trames, self._en_parole = [], False
            return seg
        return None


# ----------------------------------------------------------------------
# Capture Windows (PyAudioWPatch)
# ----------------------------------------------------------------------

def _pyaudio():
    try:
        import pyaudiowpatch as pyaudio  # type: ignore
    except ImportError as e:  # pragma: no cover - dépend de Windows
        raise RuntimeError(
            "PyAudioWPatch est introuvable. Lance lancer.bat (Windows) pour installer "
            "les dépendances, ou utilise le mode --simulation."
        ) from e
    return pyaudio


def lister_peripheriques() -> list[str]:
    pyaudio = _pyaudio()
    p = pyaudio.PyAudio()
    lignes = []
    try:
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            if d.get("maxInputChannels", 0) > 0:
                genre = "SORTIE (loopback)" if d.get("isLoopbackDevice") else "micro/entrée"
                lignes.append(f"[{i:>2}] {genre:<18} {d['name']}")
    finally:
        p.terminate()
    return lignes


def _trouver_peripherique(p, pyaudio, source: str, nom: str) -> dict:
    nom = nom.lower().strip()
    if source == "interlocuteur":
        boucles = list(p.get_loopback_device_info_generator())
        if nom:
            for d in boucles:
                if nom in d["name"].lower():
                    return d
            raise RuntimeError(f"Aucune sortie audio ne contient « {nom} ».")
        wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        defaut = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
        if defaut.get("isLoopbackDevice"):
            return defaut
        for d in boucles:
            if defaut["name"] in d["name"]:
                return d
        raise RuntimeError("Impossible de capturer la sortie audio par défaut (WASAPI loopback).")
    if nom:
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            if d.get("maxInputChannels", 0) > 0 and not d.get("isLoopbackDevice") and nom in d["name"].lower():
                return d
        raise RuntimeError(f"Aucun micro ne contient « {nom} ».")
    return p.get_default_input_device_info()


class Capture(threading.Thread):
    """Écoute une source et appelle `rappel(source, audio_16k)` à chaque réplique."""

    def __init__(self, source: str, nom_peripherique: str, segmenteur: Segmenteur,
                 rappel: Callable[[str, np.ndarray], None], journal: Callable[[str], None]):
        super().__init__(daemon=True, name=f"capture-{source}")
        self.source = source
        self.nom_peripherique = nom_peripherique
        self.segmenteur = segmenteur
        self.rappel = rappel
        self.journal = journal
        self.actif = threading.Event()
        self.actif.set()
        self._arret = threading.Event()

    def arreter(self) -> None:
        self._arret.set()

    def run(self) -> None:  # pragma: no cover - dépend du matériel
        pyaudio = _pyaudio()
        p = pyaudio.PyAudio()
        try:
            dev = _trouver_peripherique(p, pyaudio, self.source, self.nom_peripherique)
            taux = int(dev["defaultSampleRate"])
            canaux = max(1, int(dev["maxInputChannels"]))
            bloc = taux * TRAME_MS // 1000 * 4
            flux = p.open(format=pyaudio.paFloat32, channels=canaux, rate=taux, input=True,
                          input_device_index=dev["index"], frames_per_buffer=bloc)
            self.journal(f"Écoute « {self.source} » sur : {dev['name']}")
            while not self._arret.is_set():
                brut = flux.read(bloc, exception_on_overflow=False)
                if not self.actif.is_set():
                    continue
                signal = np.frombuffer(brut, dtype=np.float32)
                if canaux > 1:
                    signal = signal.reshape(-1, canaux).mean(axis=1)
                for seg in self.segmenteur.pousser(reechantillonner(signal, taux)):
                    self.rappel(self.source, seg)
            flux.stop_stream()
            flux.close()
        except Exception as e:
            self.journal(f"Erreur de capture ({self.source}) : {e}")
        finally:
            p.terminate()

