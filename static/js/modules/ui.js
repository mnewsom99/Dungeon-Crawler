

// Chat & UI Interaction Logic

function updateHeader(z) {
    const h1 = document.querySelector('h1');
    if (!h1) return;

    if (z === 1) h1.innerText = "Town of Oakhaven";
    else if (z === 0) h1.innerText = "Unknown Dungeon";
    else h1.innerText = "Dungeon Crawler";
}

/* --- Drag & Drop Logic --- */
function makeDraggable(el) {
    const handle = el.querySelector('.drag-handle');
    if (!handle) return;

    let isDragging = false;
    let startX, startY, initialLeft, initialTop;

    handle.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const rect = el.getBoundingClientRect();

        // Convert 'right' or 'transform' to absolute left/top before moving
        if (el.style.right && el.style.right !== 'auto') {
            el.style.width = rect.width + 'px';
            el.style.right = 'auto';
            el.style.left = rect.left + 'px';
        }
        if (el.style.transform) {
            el.style.transform = 'none';
            el.style.left = rect.left + 'px';
            el.style.top = rect.top + 'px';
        }

        // Re-read rect after style changes if needed, but rect.left is mostly reliable
        initialLeft = parseFloat(el.style.left) || rect.left;
        initialTop = parseFloat(el.style.top) || rect.top;

        handle.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none'; // Prevent highlighting
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        el.style.left = `${initialLeft + dx}px`;
        el.style.top = `${initialTop + dy}px`;
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            handle.style.cursor = 'move';
            document.body.style.userSelect = '';
        }
    });

    // Minimize Logic
    const minBtn = handle.querySelector('.minimize-btn');
    // Store original position
    let restoreX = '';
    let restoreY = '';

    if (minBtn) {
        minBtn.onclick = (e) => {
            e.stopPropagation(); // Don't drag
            const content = el.querySelector('.panel-content') || el.querySelector('#log-content');
            if (content) {
                if (content.style.display === 'none') {
                    // RESTORE
                    content.style.display = 'block';
                    minBtn.innerText = '_';
                    el.style.height = 'auto';

                    // Pop back to previous location
                    if (restoreY) el.style.top = restoreY;
                    if (restoreX) el.style.left = restoreX;

                } else {
                    // MINIMIZE
                    const rect = el.getBoundingClientRect();
                    restoreX = el.style.left || rect.left + 'px';
                    restoreY = el.style.top || rect.top + 'px';

                    content.style.display = 'none';
                    minBtn.innerText = '□';
                    el.style.height = 'auto';

                    // Auto drop to bottom, using actual height
                    const h = el.offsetHeight;
                    el.style.top = (window.innerHeight - h) + 'px';
                    // Keep X (left) same, so it drops straight down
                }
            }
        };
    }
}

// Init Draggables
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.draggable-panel').forEach(makeDraggable);
});

// --- Dynamic Nearby List ---
function updateNearbyList(data) {
    const listEl = document.getElementById('nearby-list');
    if (!listEl) return;

    // Retrieve previous "active" items to avoid full redraw flicker if possible?
    // For now simple redraw.

    const items = [];
    const px = data.player.xyz[0];
    const py = data.player.xyz[1];
    const pz = data.player.xyz[2];

    // NPCs
    if (data.world.npcs) {
        data.world.npcs.forEach(n => {
            if (n.xyz[2] !== pz) return;
            const dist = Math.max(Math.abs(n.xyz[0] - px), Math.abs(n.xyz[1] - py));

            if (dist <= 3) {
                items.push({
                    html: `
                        <div class="interaction-item" style="border:1px solid #005500; margin-bottom:5px; padding:5px; background: #001100;">
                            <div style="font-weight:bold; color:#0f0;">${n.name}</div>
                            <div style="font-size:0.8em; color:#8f8;">Distance: ${dist}m</div>
                            <div class="interaction-actions">
                                <button onclick="openChat('${n.id}', '${n.name}')" style="color:#0f0; border-color:#0f0;">🗣 Chat</button>
                            </div>
                        </div>
                     `
                });
            }
        });
    }

    // Corpses (Loot)
    if (data.corpses) {
        data.corpses.forEach(c => {
            const dist = Math.max(Math.abs(c.xyz[0] - px), Math.abs(c.xyz[1] - py));
            if (dist <= 1) { // Loot range is short
                items.push({
                    html: `
                        <div class="interaction-item" style="border:1px solid #772222; margin-bottom:5px; padding:5px; background: #220000;">
                            <div style="font-weight:bold; color:#f88;">${c.name}</div>
                            <div class="interaction-actions">
                                 <button onclick="lootBody('${c.id}')">☠️ Loot</button>
                            </div>
                        </div>
                     `
                });
            }
        });
    }

    // Interactive Objects (Secrets/Loot)
    if (data.world.secrets) {
        data.world.secrets.forEach(s => {
            // Filter by distance if coordinates exist (WorldObjects)
            if (s.xyz) {
                const dist = Math.max(Math.abs(s.xyz[0] - px), Math.abs(s.xyz[1] - py));
                if (dist > 3) return; // Hide if far away (3 tile strict vision)
            }

            // Determine Button Label
            let btnLabel = "✋ Interact";
            if (s.name.includes("Chest") || s.name.includes("Crate")) btnLabel = "🗝️ Open";
            else if (s.name.includes("Door")) btnLabel = "🚪 Open";

            items.push({
                html: `
                    <div class="interaction-item" style="border:1px solid #555500; margin-bottom:5px; padding:5px; background: #111100;">
                        <div style="font-weight:bold; color:#ff0;">${s.name}</div>
                        <div class="interaction-actions">
                             <button onclick="interactObject('${s.id}')">${btnLabel}</button>
                        </div>
                    </div>
                 `
            });
        });
    }

    if (items.length === 0) {
        listEl.innerHTML = '<p style="color: #666; font-style: italic;">Nothing of interest...</p>';
    } else {
        listEl.innerHTML = items.map(i => i.html).join('');
    }
}



