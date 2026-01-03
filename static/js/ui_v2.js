// UI CORE V2 - Handles DOM interactions, Dragging, and Updates
console.log("UI CORE V2 LOADING...");

// --- 1. DRAGGABLE PANELS ---
// --- 1. DRAGGABLE PANELS ---
function initDraggables() {
    const panels = document.querySelectorAll('.draggable-panel');
    let activePanel = null;
    let offsetX = 0;
    let offsetY = 0;
    let maxZ = 100;

    panels.forEach(panel => {
        // PERSISETNCE: Restore Position
        if (panel.id) {
            const saved = localStorage.getItem(`pos_${panel.id}`);
            if (saved) {
                try {
                    const pos = JSON.parse(saved);
                    panel.style.left = pos.left;
                    panel.style.top = pos.top;
                    // Ensure it's not off-screen? (Optional safety)
                } catch (e) { console.error("Bad saved pos", e); }
            }
        }

        const handle = panel.querySelector('.drag-handle');
        if (!handle) return;
        handle.addEventListener('mousedown', (e) => {
            activePanel = panel;
            const rect = panel.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            maxZ++;
            panel.style.zIndex = maxZ;
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });
    });

    function onMouseMove(e) {
        if (!activePanel) return;
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;
        activePanel.style.left = x + 'px';
        activePanel.style.top = y + 'px';
        activePanel.style.right = 'auto';
        activePanel.style.bottom = 'auto';
        activePanel.style.transform = 'none'; // reset centered transforms if any
    }

    function onMouseUp() {
        if (activePanel && activePanel.id) {
            // SAVE POSITION
            const pos = {
                left: activePanel.style.left,
                top: activePanel.style.top
            };
            localStorage.setItem(`pos_${activePanel.id}`, JSON.stringify(pos));
        }

        activePanel = null;
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    }
}

// --- 2. TAB SWITCHING ---
window.switchTab = function (tabName) {
    const interactionPanel = document.getElementById('interaction-panel');
    if (!interactionPanel) return;
    interactionPanel.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    interactionPanel.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    const targetContent = document.getElementById(tabName + '-tab');
    if (targetContent) targetContent.classList.add('active');

    const buttons = interactionPanel.querySelectorAll('.tab-btn');
    if (tabName === 'nearby') buttons[0]?.classList.add('active');
    if (tabName === 'items') buttons[1]?.classList.add('active');
    if (tabName === 'quest') buttons[2]?.classList.add('active');
};

window.switchCharTab = function (tabName) {
    const charPanel = document.getElementById('char-sheet');
    if (!charPanel) return;
    charPanel.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    charPanel.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    const targetContent = document.getElementById(tabName + '-char-tab');
    if (targetContent) targetContent.classList.add('active');

    const buttons = charPanel.querySelectorAll('.tab-btn');
    if (tabName === 'hero') buttons[0]?.classList.add('active');
    if (tabName === 'equipment') buttons[1]?.classList.add('active');
    if (tabName === 'skills') buttons[2]?.classList.add('active');
    if (tabName === 'crafting') buttons[3]?.classList.add('active');
};

// --- 3. CHAT SYSTEM ---
let activeNpcId = null;

window.openChat = async function (name, npcId) {
    activeNpcId = npcId;
    const modal = document.getElementById('chat-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    document.getElementById('chat-history').innerHTML = '<div class="chat-message npc">Loading...</div>';
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ npc_index: npcId, message: "__INIT__" })
        });
        const data = await res.json();
        renderChat(data);
    } catch (e) {
        console.error("Chat Error", e);
        document.getElementById('chat-history').textContent = "Failed to load chat.";
    }
};

window.closeChat = function () {
    const modal = document.getElementById('chat-modal');
    if (modal) modal.style.display = 'none';
};

window.sendChat = async function () {
    const input = document.getElementById('chat-input');
    if (!input || !input.value.trim()) return;
    const msg = input.value.trim();
    input.value = '';

    const hist = document.getElementById('chat-history');
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-message user';
    userDiv.textContent = msg;
    hist.appendChild(userDiv);
    hist.scrollTop = hist.scrollHeight;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ npc_index: activeNpcId, message: msg })
        });
        const data = await res.json();
        renderChat(data);
    } catch (e) { console.error(e); }
};

async function sendChatRaw(msg) {
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ npc_index: activeNpcId, message: msg.toString() })
        });
        const data = await res.json();
        renderChat(data);
    } catch (e) { console.error(e); }
}

function renderChat(data) {
    const hist = document.getElementById('chat-history');
    if (hist.querySelector('.npc')?.textContent === "Loading...") hist.innerHTML = '';
    if (data.reply) {
        let mainText = data.reply;
        let options = [];
        const parts = data.reply.split(/\n(\d+)\.\s/);
        if (parts.length > 1) {
            mainText = parts[0];
            for (let i = 1; i < parts.length; i += 2) {
                options.push({ num: parts[i], label: parts[i + 1].trim() });
            }
        }
        const div = document.createElement('div');
        div.className = 'chat-message npc';
        div.innerHTML = mainText.replace(/\n/g, '<br>');
        hist.appendChild(div);

        const optContainer = document.createElement('div');
        optContainer.style.marginTop = "10px";
        optContainer.style.display = "flex";
        optContainer.style.flexDirection = "column";
        optContainer.style.gap = "5px";

        // Special: Trade Button
        if (data.can_trade) {
            const tradeBtn = document.createElement('button');
            tradeBtn.textContent = "💰 TRADE / SHOP";
            tradeBtn.className = "chat-option-btn";
            tradeBtn.style.padding = "8px";
            tradeBtn.style.textAlign = "center";
            tradeBtn.style.background = "#2a4200";
            tradeBtn.style.border = "1px solid #480";
            tradeBtn.style.color = "#df8";
            tradeBtn.style.fontWeight = "bold";
            tradeBtn.style.cursor = "pointer";
            tradeBtn.onclick = () => {
                window.openShop();
            };
            optContainer.appendChild(tradeBtn);
        }

        if (options.length > 0) {
            options.forEach(opt => {
                const btn = document.createElement('button');
                btn.textContent = opt.label;
                btn.className = "chat-option-btn";
                btn.style.padding = "8px";
                btn.style.textAlign = "left";
                btn.style.cursor = "pointer";
                btn.onclick = () => {
                    const userDiv = document.createElement('div');
                    userDiv.className = 'chat-message user';
                    userDiv.textContent = opt.label;
                    hist.appendChild(userDiv);
                    sendChatRaw(opt.num);
                };
                optContainer.appendChild(btn);
            });
            hist.appendChild(optContainer);
        } else if (data.can_trade) {
            // If no options but can trade, render container just for trade btn
            hist.appendChild(optContainer);
        }

        const nameEl = document.getElementById('chat-overlaid-name');
        if (nameEl && data.npc_name) nameEl.textContent = data.npc_name;
        hist.scrollTop = hist.scrollHeight;
    }
}

