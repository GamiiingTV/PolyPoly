--[[
    dynamic-economy — config.lua
    All tunable values live here. Never touch server.lua / client.lua for tweaks.
--]]

Config = {}

-- ─── Framework ────────────────────────────────────────────────────────────────
-- 'qbcore' | 'esx'
Config.Framework = 'qbcore'

-- ─── Database ─────────────────────────────────────────────────────────────────
-- Table names created automatically on first run
Config.DB = {
    prices_table       = 'de_prices',
    transactions_table = 'de_transactions',
    history_table      = 'de_price_history',
}

-- ─── Economy Engine ───────────────────────────────────────────────────────────
-- How often prices are recalculated (seconds)
Config.FluctuationInterval = 300          -- 5 minutes

-- Window of transactions that influence the current price (seconds)
Config.DemandWindow = 3600                -- last 1 hour

-- How aggressively demand shifts the price (0.0 = no effect, 1.0 = very volatile)
Config.DemandSensitivity = 0.35

-- Passive price drift back toward BasePrice each cycle (0.0–1.0)
Config.MeanReversionRate = 0.08

-- Anti-manipulation: max units a single player may sell per item per hour
Config.MaxSellPerPlayerPerHour = 200

-- ─── Inflation System ─────────────────────────────────────────────────────────
Config.Inflation = {
    enabled         = true,
    -- Total server money threshold that triggers inflation (example: 50 million)
    threshold       = 50000000,
    -- Price multiplier applied globally when threshold is exceeded (e.g. 1.02 = +2%)
    multiplier      = 1.02,
    -- Check interval (seconds)
    checkInterval   = 600,
}

-- ─── Market Crash Event ───────────────────────────────────────────────────────
Config.MarketCrash = {
    enabled         = true,
    -- Probability per fluctuation cycle that a crash fires (0.0–1.0)
    chance          = 0.02,             -- 2 % per cycle ≈ rare
    -- Price multiplier during crash (e.g. 0.4 = prices drop to 40 %)
    multiplier      = 0.40,
    -- Duration the crash prices stay active (seconds) before recovering
    duration        = 180,
    -- Announce crash to all players
    notifyPlayers   = true,
    notifyMessage   = '[MARCHÉ] CRASH BOURSIER ! Les prix s\'effondrent pendant 3 minutes !',
}

-- ─── Discord Webhooks ─────────────────────────────────────────────────────────
Config.Discord = {
    enabled         = true,
    webhook         = 'https://discord.com/api/webhooks/VOTRE_WEBHOOK_ICI',
    -- Thresholds: alert when a price moves by this % in one cycle
    alertThreshold  = 0.30,             -- 30 % swing triggers an alert
    username        = 'Dynamic Economy',
    avatarUrl       = '',
}

-- ─── Admin ────────────────────────────────────────────────────────────────────
Config.AdminGroups = { 'admin', 'superadmin', 'god' }   -- QBCore job groups
Config.AdminAcePerm = 'dynamic_economy.admin'            -- ESX / vanilla ace

-- ─── NUI ──────────────────────────────────────────────────────────────────────
Config.NUI = {
    -- Keybind to open the market terminal (client-side)
    openKey = 'F7',
    -- How many hours of price history to display in the graph
    historyHours = 24,
}

-- ─── Price Cache ──────────────────────────────────────────────────────────────
-- RAM cache is refreshed every fluctuation cycle; reduces SQL load dramatically
Config.CacheEnabled = true

-- ─── OneSync / Large Servers ──────────────────────────────────────────────────
-- No extra config needed — all logic runs server-side, OneSync-compatible

-- ─────────────────────────────────────────────────────────────────────────────
--  ITEM CATALOGUE
--  Each entry defines one tradable item.
--
--  Fields:
--    label      – Display name in the NUI
--    basePrice  – Equilibrium price (both buy and sell use this as anchor)
--    minPrice   – Hard floor — price can never go below this
--    maxPrice   – Hard ceiling — price can never exceed this
--    category   – Used for grouping in the NUI ('drugs','legal','resources','crafting')
--    unit       – Unit label shown in NUI ('kg','g','unit','L', …)
-- ─────────────────────────────────────────────────────────────────────────────
Config.Items = {

    -- ── Drugs (black market) ──────────────────────────────────────────────
    ['weed_brick'] = {
        label     = 'Brique de Weed',
        basePrice = 800,
        minPrice  = 200,
        maxPrice  = 2500,
        category  = 'drugs',
        unit      = 'kg',
    },
    ['cocaine_brick'] = {
        label     = 'Brique de Cocaïne',
        basePrice = 2000,
        minPrice  = 500,
        maxPrice  = 6000,
        category  = 'drugs',
        unit      = 'kg',
    },
    ['meth_gram'] = {
        label     = 'Méthamphétamine',
        basePrice = 350,
        minPrice  = 80,
        maxPrice  = 1200,
        category  = 'drugs',
        unit      = 'g',
    },
    ['heroin_gram'] = {
        label     = 'Héroïne',
        basePrice = 600,
        minPrice  = 150,
        maxPrice  = 1800,
        category  = 'drugs',
        unit      = 'g',
    },

    -- ── Legal shops ───────────────────────────────────────────────────────
    ['bread'] = {
        label     = 'Pain',
        basePrice = 3,
        minPrice  = 1,
        maxPrice  = 15,
        category  = 'legal',
        unit      = 'unit',
    },
    ['water'] = {
        label     = 'Eau (bouteille)',
        basePrice = 2,
        minPrice  = 1,
        maxPrice  = 10,
        category  = 'legal',
        unit      = 'unit',
    },
    ['bandage'] = {
        label     = 'Bandage',
        basePrice = 12,
        minPrice  = 5,
        maxPrice  = 60,
        category  = 'legal',
        unit      = 'unit',
    },

    -- ── Resources ─────────────────────────────────────────────────────────
    ['iron_ore'] = {
        label     = 'Minerai de Fer',
        basePrice = 25,
        minPrice  = 5,
        maxPrice  = 150,
        category  = 'resources',
        unit      = 'kg',
    },
    ['wood_plank'] = {
        label     = 'Planche de Bois',
        basePrice = 15,
        minPrice  = 3,
        maxPrice  = 80,
        category  = 'resources',
        unit      = 'unit',
    },
    ['gold_ore'] = {
        label     = 'Minerai d\'Or',
        basePrice = 200,
        minPrice  = 50,
        maxPrice  = 800,
        category  = 'resources',
        unit      = 'kg',
    },
    ['diamond'] = {
        label     = 'Diamant',
        basePrice = 1200,
        minPrice  = 300,
        maxPrice  = 4000,
        category  = 'resources',
        unit      = 'unit',
    },

    -- ── Crafting materials ────────────────────────────────────────────────
    ['steel_bar'] = {
        label     = 'Barre d\'Acier',
        basePrice = 80,
        minPrice  = 20,
        maxPrice  = 350,
        category  = 'crafting',
        unit      = 'unit',
    },
    ['electronic_part'] = {
        label     = 'Composant Électronique',
        basePrice = 150,
        minPrice  = 40,
        maxPrice  = 600,
        category  = 'crafting',
        unit      = 'unit',
    },
    ['gun_part'] = {
        label     = 'Pièce d\'Arme',
        basePrice = 400,
        minPrice  = 100,
        maxPrice  = 1500,
        category  = 'crafting',
        unit      = 'unit',
    },
}
