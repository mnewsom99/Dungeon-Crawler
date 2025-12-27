
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
    if (tradeBtn) tradeBtn.style.display = 'none';

    // Update Overlaid Name
    const nameEl = document.getElementById('chat-overlaid-name');
    if (nameEl) nameEl.innerText = npcName;

    const history = document.getElementById('chat-history');
    history.innerHTML = '<div style="color:yellow; padding:10px;">Connecting to ' + npcName + '...</div>';

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

    // Auto-fetch greeting/status
    console.log("DEBUG: Sending __INIT__ to NPC", npcId);
    sendChat("__INIT__");
}

function closeChat() {
    activeChatNPCId = null;
    document.getElementById('chat-modal').style.display = 'none';
}


// We remove the manual send box in HTML via other edit, but here we update logic
async function sendChat(manualMsg) {
    // If sent via button, manualMsg is the value
    const msg = manualMsg;

    // We don't read from input anymore
    if (!msg) return;

    const history = document.getElementById('chat-history');

    // Append Player Message (Visually distinct for choices)
    // We only show it if it's NOT __INIT__
    if (msg !== "__INIT__") {
        // Find label if possible? For now, just show the choice number/text
        // Or better: Don't show player text history for choices to keep it clean, 
        // OR show "You selected: ..."
        // Let's just append the NPC response logic.
        // Actually, let's look nice:
        // history.innerHTML += `<div class="chat-message user" style="font-style:italic; opacity:0.7;">> ${msg}</div>`;
    }

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ npc_index: activeChatNPCId, message: msg })
        });

        // DEBUG: JSON Parse
        const text = await response.text();
        // console.log("CHAT RAW:", text);

        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            history.innerHTML += `<div style="color:red; background:rgba(0,0,0,0.8);">JSON Error: ${e}<br>${text.substring(0, 100)}</div>`;
            return;
        }

        // Reveal Trade Button if allowed
        if (data.can_trade) {
            document.getElementById('chat-trade-btn').style.display = 'inline-block';
        }

        // Clear previous buttons/history if we want a "fresh page" feel?
        // No, history is good. BUT we should remove OLD buttons from previous turn?
        // The previous buttons were part of the previous HTML block.
        // We can disable them.
        const oldBtns = history.querySelectorAll('button.chat-choice-btn');
        oldBtns.forEach(b => b.disabled = true);

        // 1. Text Content
        // The backend sends: "Text\n\n1. Option A\n2. Option B"
        // We need to parse this to Separate Text from Buttons
        let fullText = data.reply;
        let mainText = fullText;
        let options = [];

        // Simple Parser: Look for "1. ", "2. " pattern at end of string
        // Or better: The backend could return structured data? 
        // For now, let's split by newline and find lines starting with Digit+Dot

        const lines = fullText.split('\n');
        let textLines = [];

        lines.forEach(line => {
            const trim = line.trim();
            // Check regex like "1. Something"
            const match = trim.match(/^(\d+)\.\s+(.*)/);
            if (match) {
                options.push({ id: match[1], label: match[2] });
            } else {
                textLines.push(line);
            }
        });

        mainText = textLines.join('<br>').trim();

        // Render NPC Bubble
        const npcDiv = document.createElement('div');
        npcDiv.className = 'chat-message npc';
        npcDiv.innerHTML = `<strong>${data.npc_name}:</strong> <br>${mainText}`;
        history.appendChild(npcDiv);

        // Render Buttons Container
        if (options.length > 0) {
            const btnContainer = document.createElement('div');
            btnContainer.style.marginTop = '10px';
            btnContainer.style.display = 'flex';
            btnContainer.style.flexDirection = 'column';
            btnContainer.style.gap = '5px';

            options.forEach(opt => {
                const btn = document.createElement('button');
                btn.className = 'chat-choice-btn';
                btn.innerText = opt.label; // Clean label
                btn.style.padding = '8px';
                btn.style.background = '#333';
                btn.style.color = '#fff';
                btn.style.border = '1px solid #555';
                btn.style.cursor = 'pointer';
                btn.style.textAlign = 'left';
                btn.onmouseover = () => btn.style.background = '#444';
                btn.onmouseout = () => btn.style.background = '#333';

                btn.onclick = () => sendChat(opt.id); // Send ID (1, 2, etc)

                btnContainer.appendChild(btn);
            });

            history.appendChild(btnContainer);
        } else {
            // End of convo?
            if (data.reply.includes("(End")) {
                // Maybe close button?
            }
        }

        history.scrollTop = history.scrollHeight;

        // Refresh World State
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

