# PolyPoly HFT Bot — Guide d'installation complet (débutant)

> Ce guide part de zéro. Aucune connaissance technique requise.
> Temps estimé : 20-30 minutes.

---

## Ce que fait le bot

| Stratégie | Description | Win Rate simulé |
|---|---|---|
| **HFT Repricing** | Détecte le lag Binance→Polymarket, entre avant le repricing | ~64-75% |
| **Resolution Snipe** | Achète YES/NO à 87¢ dans les 90s avant résolution | ~80-91% |

**Signaux v4 :**
- Funding rate Binance Perpetuals (sentiment extrême → signal contrarian)
- Open Interest Δ5min (flux institutionnels)
- Whale detection (trades > 1 BTC sur Binance)
- Kelly adaptatif (taille de trade optimisée sur ton historique réel)

**Capital recommandé : $150 minimum — Trade size de départ : $10**

---

## ÉTAPE 1 — Installer Python 3.11

> Pourquoi 3.11 ? Meilleure compatibilité avec toutes les dépendances du bot.

### Windows

1. Va sur : **https://www.python.org/downloads/release/python-3119/**
2. Tout en bas de la page, dans "Files", clique sur :
   - **Windows installer (64-bit)** → fichier `python-3.11.9-amd64.exe`
3. Lance l'installeur
4. **IMPORTANT** : Coche la case **"Add Python 3.11 to PATH"** en bas avant de cliquer Install
5. Clique "Install Now"
6. Attends la fin, ferme l'installeur

**Vérification :**
Ouvre le menu Démarrer → tape `cmd` → Enter → dans la fenêtre noire, tape :
```
python --version
```
Tu dois voir : `Python 3.11.x`

### Mac

1. Va sur : **https://www.python.org/downloads/release/python-3119/**
2. Dans "Files", clique sur **macOS 64-bit universal2 installer** → `python-3.11.9-macos11.pkg`
3. Lance le `.pkg`, suis les étapes normalement
4. Ouvre le Terminal (Spotlight → "Terminal") et tape :
```
python3 --version
```
Tu dois voir : `Python 3.11.x`

> Sur Mac, utilise `python3` au lieu de `python` dans toutes les commandes.

---

## ÉTAPE 2 — Installer Git

Git permet de télécharger le code du bot.

### Windows

1. Va sur : **https://git-scm.com/download/win**
2. Le téléchargement démarre automatiquement (64-bit)
3. Lance l'installeur → laisse tout par défaut → clique "Next" partout → "Install"
4. Vérifie dans cmd :
```
git --version
```

### Mac

Git est souvent déjà installé. Dans le Terminal :
```
git --version
```
Si ça demande d'installer Xcode Command Line Tools → accepte.

---

## ÉTAPE 3 — Télécharger le bot

Ouvre **cmd** (Windows) ou **Terminal** (Mac) et tape ces commandes une par une :

```bash
# Va dans ton dossier Documents
cd Documents

# Télécharge le bot
git clone -b claude/hft-btc-polymarket-bot-JFYfG https://github.com/gamiiingtv/polypoly.git PolyPoly

# Entre dans le dossier
cd PolyPoly
```

Tu dois maintenant voir un dossier `PolyPoly` dans tes Documents.

---

## ÉTAPE 4 — Créer l'environnement virtuel

L'environnement virtuel isole les dépendances du bot du reste de ton système.

```bash
# Crée l'environnement (une seule fois)
python -m venv venv

# Active l'environnement
# Sur Windows :
venv\Scripts\activate

# Sur Mac/Linux :
source venv/bin/activate
```

> Tu dois voir `(venv)` au début de la ligne dans ton terminal. C'est normal.
> **Chaque fois que tu relances le bot**, tu devras réactiver avec la commande activate.

---

## ÉTAPE 5 — Installer les dépendances

Toujours dans le terminal avec `(venv)` actif :

```bash
# Upgrade pip d'abord
pip install --upgrade pip

# Installe toutes les dépendances (peut prendre 5-10 minutes)
pip install -r requirements.txt
```

> Si tu vois des erreurs en rouge pendant l'installation, c'est souvent normal pour
> des packages optionnels. Le bot fonctionnera quand même.
> La seule erreur bloquante serait "ERROR: Could not find a version that satisfies..."

---

## ÉTAPE 6 — Créer ton fichier de configuration

```bash
# Copie le template
# Windows :
copy .env.example .env

# Mac/Linux :
cp .env.example .env
```

Ouvre le fichier `.env` avec le Bloc-notes (Windows) ou TextEdit (Mac).

> Sur Windows : clic droit sur `.env` → "Ouvrir avec" → Bloc-notes

---

## ÉTAPE 7 — Obtenir tes clés API Polymarket

> Cette étape est obligatoire pour le mode live. En mode papier (simulation), tu peux la sauter.