// --- SHOP SYSTEM ---
window.openShop = async function () {
    try {
        const res = await fetch('/api/shop/list');
        const data = await res.json();
        renderShop(data);
    } catch (e) { console.error(e); }
};

function renderShop(data) {
    let el = document.getElementById('shop-modal');
    if (!el) {
        el = document.createElement('div');
        el.id = 'shop-modal';
        el.style.position = 'absolute';
        el.style.top = '50%';
        el.style.left = '50%';
        el.style.transform = 'translate(-50%, -50%)';
        el.style.background = '#1a1a1a';
        el.style.border = '2px solid #ffd700';
        el.style.padding = '20px';
        el.style.zIndex = '10001';
        el.style.width = '600px';
        el.style.height = '500px';
        el.style.display = 'flex';
        el.style.flexDirection = 'column';
        el.style.boxShadow = '0 0 50px rgba(0,0,0,0.95)';
        document.body.appendChild(el);
    }
    el.style.display = 'flex';

    // Header
    let html = `
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #444; padding-bottom:10px; margin-bottom:10px;">
        <h2 style="margin:0; color:#ffd700;">Town Market</h2>
        <button onclick="document.getElementById('shop-modal').style.display='none'" style="background:#422; border:1px solid #633; color:#fff; cursor:pointer; padding:5px 10px;">Close</button>
    </div>
    
    <div style="display:flex; flex:1; overflow:hidden; gap:20px;">
        <!-- BUY TAB -->
        <div style="flex:1; display:flex; flex-direction:column; border-right:1px solid #333; padding-right:10px;">
            <h3 style="color:#ada; margin-top:0;">Buy Items</h3>
            <div style="overflow-y:auto; flex:1;" id="shop-buy-list">
                 <!-- Generated JS -->
            </div>
        </div>
        
        <!-- SELL TAB -->
        <div style="flex:1; display:flex; flex-direction:column;">
            <h3 style="color:#daa; margin-top:0;">Sell Items</h3>
            <div style="overflow-y:auto; flex:1;" id="shop-sell-list">
                 <!-- Generated JS -->
            </div>
        </div>
    </div>
    `;
    el.innerHTML = html;

    // Fill Lists
    const buyList = document.getElementById('shop-buy-list');
    const shops = data.shops || {}; // { "blacksmith": [id, id], ... }
    const items = data.items || {}; // { id: {name, price...} }

    // Flatten all shop inventories for now (or filter by NPC type logic if we had it passed in)
    // For now, show ALL available shop items in game
    let allShopItems = [];
    for (let shopName in shops) {
        shops[shopName].forEach(tid => {
            if (items[tid]) allShopItems.push(items[tid]);
        });
    }

    // Render Buy
    if (allShopItems.length === 0) {
        buyList.innerHTML = "<div style='color:#666'>Nothing for sale.</div>";
    } else {
        allShopItems.forEach(item => {
            const div = document.createElement('div');
            div.style.padding = "5px"; div.style.borderBottom = "1px solid #333"; div.style.display = "flex"; div.style.justifyContent = "space-between";
            div.innerHTML = `
                <div>
                   <div style="color:#eee; font-weight:bold;">${item.name}</div>
                   <div style="font-size:0.8em; color:#888;">${item.type} | ${item.slot || '-'}</div>
                </div>
                <button onclick="buyItem('${item.id}')" style="background:#242; color:#afa; border:1px solid #363; cursor:pointer; padding:5px;">Buy ${item.value}g</button>
             `;
            buyList.appendChild(div);
        });
    }

    // Render Sell (Need Player Inventory - fetch state?)
    // Uses global player state if available or re-fetch?
    // We can assume window.playerInventory is not easily avail, so let's use a quick fetch or passed data?
    // We'll rely on updateDashboard having run recently, but better to just show "Check Inventory".
    // Or we fetch state right now
    refreshSellList();
}

async function refreshSellList() {
    try {
        const res = await fetch('/api/state');
        const data = await res.json();
        const inv = data.player ? data.player.inventory : [];
        const sellList = document.getElementById('shop-sell-list');
        if (!sellList) return;

        sellList.innerHTML = '';
        if (inv.length === 0) {
            sellList.innerHTML = "<div style='color:#666'>Your bag is empty.</div>";
            return;
        }

        inv.forEach(item => {
            // item can be obj or list, ui_v2 handles mixed. Backend usually returns Obj now?
            let name = item.name || item[0];
            let id = item.id;
            let val = item.value || 0; // Backend needs to send value
            if (val === 0) val = 5; // Fallback minimal value

            // Don't sell equipped?
            if (item.is_equipped) return;

            const div = document.createElement('div');
            div.style.padding = "5px"; div.style.borderBottom = "1px solid #333"; div.style.display = "flex"; div.style.justifyContent = "space-between";
            div.innerHTML = `
                <div>
                   <div style="color:#eee;">${name}</div>
                </div>
                <button onclick="sellItem('${id}')" style="background:#422; color:#faa; border:1px solid #633; cursor:pointer; padding:5px;">Sell ${val}g</button>
             `;
            sellList.appendChild(div);
        });

    } catch (e) { console.error(e); }
}

window.buyItem = async function (itemId) {
    try {
        const res = await fetch('/api/shop/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await res.json();
        if (data.message) window.showPopup("SHOP", data.message, data.message.includes("Bought") ? "#0f0" : "#f00");
        if (data.state) window.updateDashboard(data.state);
        // Refresh sell list (gold changed)
        // Refresh buy list? (maybe limited stock later)
    } catch (e) { console.error(e); }
};

window.sellItem = async function (itemId) {
    try {
        const res = await fetch('/api/shop/sell', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await res.json();
        if (data.message) window.showPopup("SHOP", data.message, "#ffd700");
        if (data.state) window.updateDashboard(data.state);
        refreshSellList(); // Remove item from list
    } catch (e) { console.error(e); }
};

// --- 4. LOOT & INTERACTION ---
// --- 4. LOOT & INTERACTION ---
window.lootItem = async function (type, id) {
    if (type === 'corpse') {
        try {
            const res = await fetch('/api/interact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'loot', type: 'corpse', id: id })
            });
            const data = await res.json();

            if (data.narrative) {
                // Check if it's a Loot Window Object or just text
                if (typeof data.narrative === 'object' && data.narrative.type === 'loot_window') {
                    window.showLootPopup(data.narrative);
                } else {
                    // Standard Text Response (e.g., "The corpse is empty.")
                    // Make sure to close previous loot window if it was open
                    const lootWin = document.getElementById('loot-popup');
                    if (lootWin) lootWin.style.display = 'none';

                    window.showPopup("LOOTED", data.narrative, "#ffd700", 2000);
                    if (window.logMessage) window.logMessage(data.narrative);
                }
            }
            // State update is handled by takeLoot usually, but if we emptied custom stash?
            if (data.state && window.updateDashboard) window.updateDashboard(data.state);
            else if (window.fetchState) window.fetchState();

        } catch (e) { console.error(e); }
    }
};

window.interactSecret = async function (id, type) {
    try {
        const res = await fetch('/api/interact_specific', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'inspect', target_type: type || 'secret', target_id: id })
        });
        const data = await res.json();

        if (data.narrative) {
            if (typeof data.narrative === 'object' && data.narrative.type === 'loot_window') {
                window.showLootPopup(data.narrative);
            } else {
                if (window.logMessage) window.logMessage(data.narrative);
            }
        }

        if (window.fetchState) window.fetchState();
    } catch (e) { console.error(e); }
};

