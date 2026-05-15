# PolyPoly HFT Bot — Guide d'installation

## Ce que fait le bot

Deux stratégies + 4 sources de signal sur les marchés BTC UP/DOWN 5 min Polymarket :

| Stratégie | Description | WR simulé |
|---|---|---|
| **HFT Repricing** | Détecte le lag Binance→Polymarket, entre avant le repricing | ~64-75% |
| **Resolution Snipe** | Achète YES/NO à 87¢ dans les 90s avant résolution | ~80-91% |

**Signaux supplémentaires (v4) :**
- **Funding rate Binance Perpetuals** : détecte les sentiment extrêmes (contrarian)
- **Open Interest delta 5min** : flux institutionnels (build-up / unwind)
- **Whale detection** : trades > 1 BTC ($100k+) sur Binance, pression rolling 30s
- **Kelly adaptive sizing** : taille de trade optimisée selon ton win rate réel

**Capital recommandé : $150 minimum — Trade size de départ : $10**

---

## 1. Prérequis

```bash
# Python 3.10+
python --version

# Installer les dépendances
pip install -r requirements.txt
```

---

## 2. Créer ton fichier .env

```bash
cp .env.example .env
```

Ouvre `.env` et remplis **ces valeurs obligatoires** :

---

### Polymarket (OBLIGATOIRE pour le mode live)

Va sur **https://polymarket.com** → Settings → API Keys

```env
POLYMARKET_PRIVATE_KEY=0xTA_CLÉ_PRIVÉE_WALLET_POLYGON
POLYMARKET_API_KEY=ta_api_key
POLYMARKET_API_SECRET=ta_api_secret
POLYMARKET_API_PASSPHRASE=ton_passphrase
```

> ⚠️ La clé privée = le wallet Polygon où tu déposes tes USDC.
> Crée un wallet dédié pour le bot, ne mets PAS ton wallet principal.

---

### Anthropic / Claude (optionnel — améliore les signaux)

Va sur **https://console.anthropic.com** → API Keys

```env
ANTHROPIC_API_KEY=sk-ant-XXXXXXXX
```

---

### Capital et risque (déjà configuré pour $150)

```env
HFT_CAPITAL_USD=150.0          # Ton dépôt réel
HFT_FIXED_TRADE_USD=10.0       # Base burn-in $10/trade
HFT_USE_KELLY=true             # Kelly adaptatif après 20 trades
HFT_KELLY_MAX_PCT=0.10         # Cap 10% capital par trade
HFT_DAILY_RISK_LIMIT=0.17      # Stop à -$25/jour
HFT_COMPOUND_ENABLED=true      # Gains réinvestis automatiquement
```

> 🔥 **Kelly adaptatif** : pendant les 20 premiers trades, mise = $10 fixe.
> Après, la taille s'ajuste à ton WR réel. Bonus de 1.25× après 5 gains,
> pénalité de 0.60× après 3 pertes. Le capital double → la mise double.

---

## 3. Déposer les USDC sur Polymarket

1. Va sur **https://polymarket.com**
2. Connecte ton wallet Polygon (MetaMask ou autre)
3. Dépose **$150 USDC** via le bouton "Deposit"
4. Attends la confirmation (~30 secondes)

> Le bot utilise directement ce wallet pour placer les ordres.

---

## 4. Lancer le bot

```bash
# Mode papier (simulation — aucun vrai ordre)
python run_hft_ui.py --capital 150

# Mode live (vrais ordres avec ton capital)
python run_hft_ui.py --live --capital 150

# Taille de trade personnalisée
python run_hft_ui.py --live --capital 150 --size 10
```

---

## 5. Comprendre le dashboard