function openChat(npcId, npcName) {
    activeChatNPCId = npcId;
    window.activeChatNPCName = npcName;
    document.getElementById('chat-modal').style.display = 'flex';

    // Show/Hide Trade Button - Default Hidden until confirmed by Backend
    const tradeBtn = document.getElementById('chat-trade-btn');
    tradeBtn.style.display = 'none';

    // Update Overlaid Name
    const nameEl = document.getElementById('chat-overlaid-name');
    if (nameEl) nameEl.innerText = npcName;

    document.getElementById('chat-history').innerHTML = '';

    // Set Portrait
    const portraitDiv = document.getElementById('chat-portrait');
    let imgUrl = 'static/img/player.png'; // Default/Fallback

    // Simple mapping (Case insensitive check)
    const lowerName = npcName.toLowerCase();
    if (lowerName.includes('elara')) imgUrl = 'static/img/Sorceress.jpg';
    else if (lowerName.includes('gareth')) imgUrl = 'static/img/Warrior.jpg';
    else if (lowerName.includes('skeleton')) imgUrl = 'static/img/skeleton.png';
    else if (lowerName.includes('troll')) imgUrl = 'static/img/bones.png';

    portraitDiv.style.backgroundImage = `url('${imgUrl}')`;
    document.getElementById('chat-input').focus();

    // Auto-fetch greeting/status
    // We send a hidden init message to check trade status and get greeting
    sendChat("__INIT__");
}

function closeChat() {
    activeChatNPCId = null;
    document.getElementById('chat-modal').style.display = 'none';
}

async function sendChat(manualMsg) {
    const input = document.getElementById('chat-input');
    const msg = manualMsg || input.value.trim();
    if (!msg) return;

    // Append Player Message (only if not init)
    const history = document.getElementById('chat-history');
    if (msg !== "__INIT__") {
        history.innerHTML += `<div class="chat-message user"><strong>You:</strong> ${msg}</div>`;
        input.value = '';
    }

    // Scroll to bottom
    history.scrollTop = history.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ npc_index: activeChatNPCId, message: msg })
        });
        const data = await response.json();

        // Reveal Trade Button if allowed
        if (data.can_trade) {
            document.getElementById('chat-trade-btn').style.display = 'inline-block';
        }

        // Append NPC Reply (Handle newlines)
        const formattedReply = data.reply.replace(/\n/g, '<br>');
        // If Init, might be history log vs single reply, but our backend handles it
        // The backend returns "reply".
        history.innerHTML += `<div class="chat-message npc"><strong>${data.npc_name}:</strong> ${formattedReply}</div>`;
        history.scrollTop = history.scrollHeight;

        // Refresh World State (in case NPC triggered an event/door)
        fetchState();

    } catch (e) {
        console.error(e);
        history.innerHTML += `<div style="color: red;">Error: ${e}</div>`;
    }
}

async function interactObject(objectId) {
    try {
        // We'll treat this as a specialized interact call. 
        // Currently /api/interact accepts a 'target' maybe? 
        // The backend `player_interact` took action, target_type, target_index.
        // We need an endpoint for specific interaction or piggyback on 'interact'.
        // Let's implement a direct action call or generic interact.

        // Actually the backend `dm.player_interact` handles "inspect" "secret" "secret_door_1".
        // Let's assume we send this to a generic 'action' endpoint or similar.
        // Or we can POST to /api/interact with body.

        const response = await fetch('/api/interact_specific', { // We might need to create this route
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: "inspect", target_type: "secret", target_id: objectId })
        });

        const data = await response.json();
        if (data.narrative) logMessage(data.narrative);

        // IMMEDIATE UPDATE
        fetchState();

    } catch (e) {
        console.error("Interaction Error:", e);
    }
}

