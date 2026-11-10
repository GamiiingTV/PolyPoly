"""Fenêtre « overlay » toujours au premier plan, par-dessus le jeu (tkinter)."""
from __future__ import annotations

import queue
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from .conseiller import Choix, Proposition

FOND = "#1b1610"
PANNEAU = "#272017"
SURVOL = "#3a2f20"
TEXTE = "#f1e6cc"
OR = "#d1a94f"
GRIS = "#9c8f78"
ROUGE = "#c0563f"
VERT = "#7fa35a"

AIDE = ("Écrire ici :  texte = réplique entendue  ·  moi: texte = ce que Dalibor a dit  ·  "
        "! texte = situation  ·  ? texte = redemander autrement  ·  Voix A = Kuno")


class Interface:
    def __init__(self, largeur: int, opacite: float, nombre: int, titre: str = "✠ Le Souffleur"):
        self.titre = titre
        self.racine = tk.Tk()
        self.racine.title("Le Souffleur")
        self.racine.configure(bg=FOND)
        self.racine.attributes("-topmost", True)
        try:
            self.racine.attributes("-alpha", opacite)
        except tk.TclError:
            pass
        self.racine.overrideredirect(True)
        self.racine.geometry(f"{largeur}x760+40+60")
        self.largeur = largeur
        self.nombre = nombre
        self.file: queue.Queue = queue.Queue()
        self.visible = True

        # Rappels fournis par l'application
        self.sur_choix: Callable[[Choix], None] = lambda c: None
        self.sur_saisie: Callable[[str], None] = lambda t: None
        self.sur_regenerer: Callable[[], None] = lambda: None
        self.sur_pause: Callable[[], None] = lambda: None
        self.sur_quitter: Callable[[], None] = self.racine.destroy

        base = tkfont.nametofont("TkDefaultFont").actual("family")
        self.f_titre = tkfont.Font(family="Georgia", size=12, weight="bold")
        self.f_texte = tkfont.Font(family="Georgia", size=12)
        self.f_ton = tkfont.Font(family=base, size=9, weight="bold")
        self.f_petit = tkfont.Font(family=base, size=9)
        self.f_italique = tkfont.Font(family="Georgia", size=10, slant="italic")

        self._construire()
        self.racine.after(40, self._pomper)

    # ------------------------------------------------------------------ UI
    def _bouton(self, parent, texte, commande, couleur=TEXTE):
        b = tk.Label(parent, text=texte, bg=PANNEAU, fg=couleur, font=self.f_titre, padx=6, cursor="hand2")
        b.bind("<Button-1>", lambda e: commande())
        return b

    def _construire(self) -> None:
        r = self.racine
        tete = tk.Frame(r, bg=PANNEAU)
        tete.pack(fill="x")
        titre = tk.Label(tete, text=self.titre, bg=PANNEAU, fg=OR, font=self.f_titre, padx=8, pady=4)
        titre.pack(side="left")
        self.etat = tk.Label(tete, text="● prêt", bg=PANNEAU, fg=GRIS, font=self.f_petit)
        self.etat.pack(side="left", padx=6)
        self._bouton(tete, "✕", lambda: self.sur_quitter(), ROUGE).pack(side="right")
        self.b_pause = self._bouton(tete, "⏸", lambda: self.sur_pause())
        self.b_pause.pack(side="right")
        self._bouton(tete, "⟳", lambda: self.sur_regenerer()).pack(side="right")
        for w in (tete, titre, self.etat):
            w.bind("<ButtonPress-1>", self._debut_glisser)
            w.bind("<B1-Motion>", self._glisser)

        self.l_scene = tk.Label(r, text="", bg=PANNEAU, fg=GRIS, font=self.f_petit,
                                wraplength=self.largeur - 24, justify="left", anchor="w", padx=8, pady=3)
        self.l_scene.pack(fill="x")
        self.l_situation = tk.Label(r, text="", bg=FOND, fg=OR, font=self.f_italique,
                                    wraplength=self.largeur - 24, justify="left", anchor="w")
        self.l_situation.pack(fill="x", padx=12, pady=(8, 0))
        self.l_qui = tk.Label(r, text="", bg=FOND, fg=GRIS, font=self.f_petit, anchor="w",
                              wraplength=self.largeur - 24, justify="left")
        self.l_qui.pack(fill="x", padx=12)

        self.zone_choix = tk.Frame(r, bg=FOND)
        self.zone_choix.pack(fill="x", padx=8, pady=6)

        self.l_conseil = tk.Label(r, text="", bg=FOND, fg=GRIS, font=self.f_italique,
                                  wraplength=self.largeur - 24, justify="left", anchor="w")
        self.l_conseil.pack(fill="x", padx=12)

        # Bas de fenêtre (toujours visible) : aide puis champ de saisie.
        tk.Label(r, text=AIDE, bg=FOND, fg="#6f6656", font=self.f_petit, wraplength=self.largeur - 16,
                 justify="left").pack(side="bottom", fill="x", padx=8, pady=(0, 6))
        self.saisie = tk.Entry(r, bg=PANNEAU, fg=TEXTE, insertbackground=TEXTE, relief="flat",
                               font=self.f_petit)
        self.saisie.pack(side="bottom", fill="x", padx=8, pady=(6, 2), ipady=4)
        self.saisie.bind("<Return>", self._valider)

        tk.Frame(r, bg=SURVOL, height=1).pack(fill="x", padx=8, pady=6)
        self.fil = tk.Text(r, height=5, bg=FOND, fg=GRIS, font=self.f_petit, wrap="word",
                           relief="flat", highlightthickness=0, state="disabled")
        self.fil.tag_configure("moi", foreground=VERT)
        self.fil.tag_configure("note", foreground=OR)
        self.fil.tag_configure("journal", foreground="#6f6656")
        self.fil.pack(fill="both", expand=True, padx=12)

    def _debut_glisser(self, e):
        self._dx, self._dy = e.x_root - self.racine.winfo_x(), e.y_root - self.racine.winfo_y()

    def _glisser(self, e):
        self.racine.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _valider(self, _e=None):
        texte = self.saisie.get().strip()
        self.saisie.delete(0, "end")
        if texte:
            self.sur_saisie(texte)

    # ---------------------------------------------------------- affichage
    def _afficher_proposition(self, prop: Proposition, terminee: bool) -> None:
        self.l_situation.config(text=prop.situation)
        lignes = ([f"Parle : {prop.qui}"] if prop.qui else []) + ([f"👁 {prop.vu}"] if prop.vu else [])
        self.l_qui.config(text="\n".join(lignes))
        for w in self.zone_choix.winfo_children():
            w.destroy()
        for c in prop.choix:
            cadre = tk.Frame(self.zone_choix, bg=PANNEAU, cursor="hand2")
            cadre.pack(fill="x", pady=3)
            ton = tk.Label(cadre, text=f"{c.numero}  {c.ton.upper()}", bg=PANNEAU, fg=OR,
                           font=self.f_ton, anchor="w", padx=8)
            ton.pack(fill="x", pady=(4, 0))
            txt = tk.Label(cadre, text=c.texte, bg=PANNEAU, fg=TEXTE, font=self.f_texte,
                           wraplength=self.largeur - 40, justify="left", anchor="w", padx=8)
            txt.pack(fill="x", pady=(0, 6))
            for w in (cadre, ton, txt):
                w.bind("<Button-1>", lambda e, ch=c: self.sur_choix(ch))
                w.bind("<Enter>", lambda e, f=cadre: self._survol(f, SURVOL))
                w.bind("<Leave>", lambda e, f=cadre: self._survol(f, PANNEAU))
        self.l_conseil.config(text=f"Conseil : {prop.conseil}" if prop.conseil and terminee else "")

    @staticmethod
    def _survol(cadre, couleur):
        cadre.config(bg=couleur)
        for w in cadre.winfo_children():
            w.config(bg=couleur)

    def _estomper(self) -> None:
        for cadre in self.zone_choix.winfo_children():
            for w in cadre.winfo_children():
                w.config(fg=GRIS)

    def _ajouter_fil(self, texte: str, etiquette: str = "") -> None:
        self.fil.config(state="normal")
        self.fil.insert("end", texte + "\n", etiquette)
        lignes = int(self.fil.index("end-1c").split(".")[0])
        if lignes > 200:
            self.fil.delete("1.0", f"{lignes - 200}.0")
        self.fil.see("end")
        self.fil.config(state="disabled")

    def _pomper(self) -> None:
        try:
            while True:
                genre, donnee = self.file.get_nowait()
                if genre == "debut":
                    self.etat.config(text="● le Souffleur réfléchit…", fg=OR)
                elif genre == "partiel":
                    self._afficher_proposition(donnee, False)
                elif genre == "fini":
                    prop, premier, total = donnee
                    self._afficher_proposition(prop, True)
                    delai = f"1er choix {premier:.1f}s · " if premier else ""
                    self.etat.config(text=f"● {delai}complet {total:.1f}s", fg=VERT)
                elif genre == "erreur":
                    self.etat.config(text="● erreur", fg=ROUGE)
                    self._ajouter_fil(f"⚠ {donnee}", "journal")
                elif genre == "ligne":
                    texte, etiquette = donnee
                    self._ajouter_fil(texte, etiquette)
                    if etiquette == "moi":
                        self._estomper()
                elif genre == "scene":
                    s = donnee
                    morceaux = [m for m in (s.lieu, s.moment, s.tension and f"tension : {s.tension}") if m]
                    self.l_scene.config(text="👁 " + " · ".join(morceaux))
                elif genre == "journal":
                    self._ajouter_fil(f"· {donnee}", "journal")
                elif genre == "ecoute":
                    self.etat.config(text="● écoute" if donnee else "⏸ en pause",
                                     fg=VERT if donnee else GRIS)
                    self.b_pause.config(text="⏸" if donnee else "▶")
                elif genre == "basculer":
                    self.visible = not self.visible
                    (self.racine.deiconify if self.visible else self.racine.withdraw)()
        except queue.Empty:
            pass
        self.racine.after(40, self._pomper)

    # Appelable depuis n'importe quel fil d'exécution
    def envoyer(self, genre: str, donnee=None) -> None:
        self.file.put((genre, donnee))

    def copier(self, texte: str) -> None:
        self.racine.clipboard_clear()
        self.racine.clipboard_append(texte)

    def lancer(self) -> None:
        self.racine.mainloop()
