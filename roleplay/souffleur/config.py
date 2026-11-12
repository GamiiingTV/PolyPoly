"""Chargement de config.toml avec des valeurs par défaut sûres."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"
MEMOIRE = RACINE / "memoire"


@dataclass
class ConfigJeu:
    personnage: str = "dalibor"
    univers: str = "boheme_1403"


@dataclass
class ConfigIA:
    moteur: str = "local"          # "local" (gratuit, Ollama) ou "claude" (payant)


@dataclass
class ConfigLocal:
    adresse: str = "http://localhost:11434"
    modele: str = "auto"
    reserve_jeu_go: float = 9.0
    contexte: int = 16384
    garder_en_memoire: str = "30m"


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
    silence_fin_ms: int = 700
    anticipation_ms: int = 300
    duree_min_ms: int = 400
    sensibilite: float = 3.0


@dataclass
class ConfigTranscription:
    modele: str = "large-v3-turbo"
    appareil: str = "cuda"
    precision: str = "float16"


@dataclass
class ConfigVision:
    active: bool = True
    titre_fenetre: str = "Kingdom Come"
    ecran: int = 1
    images_par_seconde: float = 2.0
    largeur_max: int = 1920
    qualite: int = 80
    joindre_aux_repliques: bool = True
    observateur: bool = True
    intervalle_min_s: float = 8.0
    battement_s: float = 45.0
    modele_observateur: str = "claude-opus-5-5"


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
    jeu: ConfigJeu = field(default_factory=ConfigJeu)
    ia: ConfigIA = field(default_factory=ConfigIA)
    local: ConfigLocal = field(default_factory=ConfigLocal)
    claude: ConfigClaude = field(default_factory=ConfigClaude)
    audio: ConfigAudio = field(default_factory=ConfigAudio)
    transcription: ConfigTranscription = field(default_factory=ConfigTranscription)
    vision: ConfigVision = field(default_factory=ConfigVision)
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
        for section in ("jeu", "ia", "local", "claude", "audio", "transcription", "vision", "interface"):
            _remplir(getattr(cfg, section), brut.get(section, {}))
    cfg.interface.nombre_de_choix = max(3, min(6, cfg.interface.nombre_de_choix))
    cfg.ia.moteur = cfg.ia.moteur.strip().lower()
    if cfg.ia.moteur not in ("local", "claude"):
        cfg.ia.moteur = "local"
    return cfg
