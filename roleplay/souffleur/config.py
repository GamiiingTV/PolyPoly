"""Chargement de config.toml avec des valeurs par défaut sûres."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"
MEMOIRE = RACINE / "memoire"


@dataclass
class ConfigClaude:
    modele: str = "claude-opus-5-5"
    effort: str = "low"
    rapide: bool = False
    modele_chroniqueur: str = "claude-opus-5-5"


@dataclass
class ConfigAudio:
    sortie: str = ""
    ecouter_micro: bool = True
    micro: str = ""
    silence_fin_ms: int = 550
    duree_min_ms: int = 400
    sensibilite: float = 3.0


@dataclass
class ConfigTranscription:
    modele: str = "large-v3-turbo"
    appareil: str = "cuda"
    precision: str = "float16"


@dataclass
class ConfigInterface:
    nombre_de_choix: int = 4
    opacite: float = 0.93
    largeur: int = 520
    touche_afficher: str = "f8"
    touche_regenerer: str = "f9"
    touche_pause: str = "f10"


@dataclass
class Config:
    claude: ConfigClaude = field(default_factory=ConfigClaude)
    audio: ConfigAudio = field(default_factory=ConfigAudio)
    transcription: ConfigTranscription = field(default_factory=ConfigTranscription)
    interface: ConfigInterface = field(default_factory=ConfigInterface)


def _remplir(cible, valeurs: dict) -> None:
    for cle, valeur in valeurs.items():
        if hasattr(cible, cle):
            setattr(cible, cle, type(getattr(cible, cle))(valeur))


def charger(chemin: Path | None = None) -> Config:
    chemin = chemin or RACINE / "config.toml"
    cfg = Config()
    if chemin.exists():
        with open(chemin, "rb") as f:
            brut = tomllib.load(f)
        for section in ("claude", "audio", "transcription", "interface"):
            _remplir(getattr(cfg, section), brut.get(section, {}))
    cfg.interface.nombre_de_choix = max(3, min(6, cfg.interface.nombre_de_choix))
    return cfg
