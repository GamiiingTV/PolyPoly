"""Les yeux du Souffleur : captures d'écran du jeu et observation continue de la scène.

- `Oeil` capture la fenêtre du jeu (ou un écran entier), la réduit et l'encode en JPEG.
- `Observateur` regarde l'écran à intervalles réguliers, seulement quand l'image a
  changé, et demande à Claude de décrire la scène (lieu, moment, personnes, tension).

L'outil ne fait que regarder : il n'envoie jamais de touche ni de clic au jeu.
"""
from __future__ import annotations

import base64
import io
import os
import threading
import time
from typing import Callable

import numpy as np

from .config import ConfigVision


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
    """Une capture prête à envoyer."""

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
        self._instantane: Image | None = None
        self._verrou = threading.Lock()
        self._fenetre_signalee = None

    def _zone(self, sct) -> dict:
        zone = _rect_fenetre(self.cfg.titre_fenetre)
        trouvee = zone is not None
        if trouvee != self._fenetre_signalee:
            self._fenetre_signalee = trouvee
            self.journal(f"Vision : fenêtre « {self.cfg.titre_fenetre} » trouvée." if trouvee else
                         f"Vision : fenêtre « {self.cfg.titre_fenetre} » introuvable, je regarde l'écran {self.cfg.ecran}.")
        if zone:
            return zone
        ecrans = sct.monitors
        return ecrans[self.cfg.ecran] if 0 < self.cfg.ecran < len(ecrans) else ecrans[1 if len(ecrans) > 1 else 0]

    def capturer(self) -> Image | None:
        import mss
        from PIL import Image as PIL
        try:
            fabrique = getattr(mss, "MSS", None) or mss.mss
            with fabrique() as sct:   # une instance par appel : mss n'aime pas les fils multiples
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

    def instantane(self) -> None:
        """À appeler quand quelqu'un commence à parler : fige ce qu'on voit à cet instant."""
        img = self.capturer()
        if img:
            with self._verrou:
                self._instantane = img

    def pour_replique(self, fraicheur_s: float = 20.0) -> Image | None:
        """L'image du moment où l'on t'a adressé la parole, sinon une capture immédiate."""
        with self._verrou:
            img = self._instantane
            self._instantane = None
        if img and time.monotonic() - img.quand <= fraicheur_s:
            return img
        return self.capturer()


class Observateur(threading.Thread):
    """Regarde la scène en continu et tient à jour sa description."""

    def __init__(self, oeil: Oeil, decrire: Callable[[Image], None], intervalle_s: float,
                 seuil_changement: float = 10.0):
        super().__init__(daemon=True, name="observateur")
        self.oeil = oeil
        self.decrire = decrire
        self.intervalle_s = max(5.0, intervalle_s)
        self.seuil = seuil_changement
        self.actif = threading.Event()
        self.actif.set()
        self._derniere: Image | None = None
        self._reveil = threading.Event()

    def maintenant(self) -> None:
        self._reveil.set()

    def run(self) -> None:
        time.sleep(3)
        while True:
            force = self._reveil.is_set()
            self._reveil.clear()
            if self.actif.is_set():
                img = self.oeil.capturer()
                if img and (force or img.difference(self._derniere) >= self.seuil):
                    self._derniere = img
                    try:
                        self.decrire(img)
                    except Exception as e:  # ne jamais tuer l'observateur
                        self.oeil.journal(f"Vision : observation ratée ({e}).")
            self._reveil.wait(self.intervalle_s)
