

// Chat & UI Interaction Logic

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

    // Interactive Objects (Secrets/Loot)
    if (data.world.secrets) {
        data.world.secrets.forEach(s => {
            items.push({
                html: `
                    <div class="interaction-item" style="border:1px solid #555500; margin-bottom:5px; padding:5px; background: #111100;">
                        <div style="font-weight:bold; color:#ff0;">${s.name}</div>
                        <div class="interaction-actions">
                             <button onclick="interactObject('${s.id}')">✋ Inspect</button>
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
    document.getElementById('chat-modal').style.display = 'flex';

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
}

function closeChat() {
    activeChatNPCId = null;
    document.getElementById('chat-modal').style.display = 'none';
}

async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    // Append Player Message
    const history = document.getElementById('chat-history');
    history.innerHTML += `<div class="chat-message user"><strong>You:</strong> ${msg}</div>`;
    input.value = '';

    // Scroll to bottom
    history.scrollTop = history.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ npc_index: activeChatNPCId, message: msg })
        });
        const data = await response.json();

        // Append NPC Reply
        history.innerHTML += `<div class="chat-message npc"><strong>${data.npc_name}:</strong> ${data.reply}</div>`;
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
    const dpad = document.querySelector('.dpad-grid');

    if (combatState && combatState.active) {
        controls.style.display = 'block';

        // Update Info
        const nameEl = document.getElementById('combat-enemy-name');
        const hpEl = document.getElementById('combat-enemy-hp');

        if (nameEl) nameEl.innerText = combatState.enemy_name || "Unknown Enemy";
        if (hpEl) hpEl.innerText = combatState.enemy_hp !== undefined ? combatState.enemy_hp : "?";

    } else {
        controls.style.display = 'none';
    }
}

async function combatAction(actionType) {
    try {
        const response = await fetch('/api/combat/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actionType })
        });
        const data = await response.json();

        if (data.narrative) logMessage(data.narrative);

        // Refresh State (check if combat ended)
        fetchState();

    } catch (e) {
        console.error("Combat Action Error:", e);
    }
}

