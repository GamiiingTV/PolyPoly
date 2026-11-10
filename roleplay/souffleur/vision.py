"""Les yeux du Souffleur : l'écran du jeu filmé en continu.

- `Oeil` filme la fenêtre du jeu (ou un écran entier) plusieurs fois par seconde et
  garde les ~30 dernières secondes en mémoire vive (jamais sur le disque).
  Pour une réplique, il fournit l'écran du moment où l'on a commencé à parler et
  l'écran actuel s'il a changé.
- `Observateur` fait décrire la scène par Claude dès qu'elle change (au plus toutes
  les `intervalle_min_s` secondes), tout de suite si elle change brutalement, et au
  moins toutes les `battement_s` secondes.

L'outil ne fait que regarder : il n'envoie jamais de touche ni de clic au jeu.
"""
from __future__ import annotations

import base64
import collections
import io
import os
import threading
import time
from typing import Callable

import numpy as np

from .config import ConfigVision

SEUIL_CHANGEMENT = 8.0     # différence moyenne (0-255) pour dire « l'image a changé »
SEUIL_RUPTURE = 30.0       # changement brutal : nouvelle scène, écran de chargement, combat


def _rect_fenetre(titre: str) -> dict | None:
    """Zone cliente de la première fenêtre visible dont le titre contient `titre` (Windows)."""
    if os.name != "nt" or not titre:
        return None
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    trouvees: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _):
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                tampon = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, tampon, n + 1)
                if titre.lower() in tampon.value.lower():
                    trouvees.append(hwnd)
                    return False
        return True

    user32.EnumWindows(_enum, 0)
    if not trouvees:
        return None
    rect, coin = wintypes.RECT(), wintypes.POINT(0, 0)
    user32.GetClientRect(trouvees[0], ctypes.byref(rect))
    user32.ClientToScreen(trouvees[0], ctypes.byref(coin))
    if rect.right < 200 or rect.bottom < 200:
        return None
    return {"left": coin.x, "top": coin.y, "width": rect.right, "height": rect.bottom}


def masquer_des_captures(fenetre_tk) -> bool:
    """Rend la fenêtre du Souffleur invisible aux captures d'écran (Windows 10 2004+),
    pour que Claude voie le jeu et non nos propres suggestions."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetAncestor(fenetre_tk.winfo_id(), 2)  # GA_ROOT
        return bool(user32.SetWindowDisplayAffinity(hwnd, 0x11))  # WDA_EXCLUDEFROMCAPTURE
    except Exception:
        return False


class Image:
    """Une image de l'écran, prête à envoyer."""

    def __init__(self, jpeg: bytes, signature: np.ndarray, quand: float):
        self.jpeg = jpeg
        self.signature = signature
        self.quand = quand

    def bloc(self) -> dict:
        return {"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg",
            "data": base64.standard_b64encode(self.jpeg).decode("ascii")}}

    def difference(self, autre: "Image | None") -> float:
        if autre is None:
            return 255.0
        return float(np.abs(self.signature - autre.signature).mean())