window.performAction = async function (action) {
    if (action === 'investigate') {
        try {
            const res = await fetch('/api/action/investigate', { method: 'POST' });
            const data = await res.json();
            if (data.message) window.logMessage(data.message, 'info');
            if (window.fetchState) window.fetchState();
        } catch (e) { console.error(e); }
    }
};

window.useItem = async function (id) {
    console.log("Use/Equip Item ID:", id);
    if (window.logMessage) window.logMessage("You inspect the item. (Equip logic pending)");
};

// --- ZOOM CONTROLS ---
window.changeZoom = function (delta) {
    if (typeof TILE_SIZE !== 'undefined') {
        // This likely requires renderer exposing TILE_SIZE or zoom function
        // For now, assume renderer handles it via global
        // Or implement zoom here if needed
    }
};

// --- POPUP SYSTEM ---
// --- POPUP SYSTEM (Queue Based) ---
const popupQueue = [];
let isPopupShowing = false;

window.showPopup = function (title, content, color, duration) {
    popupQueue.push({ title, content, color, duration: duration || 1200 }); // Default 1.2s
    processPopupQueue();
};

function processPopupQueue() {
    if (isPopupShowing || popupQueue.length === 0) return;

    const p = popupQueue.shift();
    isPopupShowing = true;

    let el = document.getElementById('game-popup');
    if (!el) {
        el = document.createElement('div');
        el.id = 'game-popup';
        el.style.position = 'absolute';
        // Move to RIGHT Side (Interaction Area)
        el.style.top = '65%'; // Moved down from 50%
        el.style.right = '50px'; // Anchored to right
        el.style.transform = 'translate(0, -50%)';
        el.style.background = 'rgba(0,0,0,0.85)';
        el.style.border = '2px solid #fff';
        el.style.padding = '15px 30px';
        el.style.zIndex = '9999';
        el.style.textAlign = 'center';
        el.style.minWidth = '250px';
        el.style.borderRadius = "8px";
        el.style.boxShadow = '0 5px 20px rgba(0,0,0,0.8)';
        // Animation
        el.style.transition = "opacity 0.2s, transform 0.2s";
        el.style.opacity = "0";
        document.body.appendChild(el);
    }

    el.style.display = 'block';
    el.style.right = '50px'; // Ensure position
    el.style.left = 'auto';  // Reset left
    el.style.transform = 'translate(0, -50%)';

    el.style.borderColor = p.color || '#fff';
    el.innerHTML = `<h2 style="color:${p.color || '#fff'}; margin:0 0 5px 0; font-size:1.4em; text-transform:uppercase; letter-spacing:1px;">${p.title}</h2>
                    <div style="color:#eee; font-size:1.1em; font-weight:bold;">${p.content}</div>`;

    // Fade In
    requestAnimationFrame(() => {
        el.style.opacity = "1";
        el.style.transform = 'translate(0, -50%) scale(1.05)';
    });

    setTimeout(() => {
        // Fade Out
        el.style.opacity = "0";
        el.style.transform = 'translate(0, -60%)';
        setTimeout(() => {
            el.style.display = 'none';
            isPopupShowing = false;
            // Short delay before next
            setTimeout(processPopupQueue, 150);
        }, 200);
    }, p.duration);
}

// --- LOOT WINDOW & MODALS ---
window.showLootPopup = function (data) {
    let el = document.getElementById('loot-popup');
    if (!el) {
        el = document.createElement('div');
        el.id = 'loot-popup';
        el.style.position = 'absolute';
        el.style.top = '50%';
        el.style.left = '50%';
        el.style.transform = 'translate(-50%, -50%)';
        el.style.background = '#1a1a1a';
        el.style.border = '2px solid #ffd700';
        el.style.padding = '20px';
        el.style.zIndex = '10000';
        el.style.minWidth = '300px';
        el.style.boxShadow = '0 0 30px rgba(0,0,0,0.9)';
        document.body.appendChild(el);
    }
    el.style.display = 'block';

    let html = `<h3 style="color:#ffd700; border-bottom:1px solid #444; padding-bottom:10px; margin-top:0;">Looting: ${data.name}</h3>`;
    html += `<div style="display:flex; flex-direction:column; gap:8px; max-height:300px; overflow-y:auto; margin-bottom:15px;">`;

    if (!data.loot || data.loot.length === 0) {
        html += `<div style="color:#888; font-style:italic;">Empty.</div>`;
    } else {
        data.loot.forEach(item => {
            // FIX: Resolve Icon HTML instead of raw filename
            const iconHtml = window.resolveIconHtml(item.icon || '📦');
            html += `<div style="display:flex; justify-content:space-between; align-items:center; background:#333; padding:8px; border-radius:4px;">
                        <span style="color:#eee; display:flex; align-items:center; gap:8px;">
                            <div style="width:24px; height:24px; display:inline-block;">${iconHtml}</div>
                            <b>${item.name}</b> <span style="font-size:0.8em; color:#aaa;">(x${item.qty || 1})</span>
                        </span>
                        <button onclick="takeLoot('${data.corpse_id}', '${item.id}')" style="background:#262; color:#cfc; border:none; padding:5px 10px; cursor:pointer;">Take</button>
                     </div>`;
        });
    }
    html += `</div>`;
    html += `<button onclick="document.getElementById('loot-popup').style.display='none'" style="width:100%; padding:10px; background:#444; border:none; color:#fff; cursor:pointer;">Close</button>`;

    el.innerHTML = html;
};

window.takeLoot = async function (corpseId, lootId) {
    try {
        const res = await fetch('/api/loot/take', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ corpse_id: corpseId, loot_id: lootId })
        });
        const result = await res.json();

        // Show small toast
        if (window.logMessage) window.logMessage(result.message);
        else window.showPopup("TAKEN", result.message, "#0f0", 800);

        // DO NOT CLOSE POPUP - REFRESH IT INSTEAD
        // Re-query the corpse. If it's empty now, the refresh logic will handle it (likely calling close or showing empty msg).
        if (corpseId) {
            window.lootItem('corpse', corpseId);
        }

        // Global State Refresh
        if (window.fetchState) window.fetchState();

    } catch (e) { console.error(e); }
};

window.closePopup = function () {
    const el = document.getElementById('game-popup');
    if (el) el.style.display = 'none';
    isPopupShowing = false;
    processPopupQueue(); // Skip to next
};

