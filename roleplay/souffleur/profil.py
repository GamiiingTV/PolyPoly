"""Fiche du personnage et guide de l'univers, interchangeables.

donnees/personnages/<nom>.md et donnees/univers/<nom>.md commencent par un petit
en-tête entre deux lignes « --- » :

    ---
    nom: Dalibor
    nom_complet: le seigneur Dalibor Medved de Suchdol
    vocabulaire: Dalibor Medved, Suchdol
    ---
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import DONNEES


def lire_fiche(chemin: Path) -> tuple[dict[str, str], str]:
    texte = chemin.read_text(encoding="utf-8")
    entete: dict[str, str] = {}
    if texte.startswith("---"):
        _, bloc, texte = texte.split("---", 2)
        for ligne in bloc.strip().splitlines():
            if ":" in ligne:
                cle, valeur = ligne.split(":", 1)
                entete[cle.strip().lower()] = valeur.strip()
    return entete, texte.strip()


@dataclass
class Profil:
    cle: str
    nom: str               # « Dalibor » : comment on l'appelle dans le fil
    nom_complet: str       # « le seigneur Dalibor Medved de Suchdol »
    fiche: str
    cadre: str             # « un mod multijoueur de KCD II, en Bohême, en l'an de grâce 1403 »
    univers: str
    vocabulaire: str       # noms propres soufflés à la transcription

    @classmethod
    def charger(cls, personnage: str, univers: str, dossier: Path = DONNEES) -> "Profil":
        chemin_p = dossier / "personnages" / f"{personnage}.md"
        chemin_u = dossier / "univers" / f"{univers}.md"
        for c in (chemin_p, chemin_u):
            if not c.exists():
                raise FileNotFoundError(f"Fichier introuvable : {c}")
        ep, fiche = lire_fiche(chemin_p)
        eu, guide = lire_fiche(chemin_u)
        nom = ep.get("nom") or personnage.capitalize()
        vocab = ", ".join(v for v in (ep.get("vocabulaire"), eu.get("vocabulaire")) if v)
        return cls(
            cle=personnage,
            nom=nom,
            nom_complet=ep.get("nom_complet") or nom,
            fiche=fiche,
            cadre=eu.get("cadre") or "un jeu de rôle",
            univers=guide,
            vocabulaire=vocab,
        )


def lister(dossier: Path = DONNEES) -> list[str]:
    return sorted(p.stem for p in (dossier / "personnages").glob("*.md") if not p.stem.startswith("_"))