async function interact() {
    // Generic interact (Triangle button)
    try {
        const response = await fetch('/api/interact', { method: 'POST' });
        const data = await response.json();
        if (data.narrative) logMessage(data.narrative);
        fetchState();
    } catch (e) {
        console.error(e);
    }
}

async function useSkill(skillName) {
    if (skillName === 'investigate') {
        logMessage("Investigating surroundings...");
        try {
            const response = await fetch('/api/action/investigate', { method: 'POST' });
            const data = await response.json();

            if (data.narrative) logMessage(data.narrative);

            // Populate Nearby Tab
            if (data.entities && data.entities.length > 0) {
                const listEl = document.getElementById('nearby-list');
                if (listEl) {
                    listEl.innerHTML = '';
                    data.entities.sort((a, b) => a.dist - b.dist);
                    data.entities.forEach(ent => {
                        const div = document.createElement('div');
                        div.className = 'item-entry';
                        div.innerHTML = `<strong>${ent.name}</strong> (${ent.dist}m)<br><span style="font-size:0.8em; color:#aaa;">${ent.status}</span>`;
                        listEl.appendChild(div);
                    });
                    switchTab('nearby');
                }
            } else {
                logMessage("You find nothing new nearby.");
            }
        } catch (e) {
            console.error(e);
            logMessage("Failed to investigate.");
        }
    }
}

async function resetGame() {
    if (!confirm("Are you sure you want to reset the world? All progress will be lost.")) return;
    await fetch('/api/debug/reset', { method: 'POST' });
    window.location.reload();
}

function updateCombatUI(combatState) {
    const controls = document.getElementById('combat-controls');

    if (combatState && combatState.active) {
        controls.style.display = 'block';

        // 1. Update Header / Main Enemy Info
        // For now, we just pick the first monster or current actor if monster
        const nameEl = document.getElementById('combat-enemy-name');
        const hpEl = document.getElementById('combat-enemy-hp');

        // Logic to find "Focused" enemy (default to first monster)
        // In future: Add `focused_target_id` to FE state
        let target = combatState.actors.find(a => a.type === 'monster');

        if (target) {
            // We need HP from the main world list, act doesn't have it
            // combatState.actors only has ID/Type/Init
            // Actually, we can assume the backend might enrich this, 
            // OR we look it up in `window.gameState.world.enemies`?
            // simpler: Let's assume for now we just show "Encounter Active"
            if (nameEl) nameEl.innerText = "Combat Encounter";
            if (hpEl) hpEl.innerText = combatState.actors.length + " Participants";
        }

        // 2. Render Turn Order List (Tiny UI)
        // We'll hijack the bottom of the panel or add a new one?
        // Let's just update the list existing
        let turnHtml = '<div style="font-size:10px; text-align:left; margin-top:5px; border-top:1px solid #555; padding-top:5px;">';
        combatState.actors.forEach((actor, idx) => {
            const isCurrent = (idx === combatState.turn_index);
            const isPlayer = actor.type === 'player';

            // Look up HP
            let hpText = "??";
            let maxHp = "??";
            let isDead = false;

            if (isPlayer && window.gameState && window.gameState.player) {
                hpText = window.gameState.player.hp;
                maxHp = window.gameState.player.max_hp;
            } else if (actor.type === 'monster' && window.gameState && window.gameState.world.enemies) {
                const ent = window.gameState.world.enemies.find(e => e.id === actor.id);
                if (ent) {
                    hpText = ent.hp;
                    maxHp = ent.max_hp;
                } else {
                    isDead = true;
                    hpText = 0;
                }
            }

            const hpDisplay = isDead ? "(Dead)" : `[HP: ${hpText}/${maxHp}]`;

            const color = isCurrent ? '#fff' : '#aaa';
            let bg = 'transparent';
            if (isCurrent) {
                bg = isPlayer ? '#004400' : '#440000'; // Green vs Red
            }
            if (isDead) {
                bg = '#111';
                color = '#555';
            }

            const indicator = isCurrent ? '▶ ' : '';
            turnHtml += `<div style="color:${color}; background:${bg}; padding:2px; display:flex; justify-content:space-between;">
                <span>${indicator}${actor.name}</span>
                <span style="font-size:0.9em;">${hpDisplay} <span style="opacity:0.7; font-size:0.8em;">(Init: ${actor.init})</span></span>
            </div>`;
        });
        turnHtml += '</div>';

        // Append or replace
        const existingList = document.getElementById('turn-order-list');
        if (existingList) {
            existingList.innerHTML = turnHtml;
        } else {
            const listDiv = document.createElement('div');
            listDiv.id = 'turn-order-list';
            listDiv.innerHTML = turnHtml;
            controls.querySelector('.panel-content').appendChild(listDiv);
        }

        // Disable buttons if not player turn
        const isPlayerTurn = combatState.current_turn === 'player';

        // Dynamic Panel Styling
        if (isPlayerTurn) {
            controls.style.borderColor = '#00aa00';
            controls.style.boxShadow = '0 0 15px rgba(0, 50, 0, 0.8)';
            const titleEl = document.getElementById('combat-enemy-name');
            if (titleEl) titleEl.style.color = '#55ff55';
        } else {
            controls.style.borderColor = '#aa0000';
            controls.style.boxShadow = '0 0 15px rgba(50, 0, 0, 0.8)';
            const titleEl = document.getElementById('combat-enemy-name');
            if (titleEl) titleEl.style.color = '#ff5555';
        }

        const btns = controls.querySelectorAll('.btn-combat');
        btns.forEach(b => {
            b.disabled = !isPlayerTurn;
            b.style.opacity = isPlayerTurn ? '1' : '0.4';
            b.style.cursor = isPlayerTurn ? 'pointer' : 'not-allowed';
        });

    } else {
        controls.style.display = 'none';
        // Clear list
        const existingList = document.getElementById('turn-order-list');
        if (existingList) existingList.remove();
    }
}

