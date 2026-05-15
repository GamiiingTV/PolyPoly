"""
Génère les credentials API Polymarket à partir de ta clé privée Polygon.

Utilisation :
    python derive_polymarket_creds.py

Le script te demande ta clé privée (collage masqué), puis affiche :
  POLYMARKET_API_KEY=...
  POLYMARKET_API_SECRET=...
  POLYMARKET_API_PASSPHRASE=...

Copie ces 3 lignes dans ton fichier .env.

Sécurité : la clé privée n'est utilisée que localement pour signer
un message EIP-712. Rien n'est envoyé sauf la requête de dérivation
au serveur Polymarket (clob.polymarket.com).
"""

from __future__ import annotations

import getpass
import sys


def main() -> int:
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.constants import POLYGON
    except ImportError:
        print("ERREUR : py-clob-client n'est pas installé.")
        print("Lance : pip install py-clob-client")
        return 1

    print("=" * 60)
    print("  Génération des credentials API Polymarket")
    print("=" * 60)
    print()
    print("Colle ta clé privée MetaMask (commence par 0x).")
    print("Le texte sera masqué pendant la saisie pour ta sécurité.")
    print()

    private_key = getpass.getpass("Clé privée : ").strip()

    if not private_key:
        print("Aucune clé fournie. Abandon.")
        return 1

    if not private_key.startswith("0x"):
        print("ATTENTION : ta clé ne commence pas par 0x. Je l'ajoute.")
        private_key = "0x" + private_key

    if len(private_key) != 66:
        print(f"ERREUR : longueur incorrecte ({len(private_key)} caractères, attendu 66).")
        print("Une clé privée Polygon valide fait exactement 64 caractères hex + '0x'.")
        return 1

    print()
    print("Connexion à Polymarket (clob.polymarket.com)...")

    try:
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=POLYGON,
        )
        creds = client.create_or_derive_api_creds()
    except Exception as exc:
        print(f"ERREUR pendant la dérivation : {exc}")
        print()
        print("Causes possibles :")
        print("  - Clé privée invalide")
        print("  - Wallet pas connecté à Polymarket (connecte-toi une fois sur polymarket.com)")
        print("  - Polymarket est down")
        return 1

    print()
    print("=" * 60)
    print("  SUCCÈS — copie ces 3 lignes dans ton .env")
    print("=" * 60)
    print()
    print(f"POLYMARKET_API_KEY={creds.api_key}")
    print(f"POLYMARKET_API_SECRET={creds.api_secret}")
    print(f"POLYMARKET_API_PASSPHRASE={creds.api_passphrase}")
    print()
    print("=" * 60)
    print("Ces credentials sont attachés à ton wallet et permanents.")
    print("Si tu les perds, relance ce script pour les régénérer.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