// --- Traditional RPG Combat Menu System ---
let combatMenuState = 'root'; // root, attack, skills, items

function updateCombatUI(combatState) {
    const controls = document.getElementById('combat-controls');
    if (combatState.active) {
        controls.style.display = 'block';
        const contentDiv = controls.querySelector('.panel-content');
        const isPlayerTurn = combatState.current_turn === 'player';

        // Base Structure (Header)
        let html = `
            <div style="text-align:center; margin-bottom:5px; border-bottom:1px solid #444; padding-bottom:5px;">
                <h3 style="margin:0; color:${isPlayerTurn ? '#5f5' : '#f55'}; text-shadow:0 0 5px ${isPlayerTurn ? '#050' : '#500'};">
                    ${isPlayerTurn ? 'YOUR COMMAND' : 'ENEMY TURN'}
                </h3>
            </div>
            <div id="combat-menu-area" style="min-height:160px;"></div>
            <div id="c-turn-order" style="font-size:0.75em; color:#888; border-top:1px dashed #444; margin-top:5px; padding-top:2px;"></div>
        `;

        if (contentDiv.innerHTML.indexOf('YOUR COMMAND') === -1 && contentDiv.innerHTML.indexOf('ENEMY TURN') === -1) {
            contentDiv.innerHTML = html;
        } else {
            // Update Header Title Only if needed
            const h3 = contentDiv.querySelector('h3');
            if (h3) {
                const newText = isPlayerTurn ? 'YOUR COMMAND' : 'ENEMY TURN';
                if (h3.innerText !== newText) {
                    h3.style.color = isPlayerTurn ? '#5f5' : '#f55';
                    h3.innerText = newText;
                    // Only reset menu if turn CHANGED
                    if (isPlayerTurn) combatMenuState = 'root';
                }
            }
        }

        // --- Render Menu Area based on State ---
        const menuArea = document.getElementById('combat-menu-area');
        if (!isPlayerTurn) {
            combatMenuState = 'root'; // Reset for next turn
            menuArea.innerHTML = `<div style="text-align:center; padding-top:40px; color:#aaa; font-style:italic;">Waiting...</div>`;
        } else {
            renderPlayerMenu(menuArea, combatState);
        }

        // --- Render Turn Order ---
        const turnHtml = (combatState.actors || []).map(actor => {
            const isCurrent = (combatState.turn_index !== undefined) && (combatState.actors.indexOf(actor) === combatState.turn_index);
            const style = isCurrent ? "color:#fff; background:#222; font-weight:bold;" : "color:#666;";
            const mark = isCurrent ? "▶" : "";
            return `<span style="${style} margin-right:5px;">${mark}${actor.name}</span>`;
        }).join(" | ");
        const orderEl = document.getElementById('c-turn-order');
        if (orderEl) orderEl.innerHTML = turnHtml;

        if (isPlayerTurn) controls.style.borderColor = '#00aa00';
        else controls.style.borderColor = '#aa0000';

    } else {
        controls.style.display = 'none';
        combatMenuState = 'root'; // Reset
    }
}

