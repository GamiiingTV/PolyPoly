"""Génération des répliques (en flux) et tenue de la chronique, via l'API Claude."""
from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

import anthropic
from pydantic import BaseModel

from . import prompts
from .config import ConfigClaude
from .memoire import Memoire, Personne

BETA_REPLI = "server-side-fallback-2026-07-01"

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
    choix: list[Choix] = field(default_factory=list)
    conseil: str = ""


def analyser_ligne(ligne: str, prop: Proposition) -> str | None:
    """Range une ligne de la réponse dans la proposition. Renvoie son type ou None."""
    ligne = ligne.strip().strip("*").strip()
    if not ligne:
        return None
    haut = ligne.upper()
    for cle, attr in (("SITUATION", "situation"), ("QUI", "qui"), ("CONSEIL", "conseil")):
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


def _avec_repli(modele: str) -> bool:
    # Pas de repli côté serveur pour Haiku.
    return not modele.startswith("claude-haiku")


class Conseiller:
    """Lance une génération à la fois ; une nouvelle demande annule la précédente."""

    def __init__(self, cfg: ConfigClaude, memoire: Memoire, nombre: int,
                 evenement: Callable[[str, object], None]):
        self.cfg = cfg
        self.memoire = memoire
        self.nombre = nombre
        self.evenement = evenement   # (type, donnée) -> interface
        self.client = anthropic.Anthropic(max_retries=1)
        self.systeme = prompts.systeme_souffleur()
        self._generation = 0
        self._verrou = threading.Lock()

    def demander(self, consigne: str = "") -> None:
        with self._verrou:
            self._generation += 1
            gen = self._generation
        threading.Thread(target=self._generer, args=(gen, consigne), daemon=True).start()

    def annuler(self) -> None:
        with self._verrou:
            self._generation += 1

    def _a_jour(self, gen: int) -> bool:
        return gen == self._generation

    def _requete(self, consigne: str) -> dict:
        demande = prompts.demande_souffleur(
            self.memoire.texte_registre(), self.memoire.situation,
            self.memoire.texte_fil(40), self.nombre, consigne,
        )
        params = dict(
            model=self.cfg.modele,
            max_tokens=4000,
            system=[{"type": "text", "text": self.systeme,
                     "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
            messages=[{"role": "user", "content": demande}],
            output_config={"effort": self.cfg.effort},
        )
        if self.cfg.rapide and self.cfg.modele == "claude-opus-5-5":
            params["speed"] = "fast"
        if _avec_repli(self.cfg.modele):
            params["betas"] = [BETA_REPLI]
            params["fallbacks"] = "default"
        return params

    def _generer(self, gen: int, consigne: str) -> None:
        debut = time.monotonic()
        self.evenement("debut", None)
        prop = Proposition()
        tampon = ""
        premier = None
        try:
            with self.client.beta.messages.stream(**self._requete(consigne)) as flux:
                for morceau in flux.text_stream:
                    if not self._a_jour(gen):
                        return                      # une demande plus récente a pris le relais
                    tampon += morceau
                    while "\n" in tampon:
                        ligne, tampon = tampon.split("\n", 1)
                        if analyser_ligne(ligne, prop):
                            if premier is None and prop.choix:
                                premier = time.monotonic() - debut
                            self.evenement("partiel", prop)
                if tampon and self._a_jour(gen):
                    analyser_ligne(tampon, prop)
                final = flux.get_final_message()
            if not self._a_jour(gen):
                return
            if final.stop_reason == "refusal":
                self.evenement("erreur", "Claude a refusé de proposer une réplique pour cette scène.")
                return
            self.evenement("fini", (prop, premier, time.monotonic() - debut))
        except anthropic.AuthenticationError:
            self.evenement("erreur", "Clé API Anthropic invalide ou absente (voir le README).")
        except anthropic.RateLimitError:
            self.evenement("erreur", "Trop de demandes d'affilée, réessaie dans un instant (F9).")
        except anthropic.APIConnectionError:
            self.evenement("erreur", "Pas de connexion à l'API Claude.")
        except anthropic.APIStatusError as e:
            self.evenement("erreur", f"Erreur de l'API Claude ({e.status_code}) : {e.message}")


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
    def __init__(self, cfg: ConfigClaude, memoire: Memoire, journal: Callable[[str], None],
                 tous_les: int = 8):
        self.cfg = cfg
        self.memoire = memoire
        self.journal = journal
        self.tous_les = tous_les
        self.client = anthropic.Anthropic(max_retries=2)
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
                f"=== NOUVELLES RÉPLIQUES ===\n{nouveau}"
            )
            params = dict(
                model=self.cfg.modele_chroniqueur,
                max_tokens=8000,
                system=prompts.CONSIGNES_CHRONIQUEUR,
                messages=[{"role": "user", "content": contenu}],
                output_format=MiseAJour,
                output_config={"effort": "low"},
            )
            reponse = self.client.messages.parse(**params)
            maj = reponse.parsed_output
            if reponse.stop_reason == "refusal" or maj is None:
                return
            self.memoire.fusionner(
                [Personne(**p.model_dump()) for p in maj.personnes], maj.faits_nouveaux, maj.resume)
            self._index = fin
            self.journal(f"Chronique mise à jour ({len(self.memoire.personnes)} personnes connues).")
        except anthropic.APIError as e:
            self.journal(f"Chronique non mise à jour : {e}")
        finally:
            self._en_cours.release()
