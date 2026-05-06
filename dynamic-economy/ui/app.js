'use strict';

// ─── State ────────────────────────────────────────────────────────────────────
let prices       = {};
let itemConfigs  = {};
let prevPrices   = {};
let selectedItem = null;
let historyData  = {};
let activeCategory = 'all';
let chartCtx     = null;
let nextCycleAt  = null;

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const terminal    = document.getElementById('terminal');
const tableBody   = document.getElementById('price-table-body');
const itemName    = document.getElementById('item-name');
const itemPrice   = document.getElementById('item-price');
const totalDisp   = document.getElementById('total-display');
const qtyInput    = document.getElementById('qty-input');
const btnBuy      = document.getElementById('btn-buy');
const btnSell     = document.getElementById('btn-sell');
const statusMsg   = document.getElementById('status-msg');
const nextUpdate  = document.getElementById('next-update');
const chartCanvas = document.getElementById('price-chart');
const chartPlaceholder = document.getElementById('chart-placeholder');
const tickerTime  = document.getElementById('ticker-time');

// ─── NUI message handler ──────────────────────────────────────────────────────
window.addEventListener('message', (e) => {
    const { action, prices: p, items, item, history } = e.data;

    switch (action) {
        case 'open':
            terminal.classList.remove('hidden');
            break;

        case 'close':
            terminal.classList.add('hidden');
            break;

        case 'setPrices':
            prevPrices  = { ...prices };
            prices      = p || {};
            if (items) itemConfigs = items;
            renderTable();
            if (selectedItem) updateSidePanel();
            statusMsg.textContent = 'Marché en ligne — ' + Object.keys(prices).length + ' items';
            scheduleNextCycle();
            break;

        case 'setHistory':
            historyData[item] = history || [];
            if (selectedItem === item) drawChart(item);
            break;
    }
});

// ─── Close on ESC ─────────────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') nuiPost('close', {});
});

// ─── Close button ─────────────────────────────────────────────────────────────
document.getElementById('btn-close').addEventListener('click', () => nuiPost('close', {}));

// ─── Category tabs ────────────────────────────────────────────────────────────
document.getElementById('tabs').addEventListener('click', (e) => {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    activeCategory = btn.dataset.cat;
    renderTable();
});

// ─── Qty buttons ──────────────────────────────────────────────────────────────
document.querySelectorAll('.qty-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const delta = parseInt(btn.dataset.delta, 10);
        qtyInput.value = Math.max(1, Math.min(9999, (parseInt(qtyInput.value) || 1) + delta));
        updateTotal();
    });
});

qtyInput.addEventListener('input', updateTotal);

// ─── Trade buttons ────────────────────────────────────────────────────────────
btnSell.addEventListener('click', () => {
    if (!selectedItem) return;
    const qty = parseInt(qtyInput.value, 10);
    if (qty < 1) return;
    nuiPost('sell', { item: selectedItem, qty });
});

btnBuy.addEventListener('click', () => {
    if (!selectedItem) return;
    const qty = parseInt(qtyInput.value, 10);
    if (qty < 1) return;
    nuiPost('buy', { item: selectedItem, qty });
});

// ─── Render price table ───────────────────────────────────────────────────────
function renderTable() {
    const entries = Object.entries(prices).filter(([item]) => {
        const cfg = itemConfigs[item];
        return activeCategory === 'all' || (cfg && cfg.category === activeCategory);
    });

    if (entries.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="loading">Aucun item dans cette catégorie.</td></tr>';
        return;
    }

    tableBody.innerHTML = '';
    for (const [item, price] of entries) {
        const cfg  = itemConfigs[item] || {};
        const prev = prevPrices[item]  || price;
        const diff = price - prev;

        let trendIcon = '─';
        let trendClass = 'trend-flat';
        if (diff > 0.01)  { trendIcon = '▲ +' + fmt(diff); trendClass = 'trend-up'; }
        if (diff < -0.01) { trendIcon = '▼ ' + fmt(diff);  trendClass = 'trend-down'; }

        const tr = document.createElement('tr');
        if (item === selectedItem) tr.classList.add('active');

        let priceClass = 'price-cell';
        if (diff > 0.01)  priceClass += ' flash-up';
        if (diff < -0.01) priceClass += ' flash-down';

        tr.innerHTML = `
            <td>${cfg.label || item}<br><span style="font-size:10px;color:var(--text-dim)">${cfg.unit || ''}</span></td>
            <td class="${priceClass}">$${fmt(price)}</td>
            <td class="min-cell">$${fmt(cfg.minPrice || 0)}</td>
            <td class="max-cell">$${fmt(cfg.maxPrice || 0)}</td>
            <td class="${trendClass}">${trendIcon}</td>
            <td><button class="btn-select" data-item="${item}">SÉLECT.</button></td>
        `;

        tr.querySelector('.btn-select').addEventListener('click', (e) => {
            e.stopPropagation();
            selectItem(item);
        });
        tr.addEventListener('click', () => selectItem(item));

        tableBody.appendChild(tr);
    }
}

