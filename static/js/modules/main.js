
// Main Game Loop & Input Handling

async function fetchState() {
    try {
        const response = await fetch('/api/state?t=' + Date.now());
        const data = await response.json();

        window.gameState = data; // Store global state for UI lookups

        drawMap(data);
        if (window.updateCombatUI) window.updateCombatUI(data.combat);
        if (window.updateNearbyList) window.updateNearbyList(data);
        if (window.updateHeader) window.updateHeader(data.player.xyz[2]);
        if (window.updateInventoryUI) window.updateInventoryUI(data.player);
        if (window.updateSkillsUI) window.updateSkillsUI(data.player);
        if (window.updateRightPanelItems) window.updateRightPanelItems(data.player);

        // Update UI Tabs if needed
        // (Inventory/Quest logic here)
    } catch (e) {
        console.error("State Fetch Error:", e);
    }
}

async function fetchNarrative() {
    try {
        const response = await fetch('/api/narrative');
        const data = await response.json();
        // Clear log and append history?
        // Or just append new?
        // For simplicity, we just log recent messages here if needed.
    } catch (e) { }
}

// Modified move function to support objects
async function move(arg) {
    if (isProcessingMove) return;

    let payload = {};
    if (typeof arg === 'string') payload = { direction: arg };
    else payload = arg; // {dx: 1, dy: 0}

    isProcessingMove = true;
    setTimeout(() => { isProcessingMove = false; }, 150); // Slight delay for pacing

    try {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (data.narrative) logMessage(data.narrative);
        else fetchNarrative();
        await fetchState();
    } catch (e) {
        console.error("Move Error:", e);
    } finally {
        isProcessingMove = false;
    }
}

// Input Listener
document.addEventListener('keydown', (e) => {
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "a", "s", "d"].includes(e.key)) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        e.preventDefault();

        if (activeChatNPCId !== null) return;

        if (e.key === 'ArrowUp' || e.key === 'w') move('north');
        if (e.key === 'ArrowDown' || e.key === 's') move('south');
        if (e.key === 'ArrowLeft' || e.key === 'a') move('west');
        if (e.key === 'ArrowRight' || e.key === 'd') move('east');
    }
});

// --- Mouse Movement Logic ---
let isMouseMoving = false;
let mouseTarget = { x: 0, y: 0 };
let moveInterval = null;

function startMouseMovement() {
    if (moveInterval) return;

    // Interval loop to keep moving while held
    moveInterval = setInterval(() => {
        if (!isMouseMoving) {
            stopMouseMovement();
            return;
        }

        // Calculate Direction relative to screen center
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;

        const dxRaw = mouseTarget.x - centerX;
        const dyRaw = mouseTarget.y - centerY;

        // Determine closest direction (Naive 8-way)
        // We normalize to -1, 0, 1

        const angle = Math.atan2(dyRaw, dxRaw);
        // angle is -PI to PI.
        // discrete 8-way mapping?
        // simple threshold:
        // if abs(dx) > threshold, dx = sign. same for dy.

        // Let's use simple threshold logic
        let moveX = 0;
        let moveY = 0;
        const limit = 40; // deadzone in pixels

        if (Math.abs(dxRaw) > limit) moveX = dxRaw > 0 ? 1 : -1;
        if (Math.abs(dyRaw) > limit) moveY = dyRaw > 0 ? 1 : -1;

        if (moveX !== 0 || moveY !== 0) {
            move({ dx: moveX, dy: moveY });
        }

    }, 200); // 200ms tick for click-move speed
}

function stopMouseMovement() {
    if (moveInterval) clearInterval(moveInterval);
    moveInterval = null;
    isMouseMoving = false;
}

// Attach to Canvas (wait for window load or just document)
window.addEventListener('mousedown', (e) => {
    // Only capture if clicking on the map canvas background, not UI panels
    if (e.target.tagName !== 'CANVAS') return;

    isMouseMoving = true;
    mouseTarget.x = e.clientX;
    mouseTarget.y = e.clientY;
    startMouseMovement();
});

window.addEventListener('mousemove', (e) => {
    if (isMouseMoving) {
        mouseTarget.x = e.clientX;
        mouseTarget.y = e.clientY;
    }
});

window.addEventListener('mouseup', () => {
    stopMouseMovement();
});
window.addEventListener('mouseleave', () => { // Stop if mouse leaves window
    stopMouseMovement();
});
// Init
window.onload = function () {
    fetchState().then(async () => {
        fetchNarrative();
        logMessage("Welcome to the dungeon...");
    });
};