function renderPlayerMenu(container, combatState) {
    let html = '';

    // ROOT MENU
    if (combatMenuState === 'root') {
        html = `
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; padding:10px;">
            <button onclick="setCombatMenu('attack')" class="rpg-btn btn-attack">⚔ ATTACK</button>
            <button onclick="setCombatMenu('skills')" class="rpg-btn btn-skills">✨ SKILLS</button>
            <button onclick="setCombatMenu('items')" class="rpg-btn btn-items">🎒 ITEMS</button>
            <button onclick="combatAction('defend')" class="rpg-btn btn-defend">🛡 DEFEND</button>
            <button onclick="combatAction('flee')" class="rpg-btn btn-flee" style="grid-column: span 2;">🏃 FLEE</button>
        </div>
        <div style="text-align:center; font-size:0.7em; color:#555; margin-top:5px;">Move: WASD</div>
        `;
    }

    // ATTACK SUB-MENU (Target Selection)
    else if (combatMenuState === 'attack') {
        const enemies = (window.gameState && window.gameState.world && window.gameState.world.enemies) ? window.gameState.world.enemies : [];

        let listHtml = '';
        if (enemies.length === 0) listHtml = '<div style="color:#666;">No targets.</div>';

        enemies.forEach(e => {
            if (e.hp <= 0) return;
            const px = window.gameState.player.xyz[0];
            const py = window.gameState.player.xyz[1];
            const dist = Math.abs(e.xyz[0] - px) + Math.abs(e.xyz[1] - py);

            // Fog of War: Hide enemies that are too far away (not seen)
            if (dist > 6) return;

            const canHit = dist <= 1.5;

            // Note: We use global function combatAction() which is defined below
            listHtml += `
            <button onclick="${canHit ? `combatAction('attack', '${e.id}')` : ''}" 
                    class="rpg-list-btn" ${canHit ? '' : 'disabled'}
                    style="${canHit ? 'border-left: 4px solid #f00;' : 'opacity:0.5;'}">
                <div style="display:flex; justify-content:space-between; pointer-events:none;">
                    <span>${e.name}</span>
                    <span>${e.hp}/${e.max_hp}</span>
                </div>
                <div style="font-size:0.8em; color:#aaa; pointer-events:none;">${canHit ? 'In Range' : dist + 'm (Too Far)'}</div>
            </button>`;
        });

        html = `
        <div class="rpg-submenu-header">
            <button onclick="setCombatMenu('root')" class="rpg-back-btn">⬅ Back</button>
            <span>Select Target</span>
        </div>
        <div class="rpg-list-container">
            ${listHtml}
        </div>`;
    }

    // SKILLS SUB-MENU
    else if (combatMenuState === 'skills') {
        // Hardcoded skills for now, can be dynamic later
        html = `
        <div class="rpg-submenu-header">
            <button onclick="setCombatMenu('root')" class="rpg-back-btn">⬅ Back</button>
            <span>Select Skill</span>
        </div>
        <div class="rpg-list-container">
            <button onclick="combatAction('second_wind')" class="rpg-list-btn" style="border-left:4px solid #0f0;">
                <b>Second Wind</b><br>
                <span style="font-size:0.8em; color:#aaa;">Recover HP (Bonus Action)</span>
            </button>
            <!-- Placeholder for future skills -->
            <button disabled class="rpg-list-btn" style="opacity:0.5;">
                <b>Fireball</b><br>
                <span style="font-size:0.8em; color:#aaa;">(Locked - Lv 3)</span>
            </button>
        </div>`;
    }

    // ITEMS SUB-MENU
    else if (combatMenuState === 'items') {
        // Need to inventory lookup? For now just Potion placeholder
        html = `
        <div class="rpg-submenu-header">
            <button onclick="setCombatMenu('root')" class="rpg-back-btn">⬅ Back</button>
            <span>Select Item</span>
        </div>
        <div class="rpg-list-container">
            <button onclick="combatAction('use_potion')" class="rpg-list-btn" style="border-left:4px solid #ff0;">
                <b>Healing Potion</b><br>
                <span style="font-size:0.8em; color:#aaa;">Restores 2d4+2 HP</span>
            </button>
        </div>`;
    }

    container.innerHTML = html;
}


const setCombatMenu = function (state) {
    combatMenuState = state;
    const controls = document.getElementById('combat-controls');
    if (controls) {
        const area = document.getElementById('combat-menu-area');
        if (area && window.gameState && window.gameState.combat) {
            renderPlayerMenu(area, window.gameState.combat);
        }
    }
};
window.setCombatMenu = setCombatMenu;