```
╔══ POLYPOLY HFT ENGINE v3.0 ══════════════════════════════╗
║  BTC $103,475  ▲ +$12  │  YES 0.542  │  LAG 187ms  ◉LIVE ║
╚══════════════════════════════════════════════════════════╝

┌─ CAPITAL ────────────────────────────────────────────────┐
│  $151.35     Session +$1.35 (+0.90%)                     │
│  Journalier  +$1.35                                      │
│  Objectif    ████████░░░░░░░░░░  45%                     │
└──────────────────────────────────────────────────────────┘

┌─ STRATÉGIES ─────────────────────────────────────────────┐
│              HFT       SNIPE                             │
│  Trades       11          35                             │
│  Win rate    64%         91%                             │
│  P&L       +4.86$     +14.32$                            │
└──────────────────────────────────────────────────────────┘
```

| Élément | Signification |
|---|---|
| `◉ LIVE` | Bot actif en mode réel |
| `○ PAPER` | Mode simulation (pas de vrais ordres) |
| `■ HALTED` | Bot arrêté (daily limit atteint ou hard stop) |
| `LAG 187ms` | Délai détecté Binance→Polymarket |
| `⏱ 45s` | Secondes avant résolution du marché actuel |
| `HFT ▲` | Trade HFT repricing en direction BULL |
| `SNP ▲` | Resolution snipe en direction BULL |
| `FUNDING +0.012% → BEAR` | Trop de longs payent les shorts → signal baissier |
| `OI Δ5m +0.85% (build-up)` | Open interest grossit → confluence avec mouvement |
| `WHALES BUY 3.2 / SELL 1.1` | Trades >$100k détectés sur Binance (rolling 30s) |
| `🔥 WIN×5` | 5 gains consécutifs → mise +25% sur le prochain |
| `❄ LOSS×3` | 3 pertes consécutives → mise -40% sur le prochain |

---

## 6. Quand le bot s'arrête

Le bot se halt automatiquement si :
- **Daily limit** : perte nette > $25 dans la journée (se réinitialise à minuit UTC)
- **Hard stop** : perte > $10 sur un seul trade

Pour reprendre manuellement :
```python
# Dans un shell Python
from hft.risk.risk_manager import RiskManager
risk = RiskManager()
risk.resume()
```

Ou relancer simplement le bot (le daily limit se reset à minuit automatiquement).

---

## 7. Projection réaliste

Basé sur la simulation sur 5 scénarios de marché différents :

| Scénario | P&L / 24h |
|---|---|
| Bon marché | +$25-50 |
| Marché normal | +$5-10 |
| Mauvaise journée | -$20 à -$25 (daily stop) |
| **Moyenne** | **+$7-10/jour** |

**Compound sur 30 jours (base $7/jour) :**
- Semaine 1 : ~$200
- Semaine 2 : ~$265
- Mois 1 : ~**$380-400**

---

## 8. Augmenter la taille de trade

Change `HFT_FIXED_TRADE_USD` dans `.env` :

| Capital | Taille recommandée | Gain attendu/jour |
|---|---|---|
| $150 | $10 | +$7-10 |
| $250 | $15 | +$12-18 |
| $500 | $25 | +$25-35 |
| $1000 | $40 | +$50-70 |

> Règle : taille ≤ 15% du capital pour résister à 3 pertes consécutives.

---

## 9. Problèmes courants

**"POLYMARKET_API_KEY absent"**
→ Vérifie que ton `.env` est bien rempli et que tu lances depuis le dossier `/PolyPoly`

**"No BTC markets found"**
→ Polymarket n'a pas de marchés BTC 5M actifs en ce moment. Le bot cherche automatiquement toutes les 30s.

**"Bot halted : limite quotidienne"**
→ Normal. Tu as perdu $25 aujourd'hui. Le bot reprend automatiquement demain à minuit UTC.

**Dashboard ne s'affiche pas bien**
→ Agrandir le terminal (au moins 120 colonnes × 40 lignes recommandé).

---

## Commandes utiles

```bash
# Voir les logs en direct
tail -f logs/hft.log

# Simulation sans les vrais marchés
python simulate_hft_v3.py --capital 150 --trade-size 10 --snipe-size 10

# Simulation ancienne (v2)
python simulate_hft_offline.py
```
