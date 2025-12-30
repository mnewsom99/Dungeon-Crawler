
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

    // Resources (Tiles)
    if (data.world.map) {
        for (let dx = -1; dx <= 1; dx++) {
            for (let dy = -1; dy <= 1; dy++) {
                if (dx === 0 && dy === 0) continue;
                const tx = px + dx;
                const ty = py + dy;
                const key = `${tx},${ty},${pz}`;

                const tileType = data.world.map[key];
                if (!tileType) continue;

                if (tileType === 'rock') {
                    items.push({
                        html: `
                            <div class="interaction-item" style="border:1px solid #555; margin-bottom:5px; padding:5px; background: #222;">
                                <div style="font-weight:bold; color:#aaa;">Iron Ore</div>
                                <div class="interaction-actions">
                                     <button onclick="performTileAction('mine', '${key}')">⛏️ Mine</button>
                                </div>
                            </div>
                         `
                    });
                } else if (tileType === 'flower_pot') {
                    items.push({
                        html: `
                            <div class="interaction-item" style="border:1px solid #0a0; margin-bottom:5px; padding:5px; background: #020;">
                                <div style="font-weight:bold; color:#afa;">Mystic Herb</div>
                                <div class="interaction-actions">
                                     <button onclick="performTileAction('gather', '${key}')">🌿 Gather</button>
                                </div>
                            </div>
                         `
                    });
                }
            }
        }
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

    // Also close Shop if open (User requested)
    const shopModal = document.getElementById('shop-modal');
    if (shopModal) shopModal.style.display = 'none';
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

// --- MODULES EXTRACTED ---
// combat-logic -> ui_combat.js
// inventory-logic -> ui_inventory.js


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
        if (actionName === 'investigate' && window.updateLog) {
            window.updateLog("<span style='color:#aaa'>Investigating area...</span>");
        }

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
// --- Stats Update ---
window.updateHeroStats = function (player) {
    if (!player) return;

    // HP
    const hpEl = document.getElementById('stat-hp');
    if (hpEl) {
        hpEl.innerText = `${player.hp}/${player.max_hp}`;
        if (player.hp <= player.max_hp * 0.3) hpEl.style.color = '#f55';
        else if (player.hp <= player.max_hp * 0.7) hpEl.style.color = '#fa0';
        else hpEl.style.color = '#0f0';
    }

    // Level & XP (Inject if missing)
    let lvlEl = document.getElementById('stat-lvl');
    if (!lvlEl) {
        // Add row to table if not exists
        const tbody = document.getElementById('stat-body');
        if (tbody) {
            const row = document.createElement('tr');
            row.innerHTML = `<td>LVL</td><td id="stat-lvl" style="color:#d4af37; font-weight:bold;">1</td><td>Level (XP: <span id="stat-xp">0</span>)</td>`;
            tbody.insertBefore(row, tbody.firstChild);
            lvlEl = document.getElementById('stat-lvl');
        }
    }
    if (lvlEl) {
        lvlEl.innerText = player.level || 1;
        const xpEl = document.getElementById('stat-xp');
        if (xpEl) xpEl.innerText = player.xp || 0;
    }

    // Core Stats
    const stats = player.stats || {};
    const points = stats.unspent_points || 0;

    // Update Header with Points
    const h3 = document.querySelector('.stat-block h3');
    if (h3) {
        if (points > 0) {
            h3.innerHTML = `Stats <span style="color:#ff0; font-size:0.8em;">(Points: ${points})</span>`;
        } else {
            h3.innerText = "Stats";
        }
    }

    ['str', 'dex', 'con', 'int', 'wis', 'cha'].forEach(key => {
        const el = document.getElementById(`stat-${key}`);
        if (el) {
            const val = stats[key] !== undefined ? stats[key] : (stats[key.toUpperCase()] || 0);

            // If points available, show upgrade button
            if (points > 0) {
                el.innerHTML = `
                    ${val} 
                    <button onclick="upgradeStat('${key}')" 
                        style="background:#0f0; color:#000; padding:0 4px; border:none; cursor:pointer; font-weight:bold; margin-left:5px; border-radius:3px;">
                        +
                    </button>
                `;
            } else {
                el.innerText = val;
            }
        }
    });

    // Check for Level 4 Feat
    checkForLevelUpFeats(player);
};

// --- Level Up Feat Modal ---
function checkForLevelUpFeats(player) {
    if (!player || player.level < 4) return;

    // Check Feat Capacity (Every 4 levels)
    const allowed = Math.floor(player.level / 4);

    // Check currently known feats
    const skills = player.skills || {};
    const feats = ['cleave', 'heavy_strike', 'kick', 'rage'];
    const knownCount = feats.filter(f => skills[f]).length;

    // If we have room for a feat
    if (knownCount < allowed) {
        if (document.getElementById('feat-modal')) return; // Already showing

        console.log("TRIGGERING LEVEL UP FEAT SELECTION");

        const modal = document.createElement('div');
        modal.id = 'feat-modal';
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.background = 'rgba(0,0,0,0.85)';
        modal.style.zIndex = '9999';
        modal.style.display = 'flex';
        modal.style.justifyContent = 'center';
        modal.style.alignItems = 'center';

        // Helper to generate card
        const renderCard = (id, name, type, desc, color) => {
            const isKnown = !!skills[id];
            const style = isKnown ? "opacity:0.4; pointer-events:none; border:1px solid #333;" : "cursor:pointer; border:1px solid #444;";
            const bg = isKnown ? "#111" : "#222";
            const click = isKnown ? "" : `onclick="selectSkill('${id}')"`;
            const badge = isKnown ? '<span style="color:#fff; background:#444; padding:2px 5px; font-size:0.7em;">KNOWN</span>' : '';

            return `
                <div class="feat-card" ${click} style="padding: 10px; background: ${bg}; ${style} position:relative;">
                    <div style="display:flex; justify-content:space-between;">
                        <strong style="color: ${color};">${name} (${type})</strong>
                        ${badge}
                    </div>
                    <div style="font-size: 0.9em; color: #aaa;">${desc}</div>
                </div>
            `;
        };

        const content = document.createElement('div');
        content.style.background = '#1a0a0a';
        content.style.border = '2px solid #d4af37';
        content.style.padding = '20px';
        content.style.width = '600px';
        content.style.textAlign = 'center';
        content.style.color = '#fff';
        content.innerHTML = `
            <h2 style="color: #ffd700; margin-top: 0;">Level ${player.level} Reached!</h2>
            <p style="color: #ccc;">You have honed your skills. Select a new feat (${knownCount}/${allowed}).</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; text-align: left;">
                ${renderCard('cleave', '🛑 Cleave', 'Action', 'Strike all enemies within reach.', '#f55')}
                ${renderCard('heavy_strike', '⚔ Heavy Strike', 'Action', 'Massive damage to one target.', '#f55')}
                ${renderCard('kick', '👢 Kick', 'Bonus', 'Knockdown enemy (Stun).', '#fa0')}
                ${renderCard('rage', '😡 Rage', 'Bonus', '+2 Damage for 2 turns.', '#f00')}
            </div>
        `;

        modal.appendChild(content);
        document.body.appendChild(modal);

        // Hover effects
        modal.querySelectorAll('.feat-card').forEach(c => {
            if (!c.style.pointerEvents.includes('none')) {
                c.onmouseenter = () => c.style.borderColor = '#d4af37';
                c.onmouseleave = () => c.style.borderColor = '#444';
            }
        });
    }
}

window.selectSkill = async function (skillId) {
    if (!confirm(`Are you sure you want to learn ${skillId.replace('_', ' ').toUpperCase()}?`)) return;

    try {
        const res = await fetch('/api/skills/choose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skill_id: skillId })
        });
        const data = await res.json();

        if (data.message) {
            const m = document.getElementById('feat-modal');
            if (m) m.remove();
            alert(data.message);
        }
        window.fetchState();
    } catch (e) { console.error(e); }
};