// ─── Select item ──────────────────────────────────────────────────────────────
function selectItem(item) {
    selectedItem = item;
    document.querySelectorAll('tbody tr').forEach(r => r.classList.remove('active'));
    const matching = [...document.querySelectorAll('tbody tr')].find(r =>
        r.querySelector(`.btn-select[data-item="${item}"]`)
    );
    if (matching) matching.classList.add('active');

    btnBuy.disabled  = false;
    btnSell.disabled = false;

    updateSidePanel();

    // Request history from server
    nuiPost('requestHistory', { item });
}

// ─── Update side panel ────────────────────────────────────────────────────────
function updateSidePanel() {
    if (!selectedItem) return;
    const cfg   = itemConfigs[selectedItem] || {};
    const price = prices[selectedItem] || 0;

    itemName.textContent  = cfg.label || selectedItem;
    itemPrice.textContent = '$' + fmt(price);

    updateTotal();
}

function updateTotal() {
    if (!selectedItem) return;
    const qty   = parseInt(qtyInput.value, 10) || 0;
    const price = prices[selectedItem] || 0;
    totalDisp.textContent = '$' + fmt(qty * price);
}

// ─── Draw chart ───────────────────────────────────────────────────────────────
function drawChart(item) {
    const data = historyData[item];
    chartPlaceholder.style.display = (!data || data.length === 0) ? 'flex' : 'none';
    if (!data || data.length === 0) return;

    const W = chartCanvas.offsetWidth  || 300;
    const H = chartCanvas.offsetHeight || 160;
    chartCanvas.width  = W;
    chartCanvas.height = H;

    const ctx   = chartCanvas.getContext('2d');
    const vals  = data.map(d => parseFloat(d.price));
    const minV  = Math.min(...vals) * 0.95;
    const maxV  = Math.max(...vals) * 1.05;
    const range = maxV - minV || 1;

    const pad  = { t: 10, r: 10, b: 20, l: 55 };
    const cW   = W - pad.l - pad.r;
    const cH   = H - pad.t - pad.b;

    ctx.clearRect(0, 0, W, H);

    // Grid lines
    ctx.strokeStyle = 'rgba(30,42,53,0.8)';
    ctx.lineWidth   = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad.t + (cH * i / 4);
        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(W - pad.r, y);
        ctx.stroke();

        // Y-axis label
        const val = maxV - (range * i / 4);
        ctx.fillStyle = 'rgba(90,112,128,0.9)';
        ctx.font      = '10px Courier New';
        ctx.textAlign = 'right';
        ctx.fillText('$' + Math.round(val), pad.l - 4, y + 3);
    }

    // Price line
    const gradient = ctx.createLinearGradient(0, pad.t, 0, H - pad.b);
    gradient.addColorStop(0,   'rgba(0,212,255,0.3)');
    gradient.addColorStop(1,   'rgba(0,212,255,0)');

    ctx.beginPath();
    data.forEach((d, i) => {
        const x = pad.l + (i / (data.length - 1 || 1)) * cW;
        const y = pad.t + cH - ((parseFloat(d.price) - minV) / range) * cH;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });

    // Fill under curve
    const lastX = pad.l + cW;
    const lastY = pad.t + cH - ((vals[vals.length - 1] - minV) / range) * cH;
    ctx.lineTo(lastX, H - pad.b);
    ctx.lineTo(pad.l, H - pad.b);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Stroke line
    ctx.beginPath();
    data.forEach((d, i) => {
        const x = pad.l + (i / (data.length - 1 || 1)) * cW;
        const y = pad.t + cH - ((parseFloat(d.price) - minV) / range) * cH;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#00d4ff';
    ctx.lineWidth   = 2;
    ctx.lineJoin    = 'round';
    ctx.stroke();

    // Current price dot
    const dotX = pad.l + cW;
    const dotY = pad.t + cH - ((vals[vals.length - 1] - minV) / range) * cH;
    ctx.beginPath();
    ctx.arc(dotX, dotY, 4, 0, Math.PI * 2);
    ctx.fillStyle   = '#00d4ff';
    ctx.shadowColor = '#00d4ff';
    ctx.shadowBlur  = 8;
    ctx.fill();
    ctx.shadowBlur = 0;
}

// ─── Next cycle countdown ─────────────────────────────────────────────────────
function scheduleNextCycle() {
    // We don't know exact server timer, so show a rolling estimate
    nextCycleAt = Date.now() + (5 * 60 * 1000); // assume 5min default
}

// ─── Clock & countdown ticker ─────────────────────────────────────────────────
setInterval(() => {
    const now = new Date();
    tickerTime.textContent = now.toLocaleTimeString('fr-FR');

    if (nextCycleAt) {
        const diff = Math.max(0, Math.floor((nextCycleAt - Date.now()) / 1000));
        const m = Math.floor(diff / 60).toString().padStart(2, '0');
        const s = (diff % 60).toString().padStart(2, '0');
        nextUpdate.textContent = 'Prochain cycle : ' + m + ':' + s;
    }
}, 1000);

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmt(n) {
    return Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function nuiPost(action, data) {
    fetch(`https://${GetParentResourceName()}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }).catch(() => {});
}

// FiveM resource name helper (falls back gracefully in browser preview)
function GetParentResourceName() {
    return (typeof window.GetParentResourceName === 'function')
        ? window.GetParentResourceName()
        : 'dynamic-economy';
}
