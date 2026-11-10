"""Mémoire du Souffleur : fil de la conversation, registre des personnes et des faits."""
from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .config import DONNEES, MEMOIRE


@dataclass
class Replique:
    source: str          # "interlocuteur" | "moi" | "note"
    qui: str             # "Voix A", "Kuno le forgeron", "Dalibor"...
    texte: str
    heure: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))

    def ligne(self) -> str:
        if self.source == "note":
            return f"[{self.heure}] (Note du joueur : {self.texte})"
        return f"[{self.heure}] {self.qui} : {self.texte}"


@dataclass
class Personne:
    nom: str
    description: str = ""
    relation: str = ""          # allié, rival, inconnu, vassal...
    derniere_fois: str = ""


class Memoire:
    def __init__(self, dossier: Path = MEMOIRE):
        self.dossier = dossier
        (dossier / "sessions").mkdir(parents=True, exist_ok=True)
        self.chemin_registre = dossier / "registre.json"
        self.chemin_session = dossier / "sessions" / f"{datetime.now():%Y-%m-%d_%Hh%M}.txt"
        self.fil: list[Replique] = []
        self.situation = ""                 # contexte saisi par le joueur
        self.personnes: dict[str, Personne] = {}
        self.faits: list[str] = []
        self.resume = ""
        self._verrou = threading.RLock()
        self._charger()

    # ------------------------------------------------------------ registre
    def _charger(self) -> None:
        if not self.chemin_registre.exists():
            return
        try:
            d = json.loads(self.chemin_registre.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.personnes = {p["nom"].lower(): Personne(**p) for p in d.get("personnes", [])}
        self.faits = list(d.get("faits", []))
        self.resume = d.get("resume", "")

    def sauvegarder(self) -> None:
        with self._verrou:
            d = {
                "personnes": [asdict(p) for p in self.personnes.values()],
                "faits": self.faits[-200:],
                "resume": self.resume,
            }
        tmp = self.chemin_registre.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.chemin_registre)

    def fusionner(self, personnes: list[Personne], faits: list[str], resume: str) -> None:
        with self._verrou:
            for p in personnes:
                cle = p.nom.lower().strip()
                if not cle:
                    continue
                ancien = self.personnes.get(cle)
                if ancien:
                    ancien.description = p.description or ancien.description
                    ancien.relation = p.relation or ancien.relation
                    ancien.derniere_fois = p.derniere_fois or ancien.derniere_fois
                else:
                    self.personnes[cle] = p
            connus = {f.lower() for f in self.faits}
            self.faits.extend(f for f in faits if f.strip() and f.lower() not in connus)
            if resume.strip():
                self.resume = resume.strip()
        self.sauvegarder()

    def texte_registre(self) -> str:
        with self._verrou:
            morceaux = []
            if self.resume:
                morceaux.append(f"Résumé des sessions passées :\n{self.resume}")
            if self.personnes:
                morceaux.append("Personnes déjà rencontrées :\n" + "\n".join(
                    f"- {p.nom} : {p.description}" + (f" (relation : {p.relation})" if p.relation else "")
                    for p in self.personnes.values()))
            if self.faits:
                morceaux.append("Faits établis :\n" + "\n".join(f"- {f}" for f in self.faits[-40:]))
        return "\n\n".join(morceaux) or "(Rien encore : c'est la première session.)"

    # ------------------------------------------------------------ fil
    def ajouter(self, r: Replique) -> None:
        with self._verrou:
            self.fil.append(r)
        try:
            with open(self.chemin_session, "a", encoding="utf-8") as f:
                f.write(r.ligne() + "\n")
        except OSError:
            pass

    def renommer(self, ancien: str, nouveau: str) -> None:
        with self._verrou:
            for r in self.fil:
                if r.qui == ancien:
                    r.qui = nouveau

    def texte_fil(self, n: int = 40) -> str:
        with self._verrou:
            return "\n".join(r.ligne() for r in self.fil[-n:]) or "(silence)"

    def depuis(self, index: int) -> tuple[str, int]:
        with self._verrou:
            return "\n".join(r.ligne() for r in self.fil[index:]), len(self.fil)


def lire_donnee(nom: str) -> str:
    chemin = DONNEES / nom
    return chemin.read_text(encoding="utf-8") if chemin.exists() else ""
