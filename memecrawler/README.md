# 🕷️ MemeCrawler — le crawler lit, Jev juge, les bots tradent

Bot de memecoins **Solana** sur le modèle « GROKBOT + JEV ».

```
CRAWLER ─► free_kill ─► trade_kill ─► chain_kill ─► soft_kill ─► PICK ─► attente du flush ─► ACHAT ─► sortie
 (DexScreener)  (gratuit)   (volume)    (RugCheck)   (Jev = Claude)
```

| Rôle | Fichier | Ce qu'il fait |
|---|---|---|
| CRAWLER / SCAN | `sources.py`, `bot.py` | Récupère les nouveaux coins Solana sur DexScreener, puis le prix, la liquidité, le volume et les transactions |
| VET | `sources.py` (RugCheck) | Vérifie les holders, le dev, la mint/freeze authority et les risques on-chain |
| SOCIAL + JEV | `jev.py` | Claude note 6 critères (dont « le compte X est-il vraiment celui du projet ») et dit oui ou non |
| filter / thresholds | `filters.py`, `thresholds.py` | Applique exactement les seuils de la vidéo, dans le même ordre |
| CHIEF | `bot.py` | Tient la watchlist des picks et ne prend jamais de position lui-même |
| SIZE | `bot.py` | Ticket = 20 % de la bank, plafonné en $ et à 2 % de la liquidité |
| FILLS | `executor.py` | Swaps Jupiter signés avec ton wallet. Une seule position à la fois |
| RISK | `strategy.py` | Stop loss, trailing stop, sortie si rug, limite de perte par jour, fichier STOP |

## Stratégie
- **Pas d'entrée sans flush.** Une fois le coin choisi, on attend qu'il baisse de 25 % depuis son plus haut. On achète au rebond (+3 % depuis le creux), et seulement si les achats dépassent les ventes sur 5 min.
- On n'achète jamais un coin qui a perdu plus de 50 % sur l'heure.
- **Sorties** :
  - stop loss à -12 % ;
  - trailing stop : il s'active à +15 %, puis on vend si le prix recule de 10 % depuis son plus haut ;
  - sortie si la liquidité fond de moitié (rug) ;
  - sortie après 4 h maximum.
- Après une sortie, le coin reste suivi pendant 12 h. Il faudra un **nouveau** flush pour y revenir (comme les deux allers-retours sur HIGGS).

Tous les réglages se changent dans `.env` (variables `MC_*`, voir `settings.py`).

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env    # remplis ANTHROPIC_API_KEY, SOLANA_PRIVATE_KEY, SOLANA_RPC_URL
```

## Lancement
```bash
python -m memecrawler --dry      # 1) crawl + Jev seulement, aucun ordre : regarde ce qu'il choisit
python -m memecrawler --paper    # 2) simulation avec les vrais prix
python -m memecrawler            # 3) LIVE (MC_MODE=live) : vrai argent
```
- **Arrêt d'urgence des achats** : `touch STOP_MEMECRAWLER` à la racine. Les ventes continuent.
- État et historique des trades : `data/memecrawler_state.json`. Logs : `logs/memecrawler.log`.
- Telegram : les alertes partent automatiquement si `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` sont remplis.

## Tests
```bash
python -m pytest memecrawler/tests -q
```

## ⚠️ À lire avant le mode live
- Utilise un **wallet dédié** et n'y mets que ce que tu acceptes de perdre entièrement.
- Le slippage et les frais réels sur les memecoins sont souvent pires que ce que montre la simulation.
- Les gains affichés dans ces vidéos (« 100 $ → 17 608 $ en 4 nuits ») ne sont pas vérifiables. Teste d'abord en `--dry` puis en `--paper` pendant plusieurs jours.
