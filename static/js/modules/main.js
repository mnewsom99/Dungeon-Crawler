
// Main Game Logic

// Global State
window.gameState = null;

// Main Loop
async function fetchState() {
    try {
        const response = await fetch('/api/state?t=' + Date.now());
        const data = await response.json();
        window.gameState = data;

        // Draw Map
        if (typeof window.drawMap === 'function') {
            window.drawMap(data);
        }

        // UI Updates
        try {
            if (window.updateHeader && data.player) window.updateHeader(data.player.xyz[2]);
            if (window.updateCombatUI && data.combat) window.updateCombatUI(data.combat);
            if (window.updateNearbyList) window.updateNearbyList(data);
            if (window.updateQuestList) window.updateQuestList(data);

            if (window.updateInventoryUI && data.player) window.updateInventoryUI(data.player);
            if (window.updateSkillsUI && data.player) window.updateSkillsUI(data.player);
            if (window.updateSkillsUI && data.player) window.updateSkillsUI(data.player);
            if (window.updateRightPanelItems && data.player) window.updateRightPanelItems(data.player);
            if (window.updateHeroStats && data.player) window.updateHeroStats(data.player);
        } catch (e) { console.error("UI Update", e); }

    } catch (e) {
        console.error("Game Loop Error:", e);
    }
}

// Init
window.onload = function () {
    console.log("Dungeon Crawler Initialized");
    if (window.audioSystem) window.audioSystem.init();

    // Canvas Click Movement Handled by graphics.js now to prevent double-move
    // (See graphics.js mousedown listener)

    // Start Loop
    fetchState();
    setInterval(fetchState, 600);

    // Initial Narrative
    setTimeout(() => {
        fetch('/api/narrative')
            .then(r => r.json())
            .then(d => {
                if (d.narrative && window.updateLog) window.updateLog(d.narrative);
            })
            .catch(console.error);
    }, 1000); // Small delay to ensure UI is ready
};

// Movement Logic
async function move(d) {
    let p = (typeof d === 'string') ? { direction: d } : d;
    try {
        const res = await fetch('/api/move', { method: 'POST', body: JSON.stringify(p), headers: { 'Content-Type': 'application/json' } });
        const json = await res.json();

        // Log Handling
        if (json.narrative && window.updateLog) {
            window.updateLog(json.narrative);
            if (json.narrative.includes("Success!") || json.narrative.includes("Gathered")) {
                if (window.showTurnNotification) window.showTurnNotification("Gathered", json.narrative, 2000, "rgba(0, 100, 0, 0.8)");
                if (window.audioSystem) window.audioSystem.play('coin');
            }
        }

        // Combat Events (e.g. Enemy Turn processing after move)
        if (json.events && window.playCombatEvents) {
            await window.playCombatEvents(json.events);
        }

        if (window.audioSystem) window.audioSystem.play('step');
        fetchState();
    } catch (e) { console.error(e); }
}
window.movePlayerCmd = move; // Expose to graphics.js

// Input Handling
document.addEventListener('keydown', (e) => {
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "a", "s", "d"].includes(e.key)) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        e.preventDefault();

        // console.log("Key:", e.key); 
        if (e.key === 'w' || e.key === 'ArrowUp') { console.log('Move North req'); move('north'); }
        if (e.key === 's' || e.key === 'ArrowDown') { console.log('Move South req'); move('south'); }
        if (e.key === 'a' || e.key === 'ArrowLeft') { console.log('Move West req'); move('west'); }
        if (e.key === 'd' || e.key === 'ArrowRight') { console.log('Move East req'); move('east'); }
    }
});
