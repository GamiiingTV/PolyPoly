--[[
    dynamic-economy — server/debug.lua
    Debug mode, conflict detection, and test suite.
    Loaded BEFORE server.lua so helpers are available immediately.
--]]

-- ─── Debug logger ─────────────────────────────────────────────────────────────
-- Usage: DELog('category', 'message', optionalData)
function DELog(category, msg, data)
    if not Config.Debug.enabled then return end

    local level = Config.Debug.levels[category]
    if level == nil then level = true end
    if not level then return end

    local prefix = '^5[DE:' .. string.upper(category) .. ']^0 '
    if data ~= nil then
        local ok, encoded = pcall(json.encode, data)
        print(prefix .. msg .. ' | ' .. (ok and encoded or tostring(data)))
    else
        print(prefix .. msg)
    end
end

-- Always-on info (ignores debug flag, used for startup banner)
function DEInfo(msg)  print('^2[dynamic-economy]^0 ' .. msg) end
function DEWarn(msg)  print('^3[dynamic-economy]^0 WARNING: ' .. msg) end
function DEError(msg) print('^1[dynamic-economy]^0 ERROR: ' .. msg) end

-- ─── Known resources catalog ──────────────────────────────────────────────────
-- Each entry: { name, severity ('error'|'warn'|'info'), reason }
local KNOWN_CONFLICTS = {

    -- ── Inventory systems ─────────────────────────────────────────────────
    -- These are fine to run alongside dynamic-economy, but the inventory
    -- exports differ. Warn if the configured framework doesn't match.
    { name = 'ox_inventory',      severity = 'warn',
      reason = 'ox_inventory uses its own item system. Verify RemovePlayerItem / AddItem calls in server.lua match ox_inventory exports if you use it.' },

    { name = 'qs-inventory',      severity = 'warn',
      reason = 'Quasar Inventory detected. Item add/remove exports differ from default QBCore/ESX — check bridge compatibility.' },

    { name = 'ps-inventory',      severity = 'warn',
      reason = 'PS-Inventory detected. Same exports as QBCore but some versions handle metadata differently.' },

    { name = 'lj-inventory',      severity = 'warn',
      reason = 'LJ-Inventory detected. Uses QBCore-style exports but may fire extra events on item changes.' },

    { name = 'tgiann-inventory',  severity = 'warn',
      reason = 'Tgiann Inventory detected. Verify item exports are compatible.' },

    { name = 'codem-inventory',   severity = 'warn',
      reason = 'CodeM Inventory detected. Verify item exports are compatible.' },

    -- ── Other economy / shop resources ────────────────────────────────────
    { name = 'esx_shops',         severity = 'info',
      reason = 'ESX Shops runs fixed prices. dynamic-economy prices won\'t affect esx_shops unless you integrate them manually.' },

    { name = 'qb-shops',          severity = 'info',
      reason = 'QB-Shops runs fixed prices. Same note as esx_shops.' },

    { name = 'esx_blackmarket',   severity = 'warn',
      reason = 'ESX Blackmarket has its own static prices. Consider disabling it to avoid price confusion with dynamic-economy drugs.' },

    { name = 'qb-drugs',          severity = 'info',
      reason = 'QB-Drugs detected. Drug sell prices in qb-drugs are static — players may prefer selling there. Consider removing static sell points or hooking dynamic-economy prices into qb-drugs.' },

    { name = 'ps-drugs',          severity = 'info',
      reason = 'PS-Drugs detected. Same as qb-drugs note.' },

    { name = 'mk_laundering',     severity = 'info',
      reason = 'MK Laundering detected. Money laundering bypasses the economy loop — inflation detection may be affected if laundered money is not tracked.' },

    -- ── Banking / money resources ─────────────────────────────────────────
    { name = 'Renewed-Banking',   severity = 'info',
      reason = 'Renewed-Banking detected. Bank balance is separate from cash. dynamic-economy currently pays in cash — verify this suits your server.' },

    { name = 'okokBanking',       severity = 'info',
      reason = 'okokBanking detected. Same note as Renewed-Banking.' },

    { name = 'qb-banking',        severity = 'info',
      reason = 'QB-Banking detected. Ensure inflation query sums both cash and bank columns if needed.' },

    -- ── Other dynamic economy mods (hard conflict) ────────────────────────
    { name = 'esx_economy',       severity = 'error',
      reason = 'ESX Economy modifies global item prices. Running both WILL cause price conflicts. Disable esx_economy.' },

    { name = 'brutal_economy',    severity = 'error',
      reason = 'Brutal Economy is another dynamic price system. Running both simultaneously WILL conflict. Choose one.' },

    { name = 'economy_system',    severity = 'error',
      reason = 'Another economy_system resource detected — likely conflicts with dynamic-economy price tables.' },

    -- ── Framework mismatches ──────────────────────────────────────────────
    -- Handled separately in CheckFrameworkMismatch()
}

