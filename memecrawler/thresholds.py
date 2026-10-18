"""
MemeCrawler — Seuils du filtre (thresholds.py)

HARD : arithmétique pure, ne coûte rien. Un seul seuil raté = coin éliminé.
SOFT : appliqué aux réponses de Jev (scores entre 0 et 1).
"""

HARD = {
    "min_age_minutes": 15,       # pas de coin de moins de 15 min
    "min_liquidity_usd": 12_000,
    "min_volume_h24": 40_000,
    "min_mcap_usd": 60_000,
    "min_trades_h24": 150,
    "max_top_wallet": 0.05,      # aucun wallet > 5 % du supply
    "max_top_10": 0.60,          # top 10 wallets < 60 % du supply
}

# nom → ("max" | "min", seuil)
SOFT = {
    "concentration_is_exit_risk": ("max", 0.55),
    "momentum_already_spent": ("max", 0.60),
    "liquidity_fits_ticket": ("min", 0.60),
    "account_is_the_project": ("min", 0.70),
    "recycled_account": ("max", 0.50),
    "dev_still_loaded": ("max", 0.55),
}