async function combatAction(actionType) {
    // 1. Lock Controls
    const controls = document.getElementById('combat-controls');
    controls.style.opacity = '0.5';
    controls.style.pointerEvents = 'none';

    try {
        const response = await fetch('/api/combat/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actionType })
        });
        const data = await response.json();

        // 2. Play Events
        if (data.result && data.result.events) {
            await playCombatEvents(data.result.events);
        } else if (data.result && typeof data.result === 'string') {
            // Legacy fallback
            logMessage(data.result);
        }

        // 3. Refresh & Unlock
        fetchState();

    } catch (e) {
        console.error("Combat Action Error:", e);
    } finally {
        controls.style.opacity = '1';
        controls.style.pointerEvents = 'auto';
    }
}

async function playCombatEvents(events) {
    for (const evt of events) {
        if (evt.type === 'text') {
            logMessage(evt.message);
            await new Promise(r => setTimeout(r, 800)); // Read time

        } else if (evt.type === 'anim') {
            // TODO: Trigger actual sprite animation in graphics.js
            // For now, visual shake or flash
            if (evt.actor === 'player') {
                document.body.style.boxShadow = "inset 0 0 50px white";
                setTimeout(() => document.body.style.boxShadow = "none", 100);
            } else if (evt.actor === 'enemy') {
                document.body.style.boxShadow = "inset 0 0 50px red";
                setTimeout(() => document.body.style.boxShadow = "none", 100);
            }
            await new Promise(r => setTimeout(r, 300));

        } else if (evt.type === 'switch_turn' || evt.type === 'turn_switch') { // Support both
            const isEnemy = evt.actor === 'enemy';
            const title = evt.title || (isEnemy ? "Enemy Turn" : "Player Turn");
            const content = evt.content || (isEnemy ? "Attacking..." : "Ready!");
            const color = isEnemy ? "rgba(100, 0, 0, 0.8)" : "rgba(0, 100, 0, 0.8)";
            await showTurnNotification(title, content, 1500, color);

        } else if (evt.type === 'popup') {
            // Check for specific keywords to determine color if not explicit
            let color = "rgba(0, 0, 0, 0.8)"; // Default Black
            if (evt.title && (evt.title.includes("HIT") || evt.title.includes("DAMAGE"))) color = "rgba(150, 0, 0, 0.9)"; // Red
            if (evt.title && (evt.title.includes("VICTORY") || evt.title.includes("Player"))) color = "rgba(0, 150, 0, 0.9)"; // Green
            if (evt.title && (evt.title.includes("MISS"))) color = "rgba(100, 100, 0, 0.9)"; // Yellow/Gold

            // Allow override
            if (evt.color) color = evt.color;

            await showTurnNotification(evt.title, evt.content, evt.duration || 1500, color);
        }
    }
}

function showTurnNotification(title, content, duration = 1500, bgColor = "rgba(0, 0, 0, 0.8)") {
    return new Promise(resolve => {
        const el = document.getElementById('turn-notification');
        const titleEl = el.querySelector('#turn-title');
        const contentEl = el.querySelector('#turn-content');

        if (title) titleEl.textContent = title;
        if (content) contentEl.innerHTML = content;

        el.style.backgroundColor = bgColor;
        el.style.display = 'block';

        // Fade In
        setTimeout(() => el.style.opacity = '1', 10);

        // Wait
        setTimeout(() => {
            // Fade Out
            el.style.opacity = '0';
            setTimeout(() => {
                el.style.display = 'none';
                resolve();
            }, 300);
        }, duration);
    });
}