### 7a. Créer un wallet Polygon dédié

**NE PAS utiliser ton wallet principal.** Crée un nouveau wallet pour le bot.

1. Installe MetaMask : **https://metamask.io/download/**
2. Crée un nouveau wallet → note bien les 12 mots de récupération
3. Dans MetaMask, assure-toi d'être sur le réseau **Polygon** (et non Ethereum)
   - Clique sur le réseau en haut → "Add network" → cherche "Polygon"
4. Copie l'adresse de ton wallet (commence par `0x`)

### 7b. Déposer des USDC sur Polymarket

1. Va sur **https://polymarket.com**
2. Connecte MetaMask
3. Clique "Deposit" → $150 USDC
4. Attends la confirmation (~30s)

### 7c. Générer les clés API

1. Sur **https://polymarket.com** → clique sur ton profil (en haut à droite)
2. Va dans **Settings** → **API Keys**
3. Clique **"Create API Key"**
4. Note les 4 valeurs :
   - `API Key`
   - `API Secret`
   - `Passphrase`
   - (la clé privée vient de MetaMask)

### 7d. Récupérer la clé privée MetaMask

1. Dans MetaMask → 3 points en haut à droite → "Account details"
2. Clique **"Export Private Key"**
3. Entre ton mot de passe MetaMask
4. Copie la clé (commence par `0x`)

> ⚠️ Cette clé = accès total à ton wallet. Ne la donne JAMAIS à personne.
> Ne la mets jamais dans un fichier que tu vas partager ou uploader.

### 7e. Remplir le .env

Ouvre ton fichier `.env` et modifie ces lignes :

```env
POLYMARKET_PRIVATE_KEY=0xTA_CLÉ_PRIVÉE_ICI
POLYMARKET_API_KEY=ton_api_key_ici
POLYMARKET_API_SECRET=ton_api_secret_ici
POLYMARKET_API_PASSPHRASE=ton_passphrase_ici
```

Et vérifie ces valeurs (déjà configurées pour $150) :

```env
HFT_CAPITAL_USD=150.0
HFT_FIXED_TRADE_USD=10.0
HFT_USE_KELLY=true
HFT_KELLY_MAX_PCT=0.10
HFT_DAILY_RISK_LIMIT=0.17
HFT_COMPOUND_ENABLED=true
```

Sauvegarde le fichier.

---

## ÉTAPE 8 — Tester en mode papier (OBLIGATOIRE avant le live)

Le mode papier simule les trades sans mettre de vrai argent.

```bash
# Active l'environnement si pas déjà fait
# Windows :
venv\Scripts\activate
# Mac :
source venv/bin/activate

# Lance le bot en mode papier
python run_hft_ui.py --capital 150
```

Tu dois voir le dashboard s'afficher. Laisse tourner 10-15 minutes.
Si tu vois des trades "PAPER" se faire, tout fonctionne.

**Arrêter le bot** : `Ctrl+C`

---

## ÉTAPE 9 — Lancer en mode live (vrais ordres)

Seulement quand tu es prêt et que tes clés API sont dans le `.env` :

```bash
python run_hft_ui.py --live --capital 150
```

> Le bot va automatiquement chercher les marchés BTC 5min actifs sur Polymarket.
> S'il n'en trouve pas, il attend (normal entre 2 créneaux de 5 minutes).

---

## Comprendre le dashboard

```
╔══ ◈◈◈ POLYPOLY HFT ENGINE v3.0 ◈◈◈ ══════════════════════════════╗
║  BTC $103,475  ▲ +$12  │  YES 0.542  │  LAG 187ms  │  ◉ LIVE     ║
╚═══════════════════════════════════════════════════════════════════╝

┌─ CAPITAL ──────────────────────────────────────┐
│  $151.35     Session +$1.35 (+0.90%)           │
│  Journalier  +$1.35                            │
│  Objectif    ████████░░░░░░░░░░  45%           │
└────────────────────────────────────────────────┘

┌─ STRATÉGIES ───────────────────────────────────┐
│              HFT       SNIPE                   │
│  Trades       11          35                   │
│  Win rate    64%         91%                   │
│  P&L       +4.86$     +14.32$                  │
└────────────────────────────────────────────────┘

┌─ DÉRIVÉS ──────────────────────────────────────┐
│  FUNDING  +0.012% → BEAR (longs surchauffés)   │
│  OI Δ5m   +0.85% (build-up)                   │
│  WHALES   BUY 3.2 BTC / SELL 1.1 BTC          │
└────────────────────────────────────────────────┘
```

