--[[
    dynamic-economy — server/server.lua
    ALL economy logic runs here. Client is display-only.
    Never trust client-side events for monetary values.
--]]

-- ─── State ────────────────────────────────────────────────────────────────────
local priceCache       = {}   -- { [item] = currentPrice }
local sellHistory      = {}   -- { [item] = { { playerId, qty, timestamp }, … } }
local playerSellCounts = {}   -- { [playerId] = { [item] = { qty, resetAt } } }
local crashActive      = false

-- ─── Bootstrap ────────────────────────────────────────────────────────────────
CreateThread(function()
    Wait(2000)  -- give oxmysql time to connect
    EnsureTables()
    LoadPricesFromDB()
    StartFluctuationLoop()
    if Config.Inflation.enabled then StartInflationLoop() end
    print('^2[dynamic-economy]^0 Loaded — ' .. tableLength(Config.Items) .. ' items tracked.')
end)

-- ─── Database setup ───────────────────────────────────────────────────────────
function EnsureTables()
    MySQL.query.await([[
        CREATE TABLE IF NOT EXISTS `]] .. Config.DB.prices_table .. [[` (
            `item`        VARCHAR(64)    NOT NULL PRIMARY KEY,
            `price`       DECIMAL(12,2)  NOT NULL,
            `updated_at`  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ]])

    MySQL.query.await([[
        CREATE TABLE IF NOT EXISTS `]] .. Config.DB.transactions_table .. [[` (
            `id`          BIGINT         UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            `player_id`   VARCHAR(64)    NOT NULL,
            `item`        VARCHAR(64)    NOT NULL,
            `qty`         INT            NOT NULL,
            `price`       DECIMAL(12,2)  NOT NULL,
            `total`       DECIMAL(14,2)  NOT NULL,
            `type`        ENUM('sell','buy') NOT NULL,
            `created_at`  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_item_time (`item`, `created_at`),
            INDEX idx_player    (`player_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ]])

    MySQL.query.await([[
        CREATE TABLE IF NOT EXISTS `]] .. Config.DB.history_table .. [[` (
            `id`          BIGINT         UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            `item`        VARCHAR(64)    NOT NULL,
            `price`       DECIMAL(12,2)  NOT NULL,
            `recorded_at` TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_item_time (`item`, `recorded_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ]])
end

-- ─── Load prices from DB (fallback to base on first run) ─────────────────────
function LoadPricesFromDB()
    local rows = MySQL.query.await('SELECT item, price FROM `' .. Config.DB.prices_table .. '`')
    local dbMap = {}
    for _, row in ipairs(rows) do dbMap[row.item] = tonumber(row.price) end

    for item, cfg in pairs(Config.Items) do
        local p = dbMap[item] or cfg.basePrice
        priceCache[item] = Clamp(p, cfg.minPrice, cfg.maxPrice)
        sellHistory[item] = {}
    end
end

-- ─── Price formula ────────────────────────────────────────────────────────────
--  supply  = units sold in the demand window
--  demand  = units bought in the demand window
--  net     = demand - supply   (positive → price rises, negative → price falls)
--  ratio   = net / (supply + demand + 1)  bounded to [-1, 1]
--  newPrice = currentPrice * (1 + sensitivity * ratio) then mean-reverts toward base
function CalculateNewPrice(item, currentPrice)
    if crashActive then
        return Clamp(
            Config.Items[item].basePrice * Config.MarketCrash.multiplier,
            Config.Items[item].minPrice,
            Config.Items[item].maxPrice
        )
    end

    local now     = os.time()
    local cutoff  = now - Config.DemandWindow
    local supply  = 0
    local demand  = 0

    for _, tx in ipairs(sellHistory[item] or {}) do
        if tx.ts >= cutoff then
            if tx.txType == 'sell' then supply = supply + tx.qty
            else demand = demand + tx.qty end
        end
    end

    local net   = demand - supply
    local denom = supply + demand + 1
    local ratio = math.max(-1.0, math.min(1.0, net / denom))

    local adjusted = currentPrice * (1.0 + Config.DemandSensitivity * ratio)

    -- mean reversion toward base price
    local base = Config.Items[item].basePrice
    adjusted = adjusted + (base - adjusted) * Config.MeanReversionRate

    return Clamp(adjusted, Config.Items[item].minPrice, Config.Items[item].maxPrice)
end

-- ─── Fluctuation loop ─────────────────────────────────────────────────────────
function StartFluctuationLoop()
    CreateThread(function()
        while true do
            Wait(Config.FluctuationInterval * 1000)

            -- Possible market crash
            if Config.MarketCrash.enabled and not crashActive then
                if math.random() < Config.MarketCrash.chance then
                    TriggerMarketCrash()
                end
            end

            local snapshots = {}

            for item, currentPrice in pairs(priceCache) do
                local oldPrice = currentPrice
                local newPrice = CalculateNewPrice(item, currentPrice)
                priceCache[item] = newPrice
                snapshots[#snapshots + 1] = { item = item, price = newPrice }

                -- Discord alert on large swings
                local swing = math.abs(newPrice - oldPrice) / (oldPrice + 1)
                if Config.Discord.enabled and swing >= Config.Discord.alertThreshold then
                    SendDiscordAlert(item, oldPrice, newPrice, swing)
                end
            end

            -- Persist prices and snapshot history async
            PersistPrices(snapshots)
            SnapshotHistory(snapshots)

            -- Purge old sell history entries to keep RAM lean
            PurgeSellHistory()

            -- Broadcast updated prices to all clients
            TriggerClientEvent('dynamic-economy:pricesUpdated', -1, priceCache)
        end
    end)
end

-- ─── Market crash ─────────────────────────────────────────────────────────────
function TriggerMarketCrash()
    crashActive = true
    print('^1[dynamic-economy]^0 MARKET CRASH triggered!')

    if Config.MarketCrash.notifyPlayers then
        TriggerClientEvent('dynamic-economy:notify', -1, Config.MarketCrash.notifyMessage, 'error')
    end

    if Config.Discord.enabled then
        SendDiscordRaw('🔴 **CRASH BOURSIER** déclenché ! Tous les prix plongent pendant ' .. Config.MarketCrash.duration .. 's.')
    end

    -- Rebroadcast crash prices immediately
    local snapshot = {}
    for item, cfg in pairs(Config.Items) do
        local crashPrice = Clamp(cfg.basePrice * Config.MarketCrash.multiplier, cfg.minPrice, cfg.maxPrice)
        priceCache[item] = crashPrice
        snapshot[#snapshot + 1] = { item = item, price = crashPrice }
    end
    TriggerClientEvent('dynamic-economy:pricesUpdated', -1, priceCache)

    SetTimeout(Config.MarketCrash.duration * 1000, function()
        crashActive = false
        if Config.MarketCrash.notifyPlayers then
            TriggerClientEvent('dynamic-economy:notify', -1, '[MARCHÉ] Les marchés se stabilisent.', 'success')
        end
        print('^2[dynamic-economy]^0 Market crash ended, prices recovering.')
    end)
end

-- ─── Inflation loop ───────────────────────────────────────────────────────────
function StartInflationLoop()
    CreateThread(function()
        while true do
            Wait(Config.Inflation.checkInterval * 1000)

            local totalMoney = GetServerTotalMoney()
            if totalMoney and totalMoney > Config.Inflation.threshold then
                local m = Config.Inflation.multiplier
                local applied = {}
                for item, price in pairs(priceCache) do
                    local cfg = Config.Items[item]
                    priceCache[item] = Clamp(price * m, cfg.minPrice, cfg.maxPrice)
                    applied[#applied + 1] = { item = item, price = priceCache[item] }
                end
                PersistPrices(applied)
                TriggerClientEvent('dynamic-economy:pricesUpdated', -1, priceCache)
                print('^3[dynamic-economy]^0 Inflation applied (x' .. m .. '). Server money: $' .. totalMoney)
            end
        end
    end)
end

-- ─── Framework bridge: get total server money ─────────────────────────────────
function GetServerTotalMoney()
    if Config.Framework == 'qbcore' then
        local result = MySQL.scalar.await('SELECT SUM(money) FROM players')
        return tonumber(result) or 0
    elseif Config.Framework == 'esx' then
        local result = MySQL.scalar.await("SELECT SUM(money) FROM users")
        return tonumber(result) or 0
    end
    return 0
end

-- ─── Framework bridge: pay player ────────────────────────────────────────────
function PayPlayer(playerId, amount)
    if Config.Framework == 'qbcore' then
        local QBCore = exports['qb-core']:GetCoreObject()
        local Player = QBCore.Functions.GetPlayer(playerId)
        if Player then
            Player.Functions.AddMoney('cash', math.floor(amount), 'dynamic-economy sell')
            return true
        end
    elseif Config.Framework == 'esx' then
        local xPlayer = exports['es_extended']:getSharedObject().GetPlayerFromId(playerId)
        if xPlayer then
            xPlayer.addMoney(math.floor(amount))
            return true
        end
    end
    return false
end

-- ─── Framework bridge: check player has item ─────────────────────────────────
function PlayerHasItem(playerId, item, qty)
    if Config.Framework == 'qbcore' then
        local QBCore = exports['qb-core']:GetCoreObject()
        local Player = QBCore.Functions.GetPlayer(playerId)
        if not Player then return false end
        local inv = Player.Functions.GetItemByName(item)
        return inv and inv.amount >= qty
    elseif Config.Framework == 'esx' then
        local xPlayer = exports['es_extended']:getSharedObject().GetPlayerFromId(playerId)
        if not xPlayer then return false end
        local count = xPlayer.getInventoryItem(item).count
        return count >= qty
    end
    return false
end

-- ─── Framework bridge: remove item from player ───────────────────────────────
function RemovePlayerItem(playerId, item, qty)
    if Config.Framework == 'qbcore' then
        local QBCore = exports['qb-core']:GetCoreObject()
        local Player = QBCore.Functions.GetPlayer(playerId)
        if Player then Player.Functions.RemoveItem(item, qty) end
    elseif Config.Framework == 'esx' then
        local xPlayer = exports['es_extended']:getSharedObject().GetPlayerFromId(playerId)
        if xPlayer then xPlayer.removeInventoryItem(item, qty) end
    end
end

-- ─── Anti-manipulation: hourly sell cap per player ───────────────────────────
function CheckSellLimit(playerId, item, qty)
    local pid = tostring(playerId)
    playerSellCounts[pid] = playerSellCounts[pid] or {}
    local entry = playerSellCounts[pid][item]
    local now   = os.time()

    if not entry or now > entry.resetAt then
        playerSellCounts[pid][item] = { qty = qty, resetAt = now + 3600 }
        return true
    end

    if entry.qty + qty > Config.MaxSellPerPlayerPerHour then
        return false
    end

    entry.qty = entry.qty + qty
    return true
end

-- ─── Core sell event (server-side validation only) ───────────────────────────
RegisterNetEvent('dynamic-economy:sellItem', function(item, qty)
    local src = source

    -- Basic input sanity
    if type(item) ~= 'string' or type(qty) ~= 'number' then return end
    qty = math.floor(qty)
    if qty <= 0 or qty > 9999 then return end

    local cfg = Config.Items[item]
    if not cfg then
        TriggerClientEvent('dynamic-economy:notify', src, 'Item inconnu.', 'error')
        return
    end

    -- Anti-manipulation cap
    if not CheckSellLimit(src, item, qty) then
        TriggerClientEvent('dynamic-economy:notify', src,
            'Limite de vente horaire atteinte pour ' .. cfg.label .. '.', 'error')
        return
    end

    -- Inventory check
    if not PlayerHasItem(src, item, qty) then
        TriggerClientEvent('dynamic-economy:notify', src, 'Inventaire insuffisant.', 'error')
        return
    end

    local price = priceCache[item] or cfg.basePrice
    local total = math.floor(price * qty)

    -- Atomic: remove items THEN pay
    RemovePlayerItem(src, item, qty)
    local paid = PayPlayer(src, total)

    if not paid then
        print('^1[dynamic-economy]^0 ERROR: PayPlayer failed for ' .. src)
        return
    end

    -- Record in history for price calculation
    sellHistory[item] = sellHistory[item] or {}
    sellHistory[item][#sellHistory[item] + 1] = { ts = os.time(), qty = qty, txType = 'sell' }

    -- Persist transaction log
    MySQL.insert.await(
        'INSERT INTO `' .. Config.DB.transactions_table ..
        '` (player_id, item, qty, price, total, type) VALUES (?, ?, ?, ?, ?, ?)',
        { GetPlayerIdentifier(src, 0) or tostring(src), item, qty, price, total, 'sell' }
    )

    TriggerClientEvent('dynamic-economy:notify', src,
        'Vendu ' .. qty .. 'x ' .. cfg.label .. ' pour $' .. total, 'success')

    print(string.format('^2[TX]^0 SELL | player=%s item=%s qty=%d price=%.2f total=%.2f',
        tostring(src), item, qty, price, total))
end)

-- ─── Buy event ────────────────────────────────────────────────────────────────
RegisterNetEvent('dynamic-economy:buyItem', function(item, qty)
    local src = source

    if type(item) ~= 'string' or type(qty) ~= 'number' then return end
    qty = math.floor(qty)
    if qty <= 0 or qty > 9999 then return end

    local cfg = Config.Items[item]
    if not cfg then
        TriggerClientEvent('dynamic-economy:notify', src, 'Item inconnu.', 'error')
        return
    end

    local price = priceCache[item] or cfg.basePrice
    local total = math.floor(price * qty)

    -- Framework: check and deduct money
    local canAfford = false
    if Config.Framework == 'qbcore' then
        local QBCore = exports['qb-core']:GetCoreObject()
        local Player = QBCore.Functions.GetPlayer(src)
        if Player and Player.Functions.GetMoney('cash') >= total then
            Player.Functions.RemoveMoney('cash', total, 'dynamic-economy buy')
            Player.Functions.AddItem(item, qty)
            TriggerClientEvent('inventory:client:ItemBox', src, QBCore.Shared.Items[item], 'add', qty)
            canAfford = true
        end
    elseif Config.Framework == 'esx' then
        local xPlayer = exports['es_extended']:getSharedObject().GetPlayerFromId(src)
        if xPlayer and xPlayer.getMoney() >= total then
            xPlayer.removeMoney(total)
            xPlayer.addInventoryItem(item, qty)
            canAfford = true
        end
    end

    if not canAfford then
        TriggerClientEvent('dynamic-economy:notify', src, 'Fonds insuffisants.', 'error')
        return
    end

    -- Record demand
    sellHistory[item] = sellHistory[item] or {}
    sellHistory[item][#sellHistory[item] + 1] = { ts = os.time(), qty = qty, txType = 'buy' }

    MySQL.insert.await(
        'INSERT INTO `' .. Config.DB.transactions_table ..
        '` (player_id, item, qty, price, total, type) VALUES (?, ?, ?, ?, ?, ?)',
        { GetPlayerIdentifier(src, 0) or tostring(src), item, qty, price, total, 'buy' }
    )

    TriggerClientEvent('dynamic-economy:notify', src,
        'Acheté ' .. qty .. 'x ' .. cfg.label .. ' pour $' .. total, 'success')
end)

-- ─── Client requests current prices (UI open) ────────────────────────────────
RegisterNetEvent('dynamic-economy:requestPrices', function()
    local src = source
    TriggerClientEvent('dynamic-economy:receivePrices', src, priceCache)
end)

-- ─── Client requests 24h price history for a specific item ───────────────────
RegisterNetEvent('dynamic-economy:requestHistory', function(item)
    local src = source
    if type(item) ~= 'string' or not Config.Items[item] then return end

    local hours = Config.NUI.historyHours
    local rows  = MySQL.query.await(
        'SELECT price, recorded_at FROM `' .. Config.DB.history_table ..
        '` WHERE item = ? AND recorded_at >= NOW() - INTERVAL ? HOUR ORDER BY recorded_at ASC',
        { item, hours }
    )
    TriggerClientEvent('dynamic-economy:receiveHistory', src, item, rows)
end)

-- ─── Admin commands ───────────────────────────────────────────────────────────
RegisterCommand('de_resetprice', function(src, args)
    if not IsAdmin(src) then return end
    local item = args[1]
    if not item or not Config.Items[item] then
        ReplyToAdmin(src, 'Usage: /de_resetprice <item>')
        return
    end
    priceCache[item] = Config.Items[item].basePrice
    PersistPrices({{ item = item, price = priceCache[item] }})
    TriggerClientEvent('dynamic-economy:pricesUpdated', -1, priceCache)
    ReplyToAdmin(src, '[DE] Prix de ' .. item .. ' remis à $' .. Config.Items[item].basePrice)
end, false)

RegisterCommand('de_setprice', function(src, args)
    if not IsAdmin(src) then return end
    local item  = args[1]
    local price = tonumber(args[2])
    if not item or not Config.Items[item] or not price then
        ReplyToAdmin(src, 'Usage: /de_setprice <item> <prix>')
        return
    end
    local cfg = Config.Items[item]
    priceCache[item] = Clamp(price, cfg.minPrice, cfg.maxPrice)
    PersistPrices({{ item = item, price = priceCache[item] }})
    TriggerClientEvent('dynamic-economy:pricesUpdated', -1, priceCache)
    ReplyToAdmin(src, '[DE] Prix de ' .. item .. ' forcé à $' .. priceCache[item])
end, false)

RegisterCommand('de_crash', function(src, args)
    if not IsAdmin(src) then return end
    TriggerMarketCrash()
    ReplyToAdmin(src, '[DE] Crash boursier déclenché manuellement.')
end, false)

RegisterCommand('de_prices', function(src, args)
    if not IsAdmin(src) then return end
    for item, price in pairs(priceCache) do
        ReplyToAdmin(src, string.format('  %s = $%.2f', item, price))
    end
end, false)

-- ─── Admin check ─────────────────────────────────────────────────────────────
function IsAdmin(src)
    if src == 0 then return true end  -- server console

    -- Ace permission check (works for both frameworks)
    if IsPlayerAceAllowed(tostring(src), Config.AdminAcePerm) then return true end

    -- QBCore group check
    if Config.Framework == 'qbcore' then
        local QBCore = exports['qb-core']:GetCoreObject()
        local Player = QBCore.Functions.GetPlayer(src)
        if Player then
            local group = Player.PlayerData.group
            for _, g in ipairs(Config.AdminGroups) do
                if group == g then return true end
            end
        end
    end

    return false
end

function ReplyToAdmin(src, msg)
    if src == 0 then
        print(msg)
    else
        TriggerClientEvent('chat:addMessage', src, { args = { msg } })
    end
end

-- ─── DB helpers ───────────────────────────────────────────────────────────────
function PersistPrices(snapshots)
    for _, s in ipairs(snapshots) do
        MySQL.query(
            'INSERT INTO `' .. Config.DB.prices_table ..
            '` (item, price) VALUES (?, ?) ON DUPLICATE KEY UPDATE price = VALUES(price)',
            { s.item, s.price }
        )
    end
end

function SnapshotHistory(snapshots)
    for _, s in ipairs(snapshots) do
        MySQL.insert(
            'INSERT INTO `' .. Config.DB.history_table .. '` (item, price) VALUES (?, ?)',
            { s.item, s.price }
        )
    end
end

function PurgeSellHistory()
    local cutoff = os.time() - Config.DemandWindow
    for item in pairs(sellHistory) do
        local cleaned = {}
        for _, tx in ipairs(sellHistory[item]) do
            if tx.ts >= cutoff then cleaned[#cleaned + 1] = tx end
        end
        sellHistory[item] = cleaned
    end

    -- Purge old history rows from DB (keep only last 7 days)
    MySQL.query("DELETE FROM `" .. Config.DB.history_table .. "` WHERE recorded_at < NOW() - INTERVAL 7 DAY")
end

-- ─── Discord webhook ─────────────────────────────────────────────────────────
function SendDiscordAlert(item, oldPrice, newPrice, swing)
    local direction = newPrice > oldPrice and '📈 HAUSSE' or '📉 BAISSE'
    local msg = string.format(
        '%s **%s** : $%.2f → $%.2f (%+.1f%%)',
        direction,
        Config.Items[item].label,
        oldPrice, newPrice,
        swing * 100 * (newPrice > oldPrice and 1 or -1)
    )
    SendDiscordRaw(msg)
end

function SendDiscordRaw(message)
    if not Config.Discord.enabled or Config.Discord.webhook == '' then return end
    PerformHttpRequest(Config.Discord.webhook, function() end, 'POST',
        json.encode({
            username   = Config.Discord.username,
            avatar_url = Config.Discord.avatarUrl,
            content    = message,
        }),
        { ['Content-Type'] = 'application/json' }
    )
end

-- ─── Utilities ────────────────────────────────────────────────────────────────
function Clamp(v, lo, hi) return math.max(lo, math.min(hi, v)) end

function tableLength(t)
    local n = 0
    for _ in pairs(t) do n = n + 1 end
    return n
end

-- Clean up player sell counts on disconnect
AddEventHandler('playerDropped', function()
    playerSellCounts[tostring(source)] = nil
end)