// --- Inventory System (Grid & Paperdoll) ---
window.updateInventoryUI = function (player) {
    if (!player || !player.inventory) return;

    const equippedDiv = document.getElementById('equipped-slots');
    const backpackUl = document.getElementById('inventory-list'); // Repurpose this container as grid

    // --- 1. Paperdoll Layout ---
    // Define Paper Doll Slots
    const dollSlots = [
        { key: 'head', icon: 'helm', x: 1, y: 0, label: "Head" },
        { key: 'neck', icon: 'ring', x: 2, y: 0, label: "Neck" }, // Close enough
        { key: 'chest', icon: 'chest', x: 1, y: 1, label: "Chest" },
        { key: 'hands', icon: 'glove', x: 0, y: 1, label: "Hands" },
        { key: 'main_hand', icon: 'sword', x: 0, y: 2, label: "Main Hand" },
        { key: 'off_hand', icon: 'shield', x: 2, y: 2, label: "Off Hand" },
        { key: 'legs', icon: 'legs', x: 1, y: 2, label: "Legs" },
        { key: 'feet', icon: 'boots', x: 1, y: 3, label: "Feet" }
    ];

    // Sprite Map (32x32 Grid) for Items.png
    // Row 1: Sword(0,0), Chest(1,0), Helm(2,0), Boots(3,0)
    // Row 2: Potion(0,1), Ore(1,1), Herb(2,1), Coin(3,1)
    // Row 3: Shield(0,2), Key(1,2), Ring(2,2), Glove(3,2)
    const iconMap = {
        'Training Sword': { x: 0, y: 0 }, 'Iron Sword': { x: 0, y: 0 },
        'Cloth Tunic': { x: 1, y: 0 }, 'Leather Armor': { x: 1, y: 0 },
        'Leather Helmet': { x: 2, y: 0 }, 'Iron Helmet': { x: 2, y: 0 },
        'Leather Boots': { x: 3, y: 0 },
        'Healing Potion': { x: 0, y: 1 },
        'Iron Ore': { x: 1, y: 1 },
        'Mystic Herb': { x: 2, y: 1 },
        'Gold': { x: 3, y: 1 },
        'Wooden Shield': { x: 0, y: 2 },
        'Iron Key': { x: 1, y: 2 },
        'Ring': { x: 2, y: 2 },
        'Leather Gloves': { x: 3, y: 2 }
    };

    // Fallback Icons
    const defaultIcons = {
        'head': { x: 2, y: 0 }, 'chest': { x: 1, y: 0 }, 'feet': { x: 3, y: 0 }, 'main_hand': { x: 0, y: 0 },
        'consumable': { x: 0, y: 1 }, 'material': { x: 1, y: 1 }
    };

    // Container for doll
    let dollHtml = `<div style="position:relative; width:120px; height:160px; margin: 0 auto; background:#111; border:1px solid #444;">`;

    dollSlots.forEach(slot => {
        const item = player.inventory.find(i => i.is_equipped && i.slot === slot.key);
        const top = slot.y * 36 + 10;
        const left = slot.x * 36 + 6;

        let content = `<div style="opacity:0.2; font-size:10px; text-align:center; padding-top:10px;">${slot.label}</div>`;
        let tooltip = slot.label;
        let onClick = "";

        if (item) {
            // Find Icon
            let bgPos = "0 0";
            let iDef = iconMap[item.name];
            if (!iDef) {
                // Try fallback by type/slot
                iDef = defaultIcons[slot.key];
            }
            if (iDef) bgPos = `-${iDef.x * 32}px -${iDef.y * 32}px`;

            content = `<div style="width:32px; height:32px; background:url('static/img/items.png') ${bgPos};"></div>`;
            tooltip = `${item.name}\nLevel: ${item.properties.level || 1}`;

            // Interaction: Unequip
            // We use a context/click approach. For now: Click to Unequip
            onClick = `onclick="if(confirm('Unequip ${item.name}?')) unequipItem(${item.id})"`;
        }

        dollHtml += `
            <div class="paper-doll-slot" ${onClick} title="${tooltip}"
                 style="position:absolute; top:${top}px; left:${left}px; width:34px; height:34px; border:1px solid #666; background:#222; cursor:pointer;">
                 ${content}
            </div>
        `;
    });
    dollHtml += `</div>`;
    equippedDiv.innerHTML = dollHtml;


    // --- 2. Grid Backpack ---
    // Max 20 slots (5x4)
    const MAX_SLOTS = 20;
    const bagItems = player.inventory.filter(i => !i.is_equipped);

    // Reuse inventory-list but style it as grid
    backpackUl.style.display = 'grid';
    backpackUl.style.gridTemplateColumns = 'repeat(5, 1fr)';
    backpackUl.style.gap = '4px';
    backpackUl.style.listStyle = 'none';
    backpackUl.style.padding = '0';

    backpackUl.innerHTML = '';

    for (let i = 0; i < MAX_SLOTS; i++) {
        const item = bagItems[i];
        const li = document.createElement('li');
        li.style.width = '36px';
        li.style.height = '36px';
        li.style.background = '#1a1a1a';
        li.style.border = '1px solid #333';
        li.style.position = 'relative';

        if (item) {
            li.style.cursor = 'pointer';
            li.title = item.name;

            // Icon
            let iDef = iconMap[item.name];
            if (!iDef && item.item_type) iDef = defaultIcons[item.item_type];
            if (!iDef) iDef = { x: 0, y: 1 }; // default potion-ish

            const bgPos = `-${iDef.x * 32}px -${iDef.y * 32}px`;

            li.innerHTML = `
                <div style="width:32px; height:32px; margin:1px; background:url('static/img/items.png') ${bgPos};"></div>
                ${item.quantity > 1 ? `<span style="position:absolute; bottom:0; right:1px; color:#fff; font-size:10px; text-shadow:1px 1px 0 #000;">${item.quantiy || item.quantity}</span>` : ''}
            `;

            // Interaction: Equip or Use
            li.onclick = () => {
                // Simple Context Menu Logic could go here
                // For now: Toggle
                if (item.slot) equipItem(item.id);
                else if (item.item_type === 'consumable') useItem(item.id);
            };
        }

        backpackUl.appendChild(li);
    }

    // Update Gold
    if (document.getElementById('stat-gold')) {
        document.getElementById('stat-gold').innerText = player.gold || 0;
    }
};

