# dynamic-economy

**Real-time supply & demand economy for FiveM**  
Compatible QBCore · ESX · OneSync · oxmysql

---

## Features

| Feature | Details |
|---|---|
| Dynamic prices | Supply/demand formula recalculates every cycle |
| Price floor & ceiling | Per-item `minPrice` / `maxPrice` in `config.lua` |
| Anti-manipulation | Per-player hourly sell cap, fully server-side |
| DB logging | Every transaction stored in `de_transactions` |
| RAM cache | Prices cached in memory, SQL only on cycle writes |
| Fluctuation cycle | Configurable interval (default 5 min) |
| NUI terminal | Financial-style UI with 24h price chart |
| Discord alerts | Webhook on price swings ≥ threshold |
| Market crash | Rare random event (2% per cycle by default) |
| Inflation system | Auto price-lift when server money exceeds threshold |
| Admin commands | `/de_setprice`, `/de_resetprice`, `/de_crash`, `/de_prices` |
| Security | Zero monetary logic client-side, all events validated server-side |

---

## Requirements

- [oxmysql](https://github.com/overextended/oxmysql)
- QBCore **or** ESX (configure in `config.lua`)
- FiveM server with OneSync enabled (recommended)

---

## Installation

1. Drop the `dynamic-economy` folder into your `resources/` directory.
2. Add `ensure dynamic-economy` to your `server.cfg` (after `oxmysql`).
3. Open `config.lua` and set:
   - `Config.Framework` → `'qbcore'` or `'esx'`
   - `Config.Discord.webhook` → your Discord webhook URL
   - Adjust items, prices, and limits as needed.
4. Start your server. Tables are created automatically.

---

## Config quick-reference

```lua
Config.Framework          = 'qbcore'          -- 'qbcore' | 'esx'
Config.FluctuationInterval = 300               -- seconds between price recalc
Config.DemandWindow        = 3600              -- transaction window for S/D calc
Config.DemandSensitivity   = 0.35             -- 0 = static, 1 = very volatile
Config.MeanReversionRate   = 0.08             -- drift back toward base price
Config.MaxSellPerPlayerPerHour = 200          -- anti-manipulation cap
```

---

## Admin commands

| Command | Description |
|---|---|
| `/de_prices` | List all current prices |
| `/de_setprice <item> <price>` | Force a price (clamped to min/max) |
| `/de_resetprice <item>` | Reset item to base price |
| `/de_crash` | Manually trigger a market crash |

Admin access requires either the `dynamic_economy.admin` ace permission  
or a QBCore group listed in `Config.AdminGroups`.

---

## Price formula

```
net   = demand_qty - supply_qty  (last DemandWindow seconds)
ratio = clamp(net / (supply + demand + 1), -1, 1)
new   = current × (1 + DemandSensitivity × ratio)
new   = new + (basePrice - new) × MeanReversionRate   ← mean reversion
new   = clamp(new, minPrice, maxPrice)
```

---

## Security model

- **All** price reads and writes happen server-side.
- The client sends only `item` + `qty`; the server validates inventory, limits, and calculates payment.
- `RegisterNUICallback` handlers on the client only forward sanitised strings/numbers.
- SQL queries use parameterised statements (oxmysql prevents injection).

---

## Database tables

| Table | Purpose |
|---|---|
| `de_prices` | Current live price per item |
| `de_transactions` | Full audit log of every buy/sell |
| `de_price_history` | Periodic price snapshots (24h graph, 7-day retention) |

---

## License

See `LICENSE` file. Not for redistribution without permission.
