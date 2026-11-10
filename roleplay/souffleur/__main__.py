"""Point d'entrée :  python -m souffleur [--simulation] [--peripheriques]"""
from __future__ import annotations

import argparse
import os
import sys


def principal() -> int:
    p = argparse.ArgumentParser(prog="souffleur", description="Le Souffleur : répliques de jeu de rôle en direct.")
    p.add_argument("--simulation", action="store_true",
                   help="sans micro ni écoute : tu écris les répliques entendues dans la fenêtre")
    p.add_argument("--peripheriques", action="store_true", help="liste les périphériques audio et quitte")
    p.add_argument("--personnage", help="fiche à utiliser (donnees/personnages/<nom>.md)")
    p.add_argument("--univers", help="guide d'univers à utiliser (donnees/univers/<nom>.md)")
    args = p.parse_args()

    if args.peripheriques:
        from .audio import lister_peripheriques
        print("\n".join(lister_peripheriques()))
        return 0

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Attention : ANTHROPIC_API_KEY n'est pas défini (fichier .env, voir README).", file=sys.stderr)

    from .app import Souffleur
    from .config import charger
    from .profil import lister
    cfg = charger()
    cfg.jeu.personnage = args.personnage or cfg.jeu.personnage
    cfg.jeu.univers = args.univers or cfg.jeu.univers
    if cfg.jeu.personnage not in lister():
        print(f"Personnage « {cfg.jeu.personnage} » introuvable. Disponibles : {', '.join(lister())}",
              file=sys.stderr)
        return 1
    Souffleur(cfg, simulation=args.simulation).demarrer()
    return 0


if __name__ == "__main__":
    sys.exit(principal())