window.updateSkillsUI = function (player) {
    const list = document.getElementById('skills-list');
    if (!list) return;

    list.innerHTML = '';
    const skills = player.skills || {};

    if (Object.keys(skills).length === 0) {
        list.innerHTML = '<span style="color:#666; font-style:italic;">No skills learnt.</span>';
        return;
    }

    for (const [key, val] of Object.entries(skills)) {
        let level = 0;
        let xp = 0;

        if (typeof val === 'object') {
            level = val.level;
            xp = val.xp;
        } else {
            level = val;
        }

        const nextThreshold = level * 50;
        const pct = Math.min(100, (xp / nextThreshold) * 100);

        const div = document.createElement('div');
        div.style.background = '#222';
        div.style.padding = '5px';
        div.style.borderRadius = '4px';
        div.style.border = '1px solid #444';

        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                <span style="font-weight:bold; text-transform:capitalize;">${key}</span>
                <span style="color:#8f8;">Lvl ${level}</span>
            </div>
            <div style="background:#000; height:4px; width:100%; border-radius:2px;">
                <div style="background:#0f0; width:${pct}%; height:100%; border-radius:2px; transition: width 0.3s;"></div>
            </div>
            <div style="font-size:0.7em; color:#888; text-align:right;">${xp} / ${nextThreshold} XP</div>
        `;
        list.appendChild(div);
    }
};

window.equipItem = async function (id) {
    try {
        const res = await fetch('/api/inventory/equip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();
        // State update happens in main loop usually, but we can force it
        // Or await next fetchState
        window.fetchState(); // from main.js (global)
    } catch (e) { console.error(e); }
};

window.unequipItem = async function (id) {
    try {
        const res = await fetch('/api/inventory/unequip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();
        window.fetchState();
    } catch (e) { console.error(e); }
};

// --- Shop System ---
window.openShop = async function (merchantName) {
    const modal = document.getElementById('shop-modal');
    const title = document.getElementById('shop-merchant-name');
    const goldDisplay = document.getElementById('shop-player-gold');
    const list = document.getElementById('shop-list');

    title.innerText = merchantName;
    if (window.gameState && window.gameState.player) {
        goldDisplay.innerText = window.gameState.player.gold || 0;
    }

    list.innerHTML = 'Loading...';
    modal.style.display = 'block';

    try {
        const res = await fetch('/api/shop/list');
        const data = await res.json();

        // Filter Items for this Merchant
        // Merchant data map
        const inventory = data.shops[merchantName];
        if (!inventory) {
            list.innerHTML = '<p style="color:#888;">"I have nothing to sell right now."</p>';
            return;
        }

        list.innerHTML = '';
        inventory.forEach(itemId => {
            const item = data.items[itemId];
            if (!item) return;

            const row = document.createElement('div');
            row.style.background = '#222';
            row.style.borderBottom = '1px solid #444';
            row.style.padding = '10px';
            row.style.display = 'flex';
            row.style.justifyContent = 'space-between';
            row.style.alignItems = 'center';

            row.innerHTML = `
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="font-size:24px;">${item.properties.icon || '📦'}</div>
                    <div>
                        <div style="color:#fff; font-weight:bold;">${item.name}</div>
                        <div style="color:#aaa; font-size:0.8em;">${item.description}</div>
                        <div style="color:#88f; font-size:0.8em;">Effect: ${item.properties.damage || item.properties.defense || item.properties.heal || 'None'}</div>
                    </div>
                </div>
                <button onclick="buyItem('${itemId}', ${item.value})" style="background:#553300; border:1px solid #d4af37; color:#ffd700; cursor:pointer; padding:5px 10px;">
                    Buy (${item.value}g)
                </button>
            `;
            list.appendChild(row);
        });

    } catch (e) {
        console.error(e);
        list.innerHTML = 'Error loading shop.';
    }
};

window.buyItem = async function (templateId, cost) {
    // Optimistic Gold Check
    const currentGold = window.gameState.player.gold || 0;
    if (currentGold < cost) {
        alert("Not enough gold!");
        return;
    }

    try {
        const res = await fetch('/api/shop/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: templateId })
        });
        const data = await res.json();
        alert(data.message);

        // Refresh State (Gold update)
        await window.fetchState();

        // Refresh Shop UI Gold
        document.getElementById('shop-player-gold').innerText = window.gameState.player.gold;

    } catch (e) { console.error(e); }
};

// --- Tab Switching ---
window.switchCharTab = function (tabName) {
    // Buttons
    document.querySelectorAll('#char-sheet .tab-btn').forEach(b => b.classList.remove('active'));
    // Content
    document.querySelectorAll('#char-sheet .tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('#char-sheet .tab-content').forEach(c => c.style.display = 'none'); // Ensure hidden

    // Activate
    const btn = document.querySelector(`#char-sheet .tab-btn[onclick="switchCharTab('${tabName}')"]`);
    if (btn) btn.classList.add('active');

    const content = document.getElementById(`${tabName}-char-tab`);
    if (content) {
        content.classList.add('active');
        content.style.display = 'block'; // force show

        if (tabName === 'hero') content.style.display = 'flex'; // Hero tab uses flex
    }
};

window.switchTab = function (tabName) {
    document.querySelectorAll('#interaction-panel .tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('#interaction-panel .tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('#interaction-panel .tab-content').forEach(c => c.style.display = 'none');

    const btn = document.querySelector(`#interaction-panel .tab-btn[onclick="switchTab('${tabName}')"]`);
    if (btn) btn.classList.add('active');

    const content = document.getElementById(`${tabName}-tab`);
    if (content) {
        content.classList.add('active');
        content.style.display = 'block';
    }
};

window.lootBody = async function (corpseId) {
    try {
        const res = await fetch('/api/interact_specific', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: "loot", target_type: "corpse", target_id: corpseId })
        });
        const data = await res.json();

        // Check payload type
        let payload = data.narrative;
        if (typeof payload === 'object' && payload.type === 'loot_window') {
            renderLootModal(payload);
        } else {
            // Fallback text
            alert(payload);
        }

        window.fetchState();
    } catch (e) { console.error(e); }
};