const combatAction = async function (actionType, targetId = null) {
    const controls = document.getElementById('combat-controls');
    if (controls) {
        controls.style.opacity = '0.5';
        controls.style.pointerEvents = 'none';
        // Add loading spinner?
    }

    console.log("Combat Triggered:", actionType, targetId); // Debug Log

    try {
        const payload = { action: actionType };
        if (targetId) payload.target_id = targetId;

        const response = await fetch('/api/combat/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.result && data.result.events) {
            await playCombatEvents(data.result.events);
        } else if (data.result && typeof data.result === 'string') {
            logMessage(data.result);
        }

        fetchState();

    } catch (e) {
        console.error("Combat Action Error:", e);
    } finally {
        if (controls) {
            controls.style.opacity = '1';
            controls.style.pointerEvents = 'auto';
        }
    }
};
window.combatAction = combatAction; // Force Global

async function playCombatEvents(events) {
    for (const evt of events) {
        if (evt.type === 'text') {
            logMessage(evt.message);
            await new Promise(r => setTimeout(r, 800));
        } else if (evt.type === 'anim') {

            if (evt.actor === 'player') {
                audioSystem.play('attack');
                document.body.style.boxShadow = "inset 0 0 50px white";
                setTimeout(() => document.body.style.boxShadow = "none", 100);
            } else if (evt.actor === 'enemy') {
                audioSystem.play('hit');
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
            if (evt.title && (evt.title.includes("VICTORY") || evt.title.includes("Player"))) {
                color = "rgba(0, 150, 0, 0.9)"; // Green
                audioSystem.play('coin'); // Victory Fanfare substitute
            }
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
    // Emoji Icons Fallback (Primary now)
    const iconMap = {
        'Training Sword': "⚔️", 'Iron Sword': "⚔️",
        'Cloth Tunic': "👕", 'Leather Armor': "👕",
        'Leather Helmet': "🧢", 'Iron Helmet': "🪖",
        'Leather Boots': "👢",
        'Healing Potion': "🧪",
        'Iron Ore': "🪨",
        'Mystic Herb': "🌿",
        'Gold': "💰",
        'Wooden Shield': "🛡️",
        'Iron Key': "🔑",
        'Ring': "💍",
        'Leather Gloves': "🧤"
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
            // Find Icon (Emoji preferred)
            let iconStr = "📦";
            if (item.properties && item.properties.icon) iconStr = item.properties.icon;
            else if (iconMap[item.name]) iconStr = iconMap[item.name];

            content = `<div style="font-size:24px; line-height:34px; text-align:center;">${iconStr}</div>`;
            tooltip = `${item.name}\n${item.item_type}`;

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

            // Icon (Emoji)
            let iconStr = "📦";
            if (item.properties && item.properties.icon) iconStr = item.properties.icon;
            else if (iconMap[item.name]) iconStr = iconMap[item.name];

            li.innerHTML = `
                <div style="font-size:24px; line-height:36px; text-align:center;">${iconStr}</div>
                ${item.quantity > 1 ? `<span style="position:absolute; bottom:0; right:1px; color:#fff; font-size:10px; text-shadow:1px 1px 0 #000;">${item.quantiy || item.quantity}</span>` : ''}
            `;

            // Interaction: Equip or Use
            li.onclick = () => {
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

        audioSystem.play('equip');

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
        audioSystem.play('equip');
        window.fetchState();
    } catch (e) { console.error(e); }
};

// --- Shop System ---
// --- Shop System (Dual Grid + Drag&Drop) ---
window.openShop = async function (merchantName) {
    const modal = document.getElementById('shop-modal');
    // Sanity check: if it was minimized, closing and re-opening might not reset position if we don't clear it.
    // The draggable logic uses internal closures for restoreX/Y, which are per-element but scoped to the `makeDraggable` call.
    // We can't access those closures easily. 
    // However, we can simply force the modal to center screen style here.

    modal.style.top = '10%';
    modal.style.left = '50%';
    modal.style.transform = 'translateX(-50%)';
    modal.style.width = '700px';
    modal.style.height = '500px';

    // Ensure content is visible (un-minimize)
    const content = modal.querySelector('.panel-content');
    if (content) content.style.display = 'flex'; // It uses flex layout now
    const minBtn = modal.querySelector('.minimize-btn');
    if (minBtn) minBtn.innerText = 'X'; // Use X as close, or _ if we supported minimize

    const title = document.getElementById('shop-merchant-name');
    const goldDisplay = document.getElementById('shop-player-gold');
    const merchantList = document.getElementById('shop-list');
    const playerList = document.getElementById('player-shop-inv');

    title.innerText = merchantName;
    if (window.gameState && window.gameState.player) {
        goldDisplay.innerText = window.gameState.player.gold || 0;
    }

    merchantList.innerHTML = '<div style="color:#aaa;">Loading...</div>';
    playerList.innerHTML = '<div style="color:#aaa;">Loading...</div>';

    modal.style.display = 'block';

    try {
        const res = await fetch('/api/shop/list');
        const data = await res.json();

        // Render Function for reuse
        const renderGrid = (container, items, source) => {
            container.innerHTML = '';

            if (items.length === 0) {
                container.innerHTML = '<div style="grid-column:1/-1; color:#555; font-style:italic; padding:10px;">Empty</div>';
                return;
            }

            items.forEach(item => {
                const slot = document.createElement('div');
                slot.draggable = true;
                slot.className = 'shop-slot';
                // Inline styles for grid box
                slot.style.width = '42px';
                slot.style.height = '42px';
                slot.style.background = '#1a1a1a';
                slot.style.border = '1px solid #444';
                slot.style.borderRadius = '4px';
                slot.style.display = 'flex';
                slot.style.alignItems = 'center';
                slot.style.justifyContent = 'center';
                slot.style.fontSize = '24px';
                slot.style.cursor = 'grab';
                slot.style.position = 'relative';

                // Data
                const cost = source === 'merchant' ? item.value : Math.max(1, Math.floor((item.value || 0) / 2));
                const itemIcon = (item.properties && item.properties.icon) ? item.properties.icon : '📦';

                slot.innerHTML = itemIcon;

                // Tooltip
                slot.title = `${item.name}\n${source === 'merchant' ? 'Buy for ' : 'Sell for '} ${cost}g\n${item.description || ''}`;

                // Drag Events
                slot.ondragstart = (e) => {
                    e.dataTransfer.setData("text/plain", JSON.stringify({
                        source: source,
                        id: item.id || item.template_id, // Merchant items use template_id logic probably?
                        cost: cost,
                        name: item.name
                    }));
                    slot.style.opacity = '0.5';
                };

                slot.ondragend = () => {
                    slot.style.opacity = '1';
                };

                // Click fallback
                slot.onclick = () => {
                    if (confirm(source === 'merchant' ? `Buy ${item.name} for ${cost}g?` : `Sell ${item.name} for ${cost}g?`)) {
                        if (source === 'merchant') buyItem(item.id || item.template_id, cost); // logic expects template_id usually
                        else sellItem(item.id);
                    }
                };

                container.appendChild(slot);
            });
        };

        // 1. Merchant Items
        const merchInvIds = data.shops[merchantName] || [];
        const merchItems = merchInvIds.map(id => {
            let t = data.items[id];
            if (t) t.template_id = id; // Ensure ID is passed
            return t;
        }).filter(x => x);

        renderGrid(merchantList, merchItems, 'merchant');

        // 2. Player Items
        // We rely on global gameState
        const playerItems = window.gameState.player.inventory || [];
        // Filter out equipped items? Usually yes
        renderGrid(playerList, playerItems.filter(i => !i.is_equipped), 'player');


        // Setup Drop Zones
        // Drop on Player List = BUY
        playerList.ondragover = (e) => e.preventDefault(); // Allow drop
        playerList.ondrop = (e) => {
            e.preventDefault();
            const raw = e.dataTransfer.getData("text/plain");
            if (!raw) return;
            const d = JSON.parse(raw);

            if (d.source === 'merchant') {
                buyItem(d.id, d.cost);
            }
        };

        // Drop on Merchant List = SELL
        merchantList.ondragover = (e) => e.preventDefault();
        merchantList.ondrop = (e) => {
            e.preventDefault();
            const raw = e.dataTransfer.getData("text/plain");
            if (!raw) return;
            const d = JSON.parse(raw);

            if (d.source === 'player') {
                sellItem(d.id);
            }
        };


    } catch (e) {
        console.error(e);
        merchantList.innerHTML = 'Error loading shop.';
    }
};

window.buyItem = async function (templateId, cost) {
    // Check Gold First
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

        // Refresh
        await window.fetchState();
        document.getElementById('shop-player-gold').innerText = window.gameState.player.gold;

        // Re-open/Refresh shop visuals?
        // simple way: just re-call openShop with current name
        const name = document.getElementById('shop-merchant-name').innerText;
        window.openShop(name);

        audioSystem.play('coin');

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

        // Refresh
        await window.fetchState();
        document.getElementById('shop-player-gold').innerText = window.gameState.player.gold;

        const name = document.getElementById('shop-merchant-name').innerText;
        window.openShop(name); // Refresh inventory lists

        audioSystem.play('coin');

    } catch (e) { console.error(e); }
};

// --- Tab Switching ---
window.switchCharTab = function (tabName) {
    audioSystem.play('page');
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

        // Popup Notification for Loot
        if (data.message && !data.message.includes("Nothing left") && !data.message.includes("removed")) {
            showTurnNotification("ACQUIRED", data.message, 1500, "rgba(0, 100, 0, 0.8)");
            if (window.audioSystem) window.audioSystem.play('coin');
        }

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

    // Icon Mapping for Box Display
    const iconMap = {
        'Training Sword': "⚔️", 'Iron Sword': "⚔️", 'Steel Sword': "⚔️", 'Rusty Dagger': "🗡️", 'Steel Dagger': "🗡️",
        'Cloth Tunic': "👕", 'Leather Armor': "👕", 'Chainmail': "⛓️",
        'Leather Helmet': "🧢", 'Iron Helmet': "🪖",
        'Leather Boots': "👢",
        'Healing Potion': "🧪",
        'Iron Ore': "🪨",
        'Mystic Herb': "🌿",
        'Gold': "💰",
        'Wooden Shield': "🛡️", 'Iron Shield': "🛡️",
        'Iron Key': "🔑",
        'Ring': "💍",
        'Leather Gloves': "🧤"
    };

    // 1. Gold Display
    let gold = player.gold || 0;
    const goldDiv = document.createElement('div');
    goldDiv.className = 'item-entry'; // Reuse class for styling if needed, or override
    goldDiv.style.color = '#ffd700';
    goldDiv.style.fontWeight = 'bold';
    goldDiv.style.borderBottom = '1px solid #444';
    goldDiv.style.marginBottom = '10px';
    goldDiv.style.paddingBottom = '5px';
    goldDiv.style.background = 'none'; // Clear default
    goldDiv.style.border = 'none';
    goldDiv.style.borderBottom = '1px solid #444';
    goldDiv.innerText = `Gold: ${gold}g`;
    list.appendChild(goldDiv);

    // 2. Items Grid Container
    const grid = document.createElement('div');
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(40px, 1fr))';
    grid.style.gap = '8px';

    const items = player.inventory || [];

    if (items.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; color:#666; font-style:italic;">Bag is empty.</div>';
    } else {
        items.forEach(item => {
            const slot = document.createElement('div');
            // Style Box
            slot.style.width = '42px';
            slot.style.height = '42px';
            slot.style.background = '#1a1a1a';
            slot.style.border = '1px solid #444';
            slot.style.borderRadius = '6px';
            slot.style.position = 'relative';
            slot.style.cursor = 'help'; // Shows it has info
            slot.style.display = 'flex';
            slot.style.alignItems = 'center';
            slot.style.justifyContent = 'center';
            slot.style.fontSize = '24px';
            slot.style.transition = 'all 0.1s';

            // Hover Effect
            slot.onmouseover = () => { slot.style.borderColor = '#888'; slot.style.background = '#222'; };
            slot.onmouseout = () => {
                slot.style.borderColor = item.is_equipped ? '#0f0' : '#444';
                slot.style.background = '#1a1a1a';
            };

            // Highlight equipped
            if (item.is_equipped) {
                slot.style.borderColor = '#0f0';
                slot.style.boxShadow = '0 0 5px rgba(0, 255, 0, 0.3)';
            }

            // Icon
            let iconStr = "📦";
            if (item.properties && item.properties.icon) iconStr = item.properties.icon;
            else if (iconMap[item.name]) iconStr = iconMap[item.name];

            slot.innerText = iconStr;

            // Tooltip (Description on Hover)
            let desc = `${item.name}`;
            if (item.is_equipped) desc += " (Equipped)";
            if (item.quantity > 1) desc += ` x${item.quantity}`;

            // Add Stats if available
            const props = item.properties || {};
            if (props.damage) desc += `\nDamage: ${props.damage}`;
            if (props.defense) desc += `\nDefense: +${props.defense}`;
            if (props.heal) desc += `\nHeals: ${props.heal}`;
            if (item.item_type) desc += `\nType: ${item.item_type}`;

            slot.title = desc;

            // Quantity Badge
            if (item.quantity > 1) {
                const badge = document.createElement('span');
                badge.style.position = 'absolute';
                badge.style.bottom = '1px';
                badge.style.right = '3px';
                badge.style.fontSize = '10px';
                badge.style.color = '#fff';
                badge.style.fontWeight = 'bold';
                badge.style.textShadow = '1px 1px 0 #000';
                badge.innerText = item.quantity;
                slot.appendChild(badge);
            }

            // Optional: Click to equip/use?
            // The user just asked for display, but interaction makes sense.
            slot.onclick = () => {
                if (confirm(`Interact with ${item.name}?`)) {
                    if (item.is_equipped) unequipItem(item.id);
                    else if (item.slot) equipItem(item.id);
                    else if (item.item_type === 'consumable') useItem(item.id);
                }
            };

            grid.appendChild(slot);
        });
    }

    list.appendChild(grid);
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
            if (payload) {
                window.updateLog(payload);
                if (payload.includes("Gathered") || payload.includes("Found") || payload.includes("Success")) {
                    showTurnNotification("GATHERED", payload, 1500, "rgba(0, 100, 0, 0.8)");
                    if (window.audioSystem) window.audioSystem.play('coin');
                }
            }
        }

        window.fetchState();
    } catch (e) { console.error(e); }
};

