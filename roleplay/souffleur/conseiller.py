"""Génération des répliques (en flux), tenue de la chronique et description de la scène."""
from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from pydantic import BaseModel

from . import prompts
from .memoire import Memoire, Personne, Replique
from .moteurs import ErreurMoteur
from .profil import Profil
from .vision import Image

_RE_CHOIX = re.compile(r"^\s*(\d+)\s*[.)\-:]\s*(?:\[([^\]]+)\]\s*)?(.+?)\s*$")


@dataclass
class Choix:
    numero: int
    ton: str
    texte: str


@dataclass
class Proposition:
    situation: str = ""
    qui: str = ""
    vu: str = ""
    choix: list[Choix] = field(default_factory=list)
    conseil: str = ""


def analyser_ligne(ligne: str, prop: Proposition) -> str | None:
    """Range une ligne de la réponse dans la proposition. Renvoie son type ou None."""
    ligne = ligne.strip().strip("*").strip()
    if not ligne:
        return None
    haut = ligne.upper()
    for cle, attr in (("SITUATION", "situation"), ("QUI", "qui"), ("VU", "vu"), ("CONSEIL", "conseil")):
        if haut.startswith(cle) and ":" in ligne[: len(cle) + 3]:
            setattr(prop, attr, ligne.split(":", 1)[1].strip())
            return attr
    m = _RE_CHOIX.match(ligne)
    if m:
        texte = m.group(3).strip().strip('"«» ').strip()
        prop.choix.append(Choix(int(m.group(1)), (m.group(2) or "").strip(), texte))
        return "choix"
    return None


def analyser(texte: str) -> Proposition:
    prop = Proposition()
    for ligne in texte.splitlines():
        analyser_ligne(ligne, prop)
    return prop


class Conseiller:
    """Lance une génération à la fois ; une nouvelle demande annule la précédente."""

    def __init__(self, moteur, profil: Profil, memoire: Memoire, nombre: int,
                 evenement: Callable[[str, object], None],
                 fournir_images: Callable[[], list[tuple[str, Image]]] | None = None):
        self.moteur = moteur
        self.profil = profil
        self.fournir_images = fournir_images
        self.memoire = memoire
        self.nombre = nombre
        self.evenement = evenement   # (type, donnée) -> interface
        self.systeme = prompts.systeme_souffleur(profil)
        self._generation = 0
        self._verrou = threading.Lock()

    def demander(self, consigne: str = "", depuis: float | None = None) -> None:
        """`depuis` : instant où la personne s'est tue, pour mesurer le délai réel."""
        with self._verrou:
            self._generation += 1
            gen = self._generation
        threading.Thread(target=self._generer, args=(gen, consigne, depuis), daemon=True).start()

    def annuler(self) -> None:
        with self._verrou:
            self._generation += 1

    def _a_jour(self, gen: int) -> bool:
        return gen == self._generation

    def prechauffer(self) -> None:
        """La première vraie demande part ainsi aussi vite que les suivantes."""
        self.moteur.prechauffer(self.systeme)

    def _contenu(self, consigne: str) -> list[dict]:
        images = self.fournir_images() if self.fournir_images else []
        contenu: list[dict] = []
        legendes = []
        for i, (legende, image) in enumerate(images, 1):
            legende = f"Image {i} : " + legende.format(nom=self.profil.nom)
            legendes.append(legende)
            contenu += [{"type": "text", "text": legende}, image.bloc()]
        demande = prompts.demande_souffleur(
            self.profil, self.memoire.texte_registre(), self.memoire.situation,
            self.memoire.texte_scenes(), self.memoire.texte_fil(40), self.nombre, consigne, legendes,
        )
        contenu.append({"type": "text", "text": demande})
        return contenu

    def _generer(self, gen: int, consigne: str, depuis: float | None = None) -> None:
        debut = depuis or time.monotonic()
        self.evenement("debut", None)
        prop = Proposition()
        tampon = ""
        premier = None
        flux = None
        try:
            flux = self.moteur.flux(self.systeme, self._contenu(consigne))
            for morceau in flux:
                if not self._a_jour(gen):
                    return                      # une demande plus récente a pris le relais
                tampon += morceau
                while "\n" in tampon:
                    ligne, tampon = tampon.split("\n", 1)
                    if analyser_ligne(ligne, prop):
                        if premier is None and prop.choix:
                            premier = time.monotonic() - debut
                        self.evenement("partiel", prop)
            if not self._a_jour(gen):
                return
            if tampon:
                analyser_ligne(tampon, prop)
            if not prop.choix:
                self.evenement("erreur", "Réponse illisible, réessaie (F9).")
                return
            self.evenement("fini", (prop, premier, time.monotonic() - debut))
        except ErreurMoteur as e:
            if self._a_jour(gen):
                self.evenement("erreur", str(e))
        finally:
            if flux is not None:
                flux.close()              # coupe la génération si elle n'est plus utile