window.renderLootModal = function (data) {
    const list = document.getElementById('loot-list');
    list.innerHTML = '';

    document.getElementById('loot-title').innerText = "LOOT: " + data.name;
    document.getElementById('loot-modal').style.display = 'block';

    window.activeLootCorpseId = data.corpse_id;

    if (data.loot.length === 0) {
        list.innerHTML = '<div style="font-style:italic">Empty...</div>';
        return;
    }

    data.loot.forEach(item => {
        const div = document.createElement('div');
        div.style.padding = '5px';
        div.style.borderBottom = '1px solid #444';
        div.style.display = 'flex';
        div.style.justifyContent = 'space-between';
        div.style.alignItems = 'center';

        div.innerHTML = `
            <div style="display:flex; align-items:center;">
                <span style="font-size:20px; margin-right:10px;">${item.icon || '📦'}</span>
                <span>${item.name}</span>
            </div>
            <button onclick="takeLoot('${item.id}')" style="cursor:pointer; background:#522; border:1px solid #844; color:#fcc; padding:2px 8px;">Take</button>
        `;
        list.appendChild(div);
    });
};

window.takeLoot = async function (lootId) {
    try {
        const res = await fetch('/api/loot/take', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ corpse_id: window.activeLootCorpseId, loot_id: lootId })
        });
        const data = await res.json();

        // If corpse is gone (empty), close modal. Otherwise refresh it.
        if (data.message === "Corpse removed." || data.message === "Nothing left.") {
            document.getElementById('loot-modal').style.display = 'none';
            window.fetchState();
        } else {
            lootBody(window.activeLootCorpseId);
        }

    } catch (e) { console.error(e); }
};