window.upgradeStat = async function (statName) {
    try {
        const res = await fetch('/api/stats/upgrade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stat: statName })
        });
        const data = await res.json();

        // Visual Feedback
        const el = document.getElementById(`stat-${statName}`);
        if (el) el.style.color = "#0f0";
        setTimeout(() => { if (el) el.style.color = ""; }, 500);

        // Refresh
        window.fetchState();

        // Show message
        if (data.message) {
            // Optional: log or toast
            console.log(data.message);
        }
    } catch (e) { console.error(e); }
};

console.log("UI.JS Ready v26");
window.logMessage = window.updateLog;

window.performTileAction = async function (action, targetId) {
    // targetId is "x,y,z"
    try {
        const res = await fetch('/api/interact_specific', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, target_type: 'tile', target_id: targetId })
        });
        const data = await res.json();
        if (data.narrative && window.updateLog) window.updateLog(data.narrative);
        window.fetchState();
    } catch (e) { console.error(e); }
};

window.updateQuestList = function (data) {
    const listEl = document.getElementById('quest-list');
    if (!listEl) return;
    listEl.innerHTML = '';

    // data.player.quest_log is the source of truth
    const quests = (data.player && data.player.quest_log) ? data.player.quest_log : [];
    console.log("DEBUG: UI received quests:", quests);

    if (quests.length === 0) {
        listEl.innerHTML = '<p style="color: #666; font-style: italic;">No active quests.</p>';
        return;
    }

    quests.forEach(q => {
        const div = document.createElement('div');
        div.className = 'interaction-item';
        div.style.borderLeft = "3px solid #ffd700";
        div.style.marginBottom = "5px";
        div.style.padding = "5px";
        div.style.background = "#221100";

        const title = q.title || q;
        const desc = q.description || "Active Quest";

        div.innerHTML = `
            <div style="color: #ffd700; font-weight: bold;">${title}</div>
            <div style="font-size: 0.9em; color: #aaa;">${desc}</div>
        `;
        listEl.appendChild(div);
    });
};
