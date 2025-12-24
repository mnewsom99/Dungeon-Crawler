
// Configuration & Globals
window.TILE_SIZE = 40;
let playerPos = [0, 0, 0];
let cameraPos = [0, 0];
let isProcessingMove = false;
let activeChatNPCId = null;

// Helper Logger
function logMessage(msg) {
    const logEl = document.getElementById('narrative-log');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = `> ${msg}`;
    logEl.appendChild(entry);
    logEl.scrollTop = logEl.scrollHeight;
}

// Tab Switching (UI)
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelector(`.tab-btn[onclick="switchTab('${tabId}')"]`).classList.add('active');
    document.getElementById(`${tabId}-tab`).classList.add('active');
}

function switchCharTab(tabId) {
    document.querySelectorAll('.char-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.char-tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelector(`.char-tab-btn[onclick="switchCharTab('${tabId}')"]`).classList.add('active');
    document.getElementById(`${tabId}-tab`).classList.add('active');
}