window.useItem = async function (id) {
    try {
        const res = await fetch('/api/inventory/use', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();

        alert(data.message);
        window.fetchState();
    } catch (e) { console.error(e); }
};

// --- Crafting System ---
window.refreshCraftingList = async function () {
    const list = document.getElementById('crafting-list');
    if (!list) return;
    list.innerHTML = '<div style="padding:10px; color:#aaa;">Loading recipes...</div>';
    try {
        const res = await fetch('/api/craft/list');
        const recipes = await res.json();
        list.innerHTML = '';

        if (Object.keys(recipes).length === 0) {
            list.innerHTML = '<div style="padding:10px;">No recipes known.</div>';
            return;
        }

        for (const [key, r] of Object.entries(recipes)) {
            let ingredients = [];
            for (let [k, v] of Object.entries(r.ingredients)) ingredients.push(`${v}x ${k}`);

            const div = document.createElement('div');
            div.style.background = '#222';
            div.style.padding = '8px';
            div.style.marginBottom = '4px';
            div.style.border = '1px solid #444';

            div.innerHTML = `
                <div style="color:#d4af37; font-weight:bold;">${r.name}</div>
                <div style="font-size:0.8em; color:#aaa; margin-bottom:4px;">Needs: ${ingredients.join(', ')}</div>
                <button onclick="craftItem('${key}')" style="background:#400; color:#faa; border:1px solid #800; width:100%; cursor:pointer; padding:4px;">Craft</button>
             `;
            list.appendChild(div);
        }
    } catch (e) { console.error(e); }
};

window.craftItem = async function (id) {
    try {
        const res = await fetch('/api/craft/make', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipe_id: id })
        });
        const d = await res.json();
        alert(d.message);
        window.fetchState();
    } catch (e) { console.error(e); }
};

// Overwrite switchCharTab to support crafting
window.switchCharTab = function (tabName) {
    const tabs = ['hero', 'equipment', 'skills', 'crafting'];
    tabs.forEach(t => {
        const pane = document.getElementById(`${t}-char-tab`);
        if (pane) {
            const isActive = (t === tabName);
            pane.classList.toggle('active', isActive);
            pane.style.display = isActive ? 'block' : 'none';
        }
    });

    // Update Button Styles using querySelector
    // We assume buttons are siblings in .tab-header. 
    // This is purely visual.
    const btns = document.querySelectorAll('#char-sheet .tab-btn');
    btns.forEach(btn => {
        if (btn.innerText.toLowerCase().includes(tabName.substring(0, 4))) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    if (tabName === 'crafting') {
        window.refreshCraftingList();
    }
};

window.updateRightPanelItems = function (player) {
    const list = document.getElementById('items-list');
    if (!list) return;

    list.innerHTML = '';

    // 1. Gold
    let gold = player.gold || 0;
    const goldDiv = document.createElement('div');
    goldDiv.className = 'item-entry';
    goldDiv.style.color = '#ffd700';
    goldDiv.style.fontWeight = 'bold';
    goldDiv.style.borderBottom = '1px solid #444';
    goldDiv.style.marginBottom = '5px';
    goldDiv.style.paddingBottom = '5px';
    goldDiv.innerText = `Gold: ${gold}g`;
    list.appendChild(goldDiv);

    // 2. Items
    const items = player.inventory || [];
    if (items.length === 0) {
        const empty = document.createElement('div');
        empty.style.fontStyle = 'italic';
        empty.style.color = '#666';
        empty.innerText = "No items.";
        list.appendChild(empty);
        return;
    }

    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'item-entry';
        div.style.marginBottom = '5px';
        div.style.background = '#222';
        div.style.padding = '5px';

        let status = "";
        let borderStyle = "1px solid #444";

        if (item.is_equipped) {
            status = `<span style="color:#8f8; font-size:0.8em; float:right;">(Equipped)</span>`;
            borderStyle = "1px solid #0f0";
        }

        div.style.border = borderStyle;

        div.innerHTML = `
            <div>
                <span style="font-weight:bold;">${item.name}</span>
                ${status}
            </div>
            <div style="font-size:0.7em; color:#aaa;">${item.properties ? (item.properties.type || item.item_type) : item.item_type}</div>
        `;
        list.appendChild(div);
    });
};

window.interactObject = async function (id) {
    try {
        const res = await fetch('/api/interact_specific', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: "inspect", target_type: "secret", target_id: id })
        });
        const data = await res.json();

        // Check payload type
        let payload = data.narrative;
        if (typeof payload === 'object' && payload.type === 'loot_window') {
            window.renderLootModal(payload);
        } else {
            // Fallback text
            if (payload) alert(payload);
        }

        window.fetchState();
    } catch (e) { console.error(e); }
};
