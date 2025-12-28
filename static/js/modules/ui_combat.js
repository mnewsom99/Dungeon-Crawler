// --- COMBAT MODULE ---
// Extracted from ui.js

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

        if (!document.getElementById('combat-menu-area')) {
            contentDiv.innerHTML = html;
        } else {
            // Update Header Title Only if needed
            const h3 = contentDiv.querySelector('h3');
            if (h3) {
                const newText = isPlayerTurn ? 'YOUR COMMAND' : 'ENEMY TURN';
                // Simple color update
                h3.style.color = isPlayerTurn ? '#5f5' : '#f55';
                h3.style.textShadow = `0 0 5px ${isPlayerTurn ? '#050' : '#500'}`;
                if (h3.innerText !== newText) {
                    h3.innerText = newText;
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
        if (orderEl && orderEl.innerHTML !== turnHtml) orderEl.innerHTML = turnHtml;

        if (isPlayerTurn) controls.style.borderColor = '#00aa00';
        else controls.style.borderColor = '#aa0000';

    } else {
        if (controls.style.display !== 'none') {
            controls.style.display = 'none';
            console.log("Combat Ended. Hiding UI.");
        }
        combatMenuState = 'root'; // Reset
    }
}

// Global state to track which tab is active in the Combat Menu
let combatTab = 'move'; // 'move', 'action', 'bonus'

function renderPlayerMenu(container, combatState) {
    // If we are showing the processing spinner, DO NOT overwrite it until we get a new result!
    // We check this by seeing if our "dataset.oldHTML" exists (set by combatAction)
    // Actually, if we are 'processing', we probably shouldn't re-render unless the 'combatState' has advanced?
    // But 'combatState' comes from the server. If server updated, we *should* render.
    // Let's rely on the html-diff check.

    let html = '';

    // Status Header (Tab Bar)
    // Always visible, allows switching, greys out if resource empty
    const hasMove = combatState.moves_left > 0;
    const hasAction = combatState.actions_left > 0;
    const hasBonus = combatState.bonus_actions_left > 0;

    // Auto-switch tab if current is exhausted and strictly impossible? 
    // No, user wants control. But maybe visual feedback.

    html += `
        <div style="display:flex; gap:2px; margin-bottom:10px;">
             ${_renderTabBtn('move', 'MOVE', combatState.moves_left, combatTab === 'move')}
             ${_renderTabBtn('action', 'ACTION', combatState.actions_left, combatTab === 'action')}
             ${_renderTabBtn('bonus', 'BONUS', combatState.bonus_actions_left, combatTab === 'bonus')}
        </div>
    `;

    html += `<div style="min-height: 120px; border:1px solid #333; padding:5px; margin-bottom:5px; background:rgba(0,0,0,0.3);">`;

    // TAB CONTENT: MOVE
    if (combatTab === 'move') {
        if (hasMove) {
            html += `
                <div style="text-align:center; padding-top:10px;">
                    <button class="rpg-btn btn-move" style="pointer-events:none; border-color:#fff;">WASD / Arrows</button>
                    <p style="color:#aaa; font-size:0.8em; margin-top:5px;">Move on map to spend moves.</p>
                </div>
             `;
        } else {
            html += `<div style="text-align:center; color:#555; padding-top:20px;">No movement remaining.</div>`;
        }
    }

    // TAB CONTENT: ACTION
    else if (combatTab === 'action') {
        if (hasAction) {
            html += `<div style="display:grid; grid-template-columns:1fr; gap:5px;">`;

            // Dynamic Enemy List for Attacks
            const enemies = (window.gameState && window.gameState.world && window.gameState.world.enemies) ? window.gameState.world.enemies : [];
            let visibleCount = 0;
            enemies.forEach(e => {
                if (e.hp <= 0) return;
                const px = window.gameState.player.xyz[0];
                const py = window.gameState.player.xyz[1];
                const dx = e.xyz[0] - px;
                const dy = e.xyz[1] - py;
                const distEucl = Math.sqrt(dx * dx + dy * dy);
                const distManh = Math.abs(dx) + Math.abs(dy);

                // VISIBILITY CHECK: Only show if within 6 tiles (~torch radius)
                if (distEucl > 6) return;

                visibleCount++;

                const inRange = distManh <= 1.5; // Melee Range

                // Show button
                html += `
                 <button onclick="combatAction('attack', '${e.id}')" class="rpg-list-btn" ${inRange ? '' : 'disabled'} style="border-left:3px solid ${inRange ? '#f00' : '#555'}; opacity:${inRange ? 1 : 0.5}">
                    <div style="display:flex; justify-content:space-between;">
                        <span>⚔ ${e.name}</span>
                        <span>${e.hp}/${e.max_hp}</span>
                    </div>
                 </button>`;
            });
            if (visibleCount === 0) html += `<div style="color:#666;">No visible targets.</div>`;

            html += `</div>`;
        } else {
            html += `<div style="text-align:center; color:#555; padding-top:20px;">Action used.</div>`;
        }
    }

    // TAB CONTENT: BONUS
    else if (combatTab === 'bonus') {
        if (hasBonus) {
            html += `
             <div style="display:flex; flex-direction:column; gap:5px;">
                <button onclick="combatAction('second_wind')" class="rpg-list-btn" style="border-left:3px solid #0f0;">
                    <b>💚 Second Wind</b> <span style="font-size:0.8em; color:#aaa; float:right;">Heal HP</span>
                </button>
                <button onclick="combatAction('use_potion')" class="rpg-list-btn" style="border-left:3px solid #ff0;">
                    <b>🧪 Potion</b> <span style="font-size:0.8em; color:#aaa; float:right;">Heal 2d4+2</span>
                </button>
             </div>
             `;
        } else {
            html += `<div style="text-align:center; color:#555; padding-top:20px;">Bonus action used.</div>`;
        }
    }

    html += `</div>`;

    // FOOTER: End Turn
    html += `
        <div style="text-align:center;">
             <button onclick="combatAction('end_turn')" class="rpg-btn" style="width:100%; border:2px solid #888; background:#220000;">
                END TURN 🏁
             </button>
             <button onclick="combatAction('flee')" style="margin-top:5px; background:none; border:none; color:#666; font-size:0.8em; cursor:pointer; text-decoration:underline;">Flee Battle</button>
        </div>
    `;

    // CRITICAL FIX: Only update DOM if Changed
    // This prevents hover state flickering (The "Pulse")
    if (container.dataset.lastHTML !== html) {
        container.innerHTML = html;
        container.dataset.lastHTML = html;
    }
}

function _renderTabBtn(key, label, value, isActive) {
    const color = isActive ? '#fff' : (value > 0 ? '#aaa' : '#444');
    const bg = isActive ? '#444' : '#222';
    const border = isActive ? '2px solid #0ff' : '1px solid #333';

    // Highlight number if available
    const numColor = value > 0 ? '#0f0' : '#666';

    // Onclick: switch local tab variable and rerender
    return `
    <button onclick="switchCombatTab('${key}')" 
            style="flex:1; background:${bg}; color:${color}; border:${border}; padding:5px; font-size:0.8em; font-weight:bold; cursor:pointer;">
        ${label} <span style="background:#000; color:${numColor}; padding:0 4px; border-radius:4px;">${value}</span>
    </button>
    `;
}

// Global switcher
window.switchCombatTab = function (tab) {
    combatTab = tab;
    // Rerender immediately if data exists
    const area = document.getElementById('combat-menu-area');
    if (area && window.gameState && window.gameState.combat) {
        renderPlayerMenu(area, window.gameState.combat);
    }
}


const setCombatMenu = function (state) {
    combatMenuState = state;
    const controls = document.getElementById('combat-controls');
    // Force rerender if we had to
    if (window.gameState && window.gameState.combat) {
        updateCombatUI(window.gameState.combat);
    }
}
window.setCombatMenu = setCombatMenu;


const combatAction = async function (actionType, targetId = null) {
    const controls = document.getElementById('combat-controls');
    if (controls) {
        controls.style.opacity = '0.5';
        controls.style.pointerEvents = 'none';

        // Visual Feedback
        const menuArea = document.getElementById('combat-menu-area');
        if (menuArea) {
            const oldHTML = menuArea.innerHTML;
            menuArea.dataset.oldHTML = oldHTML; // Backup
            menuArea.innerHTML = `<div style="text-align:center; padding-top:40px; color:#fff;">Processing... <div class="spinner"></div></div>`;
        }
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