-- ─── Conflict scanner ─────────────────────────────────────────────────────────
local conflictReport = { errors = {}, warnings = {}, infos = {} }

function RunConflictCheck()
    DEInfo('Running conflict & compatibility check…')

    for _, entry in ipairs(KNOWN_CONFLICTS) do
        local state = GetResourceState(entry.name)
        if state == 'started' or state == 'starting' then
            local line = string.format('[%s] %s — %s', string.upper(entry.severity), entry.name, entry.reason)
            if entry.severity == 'error' then
                DEError('CONFLICT: ' .. entry.name .. ' — ' .. entry.reason)
                conflictReport.errors[#conflictReport.errors + 1] = entry.name .. ': ' .. entry.reason
            elseif entry.severity == 'warn' then
                DEWarn('COMPAT: ' .. entry.name .. ' — ' .. entry.reason)
                conflictReport.warnings[#conflictReport.warnings + 1] = entry.name .. ': ' .. entry.reason
            else
                DEInfo('INFO: ' .. entry.name .. ' running — ' .. entry.reason)
                conflictReport.infos[#conflictReport.infos + 1] = entry.name .. ': ' .. entry.reason
            end
        end
    end

    CheckFrameworkMismatch()
    CheckDependencies()
    PrintConflictSummary()
end

function CheckFrameworkMismatch()
    local fw = Config.Framework

    if fw == 'qbcore' then
        if GetResourceState('qb-core') ~= 'started' then
            DEError('Config.Framework = "qbcore" but qb-core is NOT running!')
            conflictReport.errors[#conflictReport.errors + 1] = 'qb-core not started but configured as framework'
        end
        if GetResourceState('es_extended') == 'started' then
            DEWarn('es_extended is running but Config.Framework = "qbcore". If you use ESX, change the config.')
            conflictReport.warnings[#conflictReport.warnings + 1] = 'es_extended running alongside qbcore config'
        end

    elseif fw == 'esx' then
        if GetResourceState('es_extended') ~= 'started' then
            DEError('Config.Framework = "esx" but es_extended is NOT running!')
            conflictReport.errors[#conflictReport.errors + 1] = 'es_extended not started but configured as framework'
        end
        if GetResourceState('qb-core') == 'started' then
            DEWarn('qb-core is running but Config.Framework = "esx". If you use QBCore, change the config.')
            conflictReport.warnings[#conflictReport.warnings + 1] = 'qb-core running alongside esx config'
        end
    else
        DEError('Config.Framework = "' .. tostring(fw) .. '" — invalid value. Use "qbcore" or "esx".')
        conflictReport.errors[#conflictReport.errors + 1] = 'Invalid Config.Framework value: ' .. tostring(fw)
    end
end

function CheckDependencies()
    -- oxmysql
    if GetResourceState('oxmysql') ~= 'started' then
        DEError('oxmysql is NOT running! dynamic-economy requires oxmysql.')
        conflictReport.errors[#conflictReport.errors + 1] = 'oxmysql not started'
    end

    -- Discord webhook sanity
    if Config.Discord.enabled then
        if Config.Discord.webhook == '' or Config.Discord.webhook:find('VOTRE_WEBHOOK') then
            DEWarn('Discord is enabled but webhook URL is not configured (still placeholder).')
            conflictReport.warnings[#conflictReport.warnings + 1] = 'Discord webhook URL not set'
        end
    end

    -- Sell cap sanity
    if Config.MaxSellPerPlayerPerHour < 1 then
        DEWarn('MaxSellPerPlayerPerHour is < 1 — no player will be able to sell anything!')
        conflictReport.warnings[#conflictReport.warnings + 1] = 'MaxSellPerPlayerPerHour = ' .. Config.MaxSellPerPlayerPerHour
    end

    -- Price sanity per item
    for item, cfg in pairs(Config.Items) do
        if cfg.minPrice >= cfg.maxPrice then
            DEError('Item "' .. item .. '": minPrice (' .. cfg.minPrice .. ') >= maxPrice (' .. cfg.maxPrice .. ')')
            conflictReport.errors[#conflictReport.errors + 1] = 'Item ' .. item .. ': minPrice >= maxPrice'
        end
        if cfg.basePrice < cfg.minPrice or cfg.basePrice > cfg.maxPrice then
            DEWarn('Item "' .. item .. '": basePrice (' .. cfg.basePrice .. ') is outside [minPrice, maxPrice]')
            conflictReport.warnings[#conflictReport.warnings + 1] = 'Item ' .. item .. ': basePrice out of range'
        end
    end
end

function PrintConflictSummary()
    local e = #conflictReport.errors
    local w = #conflictReport.warnings
    local i = #conflictReport.infos

    if e > 0 then
        DEError(string.format('Conflict check: ^1%d error(s)^0, ^3%d warning(s)^0, %d info(s)', e, w, i))
        DEError('Fix errors above before using dynamic-economy in production!')
    elseif w > 0 then
        DEWarn(string.format('Conflict check: 0 errors, ^3%d warning(s)^0, %d info(s) — review warnings above.', w, i))
    else
        DEInfo(string.format('Conflict check: clean — 0 errors, 0 warnings, %d info note(s).', i))
    end
end

-- Expose report for /de_conflicts command (defined in server.lua)
function GetConflictReport() return conflictReport end

-- ─── Test suite ───────────────────────────────────────────────────────────────
-- /de_test runs all checks and prints a pass/fail report
function RunTestSuite(src)
    local results = {}
    local pass = 0
    local fail = 0

    local function test(name, fn)
        local ok, err = pcall(fn)
        if ok then
            results[#results + 1] = { name = name, ok = true }
            pass = pass + 1
        else
            results[#results + 1] = { name = name, ok = false, err = tostring(err) }
            fail = fail + 1
        end
    end

    -- 1. Config loaded
    test('Config table exists', function()
        assert(type(Config) == 'table', 'Config is nil')
        assert(type(Config.Items) == 'table', 'Config.Items is nil')
    end)

    -- 2. Item catalogue not empty
    test('Items catalogue populated', function()
        local n = 0
        for _ in pairs(Config.Items) do n = n + 1 end
        assert(n > 0, 'No items defined in Config.Items')
    end)

    -- 3. Price cache loaded
    test('Price cache populated', function()
        local n = 0
        for _ in pairs(priceCache) do n = n + 1 end
        assert(n > 0, 'priceCache is empty — was LoadPricesFromDB called?')
    end)

    -- 4. Every configured item has a cached price
    test('All items have a cached price', function()
        for item in pairs(Config.Items) do
            assert(priceCache[item] ~= nil, 'Missing cache entry for item: ' .. item)
        end
    end)

    -- 5. Price clamp logic
    test('Clamp function correctness', function()
        assert(Clamp(50, 100, 200)  == 100, 'Clamp below min failed')
        assert(Clamp(500, 100, 200) == 200, 'Clamp above max failed')
        assert(Clamp(150, 100, 200) == 150, 'Clamp within range failed')
    end)

    -- 6. Price formula (zero supply & demand → mean reversion only)
    test('CalculateNewPrice (zero activity → mean revert)', function()
        -- With empty history, formula should drift toward basePrice
        local item = next(Config.Items)
        local cfg  = Config.Items[item]
        -- Force cache to maxPrice then recalculate
        local savedCache = priceCache[item]
        local savedHistory = sellHistory[item]
        priceCache[item]  = cfg.maxPrice
        sellHistory[item] = {}
        local result = CalculateNewPrice(item, cfg.maxPrice)
        priceCache[item]  = savedCache
        sellHistory[item] = savedHistory
        assert(result < cfg.maxPrice, 'Mean reversion did not pull price down from max')
        assert(result >= cfg.minPrice and result <= cfg.maxPrice, 'Price out of bounds after reversion')
    end)

    -- 7. Database connectivity — prices table
    test('DB: prices table readable', function()
        local rows = MySQL.query.await('SELECT COUNT(*) as cnt FROM `' .. Config.DB.prices_table .. '`')
        assert(rows and rows[1], 'Could not query prices table')
    end)

    -- 8. Database connectivity — transactions table
    test('DB: transactions table readable', function()
        local rows = MySQL.query.await('SELECT COUNT(*) as cnt FROM `' .. Config.DB.transactions_table .. '`')
        assert(rows and rows[1], 'Could not query transactions table')
    end)

    -- 9. Database connectivity — history table
    test('DB: history table readable', function()
        local rows = MySQL.query.await('SELECT COUNT(*) as cnt FROM `' .. Config.DB.history_table .. '`')
        assert(rows and rows[1], 'Could not query history table')
    end)

    -- 10. Framework resource running
    test('Framework resource is started', function()
        if Config.Framework == 'qbcore' then
            assert(GetResourceState('qb-core') == 'started', 'qb-core not started')
        elseif Config.Framework == 'esx' then
            assert(GetResourceState('es_extended') == 'started', 'es_extended not started')
        else
            error('Unknown framework: ' .. tostring(Config.Framework))
        end
    end)

    -- 11. oxmysql running
    test('oxmysql is started', function()
        assert(GetResourceState('oxmysql') == 'started', 'oxmysql not started')
    end)

    -- 12. Anti-manipulation cap logic
    test('Sell limit: first sale allowed', function()
        local fakeId = 999999
        playerSellCounts[tostring(fakeId)] = nil
        local ok = CheckSellLimit(fakeId, 'weed_brick', 1)
        playerSellCounts[tostring(fakeId)] = nil
        assert(ok, 'First sale should be allowed')
    end)

    test('Sell limit: cap enforced', function()
        local fakeId = 999998
        playerSellCounts[tostring(fakeId)] = nil
        local item = 'weed_brick'
        local cap  = Config.MaxSellPerPlayerPerHour
        -- Fill to cap
        CheckSellLimit(fakeId, item, cap)
        -- One more should be rejected
        local ok = CheckSellLimit(fakeId, item, 1)
        playerSellCounts[tostring(fakeId)] = nil
        assert(not ok, 'Sell limit should have been enforced')
    end)

    -- 13. Market crash flag
    test('Market crash: crashActive starts false', function()
        assert(crashActive == false, 'crashActive should be false on clean start')
    end)

    -- 14. Discord webhook config
    test('Discord: webhook configured (if enabled)', function()
        if Config.Discord.enabled then
            assert(Config.Discord.webhook ~= '', 'Discord enabled but webhook is empty')
        end
    end)

    -- 15. Item price bounds in config
    test('Config: all items have valid price bounds', function()
        for item, cfg in pairs(Config.Items) do
            assert(cfg.minPrice < cfg.maxPrice,
                'Item ' .. item .. ': minPrice >= maxPrice')
            assert(type(cfg.basePrice) == 'number',
                'Item ' .. item .. ': basePrice is not a number')
        end
    end)

    -- ── Print results ─────────────────────────────────────────────────────
    local lines = {
        '═══════════════════════════════════════',
        ' dynamic-economy TEST SUITE RESULTS',
        '═══════════════════════════════════════',
    }

    for _, r in ipairs(results) do
        if r.ok then
            lines[#lines + 1] = '^2 ✓^0 ' .. r.name
        else
            lines[#lines + 1] = '^1 ✗^0 ' .. r.name
            lines[#lines + 1] = '^1   → ' .. (r.err or '?') .. '^0'
        end
    end

    lines[#lines + 1] = '───────────────────────────────────────'
    local summary = string.format(' Passed: %d / %d', pass, pass + fail)
    if fail == 0 then
        lines[#lines + 1] = '^2' .. summary .. ' — ALL PASS^0'
    else
        lines[#lines + 1] = '^1' .. summary .. ' — ' .. fail .. ' FAILED^0'
    end
    lines[#lines + 1] = '═══════════════════════════════════════'

    for _, line in ipairs(lines) do
        if src == 0 then
            print(line)
        else
            TriggerClientEvent('chat:addMessage', src, { args = { line } })
        end
    end

    -- Also send to Discord if enabled and we have errors
    if fail > 0 and Config.Discord.enabled then
        SendDiscordRaw(string.format('⚠️ **[TEST SUITE]** %d/%d tests passed — %d failed. Check server console.',
            pass, pass + fail, fail))
    end
end
