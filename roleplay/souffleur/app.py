"""Chef d'orchestre : son + écran -> transcription -> mémoire -> Claude -> fenêtre."""
from __future__ import annotations

import queue
import re
import threading
import time

import numpy as np

from .audio import Capture, Segmenteur
from .config import MEMOIRE, Config
from .conseiller import Choix, Chroniqueur, Conseiller, Regard
from .interface import Interface
from .memoire import Memoire, Replique
from .moteurs import creer_moteur
from .profil import Profil
from .vision import Observateur, Oeil, masquer_des_captures
from .voix import RegistreVoix

_RE_NOMMER = re.compile(r"^\s*(voix\s+\S+)\s*=\s*(.*)$", re.IGNORECASE)


class Souffleur:
    def __init__(self, cfg: Config, simulation: bool = False):
        self.cfg = cfg
        self.simulation = simulation
        self.profil = Profil.charger(cfg.jeu.personnage, cfg.jeu.univers)
        self.ui = Interface(cfg.interface.largeur, cfg.interface.opacite, cfg.interface.nombre_de_choix,
                            titre=f"✠ Souffleur · {self.profil.nom}")
        self.memoire = Memoire(MEMOIRE / self.profil.cle)
        self.voix = RegistreVoix()
        self.oeil: Oeil | None = None
        self.observateur: Observateur | None = None
        self.moteur = creer_moteur(cfg, self.journal)
        self.conseiller = Conseiller(self.moteur, self.profil, self.memoire, cfg.interface.nombre_de_choix,
                                     self.ui.envoyer, fournir_images=self._images_pour_replique)
        self.chroniqueur = Chroniqueur(self.moteur, self.profil, self.memoire, self.journal)
        self.captures: list[Capture] = []
        self.a_transcrire: queue.Queue = queue.Queue()
        self.ecoute = True

        self.ui.sur_choix = self.choisir
        self.ui.sur_saisie = self.saisie
        self.ui.sur_regenerer = lambda: self.conseiller.demander()
        self.ui.sur_pause = self.basculer_pause
        self.ui.sur_quitter = self.quitter

    # ------------------------------------------------------------ démarrage
    def journal(self, texte: str) -> None:
        self.ui.envoyer("journal", texte)

    def demarrer(self) -> None:
        self.journal(f"Personnage : {self.profil.nom_complet} · univers : {self.cfg.jeu.univers}")
        self.journal("Cerveau : " + ("IA locale, gratuite" if self.cfg.ia.moteur == "local"
                                     else f"Claude ({self.cfg.claude.modele}), payant"))
        self._touches()
        self.conseiller.prechauffer()
        if self.cfg.vision.active:
            if masquer_des_captures(self.ui.racine):
                self.journal("Vision : la fenêtre du Souffleur est invisible aux captures.")
            threading.Thread(target=self._preparer_vision, daemon=True).start()
        if self.simulation:
            self.journal("Mode simulation : tape dans le champ ce qu'on te dit, puis Entrée.")
        else:
            threading.Thread(target=self._preparer_audio, daemon=True).start()
        self.ui.envoyer("ecoute", True)
        self.ui.lancer()

    def _preparer_audio(self) -> None:
        self.journal("Chargement du modèle de transcription (la première fois, il se télécharge)…")
        try:
            from .transcription import Transcripteur
            t = self.cfg.transcription
            transcripteur = Transcripteur(t.modele, t.appareil, t.precision, self.journal,
                                          vocabulaire=self.profil.vocabulaire)
        except Exception as e:
            self.journal(f"Transcription indisponible : {e}. Tu peux quand même écrire les répliques.")
            return
        threading.Thread(target=self._boucle_transcription, args=(transcripteur,), daemon=True).start()
        a = self.cfg.audio
        sources = [("interlocuteur", a.sortie)] + ([("moi", a.micro)] if a.ecouter_micro else [])
        for source, nom in sources:
            seg = Segmenteur(a.silence_fin_ms, a.duree_min_ms, a.sensibilite, anticipation_ms=a.anticipation_ms)
            if source == "interlocuteur":
                seg.au_debut = self._quelquun_parle
            cap = Capture(source, nom, seg, self._segment_recu, self.journal)
            cap.start()
            self.captures.append(cap)

    def _preparer_vision(self) -> None:
        v = self.cfg.vision
        try:
            self.oeil = Oeil(v, self.journal)
        except ImportError:
            self.journal("Vision indisponible : modules « mss » et « Pillow » absents.")
            return
        self.oeil.demarrer()
        self.journal(f"Vision continue : {v.images_par_seconde:g} image(s) par seconde, {v.largeur_max} px.")
        if v.observateur:
            regard = Regard(self.moteur, self.profil, self.memoire, self.ui.envoyer, self.journal)
            self.observateur = Observateur(self.oeil, regard.decrire, v.intervalle_min_s, v.battement_s)
            self.oeil.sur_rupture = self.observateur.maintenant
            self.observateur.start()

    def _images_pour_replique(self):
        if self.oeil is None or not self.cfg.vision.joindre_aux_repliques:
            return []
        return self.oeil.pour_replique()

    def _quelquun_parle(self) -> None:
        # On repère dans le film l'instant où l'on commence à parler au personnage.
        if self.oeil is not None and self.ecoute:
            self.oeil.marquer_debut_parole()

    def _touches(self) -> None:
        try:
            import keyboard  # type: ignore
        except ImportError:
            self.journal("Module « keyboard » absent : pas de touches globales (F8/F9/F10).")
            return
        i = self.cfg.interface
        try:
            keyboard.add_hotkey(i.touche_afficher, lambda: self.ui.envoyer("basculer"))
            keyboard.add_hotkey(i.touche_regenerer, lambda: self.conseiller.demander())
            keyboard.add_hotkey(i.touche_pause, self.basculer_pause)
            self.journal(f"Touches : {i.touche_afficher.upper()} afficher/cacher · "
                         f"{i.touche_regenerer.upper()} nouvelles répliques · {i.touche_pause.upper()} pause")
        except Exception as e:  # droits insuffisants, etc.
            self.journal(f"Touches globales indisponibles : {e}")

    # ------------------------------------------------------------ audio
    def _segment_recu(self, source: str, genre: str, audio: np.ndarray) -> None:
        if self.ecoute:
            self.a_transcrire.put((source, genre, audio, time.monotonic()))

    def _boucle_transcription(self, transcripteur) -> None:
        while True:
            source, genre, audio, t_fin = self.a_transcrire.get()
            try:
                texte = transcripteur.transcrire(audio)
            except Exception as e:
                self.journal(f"Erreur de transcription : {e}")
                continue
            if not texte:
                continue
            if genre == "suite":
                # La personne a repris après une courte pause : on complète sa réplique.
                r = self.memoire.remplacer_derniere(source, texte)
                if r is not None:
                    self.ui.envoyer("ligne", ("   ↳ " + r.ligne(), "moi" if source == "moi" else ""))
                    if source != "moi":
                        self.conseiller.demander(depuis=t_fin)
                    continue
            if source == "moi":
                self.dit_par_moi(texte)
            else:
                qui = self.voix.nom(self.voix.identifier(audio))
                self.entendu(qui, texte, depuis=t_fin)

    # ------------------------------------------------------------ actions
    def entendu(self, qui: str, texte: str, depuis: float | None = None) -> None:
        r = Replique("interlocuteur", qui, texte)
        self.memoire.ajouter(r)
        self.ui.envoyer("ligne", (r.ligne(), ""))
        self.conseiller.demander(depuis=depuis)
        self.chroniqueur.peut_etre()

    def dit_par_moi(self, texte: str) -> None:
        self.conseiller.annuler()
        r = Replique("moi", self.profil.nom, texte)
        self.memoire.ajouter(r)
        self.ui.envoyer("ligne", (r.ligne(), "moi"))
        self.chroniqueur.peut_etre()

    def choisir(self, choix: Choix) -> None:
        self.ui.copier(choix.texte)
        # Si le micro n'est pas écouté, on note la réplique choisie comme dite.
        if self.simulation or not self.cfg.audio.ecouter_micro:
            self.dit_par_moi(choix.texte)
        else:
            self.journal("Réplique copiée.")

    def saisie(self, texte: str) -> None:
        m = _RE_NOMMER.match(texte)
        if m:
            etiquette = m.group(1).strip().title()
            ancien = self.voix.nom(etiquette)
            self.voix.nommer(etiquette, m.group(2))
            self.memoire.renommer(ancien, self.voix.nom(etiquette))
            self.journal(f"{etiquette} s'appelle désormais « {self.voix.nom(etiquette)} ».")
        elif texte.lower().startswith("moi:"):
            self.dit_par_moi(texte[4:].strip())
        elif texte.startswith("!"):
            self.memoire.situation = texte[1:].strip()
            self.memoire.ajouter(Replique("note", self.profil.nom, self.memoire.situation))
            self.ui.envoyer("ligne", (f"Situation : {self.memoire.situation}", "note"))
        elif texte.startswith("?"):
            self.conseiller.demander(texte[1:].strip())
        else:
            if self.oeil is not None:
                self.oeil.marquer_debut_parole()
            self.entendu("Interlocuteur", texte)

    def basculer_pause(self) -> None:
        self.ecoute = not self.ecoute
        for c in self.captures:
            (c.actif.set if self.ecoute else c.actif.clear)()
        if self.oeil:
            (self.oeil.actif.set if self.ecoute else self.oeil.actif.clear)()
        if self.observateur:
            (self.observateur.actif.set if self.ecoute else self.observateur.actif.clear)()
        self.ui.envoyer("ecoute", self.ecoute)

    def quitter(self) -> None:
        self.journal("Mise à jour de la chronique avant de partir…")
        self.ui.racine.update()
        for c in self.captures:
            c.arreter()
        self.chroniqueur.lancer(attendre=True)
        self.ui.racine.destroy()
