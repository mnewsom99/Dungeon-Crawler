const canvas = document.getElementById('map-canvas');
const ctx = canvas.getContext('2d');
const log = document.getElementById('narrative-log');

let TILE_SIZE = 40;
let viewportData = null;

const time = new Date().getTime();

function requestRedraw() {
    fetchState();
}

// Image Assets
// Environment: Using new Tiny Town Tiles
const floorImg = new Image(); floorImg.src = "/static/img/tile_0000.png"; // Grass
const wallImg = new Image(); wallImg.src = "/static/img/tile_0049.png"; // Brick Wall

// Characters: Using New Assets
const playerImg = new Image(); playerImg.src = "/static/img/Warrior.jpg";
const skeletonImg = new Image(); skeletonImg.src = "/static/img/skeleton.png";
const bonesImg = new Image(); bonesImg.src = "/static/img/bones.png";

// NPC (Elara): Fallback or Placeholder
const npcImg = new Image(); npcImg.src = "/static/img/Sorceress.jpg";

const spriteCache = {};

// Helper to draw tinted versions of characters if needed
// For environment, we draw raw.
function drawTinted(img, x, y, size, color) {
    if (!img.complete || img.naturalHeight === 0) {
        ctx.fillStyle = color;
        ctx.fillRect(x, y, size, size);
        return;
    }
    // ... (Tinting logic optionally preserved for effects, or direct draw)
    ctx.drawImage(img, x, y, size, size);
}

function requestRedraw() {
    // Only fetch if we need to, but usually we fetch via loop or events.
    // fetchState(); 
}

// ... Logger ...

// ... Fetch Logic ...

// ... Draw Logic ...

