// UI CORE V2 - Handles DOM interactions, Dragging, and Updates
console.log("UI CORE V2 LOADING...");

// --- 1. DRAGGABLE PANELS ---
function initDraggables() {
    const panels = document.querySelectorAll('.draggable-panel');
    let activePanel = null;
    let offsetX = 0;
    let offsetY = 0;
    let maxZ = 100;

    panels.forEach(panel => {
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
        activePanel.style.transform = 'none';
    }

    function onMouseUp() {
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

        if (options.length > 0) {
            const optContainer = document.createElement('div');
            optContainer.style.marginTop = "10px";
            optContainer.style.display = "flex";
            optContainer.style.flexDirection = "column";
            optContainer.style.gap = "5px";
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
        }
        const nameEl = document.getElementById('chat-overlaid-name');
        if (nameEl && data.npc_name) nameEl.textContent = data.npc_name;
        hist.scrollTop = hist.scrollHeight;
    }
}

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
                window.showPopup("LOOTED", data.narrative, "#ffd700", 2000);
                // Also log
                if (window.logMessage) window.logMessage(data.narrative);
            }
            if (data.state && window.updateDashboard) window.updateDashboard(data.state);
            else if (window.fetchState) window.fetchState(); // Fallback refresh

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
        if (data.narrative && window.logMessage) window.logMessage(data.narrative);
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
            html += `<div style="display:flex; justify-content:space-between; align-items:center; background:#333; padding:8px; border-radius:4px;">
                        <span style="color:#eee;">${item.icon || '📦'} <b>${item.name}</b> <span style="font-size:0.8em; color:#aaa;">(x${item.qty || 1})</span></span>
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

        // Close modal and show toaster
        document.getElementById('loot-popup').style.display = 'none';

        // Show small toast instead of blocking popup
        if (window.logMessage) window.logMessage(result.message); // logMessage is better than popup for small stuff
        else window.showPopup("TAKEN", result.message, "#0f0", 800);

        // Refresh
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

        setText('stat-lvl', data.player.level || 1);
        setText('stat-xp', data.player.xp || 0);
        setText('stat-hp', `${hp}/${max}`);
        setText('stat-str', s.str);
        setText('stat-dex', s.dex);
        setText('stat-con', s.con);
        setText('stat-int', s.int);
        setText('stat-wis', s.wis);
        setText('stat-cha', s.cha);
    }

    // Update Sub-Modules
    updateInventory(data);
    updateNearby(data);
    updateCombat(data);
    updateQuests(data);
};

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function updateInventory(data) {
    const invList = document.getElementById('inventory-list');
    if (!invList) return;
    const items = data.player && data.player.inventory ? data.player.inventory : [];

    if (items.length === 0) {
        invList.innerHTML = '<div style="color:#666; font-style:italic; padding:5px;">Bag is empty.</div>';
    } else {
        invList.innerHTML = '';
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'interaction-item';
            div.style.padding = "5px";
            div.style.borderBottom = "1px solid #333";
            div.style.display = "flex";
            div.style.justifyContent = "space-between";
            div.style.alignItems = "center";

            let name = "Unknown", slot = "Bag", eq = false, id = null;
            if (typeof item === 'object' && !Array.isArray(item)) {
                name = item.name; slot = item.slot; eq = item.is_equipped; id = item.id;
            } else if (Array.isArray(item)) {
                name = item[0]; slot = item[1];
            } else { name = item; }

            const equippedStr = eq ? ' <span style="color:#0f0; font-size:0.8em">[E]</span>' : '';
            div.innerHTML = `
                <div><div style="color: #eee; font-weight: bold;">${name}${equippedStr}</div><div style="font-size: 0.8em; color: #888;">${slot || 'Item'}</div></div>
                <div>${!eq ? `<button style="font-size:10px; padding:2px 5px; cursor:pointer;" onclick="useItem('${id}')">Equip/Use</button>` : ''}</div>
            `;
            invList.appendChild(div);
        });

        // Sync with #items-list (Interaction Panel)
        const panelList = document.getElementById('items-list');
        if (panelList) {
            panelList.innerHTML = invList.innerHTML;
        }
    }
}

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
                    const style = outOfReach ? "opacity:0.5; color:#888; cursor:not-allowed;" : "color:#eee; cursor:pointer;";
                    const name = outOfReach ? `${e.name} (Too Far)` : `<span style="color:#faa">⚔ ${e.name}</span>`;
                    const clickAction = outOfReach ? "" : `selectTarget('${e.id}'); combatAction('attack')`; // One-click attack

                    // Highlight selected
                    const isSel = selectedCombatTarget === e.id;

                    html += `
                     <div onclick="${clickAction}" class="enemy-row" style="padding:6px 8px; border-bottom:1px solid #222; display:flex; justify-content:space-between; align-items:center; background:${isSel ? '#333' : ''}; ${style}">
                        <span style="font-weight:${isSel ? 'bold' : 'normal'}">${name}</span>
                        <span style="font-size:0.9em; color:${e.hp < e.max_hp * 0.3 ? 'red' : 'orange'}">${e.hp}/${e.max_hp} HP</span>
                     </div>`;
                });
            }
            html += `</div>`;

            // Special Actions (Skills)
            if (pLevel >= 4) {
                html += `<div style="display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:5px;">`;
                html += `<button class="btn-combat" onclick="combatAction('heavy_strike')">💥 H. Strike</button>`;
                html += `<button class="btn-combat" onclick="combatAction('cleave')">🪓 Cleave</button>`;
                html += `</div>`;
            } else {
                html += `<div style="text-align:center; color:#555; font-size:0.8em; margin-top:5px;">Level up to unlock Skills</div>`;
            }
            html += `</div>`;
        }
        else if (currentCombatTab === 'bonus') {
            html += `<div style="display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:5px; align-content:start; flex:1;">`;

            const hasPotion = (data.player.inventory || []).some(i => {
                const n = (typeof i === 'string' ? i : i.name).toLowerCase();
                return n.includes('potion');
            });

            if (hasPotion) {
                html += `<button class="btn-combat" onclick="combatAction('use_potion')">🧪 Potion</button>`;
            } else {
                html += `<button class="btn-combat" style="opacity:0.3; cursor:not-allowed;" title="No potions">🧪 Potion (0)</button>`;
            }

            html += `<button class="btn-combat" onclick="combatAction('second_wind')">💚 2nd Wind</button>`;

            if (pLevel >= 4) {
                html += `<button class="btn-combat" onclick="combatAction('kick')">🦵 Kick</button>`;
                html += `<button class="btn-combat" onclick="combatAction('rage')">😡 Rage</button>`;
            }
            html += `</div>`;
        }
        html += `</div>`; // End Content Container

        // 4. Footer (Persistent)
        html += `
        <div style="margin-top:10px; padding-top:10px; border-top:1px solid #333; display:grid; grid-template-columns: 1fr 2fr; gap:10px;">
             <button class="btn-combat" onclick="combatAction('flee')" style="background:#522; font-size:11px;">🏃 Flee</button>
             <button class="btn-combat" onclick="combatAction('end_turn')" style="background:#444; font-weight:bold;">END TURN</button>
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
    } catch (e) { console.error(e); }
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