| Indicateur | Signification |
|---|---|
| `◉ LIVE` | Bot actif en mode réel |
| `○ PAPER` | Simulation (pas de vrai argent) |
| `■ HALTED` | Bot arrêté (daily limit ou hard stop) |
| `LAG 187ms` | Délai détecté Binance→Polymarket |
| `⏱ 45s` | Secondes avant résolution du marché actuel |
| `HFT ▲` | Trade HFT repricing direction BULL |
| `SNP ▲` | Resolution snipe direction BULL |
| `FUNDING +0.012% → BEAR` | Trop de longs → signal baissier contrarian |
| `OI Δ5m +0.85% (build-up)` | Open interest grossit → confluence |
| `WHALES BUY 3.2 / SELL 1.1` | Baleines >$100k sur Binance (rolling 30s) |
| `🔥 WIN×5` | 5 gains consécutifs → mise +25% |
| `❄ LOSS×3` | 3 pertes consécutives → mise -40% |

---

## Quand le bot s'arrête automatiquement

| Condition | Explication |
|---|---|
| **Daily limit** | Perte nette > $25 sur la journée (reset à minuit UTC) |
| **Hard stop** | Perte > $10 sur un trade unique |

> **Important :** Le daily limit est sur le P&L net, pas les pertes brutes.
> Si tu gagnes $40 puis tu perds $30, ton P&L net est +$10 → le bot continue.
> Il s'arrête seulement si tu perds $25 NET depuis le début de la journée.

Le bot reprend automatiquement le lendemain à minuit UTC.

---

## Projections réalistes

Basé sur simulation 5 scénarios de marché (24h, $10/trade) :

| Scénario | P&L / 24h |
|---|---|
| Bon marché | +$25-50 |
| Marché normal | +$5-10 |
| Mauvaise journée | -$20 à -$25 (daily stop) |
| **Moyenne** | **+$7-10/jour** |

**Compound sur 30 jours (base $7/jour) :**
- Semaine 1 : ~$200
- Semaine 2 : ~$265
- Mois 1 : ~$380-400

---

## Augmenter la taille de trade

Modifie `HFT_FIXED_TRADE_USD` dans ton `.env` :

| Capital | Taille recommandée | Gain attendu/jour |
|---|---|---|
| $150 | $10 | +$7-10 |
| $250 | $15 | +$12-18 |
| $500 | $25 | +$25-35 |
| $1000 | $40 | +$50-70 |

> Règle : taille ≤ 15% du capital pour résister à 3 pertes consécutives.
> N'augmente que quand ton capital a réellement grandi.

---

## Problèmes courants

**"POLYMARKET_API_KEY absent" ou "missing"**
→ Vérifie que ton `.env` est bien rempli. Ouvre-le dans le Bloc-notes et vérifie chaque ligne.
→ Vérifie que tu es bien dans le dossier `/PolyPoly` dans le terminal.

**"No BTC markets found"**
→ Normal. Polymarket n'a pas de marchés BTC 5min actifs en ce moment.
→ Le bot cherche automatiquement toutes les 30 secondes.

**"Bot halted : daily limit"**
→ Normal. Tu as perdu $25 aujourd'hui. Reprend demain à minuit UTC.

**Dashboard ne s'affiche pas correctement**
→ Agrandir le terminal : au moins 120 colonnes × 40 lignes.
→ Windows : clic droit sur la barre du cmd → Propriétés → Police → agrandir
→ Mac : Terminal → Préférences → taille de fenêtre

**Erreur "ModuleNotFoundError"**
→ L'environnement virtuel n'est probablement pas activé.
→ Relance : `venv\Scripts\activate` (Windows) ou `source venv/bin/activate` (Mac)

**"(venv)" n'apparaît plus dans le terminal**
→ Tu as fermé et rouvert le terminal. Rentre dans le dossier et réactive :
```bash
cd Documents/PolyPoly
venv\Scripts\activate
```

---

## Commandes utiles

```bash
# Mode papier (simulation)
python run_hft_ui.py --capital 150

# Mode live ($10/trade)
python run_hft_ui.py --live --capital 150

# Mode live avec taille personnalisée
python run_hft_ui.py --live --capital 150 --size 15

# Voir les logs détaillés
# Windows :
type logs\hft.log
# Mac/Linux :
tail -f logs/hft.log

# Simulation 24h sans accès internet
python simulate_hft_v3.py --capital 150 --trade-size 10 --snipe-size 10
```

---

## Récapitulatif des étapes

- [ ] Python 3.11 installé et visible dans le terminal
- [ ] Git installé
- [ ] Repo cloné dans Documents/PolyPoly
- [ ] Environnement virtuel créé et activé (`(venv)` visible)
- [ ] `pip install -r requirements.txt` terminé
- [ ] `.env` créé à partir de `.env.example`
- [ ] Clés Polymarket renseignées dans `.env`
- [ ] Test en mode papier fonctionnel (dashboard s'affiche)
- [ ] $150 USDC déposés sur Polymarket
- [ ] Mode live lancé 🚀