function drawMap(playerPos, visibleMap, enemies, corpses, npcs) {
    if (!visibleMap) visibleMap = {};
    if (!enemies) enemies = [];
    if (!corpses) corpses = [];
    if (!npcs) npcs = [];

    if (!cameraPos) cameraPos = [...playerPos];

    // Camera Logic
    const BOUNDARY_X = 3;
    const BOUNDARY_Y = 2;
    let dx = playerPos[0] - cameraPos[0];
    let dy = playerPos[1] - cameraPos[1];
    if (dx > BOUNDARY_X) cameraPos[0] += (dx - BOUNDARY_X);
    if (dx < -BOUNDARY_X) cameraPos[0] += (dx + BOUNDARY_X);
    if (dy > BOUNDARY_Y) cameraPos[1] += (dy - BOUNDARY_Y);
    if (dy < -BOUNDARY_Y) cameraPos[1] += (dy + BOUNDARY_Y);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#1e1e1e"; // Darker Background
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    const DRAW_RADIUS_X = Math.ceil(canvas.width / (2 * TILE_SIZE)) + 2;
    const DRAW_RADIUS_Y = Math.ceil(canvas.height / (2 * TILE_SIZE)) + 2;

    for (let x = -DRAW_RADIUS_X; x <= DRAW_RADIUS_X; x++) {
        for (let y = -DRAW_RADIUS_Y; y <= DRAW_RADIUS_Y; y++) {
            const worldX = Math.floor(cameraPos[0] + x);
            const worldY = Math.floor(cameraPos[1] + y);
            const worldZ = cameraPos[2];

            const drawX = centerX + (worldX - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
            const drawY = centerY + (worldY - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

            const tileKey = `${worldX},${worldY},${worldZ}`;
            const tileType = visibleMap[tileKey];

            if (tileType) {
                if (tileType === 'floor') {
                    // Draw Colored Floor Directly
                    if (floorImg.complete) ctx.drawImage(floorImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
                    else { ctx.fillStyle = '#2e3b28'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }
                } else if (tileType === 'wall') {
                    // Draw Colored Wall Directly
                    if (wallImg.complete) ctx.drawImage(wallImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
                    else { ctx.fillStyle = '#a05b35'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }
                } else {
                    ctx.fillStyle = '#111';
                    ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                }

                // LOS / Lighting Overlay
                const dist = Math.sqrt(Math.pow(worldX - playerPos[0], 2) + Math.pow(worldY - playerPos[1], 2));
                if (dist > 5) {
                    ctx.fillStyle = `rgba(0, 0, 0, ${Math.min((dist - 5) * 0.2, 0.9)})`;
                    ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                }
            }
        }
    }

    // Draw Corpses
    corpses.forEach(corpse => {
        const [cx, cy, cz] = corpse.xyz;
        if (Math.abs(cx - cameraPos[0]) <= DRAW_RADIUS_X && Math.abs(cy - cameraPos[1]) <= DRAW_RADIUS_Y) {
            const drawX = centerX + (cx - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
            const drawY = centerY + (cy - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);
            // Use old bones image or placeholder
            if (bonesImg.complete) ctx.drawImage(bonesImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            else { ctx.fillStyle = '#ccc'; ctx.fillRect(drawX + 10, drawY + 10, 10, 10); }
        }
    });

    // Draw NPCs
    npcs.forEach(npc => {
        const [nx, ny, nz] = npc.xyz;
        if (Math.abs(nx - cameraPos[0]) <= DRAW_RADIUS_X && Math.abs(ny - cameraPos[1]) <= DRAW_RADIUS_Y) {
            const drawX = centerX + (nx - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
            const drawY = centerY + (ny - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

            // Draw NPC (Cyan Box fallback or Image)
            ctx.fillStyle = '#00ffff';
            ctx.fillRect(drawX + 5, drawY + 5, TILE_SIZE - 10, TILE_SIZE - 10);

            // Name tag
            ctx.fillStyle = 'white';
            ctx.font = '10px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(npc.name, drawX + TILE_SIZE / 2, drawY - 4);
        }
    });

    // Draw Enemies
    enemies.forEach(enemy => {
        const [ex, ey, ez] = enemy.xyz;
        if (Math.abs(ex - cameraPos[0]) <= DRAW_RADIUS_X && Math.abs(ey - cameraPos[1]) <= DRAW_RADIUS_Y) {
            const drawX = centerX + (ex - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
            const drawY = centerY + (ey - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

            if (skeletonImg.complete) ctx.drawImage(skeletonImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            else { ctx.fillStyle = 'red'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }

            // HP bar
            const hpPct = enemy.hp / enemy.max_hp;
            ctx.fillStyle = '#500';
            ctx.fillRect(drawX, drawY - 6, TILE_SIZE, 4);
            ctx.fillStyle = '#f00';
            ctx.fillRect(drawX, drawY - 6, TILE_SIZE * hpPct, 4);
        }
    });

    // Draw Player
    const pDrawX = centerX + (playerPos[0] - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
    const pDrawY = centerY + (playerPos[1] - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);
    if (playerImg.complete) ctx.drawImage(playerImg, pDrawX, pDrawY, TILE_SIZE, TILE_SIZE);
    else { ctx.fillStyle = 'green'; ctx.fillRect(pDrawX, pDrawY, TILE_SIZE, TILE_SIZE); }
}

function logMessage(msg) {
    const p = document.createElement('p');
    p.textContent = "> " + msg;
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
}

async function fetchNarrative() {
    logMessage("...");
    const response = await fetch('/api/narrative');
    const data = await response.json();
    logMessage(data.narrative);
}

async function fetchState() {
    const response = await fetch(`/api/state?t=${new Date().getTime()}`);
    const rawData = await response.json();

    // Adapt new DB structure to old frontend expectations
    const data = {
        position: rawData.player.xyz,
        map: rawData.world.map,
        enemies: rawData.world.enemies,
        npcs: rawData.world.npcs, // Add NPCs
        corpses: rawData.corpses,
        combat: rawData.combat,
        stats: rawData.player.stats
    };

    viewportData = data;

    // DEBUG LOG
    console.log("State Fetched:", data);
    console.log("Map Keys:", Object.keys(data.map).length);
    console.log("Player Pos:", data.position);

    drawMap(data.position, data.map, data.enemies, data.corpses, data.npcs);

    // UI Updates
    if (data.combat && data.combat.active) {
        console.log("Combat Mode Active!");
        document.getElementById('controls').style.display = 'none';
        document.getElementById('combat-controls').style.display = 'block';
    } else {
        document.getElementById('controls').style.display = 'block';
        document.getElementById('combat-controls').style.display = 'none';
    }

    const stats = data.stats || {};
    if (stats.str) document.getElementById('stat-str').textContent = stats.str;
    if (stats.dex) document.getElementById('stat-dex').textContent = stats.dex;
    if (stats.con) document.getElementById('stat-con').textContent = stats.con;
    if (stats.int) document.getElementById('stat-int').textContent = stats.int;
    if (stats.wis) document.getElementById('stat-wis').textContent = stats.wis;
    if (stats.cha) document.getElementById('stat-cha').textContent = stats.cha;

    const nearbyList = document.getElementById('nearby-list');
    nearbyList.innerHTML = '';
    let foundSomething = false;
    const [px, py, pz] = data.position;

    if (data.corpses) {
        data.corpses.forEach((corpse, index) => {
            const [cx, cy, cz] = corpse.xyz;
            const dist = Math.max(Math.abs(cx - px), Math.abs(cy - py));
            if (dist <= 1) {
                foundSomething = true;
                const div = document.createElement('div');
                div.className = 'interaction-item';
                div.innerHTML = `
                    <div style="color: #ccc; font-weight: bold;">Pile of Bones</div>
                    <div class="interaction-actions">
                        <button onclick="interact('inspect', 'corpse', ${index})">Inspect</button>
                        <button onclick="interact('loot', 'corpse', ${index})">Bag</button>
                    </div>
                 `;
                nearbyList.appendChild(div);
            }
        });
    }

    if (!foundSomething) {
        nearbyList.innerHTML = '<p style="color: #666; font-style: italic;">Nothing of interest...</p>';
    }
}

async function interact(action, type, id) {
    if (action === 'inspect') {
        logMessage("You see a pile of bleached bones. It seems to be a human skeleton.");
    } else if (action === 'loot') {
        logMessage("You rummage through the bones... found a rusty dagger! (Added to inventory)");
    }
}

function changeZoom(delta) {
    TILE_SIZE += delta;
    if (TILE_SIZE < 10) TILE_SIZE = 10;
    if (TILE_SIZE > 100) TILE_SIZE = 100;
    if (viewportData) {
        drawMap(viewportData.position, viewportData.map, viewportData.enemies, viewportData.corpses);
    }
}

function toggleMap() {
    const modal = document.getElementById('map-modal');
    if (modal.style.display === 'none') {
        modal.style.display = 'flex';
        if (viewportData) {
            drawFullMap(viewportData.position, viewportData.map);
        }
    } else {
        modal.style.display = 'none';
    }
}

function drawFullMap(playerPos, visibleMap) {
    const fCanvas = document.getElementById('full-map-canvas');
    const fCtx = fCanvas.getContext('2d');
    fCtx.clearRect(0, 0, fCanvas.width, fCanvas.height);

    let minX = playerPos[0], maxX = playerPos[0];
    let minY = playerPos[1], maxY = playerPos[1];
    const keys = Object.keys(visibleMap);
    if (keys.length === 0) return;

    keys.forEach(key => {
        const [x, y, z] = key.split(',').map(Number);
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
    });

    minX -= 2; maxX += 2;
    minY -= 2; maxY += 2;

    const mapWidth = maxX - minX + 1;
    const mapHeight = maxY - minY + 1;
    const scaleX = fCanvas.width / mapWidth;
    const scaleY = fCanvas.height / mapHeight;
    const scale = Math.min(scaleX, scaleY, 40);

    const offsetX = (fCanvas.width - mapWidth * scale) / 2;
    const offsetY = (fCanvas.height - mapHeight * scale) / 2;

    keys.forEach(key => {
        const [x, y, z] = key.split(',').map(Number);
        if (visibleMap[key]) {
            const drawX = offsetX + (x - minX) * scale;
            const drawY = offsetY + (y - minY) * scale;
            if (visibleMap[key] === 'floor') fCtx.fillStyle = '#444';
            else if (visibleMap[key] === 'wall') fCtx.fillStyle = '#8B4513';
            else fCtx.fillStyle = '#220022';
            fCtx.fillRect(drawX, drawY, scale, scale);
        }
    });

    const pdX = offsetX + (playerPos[0] - minX) * scale;
    const pdY = offsetY + (playerPos[1] - minY) * scale;
    fCtx.fillStyle = '#00ff00';
    fCtx.fillRect(pdX, pdY, scale, scale);
}

async function combatAction(action) {
    const response = await fetch('/api/combat/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
    });
    const data = await response.json();
    logMessage(data.narrative);
    fetchState();
}

async function resetGame() {
    if (!confirm("Are you sure you want to reset the world? All progress will be lost.")) return;
    await fetch('/api/debug/reset', { method: 'POST' });
    window.location.reload();
}

async function move(direction) {
    const response = await fetch('/api/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: direction })
    });
    const data = await response.json();
    if (data.narrative) logMessage(data.narrative);
    else fetchNarrative();
    fetchState();
}

let cameraPos = null;

function drawMap(playerPos, visibleMap, enemies, corpses, npcs) {
    if (!visibleMap) visibleMap = {};
    if (!enemies) enemies = [];
    if (!corpses) corpses = [];
    if (!npcs) npcs = [];

    if (!cameraPos) cameraPos = [...playerPos];

    // Camera Logic
    const BOUNDARY_X = 3;
    const BOUNDARY_Y = 2;

    let dx = playerPos[0] - cameraPos[0];
    let dy = playerPos[1] - cameraPos[1];

    if (dx > BOUNDARY_X) cameraPos[0] += (dx - BOUNDARY_X);
    if (dx < -BOUNDARY_X) cameraPos[0] += (dx + BOUNDARY_X);
    if (dy > BOUNDARY_Y) cameraPos[1] += (dy - BOUNDARY_Y);
    if (dy < -BOUNDARY_Y) cameraPos[1] += (dy + BOUNDARY_Y);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    const DRAW_RADIUS_X = Math.ceil(canvas.width / (2 * TILE_SIZE)) + 2;
    const DRAW_RADIUS_Y = Math.ceil(canvas.height / (2 * TILE_SIZE)) + 2;

    for (let x = -DRAW_RADIUS_X; x <= DRAW_RADIUS_X; x++) {
        for (let y = -DRAW_RADIUS_Y; y <= DRAW_RADIUS_Y; y++) {
            const worldX = Math.floor(cameraPos[0] + x);
            const worldY = Math.floor(cameraPos[1] + y);
            const worldZ = cameraPos[2];

            const screenOffsetX = (worldX - cameraPos[0]) * TILE_SIZE;
            const screenOffsetY = (worldY - cameraPos[1]) * TILE_SIZE;

            const drawX = centerX + screenOffsetX - (TILE_SIZE / 2);
            const drawY = centerY + screenOffsetY - (TILE_SIZE / 2);

            // Bounds check for styling
            // ctx.strokeStyle = '#333';
            // ctx.lineWidth = 1;
            // ctx.strokeRect(drawX, drawY, TILE_SIZE, TILE_SIZE);

            const tileKey = `${worldX},${worldY},${worldZ}`;
            const tileType = visibleMap[tileKey];

            if (tileType) {
                if (tileType === 'floor') {
                    if (floorImg.complete && floorImg.naturalHeight !== 0) ctx.drawImage(floorImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
                    else {
                        ctx.fillStyle = '#ff00ff'; // DEBUG PINK
                        ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                    }
                } else if (tileType === 'wall') {
                    // Force fallback to debug image issues
                    // if (wallImg.complete && wallImg.naturalHeight !== 0) ctx.drawImage(wallImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
                    // else { 
                    ctx.fillStyle = '#654321'; // Dark Brown
                    ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                    ctx.strokeStyle = '#DAA520';
                    ctx.strokeRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                    // }
                } else {
                    ctx.fillStyle = '#444';
                    ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                }

                // Lighting
                const dist = Math.sqrt(Math.pow(worldX - playerPos[0], 2) + Math.pow(worldY - playerPos[1], 2));
                if (dist > 3.5) { // Increased visibility for testing
                    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
                    ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                }
            } else {
                // Draw grid for void to verify canvas is working
                ctx.strokeStyle = '#222';
                ctx.lineWidth = 1;
                ctx.strokeRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
            }
        }
    }

    // Draw Corpses relative to CAMERA
    corpses.forEach(corpse => {
        const [cx, cy, cz] = corpse.xyz;

        const screenOffsetX = (cx - cameraPos[0]) * TILE_SIZE;
        const screenOffsetY = (cy - cameraPos[1]) * TILE_SIZE;

        if (Math.abs(cx - cameraPos[0]) <= DRAW_RADIUS_X && Math.abs(cy - cameraPos[1]) <= DRAW_RADIUS_Y) {
            const drawX = centerX + screenOffsetX - (TILE_SIZE / 2);
            const drawY = centerY + screenOffsetY - (TILE_SIZE / 2);

            if (bonesImg.complete && bonesImg.naturalHeight !== 0) {
                ctx.drawImage(bonesImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            } else {
                ctx.fillStyle = '#ccc';
                ctx.fillRect(drawX + 15, drawY + 15, 10, 10);
            }
        }
    });

    // Draw NPCs
    npcs.forEach(npc => {
        const [nx, ny, nz] = npc.xyz;
        const screenOffsetX = (nx - cameraPos[0]) * TILE_SIZE;
        const screenOffsetY = (ny - cameraPos[1]) * TILE_SIZE;

        if (Math.abs(nx - cameraPos[0]) <= DRAW_RADIUS_X && Math.abs(ny - cameraPos[1]) <= DRAW_RADIUS_Y) {
            const drawX = centerX + screenOffsetX - (TILE_SIZE / 2);
            const drawY = centerY + screenOffsetY - (TILE_SIZE / 2);

            // Placeholder for NPC
            ctx.fillStyle = '#00ffff'; // Cyan
            ctx.fillRect(drawX + 5, drawY + 5, TILE_SIZE - 10, TILE_SIZE - 10);

            // Name tag
            ctx.fillStyle = 'white';
            ctx.font = '10px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(npc.name, drawX + TILE_SIZE / 2, drawY - 2);
        }
    });

    // Draw Enemies relative to CAMERA
    enemies.forEach(enemy => {
        const [ex, ey, ez] = enemy.xyz;

        const screenOffsetX = (ex - cameraPos[0]) * TILE_SIZE;
        const screenOffsetY = (ey - cameraPos[1]) * TILE_SIZE;

        if (Math.abs(ex - cameraPos[0]) <= DRAW_RADIUS_X && Math.abs(ey - cameraPos[1]) <= DRAW_RADIUS_Y) {
            const drawX = centerX + screenOffsetX - (TILE_SIZE / 2);
            const drawY = centerY + screenOffsetY - (TILE_SIZE / 2);

            if (skeletonImg.complete && skeletonImg.naturalHeight !== 0) {
                ctx.drawImage(skeletonImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            } else {
                ctx.fillStyle = 'red';
                ctx.fillRect(drawX + 10, drawY + 10, 20, 20);
            }

            // Draw HP bar
            const hpPct = enemy.hp / enemy.max_hp;
            ctx.fillStyle = 'red';
            ctx.fillRect(drawX, drawY - 5, TILE_SIZE, 4);
            ctx.fillStyle = 'green';
            ctx.fillRect(drawX, drawY - 5, TILE_SIZE * hpPct, 4);
        }
    });
    const pScreenOffsetX = (playerPos[0] - cameraPos[0]) * TILE_SIZE;
    const pScreenOffsetY = (playerPos[1] - cameraPos[1]) * TILE_SIZE;
    const pDrawX = centerX + pScreenOffsetX - (TILE_SIZE / 2);
    const pDrawY = centerY + pScreenOffsetY - (TILE_SIZE / 2);

    if (playerImg.complete && playerImg.naturalHeight !== 0) {
        ctx.drawImage(playerImg, pDrawX, pDrawY, TILE_SIZE, TILE_SIZE);
    } else {
        ctx.fillStyle = '#00ff00';
        ctx.fillRect(pDrawX + 10, pDrawY + 10, 20, 20);
    }
}

fetchState().then(async () => {
    fetchNarrative();
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowUp' || e.key === 'w') move('north');
    if (e.key === 'ArrowDown' || e.key === 's') move('south');
    if (e.key === 'ArrowLeft' || e.key === 'a') move('west');
    if (e.key === 'ArrowRight' || e.key === 'd') move('east');
});