class Oeil:
    def __init__(self, cfg: ConfigVision, journal: Callable[[str], None]):
        import mss  # noqa: F401  (vérifie la présence)
        from PIL import Image as _PIL  # noqa: F401
        self.cfg = cfg
        self.journal = journal
        self.periode = 1.0 / max(0.2, min(10.0, cfg.images_par_seconde))
        self.images: collections.deque[Image] = collections.deque(maxlen=max(4, int(30 / self.periode)))
        self.actif = threading.Event()
        self.actif.set()
        self.sur_rupture: Callable[[], None] | None = None
        self._debut_parole: float | None = None
        self._verrou = threading.Lock()
        self._fenetre_signalee = None
        self._zone_cache: tuple[float, dict] | None = None

    # ------------------------------------------------------------ capture
    def _zone(self, sct) -> dict:
        maintenant = time.monotonic()
        if self._zone_cache and maintenant - self._zone_cache[0] < 2.0:
            return self._zone_cache[1]
        zone = _rect_fenetre(self.cfg.titre_fenetre)
        trouvee = zone is not None
        if trouvee != self._fenetre_signalee:
            self._fenetre_signalee = trouvee
            self.journal(f"Vision : fenêtre « {self.cfg.titre_fenetre} » trouvée." if trouvee else
                         f"Vision : fenêtre « {self.cfg.titre_fenetre} » introuvable, je regarde l'écran {self.cfg.ecran}.")
        if not zone:
            ecrans = sct.monitors
            zone = ecrans[self.cfg.ecran] if 0 < self.cfg.ecran < len(ecrans) else ecrans[1 if len(ecrans) > 1 else 0]
        self._zone_cache = (maintenant, zone)
        return zone

    def capturer(self, sct=None) -> Image | None:
        import mss
        from PIL import Image as PIL
        try:
            if sct is None:
                fabrique = getattr(mss, "MSS", None) or mss.mss
                with fabrique() as s:
                    brut = s.grab(self._zone(s))
            else:
                brut = sct.grab(self._zone(sct))
            img = PIL.frombytes("RGB", brut.size, brut.bgra, "raw", "BGRX")
        except Exception as e:
            self.journal(f"Vision : capture impossible ({e}).")
            return None
        img.thumbnail((self.cfg.largeur_max, self.cfg.largeur_max))
        signature = np.asarray(img.convert("L").resize((48, 27)), dtype=np.float32)
        tampon = io.BytesIO()
        img.save(tampon, format="JPEG", quality=self.cfg.qualite)
        return Image(tampon.getvalue(), signature, time.monotonic())

    def filmer(self) -> None:
        """Boucle de capture continue (à lancer dans un fil dédié)."""
        import mss
        fabrique = getattr(mss, "MSS", None) or mss.mss
        with fabrique() as sct:   # une instance par fil : mss n'aime pas être partagé
            while True:
                debut = time.monotonic()
                if self.actif.is_set():
                    img = self.capturer(sct)
                    if img:
                        precedente = self.derniere()
                        with self._verrou:
                            self.images.append(img)
                        if precedente and img.difference(precedente) >= SEUIL_RUPTURE and self.sur_rupture:
                            self.sur_rupture()
                time.sleep(max(0.0, self.periode - (time.monotonic() - debut)))

    def demarrer(self) -> None:
        threading.Thread(target=self.filmer, daemon=True, name="oeil").start()

    # ------------------------------------------------------------ lecture
    def derniere(self) -> Image | None:
        with self._verrou:
            return self.images[-1] if self.images else None

    def a_l_instant(self, quand: float) -> Image | None:
        with self._verrou:
            avant = [i for i in self.images if i.quand <= quand + 0.2]
            return avant[-1] if avant else (self.images[0] if self.images else None)

    def marquer_debut_parole(self) -> None:
        self._debut_parole = time.monotonic()

    def pour_replique(self) -> list[tuple[str, Image]]:
        """L'écran du début de la réplique, puis l'écran actuel s'il a changé."""
        actuelle = self.derniere()
        if actuelle is None or time.monotonic() - actuelle.quand > 3 * self.periode + 1:
            actuelle = self.capturer() or actuelle      # flux arrêté : capture immédiate
        if actuelle is None:
            return []
        debut = self._debut_parole
        if debut is not None and time.monotonic() - debut < 30:
            initiale = self.a_l_instant(debut)
            if initiale is not None and initiale is not actuelle and initiale.difference(actuelle) >= SEUIL_CHANGEMENT:
                ecart = actuelle.quand - initiale.quand
                return [("l'écran quand on a commencé à parler à {nom}", initiale),
                        (f"l'écran maintenant, {ecart:.0f} s plus tard", actuelle)]
        return [("l'écran maintenant", actuelle)]


class Observateur(threading.Thread):
    """Fait décrire la scène dès qu'elle change, sur le flux continu de l'Oeil."""

    def __init__(self, oeil: Oeil, decrire: Callable[[Image], None], intervalle_min_s: float,
                 battement_s: float):
        super().__init__(daemon=True, name="observateur")
        self.oeil = oeil
        self.decrire = decrire
        self.intervalle_min_s = max(3.0, intervalle_min_s)
        self.battement_s = max(self.intervalle_min_s, battement_s)
        self.actif = threading.Event()
        self.actif.set()
        self._decrite: Image | None = None
        self._quand = 0.0
        self._urgence = threading.Event()

    def maintenant(self) -> None:
        self._urgence.set()

    def run(self) -> None:
        time.sleep(2)
        while True:
            urgent = self._urgence.wait(1.0)
            if not self.actif.is_set():
                self._urgence.clear()
                continue
            img = self.oeil.derniere()
            ecoule = time.monotonic() - self._quand
            if img is None or img is self._decrite:
                self._urgence.clear()
                continue
            change = img.difference(self._decrite) >= SEUIL_CHANGEMENT
            if (urgent and ecoule >= 2.0) or (change and ecoule >= self.intervalle_min_s) \
                    or ecoule >= self.battement_s:
                self._urgence.clear()
                if urgent:
                    time.sleep(0.8)                      # laisse la nouvelle scène se poser
                    img = self.oeil.derniere() or img
                self._decrite, self._quand = img, time.monotonic()
                try:
                    self.decrire(img)
                except Exception as e:   # ne jamais tuer l'observateur
                    self.oeil.journal(f"Vision : observation ratée ({e}).")
            elif urgent:
                time.sleep(0.25)                         # urgence trop proche de la dernière vue
