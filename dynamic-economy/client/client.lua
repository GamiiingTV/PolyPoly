--[[
    dynamic-economy — client/client.lua
    Display & input only. Zero monetary logic here.
    All economic events are validated server-side.
--]]

local uiOpen = false

-- ─── Open / close NUI ─────────────────────────────────────────────────────────
RegisterCommand('de_market', function()
    ToggleUI()
end, false)

RegisterKeyMapping('de_market', 'Ouvrir le marché dynamique', 'keyboard', Config.NUI.openKey)

function ToggleUI()
    uiOpen = not uiOpen
    SetNuiFocus(uiOpen, uiOpen)
    SendNUIMessage({ action = uiOpen and 'open' or 'close' })

    if uiOpen then
        -- Request fresh price list from server
        TriggerServerEvent('dynamic-economy:requestPrices')
    end
end

-- ─── Receive full price table (on open or after fluctuation) ─────────────────
RegisterNetEvent('dynamic-economy:receivePrices', function(prices)
    SendNUIMessage({ action = 'setPrices', prices = prices, items = Config.Items })
end)

-- ─── Live price update broadcast (after each cycle) ──────────────────────────
RegisterNetEvent('dynamic-economy:pricesUpdated', function(prices)
    if uiOpen then
        SendNUIMessage({ action = 'setPrices', prices = prices, items = Config.Items })
    end
end)

-- ─── Receive price history for graph ─────────────────────────────────────────
RegisterNetEvent('dynamic-economy:receiveHistory', function(item, history)
    SendNUIMessage({ action = 'setHistory', item = item, history = history })
end)

-- ─── Notifications ────────────────────────────────────────────────────────────
RegisterNetEvent('dynamic-economy:notify', function(message, notifType)
    -- Forward to framework notification system if available, else fallback
    if Config.Framework == 'qbcore' then
        local QBCore = exports['qb-core']:GetCoreObject()
        QBCore.Functions.Notify(message, notifType or 'primary', 5000)
    elseif Config.Framework == 'esx' then
        exports['es_extended']:getSharedObject().ShowNotification(message)
    else
        -- Vanilla fallback
        BeginTextCommandThefeedPost('STRING')
        AddTextComponentSubstringPlayerName(message)
        EndTextCommandThefeedPostTicker(false, true)
    end
end)

-- ─── NUI Callbacks ────────────────────────────────────────────────────────────

-- Player pressed "Sell" in the UI
RegisterNUICallback('sell', function(data, cb)
    local item = data.item
    local qty  = tonumber(data.qty)

    if not item or not qty or qty <= 0 then
        cb({ ok = false })
        return
    end

    TriggerServerEvent('dynamic-economy:sellItem', item, qty)
    cb({ ok = true })
end)

-- Player pressed "Buy" in the UI
RegisterNUICallback('buy', function(data, cb)
    local item = data.item
    local qty  = tonumber(data.qty)

    if not item or not qty or qty <= 0 then
        cb({ ok = false })
        return
    end

    TriggerServerEvent('dynamic-economy:buyItem', item, qty)
    cb({ ok = true })
end)

-- Player selected an item to view its 24h graph
RegisterNUICallback('requestHistory', function(data, cb)
    TriggerServerEvent('dynamic-economy:requestHistory', data.item)
    cb({ ok = true })
end)

-- Player closed the NUI
RegisterNUICallback('close', function(_, cb)
    uiOpen = false
    SetNuiFocus(false, false)
    cb({ ok = true })
end)
