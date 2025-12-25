
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
            if (window.updateInventoryUI && data.player) window.updateInventoryUI(data.player);
            if (window.updateSkillsUI && data.player) window.updateSkillsUI(data.player);
            if (window.updateRightPanelItems && data.player) window.updateRightPanelItems(data.player);
        } catch (e) { console.error("UI Update", e); }

    } catch (e) {
        console.error("Game Loop Error:", e);
    }
}

// Init
window.onload = function () {
    console.log("Dungeon Crawler Initialized");
    if (window.audioSystem) window.audioSystem.init();

    // Canvas Click Movement
    const canvas = document.getElementById('map-canvas');
    if (canvas) {
        canvas.addEventListener('click', (e) => {
            const rect = canvas.getBoundingClientRect();
            const cx = e.clientX - rect.left - canvas.width / 2;
            const cy = e.clientY - rect.top - canvas.height / 2;

            if (Math.abs(cx) > Math.abs(cy)) {
                if (cx > 0) move('east');
                else move('west');
            } else {
                if (cy > 0) move('south');
                else move('north');
            }
        });
    }

    // Start Loop
    fetchState();
    setInterval(fetchState, 500);
};

// Movement Logic
async function move(d) {
    let p = (typeof d === 'string') ? { direction: d } : d;
    try {
        await fetch('/api/move', { method: 'POST', body: JSON.stringify(p), headers: { 'Content-Type': 'application/json' } });
        if (window.audioSystem) window.audioSystem.play('step');
        fetchState();
    } catch (e) { console.error(e); }
}

// Input Handling
document.addEventListener('keydown', (e) => {
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "a", "s", "d"].includes(e.key)) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        e.preventDefault();

        if (e.key === 'w' || e.key === 'ArrowUp') move('north');
        if (e.key === 's' || e.key === 'ArrowDown') move('south');
        if (e.key === 'a' || e.key === 'ArrowLeft') move('west');
        if (e.key === 'd' || e.key === 'ArrowRight') move('east');
    }
});