// --- DASHBOARD UPDATES ---
window.updateDashboard = function (data) {
    if (!data) return;

    // A. STATS & INFO
    if (data.player) {
        // Title Update based on Zone
        const titleEl = document.getElementById('game-title');
        if (titleEl) {
            const z = data.player.z;
            if (z === 0) titleEl.textContent = "Unknown Dungeon";
            else if (z === 1) titleEl.textContent = "Oakhaven Town";
            else if (z === 2) titleEl.textContent = "North Forest";
            else if (z === 3) titleEl.textContent = "Volcanic Depths";
            else if (z === 4) titleEl.textContent = "Frozen Caverns";
            else titleEl.textContent = "Dungeon Crawler";
        }

        const s = data.player.stats || {};
        const hp = data.player.hp !== undefined ? data.player.hp : s.hp;
        const max = data.player.max_hp !== undefined ? data.player.max_hp : s.max_hp;

        // Dynamic Stat Table with Tooltips & Upgrades
        const sb = document.getElementById('stat-body');
        const points = s.unspent_points || 0;

        // Display Points if available
        if (points > 0) {
            setText('stat-lvl', `${data.player.level} (+${points} Avail)`);
            const lvlEl = document.getElementById('stat-lvl');
            if (lvlEl) lvlEl.style.color = '#0ff';
        }

        const statDefs = [
            { key: 'str', label: 'STR', desc: 'Physical power', tooltip: 'Melee Hit/Damage & Physical Resistance (Push/Prone).' },
            { key: 'dex', label: 'DEX', desc: 'Agility', tooltip: 'Initiative, Armor Class (AC), and Ranged/Finesse Attacks.' },
            { key: 'con', label: 'CON', desc: 'Endurance', tooltip: 'Determines Max HP Gain per Level & Concentration Checks.' },
            { key: 'int', label: 'INT', desc: 'Reasoning', tooltip: 'Wizard Spell Power (DC) & Investigation/Arcana.' },
            { key: 'wis', label: 'WIS', desc: 'Intuition', tooltip: 'Cleric/Druid Magic, Perception & Resisting Mind Effects.' },
            { key: 'cha', label: 'CHA', desc: 'Presence', tooltip: 'Paladin/Sorcerer Magic & Social Influence.' }
        ];

        // Rebuild Table Rows (skip first 3 which are static in HTML: LVL, XP, HP)
        // Wait, the HTML has LVL, XP, HP as rows 1-3. We should target specific rows or just rebuild the bottom half?
        // To obtain "hover ability", we need to ensure the row/cell has the title.
        // The original HTML had rows for stats. We can clear and rebuild, or update.
        // Let's rebuilding the stats part (rows 4+) to be safe and clean.
        // But 'stat-body' contains ALL rows.
        // We will keep LVL/XP/HP as they are updated by setText above, and we only need to rebuild the attribute rows?
        // Actually, it's cleaner to generate the whole table or just the attributes. 
        // Let's stick to updating the attributes which are usually rows 3-8 (0-indexed).

        // Strategy: Iterate and find or create rows for attributes. 
        // Simpler: Let's assume the table structure in HTML. 
        // Actually, replacing innerHTML of a specific container is easiest.
        // The user provided HTML has 'stat-body'. 
        // We will regenerate the LVL, XP, HP rows + the Attribute rows to ensure order.

        let html = `
            <tr title="Current Hero Level. Gains stats on level up.">
                <td>LVL</td>
                <td style="color:${points > 0 ? '#0ff' : '#ffd700'}; font-weight:bold;">${data.player.level || 1}${points > 0 ? ` <span style="font-size:0.8em">(${points} pts)</span>` : ''}</td>
                <td>Hero Level</td>
            </tr>
            <tr title="Experience Points. Reach threshold to level up.">
                <td>XP</td>
                <td>${data.player.xp || 0}</td>
                <td>Experience</td>
            </tr>
            <tr title="Health Points. If 0, you die.">
                <td>HP</td>
                <td style="color:#0f0; font-weight:bold;">${hp}/${max}</td>
                <td>Health Points</td>
            </tr>
        `;

        statDefs.forEach(def => {
            const val = s[def.key] || 10;
            html += `
            <tr title="${def.tooltip}">
                <td style="cursor:help; text-decoration:underline dotted; color:#ddd;">${def.label}</td>
                <td>
                    ${val}
                    ${points > 0 ? `<button onclick="upgradeStat('${def.key}')" style="background:#242; border:1px solid #484; color:#afa; cursor:pointer; font-size:10px; padding:0 3px; margin-left:4px;" title="Spend point to increase ${def.label}">+</button>` : ''}
                </td>
                <td style="font-size:0.8em; color:#aaa;">${def.desc}</td>
            </tr>
            `;
        });

        if (sb) sb.innerHTML = html;
    }

    // Update Sub-Modules
    updateInventory(data);
    updateNearby(data);
    updateCombat(data);
    updateQuests(data);
};

window.upgradeStat = async function (stat) {
    try {
        const res = await fetch('/api/stats/upgrade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stat: stat })
        });
        const data = await res.json();
        if (data.message && window.logMessage) window.logMessage(data.message, 'loot');
        if (data.state && window.updateDashboard) window.updateDashboard(data.state);
    } catch (e) { console.error(e); }
};

// --- DRAG & DROP LOGIC ---
window.handleItemDragStart = function (e, id, slot, type) {
    if (!id) return;
    e.dataTransfer.setData("item_id", id);
    e.dataTransfer.setData("item_slot", slot || "");
    e.dataTransfer.setData("item_type", type || "misc");
    e.dataTransfer.effectAllowed = "move";
    // Optional: Set Drag Image
};

window.allowDrop = function (e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move"; // Show copy/move cursor
};

window.handleItemDrop = function (e, targetSlot) {
    e.preventDefault();
    const id = e.dataTransfer.getData("item_id");
    const itemSlot = e.dataTransfer.getData("item_slot");
    const itemType = e.dataTransfer.getData("item_type");

    // Validate Slot Compatibility
    // If target is specific (e.g., 'head') and item slot doesn't match
    if (targetSlot && itemSlot !== targetSlot) {
        window.logMessage("That item doesn't fit there!");
        window.showPopup("INVALID", "Wrong Slot", "#f88", 1000);
        return;
    }

    // Execute Equip
    window.useItem(id);
};

