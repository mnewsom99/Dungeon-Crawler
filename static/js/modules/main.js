
// Main Game Loop & Input Handling

async function fetchState() {
    try {
        const response = await fetch('/api/state?t=' + Date.now());
        const data = await response.json();
        drawMap(data);
        if (window.updateCombatUI) window.updateCombatUI(data.combat);
        if (window.updateNearbyList) window.updateNearbyList(data);

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

async function move(direction) {
    if (isProcessingMove) {
        console.log("Skipping move: Busy");
        return;
    }
    isProcessingMove = true;
    setTimeout(() => { isProcessingMove = false; }, 120);

    try {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction: direction })
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
        if (isProcessingMove) return;

        if (e.key === 'ArrowUp' || e.key === 'w') move('north');
        if (e.key === 'ArrowDown' || e.key === 's') move('south');
        if (e.key === 'ArrowLeft' || e.key === 'a') move('west');
        if (e.key === 'ArrowRight' || e.key === 'd') move('east');
    }
});

// Init
window.onload = function () {
    fetchState().then(async () => {
        fetchNarrative();
        logMessage("Welcome to the dungeon...");
    });
};