# ----------------------------------------------------------------------
# Chroniqueur : met à jour la mémoire en arrière-plan
# ----------------------------------------------------------------------

class PersonneSortie(BaseModel):
    nom: str
    description: str
    relation: str
    derniere_fois: str


class MiseAJour(BaseModel):
    personnes: list[PersonneSortie]
    faits_nouveaux: list[str]
    resume: str


class Chroniqueur:
    def __init__(self, moteur, profil: Profil, memoire: Memoire,
                 journal: Callable[[str], None], tous_les: int = 8):
        self.moteur = moteur
        self.systeme = prompts.systeme_chroniqueur(profil)
        self.memoire = memoire
        self.journal = journal
        self.tous_les = tous_les
        self._index = 0
        self._en_cours = threading.Lock()

    def peut_etre(self) -> None:
        if len(self.memoire.fil) - self._index >= self.tous_les:
            self.lancer()

    def lancer(self, attendre: bool = False) -> None:
        t = threading.Thread(target=self._tenir, daemon=not attendre)
        t.start()
        if attendre:
            t.join(timeout=60)

    def _tenir(self) -> None:
        if not self._en_cours.acquire(blocking=False):
            return
        try:
            nouveau, fin = self.memoire.depuis(self._index)
            if not nouveau.strip():
                return
            contenu = (
                f"=== MÉMOIRE ACTUELLE ===\n{self.memoire.texte_registre()}\n\n"
                f"=== NOUVELLES LIGNES ===\n{nouveau}"
            )
            maj = self.moteur.structure("chronique", self.systeme,
                                        [{"type": "text", "text": contenu}], MiseAJour)
            if maj is None:
                return
            self.memoire.fusionner(
                [Personne(**p.model_dump()) for p in maj.personnes], maj.faits_nouveaux, maj.resume)
            self._index = fin
            self.journal(f"Chronique mise à jour ({len(self.memoire.personnes)} personnes connues).")
        except ErreurMoteur as e:
            self.journal(f"Chronique non mise à jour : {e}")
        finally:
            self._en_cours.release()


# ----------------------------------------------------------------------
# Regard : décrit la scène vue à l'écran (appelé par l'Observateur)
# ----------------------------------------------------------------------

class SceneVue(BaseModel):
    lieu: str
    moment: str
    personnes: list[str]
    tension: str
    etat_du_personnage: str
    details_utiles: str
    changement_notable: bool
    resume: str


class Regard:
    def __init__(self, moteur, profil: Profil, memoire: Memoire,
                 evenement: Callable[[str, object], None], journal: Callable[[str], None]):
        self.moteur = moteur
        self.profil = profil
        self.systeme = prompts.systeme_observateur(profil)
        self.memoire = memoire
        self.evenement = evenement
        self.journal = journal

    def decrire(self, image: Image) -> None:
        precedente = self.memoire.scene or "(aucune)"
        try:
            s = self.moteur.structure("regard", self.systeme, [
                image.bloc(),
                {"type": "text", "text": (
                    f"Description précédente : {precedente}\n\n"
                    f"Derniers échanges entendus (pour reconnaître qui est qui) :\n"
                    f"{self.memoire.texte_fil(6)}\n\nDécris la scène actuelle.")},
            ], SceneVue)
        except ErreurMoteur as e:
            self.journal(f"Vision : observation impossible ({e}).")
            return
        if s is None:
            return
        morceaux = [s.lieu, s.moment]
        if s.personnes:
            morceaux.append("présents : " + ", ".join(s.personnes))
        if s.tension:
            morceaux.append(f"tension : {s.tension}")
        if s.etat_du_personnage:
            morceaux.append(f"{self.profil.nom} : {s.etat_du_personnage}")
        if s.details_utiles:
            morceaux.append(s.details_utiles)
        self.memoire.noter_scene(" · ".join(m for m in morceaux if m))
        self.evenement("scene", s)
        if s.changement_notable and s.resume:
            r = Replique("vue", "écran", s.resume)
            self.memoire.ajouter(r)
            self.evenement("ligne", (r.ligne(), "note"))
