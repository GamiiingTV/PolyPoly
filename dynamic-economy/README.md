# dynamic-economy

**Économie dynamique temps réel pour FiveM**  
Prix qui fluctuent selon l'offre et la demande de vos joueurs.  
Compatible **QBCore** et **ESX** · Nécessite **oxmysql**

---

## Sommaire

1. [Ce que fait ce script](#ce-que-fait-ce-script)
2. [Ce dont vous avez besoin](#ce-dont-vous-avez-besoin)
3. [Installation étape par étape](#installation-étape-par-étape)
4. [Configuration (config.lua)](#configuration-configlua)
5. [Commandes admin](#commandes-admin)
6. [Tester que tout fonctionne](#tester-que-tout-fonctionne)
7. [Détecter les conflits avec vos autres mods](#détecter-les-conflits-avec-vos-autres-mods)
8. [Mode debug](#mode-debug)
9. [Questions fréquentes](#questions-fréquentes)
10. [Formule des prix expliquée](#formule-des-prix-expliquée)
11. [Sécurité](#sécurité)

---

## Ce que fait ce script

Imaginez la bourse, mais pour votre serveur FiveM.

- Quand beaucoup de joueurs vendent de la drogue → le prix chute (trop d'offre)
- Quand personne ne récolte du minerai → le prix monte (manque d'offre)
- Un "crash boursier" peut survenir aléatoirement et faire chuter tous les prix
- Si trop d'argent circule sur le serveur → inflation automatique
- Chaque joueur peut voir l'évolution des prix sur 24h dans une interface style terminal financier

Tout se passe **côté serveur**. Les joueurs ne peuvent pas tricher en envoyant de faux montants.

---

## Ce dont vous avez besoin

| Requis | Version minimum |
|---|---|
| **oxmysql** | 2.x |
| **QBCore** ou **ESX** | n'importe laquelle récente |
| FiveM server avec **OneSync** | recommandé |

> oxmysql est gratuit : https://github.com/overextended/oxmysql

---

## Installation étape par étape

### Étape 1 — Copier les fichiers

Déposez le dossier `dynamic-economy` dans votre dossier `resources/` :

```
resources/
└── dynamic-economy/       ← déposez tout ici
    ├── fxmanifest.lua
    ├── config.lua
    ├── server/
    ├── client/
    └── ui/
```

### Étape 2 — Ajouter dans server.cfg

Ouvrez votre `server.cfg` et ajoutez **après** la ligne `ensure oxmysql` :

```
ensure dynamic-economy
```

> Ordre important : oxmysql doit démarrer AVANT dynamic-economy.

### Étape 3 — Configurer config.lua

Ouvrez `config.lua` et modifiez au minimum ces lignes :

```lua
-- Mettez 'qbcore' ou 'esx' selon votre serveur
Config.Framework = 'qbcore'

-- Collez votre webhook Discord ici (ou mettez Discord.enabled = false)
Config.Discord.webhook = 'https://discord.com/api/webhooks/...'
```

### Étape 4 — Démarrer le serveur

Les tables de base de données (`de_prices`, `de_transactions`, `de_price_history`)  
sont créées **automatiquement** au premier démarrage. Rien à importer.

### Étape 5 — Vérifier que tout fonctionne

Dans la console serveur ou en jeu avec un compte admin, tapez :

```
/de_test
```

Vous verrez un rapport ✓/✗ pour chaque composant. Voir la section dédiée ci-dessous.

---

## Configuration (config.lua)

Tout se passe dans `config.lua`. Vous ne devez **jamais** modifier `server.lua` ou `client.lua`.

### Les réglages les plus importants

```lua
Config.Framework = 'qbcore'      -- 'qbcore' ou 'esx'
Config.FluctuationInterval = 300 -- Recalcul des prix toutes les X secondes (300 = 5 min)
Config.DemandWindow = 3600       -- Fenêtre de temps pour calculer l'offre/demande (en secondes)
Config.DemandSensitivity = 0.35  -- 0.0 = prix fixes, 1.0 = prix très volatils
Config.MaxSellPerPlayerPerHour = 200  -- Max qu'un joueur peut vendre par item par heure
```

### Réglages moins urgents

```lua
Config.MeanReversionRate = 0.08  -- Vitesse de retour vers le prix de base (0.0–1.0)
                                 -- Plus élevé = prix se stabilisent plus vite

Config.Inflation.threshold = 50000000  -- Seuil d'argent total sur le serveur
                                        -- avant que l'inflation se déclenche ($50M)
Config.Inflation.multiplier = 1.02     -- Hausse des prix à chaque cycle d'inflation (+2%)

Config.MarketCrash.chance = 0.02       -- Probabilité de crash à chaque cycle (2%)
Config.MarketCrash.multiplier = 0.40   -- Prix tombent à 40% de leur valeur pendant le crash
Config.MarketCrash.duration = 180      -- Durée du crash en secondes (3 min)
```

### Ajouter ou modifier un item

Dans `Config.Items`, chaque item ressemble à ceci :

```lua
['weed_brick'] = {
    label     = 'Brique de Weed',    -- Nom affiché dans l'interface
    basePrice = 800,                  -- Prix d'équilibre (point de référence)
    minPrice  = 200,                  -- Prix minimum absolu (plancher)
    maxPrice  = 2500,                 -- Prix maximum absolu (plafond)
    category  = 'drugs',             -- 'drugs', 'legal', 'resources', ou 'crafting'
    unit      = 'kg',                -- Unité affichée ('kg', 'g', 'unit', 'L'…)
},
```

> Le nom entre crochets (`'weed_brick'`) doit correspondre exactement au nom de l'item  
> dans votre inventaire (QBCore ou ESX).

---

## Commandes admin

Pour utiliser ces commandes en jeu, votre joueur doit être admin  
(groupe `admin`/`superadmin` dans QBCore, ou ace `dynamic_economy.admin`).  
Depuis la console serveur, toutes les commandes fonctionnent sans restriction.

| Commande | Ce qu'elle fait |
|---|---|
| `/de_test` | Lance tous les tests et affiche un rapport ✓/✗ |
| `/de_conflicts` | Affiche le rapport de conflits avec vos autres mods |
| `/de_debug` | Active/désactive le mode debug à chaud (sans redémarrer) |
| `/de_prices` | Liste tous les prix actuels |
| `/de_setprice weed_brick 1500` | Force le prix d'un item à une valeur précise |
| `/de_resetprice weed_brick` | Remet un item à son `basePrice` |
| `/de_crash` | Déclenche un crash boursier manuellement |

---

## Tester que tout fonctionne

### Test automatique complet

Tapez `/de_test` dans la console serveur ou en jeu (admin requis).

Vous obtenez un rapport comme celui-ci :

```
═══════════════════════════════════════
 dynamic-economy TEST SUITE RESULTS
═══════════════════════════════════════
 ✓ Config table exists
 ✓ Items catalogue populated
 ✓ Price cache populated
 ✓ All items have a cached price
 ✓ Clamp function correctness
 ✓ CalculateNewPrice (zero activity → mean revert)
 ✓ DB: prices table readable
 ✓ DB: transactions table readable
 ✓ DB: history table readable
 ✓ Framework resource is started
 ✓ oxmysql is started
 ✓ Sell limit: first sale allowed
 ✓ Sell limit: cap enforced
 ✓ Market crash: crashActive starts false
 ✓ Discord: webhook configured (if enabled)
 ✓ Config: all items have valid price bounds
───────────────────────────────────────
 Passed: 16 / 16 — ALL PASS
═══════════════════════════════════════
```

Si un test échoue, la ligne affiche ✗ avec la raison. Exemples de causes fréquentes :

| Erreur | Solution |
|---|---|
| `qb-core not started` | Vérifiez que qb-core est dans server.cfg avant dynamic-economy |
| `oxmysql not started` | Ajoutez `ensure oxmysql` avant `ensure dynamic-economy` |
| `priceCache is empty` | Le script a planté au démarrage — regardez la console serveur |
| `minPrice >= maxPrice` pour un item | Corrigez les valeurs dans config.lua |
| `Discord webhook not set` | Renseignez le webhook ou désactivez Discord |

### Tests manuels recommandés

**Tester la vente :**
1. Donnez-vous un item (`/giveitem weed_brick 10` ou équivalent)
2. Ouvrez le terminal marché avec `F7`
3. Sélectionnez l'item, entrez 5, cliquez VENDRE
4. Vérifiez que l'argent a été ajouté et l'item retiré de l'inventaire
5. Regardez dans la console si la ligne `[DE:SELL]` apparaît (debug activé)

**Tester la fluctuation :**
1. Vendez beaucoup du même item (plusieurs joueurs ou utilisez /de_test)
2. Attendez le prochain cycle (par défaut 5 min) ou réduisez `FluctuationInterval` à 10 dans config pour tester
3. Le prix de cet item doit avoir baissé

**Tester le crash boursier :**
1. Tapez `/de_crash` en admin
2. Un message doit s'afficher à tous les joueurs
3. Tous les prix doivent chuter dans l'interface

**Tester la limite anti-manipulation :**
1. Essayez de vendre plus que `MaxSellPerPlayerPerHour` d'un même item
2. Le serveur doit refuser et afficher un message d'erreur

---

## Détecter les conflits avec vos autres mods

Au **démarrage automatique**, dynamic-economy analyse les ressources actives  
et signale ce qui pourrait poser problème. Les résultats apparaissent dans la console serveur.

Vous pouvez aussi relire ce rapport à tout moment avec `/de_conflicts`.

### Les niveaux de sévérité

| Niveau | Signification |
|---|---|
| `[ERROR]` | **Conflit critique** — les deux ressources ne peuvent pas tourner ensemble telles quelles |
| `[WARN]` | **Attention** — fonctionne, mais vérifiez la compatibilité des exports |
| `[INFO]` | **Note** — aucun conflit, mais il faut savoir que cette ressource tourne |

### Ressources connues analysées

**Inventaires** (warn si détectés — exports potentiellement différents) :
- `ox_inventory`, `qs-inventory`, `ps-inventory`, `lj-inventory`, `tgiann-inventory`, `codem-inventory`

**Économies concurrentes** (error si détectées) :
- `esx_economy`, `brutal_economy`, `economy_system`

**Shops à prix fixes** (info — aucun conflit, mais les prix ne seront pas dynamiques là-bas) :
- `esx_shops`, `qb-shops`, `esx_blackmarket`

**Drogues** (info) :
- `qb-drugs`, `ps-drugs` — leurs points de vente ont des prix fixes

**Banking** (info) :
- `Renewed-Banking`, `okokBanking`, `qb-banking`

### Que faire si vous avez un inventaire non-supporté ?

Si vous utilisez `ox_inventory` par exemple, ouvrez `server/server.lua`  
et cherchez les fonctions `PlayerHasItem`, `RemovePlayerItem`, et la section `buyItem`.  
Remplacez les exports framework par les exports `ox_inventory` correspondants.  
Des instructions détaillées seront ajoutées dans les prochaines mises à jour.

---

## Mode debug

Le mode debug affiche dans la console serveur le détail de chaque opération.

**Activer en config (permanent) :**
```lua
Config.Debug = {
    enabled = true,
    levels = {
        price   = true,   -- recalculs de prix
        sell    = true,   -- ventes
        buy     = true,   -- achats
        db      = true,   -- opérations SQL
        crash   = true,   -- crash boursier
        inflate = true,   -- inflation
    }
}
```

**Activer/désactiver à chaud (sans redémarrer) :**
```
/de_debug
```

**Désactiver en production :**

Mettez `enabled = false` dans `Config.Debug` pour éviter de polluer la console  
et d'exposer des informations sensibles dans les logs.

**Exemple de sortie debug :**
```
[DE:PRICE] weed_brick: $800.00 → $742.15 (Δ-7.2%)
[DE:SELL] player=license:abc123 item=weed_brick qty=5 price=742.15 total=3710.75
[DE:CRASH] MARKET CRASH triggered!
[DE:INFLATE] Inflation applied (x1.02). Server money: $52340000
```

---

## Questions fréquentes

**Q : Les prix sont-ils sauvegardés si je redémarre le serveur ?**  
R : Oui. Les prix sont persistés en base de données à chaque cycle et rechargés au démarrage.

**Q : Est-ce que les joueurs peuvent tricher les prix ?**  
R : Non. Toute la logique monétaire (calcul du prix, vérification de l'inventaire, paiement)  
se passe côté serveur. Le client envoie uniquement "je veux vendre X de tel item".

**Q : Comment intégrer les prix dynamiques dans mes autres scripts (qb-drugs, etc.) ?**  
R : Utilisez l'export serveur `exports['dynamic-economy']:GetPrice('weed_brick')`  
(à venir dans la v1.1). Pour l'instant, les deux systèmes coexistent.

**Q : Est-ce compatible OneSync Infinity (64+ joueurs) ?**  
R : Oui. Toute la logique est serveur-side, il n'y a pas de limitation OneSync.

**Q : J'ai changé `FluctuationInterval` mais ça ne prend pas effet.**  
R : Redémarrez la ressource. Le cycle est démarré au lancement, il faut `restart dynamic-economy`.

**Q : Puis-je ajouter mes propres catégories ?**  
R : Oui. Ajoutez `category = 'macategorie'` dans les items, puis ajoutez un onglet  
dans `ui/index.html` avec `data-cat="macategorie"`.

---

## Formule des prix expliquée

```
supply = nombre d'unités vendues dans la dernière heure
demand = nombre d'unités achetées dans la dernière heure

ratio  = (demand - supply) / (supply + demand + 1)
         ← borné entre -1.0 et +1.0

nouveau_prix = prix_actuel × (1 + DemandSensitivity × ratio)
nouveau_prix = nouveau_prix + (basePrice - nouveau_prix) × MeanReversionRate
nouveau_prix = clamp(nouveau_prix, minPrice, maxPrice)
```

**Exemple concret :**
- `weed_brick` à 800$, 50 unités vendues, 10 achetées
- ratio = (10 - 50) / (50 + 10 + 1) = -0.66
- nouveau = 800 × (1 + 0.35 × -0.66) = 800 × 0.769 = **615$**
- mean reversion : 615 + (800 - 615) × 0.08 = **630$**

---

## Sécurité

- Toutes les transactions sont validées **côté serveur uniquement**
- Le client n'envoie que `item` + `qty` — jamais de montant
- Les inventaires sont vérifiés avant toute transaction
- La base de données utilise des **requêtes paramétrées** (protection injection SQL)
- Chaque transaction est loggée dans `de_transactions` pour audit
- La limite par joueur/heure (`MaxSellPerPlayerPerHour`) bloque la manipulation de masse

---

## Support & mises à jour

En cas de problème :

1. Activez le mode debug (`Config.Debug.enabled = true`)
2. Lancez `/de_test` et copiez le résultat
3. Lancez `/de_conflicts` et copiez le résultat
4. Partagez les deux rapports + votre `config.lua` (sans le webhook Discord)

---

*dynamic-economy v1.0 — Tous droits réservés*