window.useItem = async function (id) {
    console.log("Using Item:", id);
    try {
        // Backend 'use' endpoint usually handles both Consume and Equip based on type
        // Wait, backend logic for 'equip' is `dm.equip_item`.
        // backend `views.py` usually maps `/api/inventory/use` to `dm.use_item`.
        // We might need a specific `equip` endpoint if `use` is only for consumables?
        // Let's try calling `use` first. If it fails for equipment, we add `equip`.
        // Actually, looking at previous context, `dm.use_item` checks "consumable".
        // `dm.equip_item` is separate.
        // We likely need to check item type or try both? 
        // Or cleaner: Try Equip. If backend says "Not equipment", Try Use.

        let res = await fetch('/api/inventory/equip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        let data = await res.json();

        if (data.message && (data.message.includes("Equipped") || data.message.includes("Swap"))) {
            if (window.logMessage) window.logMessage(data.message);
            if (data.state) window.updateDashboard(data.state);
            return;
        }

        // If Equip failed (or not equipment), try Use (Consumable)
        res = await fetch('/api/inventory/use', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        data = await res.json();

        if (data.message) {
            if (window.logMessage) window.logMessage(data.message);
            else window.showPopup("ITEM", data.message, "#ffd700");
        }
        if (data.state && window.updateDashboard) window.updateDashboard(data.state);

    } catch (e) { console.error(e); }
};

// Helper to determine if icon is an image path or emoji
window.resolveIconHtml = function (iconStr) {
    if (!iconStr) return "📦";
    // Check if it looks like a file path (has extension or path separators)
    if (iconStr.match(/\.(png|jpg|jpeg|gif|webp)$/i) || iconStr.includes('/')) {
        let src = iconStr;
        if (!src.startsWith('/') && !src.startsWith('http')) {
            src = `/static/img/${src}`;
        }
        return `<img src="${src}" style="width:100%; height:100%; object-fit:contain; pixelated;">`;
    }
    // Fallback to Text/Emoji
    return `<span style="font-size:1.5em; line-height:1;">${iconStr}</span>`;
};

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function updateInventory(data) {
    const invList = document.getElementById('inventory-list');
    if (!invList) return;
    const items = data.player && data.player.inventory ? data.player.inventory : [];

    // Update Gold Display
    const goldEl = document.getElementById('hero-gold-display');
    if (goldEl) goldEl.textContent = data.player.gold || 0;

    // 1. Reset Slots to Default Icons & Attach Drop Listeners
    const defaultIcons = {
        'head': '🧢', 'chest': '👕', 'legs': '👖', 'feet': '👢',
        'main_hand': '⚔️', 'off_hand': '🛡️'
    };

    // Clear and Setup Slots
    for (let slot in defaultIcons) {
        const el = document.getElementById(`slot-${slot}`);
        if (el) {
            // Only reset if NOT holding a valid item (backend data drives this, so we clear first?)
            // Actually, we re-render "equipped" items below, so clearing here is correct.
            el.innerHTML = defaultIcons[slot]; // Use innerHTML to reset to emoji
            el.style.color = "#666";
            el.removeAttribute('data-item-id');
            el.title = "Empty";
            el.parentElement.style.borderColor = "#444";

            // ATTACH DROP LISTENERS TO PARENT CONTAINER
            // (Remove old ones to prevent dupes? Actually overwriting .ondrop property is safer than addEventListener for frequent updates)
            const container = el.parentElement;
            container.ondragover = window.allowDrop;
            container.ondrop = (e) => window.handleItemDrop(e, slot);
        }
    }

    // 2. Clear Inventory Grid
    invList.innerHTML = '';

    if (items.length === 0) {
        invList.innerHTML = '<div style="color:#666; font-style:italic; grid-column: 1 / -1;">Bag is empty.</div>';
    }

    // 3. Process Items & Build Side Panel List
    const sideListHtml = [];

    items.forEach(item => {
        let name = "Unknown", slot = "Bag", eq = false, id = null;
        let icon = "📦";
        let type = "misc";
        let props = {};

        if (typeof item === 'object' && !Array.isArray(item)) {
            name = item.name; slot = item.slot; eq = item.is_equipped; id = item.id;
            type = item.item_type || "misc";
            props = item.properties || {};
            if (props.icon) icon = props.icon;
        } else if (Array.isArray(item)) {
            name = item[0]; slot = item[1]; // Legacy fallback
        } else { name = item; }

        // Resolve Icon HTML (Image or Emoji)
        const iconHtml = window.resolveIconHtml(icon);

        // Build Tooltip text
        let tooltip = `${name} (${type})`;
        if (props.damage) tooltip += `\nDamage: ${props.damage}`;
        if (props.defense) tooltip += `\nDefense: ${props.defense}`;
        if (props.heal) tooltip += `\nHeals: ${props.heal}`;
        if (props.effect) tooltip += `\nEffect: ${props.effect}`;
        if (props.description) tooltip += `\n"${props.description}"`;

        if (eq && slot) {
            // Render into Slot (Paper Doll)
            const slotEl = document.getElementById(`slot-${slot}`);
            if (slotEl) {
                slotEl.innerHTML = iconHtml;
                slotEl.style.color = "#fff";
                slotEl.setAttribute('data-item-id', id);
                slotEl.title = `${tooltip}\n(Click to Unequip)`;
                // Highlight border
                slotEl.parentElement.style.borderColor = "#ffd700";
            }
        } else {
            // Render into Backpack Grid
            const div = document.createElement('div');
            div.className = 'inventory-grid-item';
            div.style.border = "1px solid #444";
            div.style.background = "#222";
            div.style.aspectRatio = "1/1";
            div.style.display = "flex";
            div.style.justifyContent = "center";
            div.style.alignItems = "center";
            div.style.cursor = "grab"; // Grab cursor for draggable
            div.style.fontSize = "1.2em";
            div.style.position = "relative";
            div.title = tooltip;

            // DRAGGABLE ATTRIBUTES
            div.draggable = true;
            div.ondragstart = (e) => window.handleItemDragStart(e, id, slot, type);
            // Click to Use fallback
            div.onclick = () => window.useItem(id);

            div.innerHTML = iconHtml;

            if (item.quantity > 1) {
                const qtySpan = document.createElement('span');
                qtySpan.style.position = "absolute";
                qtySpan.style.bottom = "1px";
                qtySpan.style.right = "2px";
                qtySpan.style.fontSize = "0.7em";
                qtySpan.style.color = "#fff";
                qtySpan.style.textShadow = "1px 1px 0 #000";
                qtySpan.textContent = item.quantity;
                div.appendChild(qtySpan);
            }
            invList.appendChild(div);

            // Side List
            sideListHtml.push(`
                <div style="padding:4px; border-bottom:1px solid #333; display:flex; justify-content:space-between; align-items:center;">
                    <span style="display:flex; align-items:center; gap:5px;">
                        <div style="width:20px; height:20px; display:flex; align-items:center; justify-content:center;">${iconHtml}</div>
                        ${name} ${item.quantity > 1 ? `x${item.quantity}` : ''}
                    </span>
                    <button onclick="useItem('${id}')" style="font-size:10px; cursor:pointer;">Use</button>
                </div>
            `);
        }
    });

    // Fill remaining grid spots
    const totalSlots = 15;
    const currentCount = items.filter(i => !i.is_equipped).length;
    for (let i = 0; i < (totalSlots - currentCount); i++) {
        const emptyDiv = document.createElement('div');
        emptyDiv.style.border = "1px dashed #333";
        emptyDiv.style.background = "rgba(0,0,0,0.2)";
        emptyDiv.style.aspectRatio = "1/1";
        invList.appendChild(emptyDiv);
    }

    // Sync Side Panel
    const sidePanel = document.getElementById('items-list');
    if (sidePanel) {
        if (sideListHtml.length === 0) {
            sidePanel.innerHTML = '<div style="color:#666; font-style:italic;">Your bag is empty.</div>';
        } else {
            sidePanel.innerHTML = sideListHtml.join('');
        }
    }
}

window.unequipSlot = async function (slotName) {
    const el = document.getElementById(`slot-${slotName}`);
    if (!el) return;
    const itemId = el.getAttribute('data-item-id');
    if (!itemId) return; // Empty slot

    try {
        const res = await fetch('/api/inventory/unequip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await res.json();
        if (data.message) window.logMessage(data.message);
        if (data.state) window.updateDashboard(data.state);
    } catch (e) { console.error(e); }
};

function updateNearby(data) {
    const list = document.getElementById('nearby-list');
    if (!list) return;
    let html = '';
    let found = false;
    const px = data.player.xyz[0], py = data.player.xyz[1], pz = data.player.xyz[2];

    if (data.world.npcs) {
        data.world.npcs.forEach(npc => {
            const [nx, ny, nz] = npc.xyz;
            if (nz !== pz) return;
            if (Math.max(Math.abs(nx - px), Math.abs(ny - py)) <= 2) {
                found = true;
                const safeId = npc.id || npc.name;
                html += `<div class="interaction-item"><div style="color:cyan; font-weight:bold">${npc.name}</div><button onclick="openChat('${npc.name}', '${safeId}')">Talk</button></div>`;
            }
        });
    }
    if (data.corpses) {
        data.corpses.forEach((c) => {
            const [cx, cy, cz] = c.xyz;
            if (Math.max(Math.abs(cx - px), Math.abs(cy - py)) <= 1.5) {
                found = true;
                html += `<div class="interaction-item">Pile of Bones <button onclick="lootItem('corpse', '${c.id}')">Loot</button></div>`;
            }
        });
    }
    if (data.world && data.world.secrets) {
        data.world.secrets.forEach(s => {
            const [sx, sy, sz] = s.xyz || [999, 999, 999];
            if (Math.max(Math.abs(sx - px), Math.abs(sy - py)) <= 1.5) {
                found = true;
                html += `<div class="interaction-item"><div style="color:gold; font-weight:bold">${s.name}</div><button onclick="interactSecret('${s.id}', '${s.type}')">Interact</button></div>`;
            }
        });
    }

    // --- RENDER OBJECTS (Crates, etc) ---
    if (data.world && data.world.objects) {
        // This is for the UI list, but the user asked about seeing it on the MAP.
        // Wait, the REQUEST is about the user NOT SEEING IT (presumably on the map).
        // The previous context was rendering (renderer_v3.js).
        // This file is UI_v2.js.
        // I need to check renderer_v3.js for object rendering.
        // But I am currently editing ui_v2.js? 
        // No, I am tasked to "Update renderer".
        // Ah, I see I viewed renderer_v3.js in the previous step.
        // But clearly I am expected to edit renderer_v3.js.
        // Let me re-read the plan.
        // The plan is "Update renderer to display objects". 
        // So I should edit renderer_v3.js.
        // But the current tool call target file is ui_v2.js?
        // Wait, I haven't specified the target file yet really.
        // Ah, I must have gotten confused. 
        // The user request "there is an armort crate but i dont see it".
        // The image shows the UI list has "Armory Crate".
        // But the MAP (black background) does not show a crate.
        // So I need to edit renderer_v3.js.
    }
    list.innerHTML = found ? html : '<div style="color:#666; font-style:italic">Nothing nearby.</div>';
}

function updateQuests(data) {
    const questList = document.getElementById('quest-list');
    if (!questList) return;
    questList.innerHTML = '';
    let questCount = 0;
    const activeQuests = data.player.quest_log || [];

    activeQuests.forEach(quest => {
        const div = document.createElement('div');
        div.className = 'interaction-item';
        div.style.borderLeft = "3px solid #ffd700"; div.style.padding = "5px"; div.style.marginBottom = "5px"; div.style.backgroundColor = "rgba(40,40,40,0.5)";
        const title = quest.title || (typeof quest === 'string' ? quest : "Active Quest");
        const desc = quest.description || (typeof quest === 'string' ? "" : "In Progress");
        div.innerHTML = `<div style="color: #ffd700; font-weight: bold; font-size: 0.95em;">${title}</div><div style="font-size: 0.85em; color: #aaa;">${desc}</div>`;
        questList.appendChild(div);
        questCount++;
    });
    if (questCount === 0) questList.innerHTML = '<div style="color: #666; font-style: italic; padding:5px;">No active quests.</div>';
}

// --- COMBAT LOGIC ---
let selectedCombatTarget = null;
let currentCombatTab = 'action';

window.selectTarget = function (id) {
    selectedCombatTarget = id;
    if (window.fetchState) window.fetchState();
};

function updateCombat(data) {
    const combatWin = document.getElementById('combat-controls');
    if (!combatWin) return;
    const content = combatWin.querySelector('.panel-content');
    if (!content) return;

    if (data.combat && data.combat.active) {
        combatWin.style.display = 'block';
        const c = data.combat;
        const pLevel = data.player ? (data.player.level || 1) : 1;

        // 1. TABS (Top) with Counters
        const moveCount = c.moves_left > 0 ? c.moves_left : 0;
        const actionCount = c.actions_left > 0 ? c.actions_left : 0;
        const bonusCount = c.bonus_actions_left > 0 ? c.bonus_actions_left : 0;

        const tabStyle = (active) => `flex:1; padding:8px; text-align:center; cursor:pointer; background:${active ? '#444' : '#222'}; color:${active ? '#fff' : '#888'}; border-bottom:${active ? '2px solid #a00' : '1px solid #444'}; font-weight:${active ? 'bold' : 'normal'}; font-size:12px;`;

        // Helper to format tab label
        const tabLabel = (name, count) => `${name} <span style="font-size:0.9em; opacity:0.7">(${count})</span>`;

        let html = `
        <div style="display:flex; margin-bottom:10px; margin-left:-10px; margin-right:-10px; margin-top:-10px;">
            <div onclick="switchCombatTab('move')" style="${tabStyle(currentCombatTab === 'move')}">${tabLabel('MOVE', moveCount)}</div>
            <div onclick="switchCombatTab('action')" style="${tabStyle(currentCombatTab === 'action')}">${tabLabel('ACTION', actionCount)}</div>
            <div onclick="switchCombatTab('bonus')" style="${tabStyle(currentCombatTab === 'bonus')}">${tabLabel('BONUS', bonusCount)}</div>
        </div>
        `;

        // 2. Turn Info (simplified)
        html += `
        <div style="text-align:center; font-size:0.8em; color:#ccc; margin-bottom:10px; border-bottom:1px solid #333; padding-bottom:5px;">
            <span style="color:${c.current_turn === 'player' ? '#bfb' : '#f88'}; font-weight:bold; letter-spacing:1px;">${c.current_turn === 'player' ? "YOUR TURN" : "ENEMY TURN"}</span>
        </div>
        `;

        // 3. Tab Content Container (Min Height for consistency)
        html += `<div style="min-height:160px; display:flex; flex-direction:column;">`;

        if (currentCombatTab === 'move') {
            html += `<div style="text-align:center; padding-top:20px; color:#aaa; flex:1;">
                <div style="font-weight:bold; color:#fff; margin-bottom:5px;">Move up to 6 places</div>
                <div style="font-size:0.8em; color:#666;">Use WASD or Arrow Keys</div>
             </div>`;
        }
        else if (currentCombatTab === 'action') {
            // Enemy List (Combat Only)
            html += `<div style="flex:1; display:flex; flex-direction:column;">`;
            html += `<div style="padding-bottom:5px; color:#aaa; font-size:0.8em;">Select Enemy to Attack:</div>`;
            html += `<div style="height:100px; overflow-y:auto; background:#111; border:1px solid #333; margin-bottom:5px;">`;

            let enemies = data.world.enemies || [];
            // STRICT FILTER: Only show enemies actually in combat
            let activeEnemies = enemies.filter(e => e.state === 'combat');

            if (activeEnemies.length === 0) {
                html += `<div style="padding:5px; color:#666; font-style:italic;">No engaged enemies.</div>`;
            } else {
                activeEnemies.forEach(e => {
                    const dist = Math.max(Math.abs(e.xyz[0] - data.player.xyz[0]), Math.abs(e.xyz[1] - data.player.xyz[1]));
                    const outOfReach = dist > 1.5;
                    const hasAction = actionCount > 0;

                    let style = "";
                    let name = e.name;
                    let clickAction = "";

                    // Condition 1: No Actions = Grey Out Everything
                    if (!hasAction) {
                        style = "opacity:0.3; color:#666; cursor:not-allowed; border-left: 3px solid #444;";
                        name = `${e.name}`;
                        clickAction = ""; // No click
                    }
                    // Condition 2: Has Action + In Range = Highlight!
                    else if (!outOfReach) {
                        style = "color:#fff; cursor:pointer; border: 1px solid rgba(255,255,255,0.4); background:rgba(255,50,50,0.1); border-left: 3px solid #f22;";
                        name = `<span style="font-weight:bold; color:#faa;">⚔ ${e.name}</span>`;
                        clickAction = `selectTarget('${e.id}')`; // Just Select
                    }
                    // Condition 3: Has Action + Out of Range = Grey/Warning
                    else {
                        style = "opacity:0.5; color:#888; cursor:not-allowed; border-left: 3px solid #555;";
                        name = `${e.name} (Too Far)`;
                        clickAction = "";
                    }

                    // Highlight currently selected (if logic persists)
                    const isSel = selectedCombatTarget === e.id;
                    if (isSel) style += " background:#422;";

                    html += `
                     <div onclick="${clickAction}" class="enemy-row" style="padding:6px 8px; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center; ${style}">
                        <span>${name}</span>
                        <span style="font-size:0.9em; color:${e.hp < e.max_hp * 0.3 ? 'red' : 'orange'}">${e.hp}/${e.max_hp} HP</span>
                     </div>`;
                });
            }
            html += `</div>`;

            // ACTION GRID: Standard Attack + Skills moved here
            html += `<div style="display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:5px;">`;

            // 1. Basic Attack
            html += `<button class="btn-combat" onclick="combatAction('attack')" style="background:#522; font-weight:bold;">⚔ Attack [1]</button>`;

            // 2. Skills
            if (pLevel >= 4) {
                html += `<button class="btn-combat" onclick="combatAction('heavy_strike')">💥 H. Strike [2]</button>`;
                html += `<button class="btn-combat" onclick="combatAction('cleave')">🪓 Cleave [3]</button>`;
                // Placeholder for symmetry
                html += `<div style="opacity:0"></div>`;
            } else {
                html += `<button class="btn-combat" style="opacity:0.3; cursor:not-allowed;" title="Unlock Level 4">Locked [2]</button>`;
            }

            html += `</div>`;

            // Note for User
            if (pLevel < 4) {
                html += `<div style="text-align:center; color:#555; font-size:0.8em; margin-top:5px;">Level up to unlock Skills</div>`;
            }

            html += `</div>`; // Close Main Flex Column
        }
        else if (currentCombatTab === 'bonus') {
            html += `<div style="flex:1; display:flex; flex-direction:column;">`;

            // --- ENEMY LIST FOR BONUS ACTIONS ---
            html += `<div style="padding-bottom:5px; color:#aaa; font-size:0.8em;">Select Enemy (for Kick):</div>`;
            html += `<div style="height:100px; overflow-y:auto; background:#111; border:1px solid #333; margin-bottom:5px;">`;

            let enemies = data.world.enemies || [];
            let activeEnemies = enemies.filter(e => e.state === 'combat');

            if (activeEnemies.length === 0) {
                html += `<div style="padding:5px; color:#666; font-style:italic;">No engaged enemies.</div>`;
            } else {
                activeEnemies.forEach(e => {
                    const dist = Math.max(Math.abs(e.xyz[0] - data.player.xyz[0]), Math.abs(e.xyz[1] - data.player.xyz[1]));
                    const outOfReach = dist > 1.5;
                    const hasAction = bonusCount > 0;

                    let style = "";
                    let name = e.name;
                    let clickAction = "";

                    if (!hasAction) {
                        style = "opacity:0.3; color:#666; cursor:not-allowed; border-left: 3px solid #444;";
                        name = `${e.name}`;
                        clickAction = "";
                    }
                    else if (!outOfReach) {
                        style = "color:#fff; cursor:pointer; border: 1px solid rgba(255,255,255,0.4); background:rgba(255,50,50,0.1); border-left: 3px solid #f22;";
                        name = `<span style="font-weight:bold; color:#faa;">⚔ ${e.name}</span>`;
                        clickAction = `selectTarget('${e.id}')`;
                    }
                    else {
                        style = "opacity:0.5; color:#888; cursor:not-allowed; border-left: 3px solid #555;";
                        name = `${e.name} (Too Far)`;
                        clickAction = "";
                    }
                    const isSel = selectedCombatTarget === e.id;
                    if (isSel) style += " background:#422;";

                    html += `<div onclick="${clickAction}" class="enemy-row" style="padding:6px 8px; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center; ${style}">
                        <span>${name}</span> <span style="font-size:0.9em; color:${e.hp < e.max_hp * 0.3 ? 'red' : 'orange'}">${e.hp}/${e.max_hp} HP</span></div>`;
                });
            }
            html += `</div>`;

            html += `<div style="display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:5px; align-content:start; flex:1;">`;

            const hasPotion = (data.player.inventory || []).some(i => {
                const n = (typeof i === 'string' ? i : i.name).toLowerCase();
                return n.includes('potion');
            });

            if (hasPotion) {
                html += `<button class="btn-combat" onclick="combatAction('use_potion')">🧪 Potion [1]</button>`;
            } else {
                html += `<button class="btn-combat" style="opacity:0.3; cursor:not-allowed;" title="No potions">🧪 Potion (0)</button>`;
            }

            html += `<button class="btn-combat" onclick="combatAction('second_wind')">💚 2nd Wind [2]</button>`;

            if (pLevel >= 4) {
                html += `<button class="btn-combat" onclick="combatAction('kick')">🦵 Kick [3]</button>`;
                html += `<button class="btn-combat" onclick="combatAction('rage')">😡 Rage [4]</button>`;
            }
            html += `</div>`;
            html += `</div>`; // Close Main Flex Column (Bonus Tab)
        }
        html += `</div>`; // End Content Container

        // 4. Footer (Persistent)
        html += `
        <div style="margin-top:10px; padding-top:10px; border-top:1px solid #333; display:grid; grid-template-columns: 1fr 2fr; gap:10px;">
             <button class="btn-combat" onclick="combatAction('flee')" style="background:#522; font-size:11px;">🏃 Flee [F]</button>
             <button class="btn-combat" onclick="combatAction('end_turn')" style="background:#444; font-weight:bold;">END TURN [SPACE]</button>
        </div>
        `;

        content.innerHTML = html;

    } else {
        combatWin.style.display = 'none';
        if (document.getElementById('turn-notification')) document.getElementById('turn-notification').style.display = 'none';
    }
}

window.switchCombatTab = function (tab) {
    currentCombatTab = tab;
    if (window.fetchState) window.fetchState();
};

function addBtn(parent, text, onclick, bg) {
    const btn = document.createElement('button');
    btn.innerHTML = text;
    btn.setAttribute('onclick', onclick);
    btn.className = "btn-combat";
    btn.style.padding = "6px"; btn.style.cursor = "pointer"; btn.style.background = bg || "#222"; btn.style.color = "#eee"; btn.style.border = "1px solid #444"; btn.style.fontSize = "11px";
    btn.onmouseover = () => btn.style.background = "#444";
    btn.onmouseout = () => btn.style.background = (bg || "#222");
    parent.appendChild(btn);
}

window.combatAction = async function (action) {
    // 1. Immediate Visual Feedback
    const buttons = document.querySelectorAll('.btn-combat');
    buttons.forEach(b => {
        b.disabled = true;
        b.style.opacity = "0.5";
        b.style.cursor = "wait";
    });

    // Optional: Show spinner or highlight clicked button?
    // For now, the global disable is enough to show "processing".

    const payload = { action: action };
    if (selectedCombatTarget) payload.target_id = selectedCombatTarget;

    try {
        const res = await fetch('/api/combat/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.result && data.result.events) {
            data.result.events.forEach(e => {
                if (e.type === 'text' && window.logMessage) window.logMessage(e.message, 'combat');
                if (e.type === 'popup') window.showPopup(e.title, e.content, e.color, e.duration || 2500);
            });
        }
        if (window.fetchState) window.fetchState();

    } catch (e) {
        console.error(e);
        // Re-enable on error just in case (though fetchState usually refreshes UI)
        buttons.forEach(b => {
            b.disabled = false;
            b.style.opacity = "1";
            b.style.cursor = "pointer";
        });
    }
};

window.logMessage = function (msg, type = "info") {
    const logEl = document.getElementById('log-content');
    if (!logEl) return;
    const div = document.createElement('div');
    div.style.marginBottom = "4px"; div.style.borderBottom = "1px solid #333"; div.style.paddingBottom = "2px";
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const spanMsg = document.createElement('span');
    spanMsg.innerHTML = msg;
    if (type === 'combat') spanMsg.style.color = '#ffaaaa';
    else if (type === 'loot') spanMsg.style.color = '#ffd700';
    else if (type === 'chat') spanMsg.style.color = '#aaddff';
    else spanMsg.style.color = '#ccc';
    div.innerHTML = `<span style="color:#666; font-size:0.8em">[${time}] </span>`;
    div.appendChild(spanMsg);
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;

    // Persist Log
    if (logEl.innerHTML.length < 100000) { // Safety limit
        localStorage.setItem('dungeon_crawler_log_v2', logEl.innerHTML);
    }
};

// Init Log
document.addEventListener('DOMContentLoaded', () => {
    const logEl = document.getElementById('log-content');
    const saved = localStorage.getItem('dungeon_crawler_log_v2');
    if (logEl && saved) {
        logEl.innerHTML = saved;
        logEl.scrollTop = logEl.scrollHeight;
        // Append reload marker
        const marker = document.createElement('div');
        marker.style.borderTop = "1px dashed #444";
        marker.style.marginTop = "5px";
        marker.style.color = "#666";
        marker.style.fontSize = "0.7em";
        marker.textContent = "--- Session Restored ---";
        logEl.appendChild(marker);
    }
});
// --- KEYBOARD SHORTCUTS ---
document.addEventListener('keydown', (e) => {
    // Only if combat panel is visible
    const panel = document.getElementById('combat-controls');
    if (!panel || panel.style.display === 'none') return;

    // Ignore if typing in chat
    const active = document.activeElement;
    if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) return;

    const key = e.key.toLowerCase();

    // Tabs
    if (key === 'q') switchCombatTab('move');
    if (key === 'w') switchCombatTab('action');
    if (key === 'e') switchCombatTab('bonus');

    // Actions (Context Sensitive)
    if (currentCombatTab === 'action') {
        if (key === '1') combatAction('attack');
        // Skills require Level 4 check handled by backend/UI availability, 
        // but we can just trigger them blindly and let backend reject or UI logic handle it.
        // Actually best to trigger click on the button if it exists to reuse logic?
        if (key === '2') clickBtnByText('H. Strike');
        if (key === '3') clickBtnByText('Cleave');
    } else if (currentCombatTab === 'bonus') {
        if (key === '1') clickBtnByText('Potion');
        if (key === '2') clickBtnByText('2nd Wind');
        if (key === '3') clickBtnByText('Kick');
        if (key === '4') clickBtnByText('Rage');
    }

    // Global Combat Keys
    if (e.code === 'Space') {
        e.preventDefault(); // Stop scrolling
        combatAction('end_turn');
    }

    if (key === 'f') combatAction('flee');
});

// Helper to click button programmatically (so we get visuals + logic)
function clickBtnByText(txtSubset) {
    const btns = document.querySelectorAll('#combat-controls button');
    for (let b of btns) {
        if (b.textContent.includes(txtSubset)) {
            b.click();
            return;
        }
    }
}
