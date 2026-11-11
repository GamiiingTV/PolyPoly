"""Les « cerveaux » possibles du Souffleur.

- `MoteurLocal` (gratuit) : une IA qui tourne sur ton PC via Ollama (https://ollama.com).
  Rien ne sort de ta machine, rien n'est facturé.
- `MoteurClaude` (payant) : l'API Claude d'Anthropic, de meilleure qualité.

Les deux reçoivent le même contenu (blocs texte et image au format de l'API Claude)
et offrent les mêmes trois services : réponse en flux, réponse structurée (JSON
validé par un modèle pydantic) et préchauffage.
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Callable, Iterator, TypeVar

from pydantic import BaseModel, ValidationError

from .config import ConfigClaude, ConfigLocal

M = TypeVar("M", bound=BaseModel)


class ErreurMoteur(Exception):
    """Erreur lisible par le joueur."""


# ======================================================================
# Moteur local (Ollama) — gratuit
# ======================================================================

class MoteurLocal:
    nom = "IA locale"

    def __init__(self, cfg: ConfigLocal, journal: Callable[[str], None]):
        self.cfg = cfg
        self.journal = journal
        self.adresse = cfg.adresse.rstrip("/")
        self._repliques_en_cours = 0
        self._verrou = threading.Lock()

    # ------------------------------------------------------------ HTTP
    def _post(self, chemin: str, corps: dict, delai: float = 300):
        req = urllib.request.Request(
            self.adresse + chemin, data=json.dumps(corps).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            return urllib.request.urlopen(req, timeout=delai)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 404:
                raise ErreurMoteur(f"Modèle « {self.cfg.modele} » absent d'Ollama ({detail}).") from e
            raise ErreurMoteur(f"Erreur d'Ollama ({e.code}) : {detail}") from e
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            raise ErreurMoteur("Ollama ne répond pas : est-il installé et lancé ? (voir le README)") from e

    @staticmethod
    def _messages(systeme: str, contenu: list[dict]) -> list[dict]:
        textes, images = [], []
        for bloc in contenu:
            if bloc["type"] == "text":
                textes.append(bloc["text"])
            elif bloc["type"] == "image":
                images.append(bloc["source"]["data"])
        utilisateur = {"role": "user", "content": "\n\n".join(textes)}
        if images:
            utilisateur["images"] = images
        return [{"role": "system", "content": systeme}, utilisateur]

    def _options(self, **extra) -> dict:
        return {"num_ctx": self.cfg.contexte, "temperature": 0.7, **extra}

    # ------------------------------------------------------------ préparation
    def preparer(self) -> bool:
        """Vérifie qu'Ollama tourne et télécharge le modèle s'il manque."""
        try:
            with urllib.request.urlopen(self.adresse + "/api/tags", timeout=5) as r:
                presents = {m["name"] for m in json.load(r).get("models", [])}
        except (urllib.error.URLError, ConnectionError, TimeoutError, ValueError):
            self.journal("IA locale : Ollama ne répond pas. Installe-le depuis ollama.com, puis relance.")
            return False
        voulu = self.cfg.modele if ":" in self.cfg.modele else self.cfg.modele + ":latest"
        if voulu not in presents:
            self.journal(f"IA locale : téléchargement de « {self.cfg.modele} » (une seule fois, plusieurs Go)…")
            try:
                with self._post("/api/pull", {"model": self.cfg.modele, "stream": True}, delai=7200) as r:
                    dernier = -10
                    for ligne in r:
                        etat = json.loads(ligne)
                        if etat.get("error"):
                            raise ErreurMoteur(etat["error"])
                        total, fait = etat.get("total"), etat.get("completed")
                        if total and fait:
                            pct = int(100 * fait / total)
                            if pct >= dernier + 10:
                                dernier = pct
                                self.journal(f"IA locale : téléchargement {pct} %")
            except ErreurMoteur as e:
                self.journal(f"IA locale : téléchargement impossible ({e}).")
                return False
        self.journal(f"IA locale prête : {self.cfg.modele} (gratuit, sur ton PC).")
        return True

    def prechauffer(self, systeme: str) -> None:
        """Charge le modèle sur la carte graphique et calcule d'avance les consignes."""
        def _chauffer():
            if not self.preparer():
                return
            try:
                corps = {"model": self.cfg.modele, "stream": False, "keep_alive": self.cfg.garder_en_memoire,
                         "messages": self._messages(systeme, [{"type": "text", "text": "Prêt ?"}]),
                         "options": self._options(num_predict=1)}
                with self._post("/api/chat", corps):
                    pass
            except ErreurMoteur:
                pass
        threading.Thread(target=_chauffer, daemon=True).start()

    # ------------------------------------------------------------ services
    def flux(self, systeme: str, contenu: list[dict]) -> Iterator[str]:
        corps = {"model": self.cfg.modele, "stream": True, "keep_alive": self.cfg.garder_en_memoire,
                 "messages": self._messages(systeme, contenu), "options": self._options(num_predict=700)}
        with self._verrou:
            self._repliques_en_cours += 1
        try:
            with self._post("/api/chat", corps) as r:
                for ligne in r:
                    if not ligne.strip():
                        continue
                    morceau = json.loads(ligne)
                    if morceau.get("error"):
                        raise ErreurMoteur(f"IA locale : {morceau['error']}")
                    texte = morceau.get("message", {}).get("content", "")
                    if texte:
                        yield texte
                    if morceau.get("done"):
                        break
        finally:
            with self._verrou:
                self._repliques_en_cours -= 1

    def structure(self, role: str, systeme: str, contenu: list[dict], modele: type[M]) -> M | None:
        # Une seule carte graphique : les tâches de fond laissent passer les répliques.
        if self._repliques_en_cours:
            return None
        corps = {"model": self.cfg.modele, "stream": False, "keep_alive": self.cfg.garder_en_memoire,
                 "messages": self._messages(systeme, contenu), "format": modele.model_json_schema(),
                 "options": self._options(temperature=0.2, num_predict=1500)}
        with self._post("/api/chat", corps) as r:
            texte = json.load(r).get("message", {}).get("content", "")
        try:
            return modele.model_validate_json(texte)
        except ValidationError:
            return None