window.performAction = async function (actionName) {
    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actionName })
        });
        const data = await res.json();

        if (data.narrative && window.updateLog) {
            window.updateLog(data.narrative);
        }

        // Refresh
        window.fetchState();

    } catch (e) { console.error(e); }
};

// --- Logging ---
window.updateLog = function (msg) {
    if (!msg) return;
    const logDiv = document.getElementById('log-content');
    if (!logDiv) return;

    // Check duplicates to avoid spam
    if (logDiv.lastElementChild && logDiv.lastElementChild.innerHTML.includes(msg)) return;

    const p = document.createElement('p');
    p.innerHTML = msg;
    p.style.margin = "5px 0";
    p.style.borderBottom = "1px solid #333";
    p.style.paddingBottom = "2px";

    // Animate
    p.style.opacity = "0";
    logDiv.appendChild(p);

    // Trigger Reflow
    void p.offsetWidth;
    p.style.transition = "opacity 0.5s";
    p.style.opacity = "1";

    logDiv.scrollTop = logDiv.scrollHeight;
};

// --- Stats Update ---
window.updateHeroStats = function (player) {
    if (!player) return;

    // HP
    const hpEl = document.getElementById('stat-hp');
    if (hpEl) {
        hpEl.innerText = `${player.hp}/${player.max_hp}`;
        // Color coding
        if (player.hp <= player.max_hp * 0.3) hpEl.style.color = '#f55';
        else if (player.hp <= player.max_hp * 0.7) hpEl.style.color = '#fa0';
        else hpEl.style.color = '#0f0';
    }

    // Core Stats
    const stats = player.stats || {};
    ['str', 'dex', 'con', 'int', 'wis', 'cha'].forEach(key => {
        const el = document.getElementById(`stat-${key}`);
        if (el) {
            // Backend sends lowercase keys usually, but let's be safe
            const val = stats[key] !== undefined ? stats[key] : (stats[key.toUpperCase()] || 0);
            el.innerText = val;
        }
    });
};

console.log("UI.JS Ready v26");