# ======================================================================
# Moteur Claude (API Anthropic) — payant
# ======================================================================

BETA_REPLI = "server-side-fallback-2026-07-01"


class MoteurClaude:
    nom = "Claude"

    def __init__(self, cfg: ConfigClaude, modele_regard: str, journal: Callable[[str], None]):
        import anthropic
        self.anthropic = anthropic
        self.cfg = cfg
        self.journal = journal
        self.modeles = {"repliques": cfg.modele, "chronique": cfg.modele_chroniqueur, "regard": modele_regard}
        self.client = anthropic.Anthropic(max_retries=1)

    def _systeme(self, systeme: str) -> list[dict]:
        return [{"type": "text", "text": systeme, "cache_control": {"type": "ephemeral", "ttl": "1h"}}]

    def _rapide(self) -> dict:
        return {"speed": "fast"} if self.cfg.rapide and self.cfg.modele == "claude-opus-5-5" else {}

    def _traduire(self, e: Exception) -> ErreurMoteur:
        a = self.anthropic
        if isinstance(e, a.AuthenticationError):
            return ErreurMoteur("Clé API Anthropic invalide ou absente (voir le README).")
        if isinstance(e, a.RateLimitError):
            return ErreurMoteur("Trop de demandes d'affilée, réessaie dans un instant (F9).")
        if isinstance(e, a.APIConnectionError):
            return ErreurMoteur("Pas de connexion à l'API Claude.")
        if isinstance(e, a.APIStatusError):
            return ErreurMoteur(f"Erreur de l'API Claude ({e.status_code}) : {e.message}")
        return ErreurMoteur(f"Erreur de l'API Claude : {e}")

    def prechauffer(self, systeme: str) -> None:
        """Charge les consignes dans le cache de Claude avant la première réplique."""
        def _chauffer():
            try:
                self.client.messages.create(
                    model=self.cfg.modele, max_tokens=0, system=self._systeme(systeme),
                    messages=[{"role": "user", "content": "Prêt."}], **self._rapide())
            except self.anthropic.APIError:
                pass   # sans gravité : la première réplique remplira le cache
        threading.Thread(target=_chauffer, daemon=True).start()

    def flux(self, systeme: str, contenu: list[dict]) -> Iterator[str]:
        params = dict(
            model=self.cfg.modele, max_tokens=4000, system=self._systeme(systeme),
            messages=[{"role": "user", "content": contenu}],
            output_config={"effort": self.cfg.effort}, **self._rapide(),
        )
        if not self.cfg.modele.startswith("claude-haiku"):   # pas de repli serveur pour Haiku
            params["betas"] = [BETA_REPLI]
            params["fallbacks"] = "default"
        try:
            with self.client.beta.messages.stream(**params) as flux:
                yield from flux.text_stream
                final = flux.get_final_message()
        except self.anthropic.APIError as e:
            raise self._traduire(e) from e
        if final.stop_reason == "refusal":
            raise ErreurMoteur("Claude a refusé de proposer une réplique pour cette scène.")

    def structure(self, role: str, systeme: str, contenu: list[dict], modele: type[M]) -> M | None:
        try:
            reponse = self.client.messages.parse(
                model=self.modeles[role], max_tokens=8000, system=systeme,
                messages=[{"role": "user", "content": contenu}],
                output_format=modele, output_config={"effort": "low"},
            )
        except self.anthropic.APIError as e:
            raise self._traduire(e) from e
        if reponse.stop_reason == "refusal":
            return None
        return reponse.parsed_output


def creer_moteur(cfg, journal: Callable[[str], None]):
    if cfg.ia.moteur == "claude":
        return MoteurClaude(cfg.claude, cfg.vision.modele_observateur, journal)
    return MoteurLocal(cfg.local, journal)
