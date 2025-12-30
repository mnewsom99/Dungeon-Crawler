const canvas = document.getElementById('map-canvas');
const ctx = canvas.getContext('2d');
const log = document.getElementById('log-content');

const TILE_SIZE = 32;
const MAP_WIDTH = 800; // Canvas size
const MAP_HEIGHT = 600;

console.log("GAME CORE JS LOADED");
// alert("Game Core Logic Loaded!"); // Uncomment if needed for extreme debugging

let viewportData = null;

const time = new Date().getTime();

function requestRedraw() {
    fetchState();
}

// Image Assets
// Environment: Using new Tiny Town Tiles
const floorImg = new Image(); floorImg.src = "/static/img/grey_black_floor_tile.png"; // Stone/Dark Floor
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
    // Camera Logic (Locked)
    cameraPos = [...playerPos];

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#1e1e1e"; // Darker Background
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    const DRAW_RADIUS_X = Math.ceil(canvas.width / (2 * TILE_SIZE)) + 2;
    const DRAW_RADIUS_Y = Math.ceil(canvas.height / (2 * TILE_SIZE)) + 2;

    // Generic Rendering
    const isSurface = playerPos[2] > 0;

    for (const tileKey in visibleMap) {
        const [worldX, worldY, worldZ] = tileKey.split(',').map(Number); // Assuming tileKey is "x,y,z"

        // Only draw tiles that are on the same Z-level as the player
        if (worldZ !== playerPos[2]) continue;

        // Convert World Coords to Canvas Coords
        const drawX = centerX + (worldX - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
        const drawY = centerY + (worldY - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

        const tileType = visibleMap[tileKey];

        // --- TILE RENDERING ---
        // --- TILE RENDERING ---

        // Universal Forest Background (Grass) for blending transparent assets
        if (playerPos[2] == 2) {
            ctx.fillStyle = '#228b22';
            ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
            ctx.fillStyle = '#006400';
            ctx.fillRect(drawX + 8, drawY + 8, 2, 4);
            ctx.fillRect(drawX + 20, drawY + 14, 2, 4);
        }

        if (tileType === 'floor') {
            if (playerPos[2] == '1') { // Check Z-level from player position
                // Town Grass
                ctx.fillStyle = '#228b22'; // Forest Green
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                // Add blade texture
                ctx.fillStyle = '#006400';
                ctx.fillRect(drawX + 8, drawY + 8, 2, 4);
                ctx.fillRect(drawX + 20, drawY + 14, 2, 4);
            } else if (playerPos[2] == '2') {
                // Forest Path (Dirt) - Draw dirt OVER the grass we just drew
                ctx.fillStyle = '#5d4037'; // Dirt Brown
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = '#4e342e';
                ctx.fillRect(drawX + 5, drawY + 5, 2, 2);
            } else {
                // Dungeon Floor
                if (floorImg.complete && floorImg.naturalHeight !== 0) ctx.drawImage(floorImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
                else { ctx.fillStyle = '#2b2b2b'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }
            }
        } else if (tileType.startsWith('mtn_') || tileType === 'door_stone') {
            // 1. Draw Background (Grass) so alpha transparency works
            // We use conditional grass here in case we reuse this tile elsewhere
            if (playerPos[2] == 2) {
                ctx.fillStyle = '#228b22';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
            }

            // 2. Draw Image
            // 2. Draw Image if available and NOT a procedural type override
            // We want procedural for things like 'water' (animation) but images for 'floor_volcanic'
            const proceduralTypes = ['water', 'lava', 'void'];

            if (!proceduralTypes.includes(tileType)) {
                if (!spriteCache[tileType]) {
                    const img = new Image();
                    img.src = '/static/img/' + tileType + '.png';
                    img.onload = () => requestRedraw();
                    spriteCache[tileType] = img;
                }

                const img = spriteCache[tileType];
                if (img && img.complete && img.naturalHeight !== 0) {
                    ctx.drawImage(img, drawX, drawY, TILE_SIZE, TILE_SIZE);
                    // Continue to next tile (skip procedural else-ifs)
                    continue;
                }
            } else if (tileType === 'water') {
                ctx.fillStyle = '#4169E1'; // RoyalBlue
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                // Ripple
                ctx.fillStyle = '#87CEFA';
                ctx.fillRect(drawX + 8, drawY + 8, 8, 2);
            } else if (tileType === 'floor_wood') {
                // Interior Wood Floor
                ctx.fillStyle = '#8B4513'; // SaddleBrown
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                // Plank lines
                ctx.fillStyle = '#5c2e0e';
                ctx.fillRect(drawX, drawY + 7, TILE_SIZE, 1);
                ctx.fillRect(drawX, drawY + 15, TILE_SIZE, 1);
                ctx.fillRect(drawX, drawY + 23, TILE_SIZE, 1);
            } else if (tileType === 'tree') {
                // Grass Background
                ctx.fillStyle = '#228b22';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                // Tree Trunk
                ctx.fillStyle = '#4b3621';
                ctx.fillRect(drawX + 12, drawY + 16, 8, 16);
                // Tree Top (Circle-ish)
                ctx.fillStyle = '#006400';
                ctx.beginPath();
                ctx.arc(drawX + 16, drawY + 12, 12, 0, 2 * Math.PI);
                ctx.fill();
            } else if (tileType === 'wall' || tileType === 'wall_house') {
                // Standard Wall / House Wall
                if (wallImg.complete) ctx.drawImage(wallImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
                else { ctx.fillStyle = '#a05b35'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }
            } else if (tileType === 'door') {
                // Floor background
                ctx.fillStyle = (playerPos[2] == '1') ? '#8B4513' : '#2b2b2b';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);

                // Door Frame
                ctx.fillStyle = '#654321';
                ctx.fillRect(drawX + 4, drawY + 4, TILE_SIZE - 8, TILE_SIZE - 8);
                // Knob
                ctx.fillStyle = '#FFD700';
                ctx.fillRect(drawX + TILE_SIZE - 10, drawY + TILE_SIZE / 2, 4, 4);
            } else if (tileType === 'herb') {
                // Grass Base
                ctx.fillStyle = '#228b22';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                // Flower Cluster
                ctx.fillStyle = '#FF69B4'; // HotPink Flowers
                ctx.beginPath();
                ctx.arc(drawX + 8, drawY + 8, 3, 0, Math.PI * 2);
                ctx.arc(drawX + 24, drawY + 24, 3, 0, Math.PI * 2);
                ctx.arc(drawX + 8, drawY + 24, 3, 0, Math.PI * 2);
                ctx.arc(drawX + 24, drawY + 8, 3, 0, Math.PI * 2);
                ctx.fill();
            } else if (tileType === 'anvil') {
                // ... (keep existing) ...
                ctx.fillStyle = '#8B4513';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = '#2F4F4F';
                ctx.fillRect(drawX + 8, drawY + 10, 16, 16);
                ctx.fillStyle = '#708090';
                ctx.fillRect(drawX + 4, drawY + 8, 24, 8);
            } else if (tileType === 'shelf') {
                // ... (keep existing) ...
                ctx.fillStyle = '#8B4513';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = '#DEB887';
                ctx.fillRect(drawX + 2, drawY + 4, 28, 6);
                ctx.fillRect(drawX + 2, drawY + 14, 28, 6);
                ctx.fillRect(drawX + 2, drawY + 24, 28, 6);
            } else if (tileType === 'lava') {
                ctx.fillStyle = '#cf1020'; // Lava Red
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = '#ff8c00';
                ctx.fillRect(drawX + Math.random() * 20, drawY + Math.random() * 20, 6, 6);
            } else if (tileType === 'ice') {
                ctx.fillStyle = '#a5f2f3'; // Ice Blue
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(drawX + 5, drawY + 5, 8, 2);
            } else if (tileType === 'void') {
                // Starfield
                ctx.fillStyle = '#110022';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = '#fff';
                if (Math.random() > 0.9) ctx.fillRect(drawX + Math.random() * 32, drawY + Math.random() * 32, 1, 1);
            } else if (tileType === 'rock') {
                // Grass Base (since it's in forest)
                ctx.fillStyle = '#228b22';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                // Rock
                ctx.fillStyle = '#555';
                ctx.beginPath();
                ctx.arc(drawX + 16, drawY + 16, 10, 0, Math.PI * 2);
                ctx.fill();
                // Highlight
                ctx.fillStyle = '#777';
                ctx.beginPath();
                ctx.arc(drawX + 12, drawY + 12, 4, 0, Math.PI * 2);
                ctx.fill();
            } else {
                // Unknown
                ctx.fillStyle = '#000';
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
            }

            // LOS / Lighting Overlay
            const dist = Math.sqrt(Math.pow(worldX - playerPos[0], 2) + Math.pow(worldY - playerPos[1], 2));
            if (dist > 5) {
                ctx.fillStyle = `rgba(0, 0, 0, ${Math.min((dist - 5) * 0.2, 0.9)})`;
                ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
            }
        }


        // Draw Corpses
        corpses.forEach(corpse => {
            const [cx, cy, cz] = corpse.xyz;

            // Visibility Check: Must be on a visible/revealed tile
            const tileKey = `${cx},${cy},${cz}`;
            if (!visibleMap[tileKey]) return;

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

            // Visibility Check
            const tileKey = `${nx},${ny},${nz}`;
            if (!visibleMap[tileKey]) return;

            // Optional: Distance check? (Uncomment if NPCs should also fade in dark)
            // const distToPlayer = Math.sqrt(Math.pow(nx - playerPos[0], 2) + Math.pow(ny - playerPos[1], 2));
            // if (distToPlayer > 6) return;

            if (Math.abs(nx - cameraPos[0]) <= DRAW_RADIUS_X && Math.abs(ny - cameraPos[1]) <= DRAW_RADIUS_Y) {
                const drawX = centerX + (nx - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
                const drawY = centerY + (ny - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

                // Draw NPC
                if (npc.asset) {
                    if (!spriteCache[npc.asset]) {
                        const img = new Image();
                        img.src = "/static/img/" + npc.asset;
                        spriteCache[npc.asset] = img;
                    }
                    const img = spriteCache[npc.asset];
                    if (img.complete && img.naturalHeight !== 0) {
                        ctx.drawImage(img, drawX, drawY, TILE_SIZE, TILE_SIZE);
                    } else {
                        ctx.fillStyle = '#00ffff';
                        ctx.fillRect(drawX + 5, drawY + 5, TILE_SIZE - 10, TILE_SIZE - 10);
                    }
                } else {
                    ctx.fillStyle = '#00ffff';
                    ctx.fillRect(drawX + 5, drawY + 5, TILE_SIZE - 10, TILE_SIZE - 10);
                }

                // Name tag
                ctx.fillStyle = 'white';
                ctx.font = '10px monospace';
                ctx.textAlign = 'center';
                ctx.fillText(npc.name, drawX + TILE_SIZE / 2, drawY - 4);

                // Quest Indicators
                if (npc.quest_status && npc.quest_status !== "none") {
                    console.log(`DEBUG: ICON DRAW for ${npc.name}: ${npc.quest_status}`);
                    const bounce = Math.sin(new Date().getTime() / 200) * 3;
                    ctx.font = 'bold 20px monospace';

                    if (npc.quest_status === "available") {
                        ctx.fillStyle = "#ffff00"; // Yellow !
                        ctx.fillText("!", drawX + TILE_SIZE / 2, drawY - 20 + bounce);
                    } else if (npc.quest_status === "turn_in") {
                        ctx.fillStyle = "#ffd700"; // Gold ?
                        ctx.fillText("?", drawX + TILE_SIZE / 2, drawY - 20 + bounce);
                    }
                }
            }
        });

        // Draw Enemies
        enemies.forEach(enemy => {
            const [ex, ey, ez] = enemy.xyz;

            // Visibility Check
            const tileKey = `${ex},${ey},${ez}`;
            if (!visibleMap[tileKey]) return; // Must be on a valid tile

            // Strict Fog of War: Don't show enemies in the "memory" shroud (distance > 6)
            // This prevents seeing enemies down dark hallways before you get close
            const distToPlayer = Math.sqrt(Math.pow(ex - playerPos[0], 2) + Math.pow(ey - playerPos[1], 2));
            if (distToPlayer > 6.0) return;

            if (Math.abs(ex - cameraPos[0]) <= DRAW_RADIUS_X && Math.abs(ey - cameraPos[1]) <= DRAW_RADIUS_Y) {
                const drawX = centerX + (ex - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
                const drawY = centerY + (ey - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

                // Determine Enemy Sprite
                let eImg = skeletonImg;
                const name = (enemy.name || "").toLowerCase();
                // console.log(`Processing enemy: ${enemy.name} -> '${name}'`);

                let assetKey = null;
                if (name.includes("knife")) {
                    // Bypass standard logic completely
                    if (window.drawDebugGoblin) {
                        window.drawDebugGoblin(ctx, drawX, drawY, TILE_SIZE);
                    } else {
                        ctx.fillStyle = "orange";
                        ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                    }

                    // HP bar (Redraw over debug)
                    const hpPct = enemy.hp / enemy.max_hp;
                    ctx.fillStyle = '#500';
                    ctx.fillRect(drawX, drawY - 6, TILE_SIZE, 4);
                    ctx.fillStyle = '#f00';
                    ctx.fillRect(drawX, drawY - 6, TILE_SIZE * hpPct, 4);
                    return; // SKIP REST OF LOOP
                }
                else if (name.includes("cinder")) assetKey = "cinder_hound";
                else if (name.includes("sentinel")) assetKey = "obsidian_sentinel";
                else if (name.includes("bat")) assetKey = "sulfur_bat";
                else if (name.includes("weaver")) assetKey = "magma_weaver";
                else if (name.includes("wolf")) assetKey = "wolf";
                else if (name.includes("bear")) assetKey = "bear";
                else if (name.includes("knife")) assetKey = "knife_goblin";
                else if (name.includes("guard")) assetKey = "fire_guardian"; // Fallback for guardians

                if (assetKey) {
                    if (!spriteCache[assetKey]) {
                        const img = new Image();
                        img.onload = () => requestRedraw();
                        img.onerror = (e) => {
                            console.error(`Failed to load ${assetKey} from ${img.src}`, e);
                            alert(`FAILED TO LOAD IMAGE: ${assetKey}\nPath: ${img.src}`);
                        };
                        img.src = '/static/img/' + assetKey + '.png?v=2';
                        spriteCache[assetKey] = img;
                    }
                    if (spriteCache[assetKey].complete && spriteCache[assetKey].naturalHeight !== 0) {
                        eImg = spriteCache[assetKey];
                    }
                }

                if (eImg.complete) {
                    // ctx.drawImage(eImg, drawX, drawY, TILE_SIZE, TILE_SIZE); // TEST: HIDE ALL STANDARD SPRITES
                    ctx.fillStyle = "rgba(255, 0, 0, 0.5)";
                    ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                } else {
                    ctx.fillStyle = 'red';
                    ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                }

                // HP bar
                const hpPct = enemy.hp / enemy.max_hp;
                ctx.fillStyle = '#500';
                ctx.fillRect(drawX, drawY - 6, TILE_SIZE, 4);
                ctx.fillStyle = '#f00';
                ctx.fillRect(drawX, drawY - 6, TILE_SIZE * hpPct, 4);

                // DEEP DEBUG
                ctx.fillStyle = 'white';
                ctx.font = '8px monospace';
                ctx.fillText(`Key:${assetKey}`, drawX, drawY - 20);

                if (assetKey && spriteCache[assetKey]) {
                    const img = spriteCache[assetKey];
                    ctx.fillText(`Comp:${img.complete} H:${img.naturalHeight}`, drawX, drawY - 10);
                } else {
                    ctx.fillText(`No Cache`, drawX, drawY - 10);
                }
            }
        });

        // Draw Player
        const pDrawX = centerX + (playerPos[0] - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
        const pDrawY = centerY + (playerPos[1] - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);
        if (playerImg.complete) ctx.drawImage(playerImg, pDrawX, pDrawY, TILE_SIZE, TILE_SIZE);
        else { ctx.fillStyle = 'green'; ctx.fillRect(pDrawX, pDrawY, TILE_SIZE, TILE_SIZE); }
        // --- DEBUG OVERLAY (Disabled) ---
        // ctx.font = '12px monospace';
        // ctx.fillStyle = '#ffff00';
        // ctx.textAlign = 'left';
        // ctx.fillText(`Player: ${playerPos[0]}, ${playerPos[1]}, ${playerPos[2]}`, 10, 20);
        // ctx.fillText(`Camera: ${cameraPos[0]}, ${cameraPos[1]}`, 10, 35);
        // ctx.fillText(`Processing: ${isProcessingMove}`, 10, 50);
    }

    // --- Tab Logic ---
    window.switchTab = function (tabName) {
        // Hide all contents for Interaction Panel
        const interactionPanel = document.getElementById('interaction-panel');
        interactionPanel.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        interactionPanel.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

        // Show Selected
        document.getElementById(tabName + '-tab').classList.add('active');

        // Highlight Button (Simple search)
        const buttons = interactionPanel.querySelectorAll('.tab-btn');
        if (tabName === 'nearby') buttons[0].classList.add('active');
        if (tabName === 'items') buttons[1].classList.add('active');
        if (tabName === 'quest') buttons[2].classList.add('active');
    }

    window.switchCharTab = function (tabName) {
        // Hide all contents for Character Panel
        const charPanel = document.getElementById('char-sheet');
        charPanel.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        charPanel.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

        // Show Selected
        document.getElementById(tabName + '-char-tab').classList.add('active');

        // Highlight Button
        const buttons = charPanel.querySelectorAll('.tab-btn');
        if (tabName === 'hero') buttons[0].classList.add('active');
        if (tabName === 'equipment') buttons[1].classList.add('active');
        if (tabName === 'skills') buttons[2].classList.add('active');
    }

    function logMessage(msg) {
        const logEl = document.getElementById('log-content');
        if (!logEl) return;
        const p = document.createElement('div');
        p.innerHTML = "> " + msg;
        p.style.borderBottom = "1px solid #333";
        p.style.padding = "2px 0";
        p.style.fontSize = "0.9em";
        logEl.appendChild(p);
        logEl.scrollTop = logEl.scrollHeight;
    }

    // ... (fetchNarrative skipped)

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
            stats: rawData.player.stats,
            inventory: rawData.player.inventory // New Inventory Data
        };

        viewportData = data;

        // DEBUG LOG
        // console.log("State Fetched:", data);

        drawMap(data.position, data.map, data.enemies, data.corpses, data.npcs);

        // UI Updates
        if (data.combat && data.combat.active) {
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

        // --- POPULATE TABS ---

        // 1. NEARBY TAB
        const nearbyList = document.getElementById('nearby-list');
        nearbyList.innerHTML = '';
        let foundSomething = false;

        // Combat Priority
        if (data.combat && data.combat.active) {
            foundSomething = true;
            const enemyName = data.combat.enemy_name || "Unknown Enemy";
            const enemyHp = data.combat.enemy_hp;

            const div = document.createElement('div');
            div.className = 'interaction-item';
            div.style.borderColor = '#ff0000';
            div.innerHTML = `
            <div style="color: #ff4444; font-weight: bold; text-transform: uppercase;">COMBAT ACTIVE</div>
            <div style="font-size: 1.1em; color: white;">${enemyName}</div>
            <div style="margin: 5px 0; color: #aaa;">
                HP: <span style="color: #f00;">${enemyHp}</span>
            </div>
            <div style="font-size: 0.9em; font-style: italic; color: #666;">
                Threat: High
            </div>
         `;
            nearbyList.appendChild(div);

            switchTab('nearby'); // Force switch to nearby on combat
        } else {
            const [px, py, pz] = data.position;

            // Corpses
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

            // NPCs
            if (data.npcs) {
                data.npcs.forEach((npc, index) => {
                    const [nx, ny, nz] = npc.xyz;
                    const dist = Math.max(Math.abs(nx - px), Math.abs(ny - py));
                    if (dist <= 1) {
                        foundSomething = true;
                        const div = document.createElement('div');
                        div.className = 'interaction-item';
                        div.innerHTML = `
                        <div style="color: #00ffff; font-weight: bold;">${npc.name}</div>
                        <div class="interaction-actions">
                            <button onclick="interact('talk', 'npc', ${npc.id})">Talk</button>
                        </div>
                     `;
                        nearbyList.appendChild(div);
                    }
                });
            }

            // Secrets
            if (data.map && data.world && data.world.secrets) {
                data.world.secrets.forEach(secret => {
                    foundSomething = true;
                    const div = document.createElement('div');
                    div.className = 'interaction-item';
                    div.innerHTML = `
                     <div style="color: #ffd700; font-weight: bold;">${secret.name}</div>
                     <div class="interaction-actions">
                         <button onclick="interact('inspect', 'secret', '${secret.id}')">Inspect</button>
                     </div>
                  `;
                    nearbyList.appendChild(div);
                });
            }

            if (!foundSomething) {
                nearbyList.innerHTML = '<p style="color: #666; font-style: italic;">Nothing of interest nearby.</p>';
            }
        }

        // 2. ITEMS TAB
        const itemsList = document.getElementById('items-list');
        itemsList.innerHTML = '';
        if (data.inventory && data.inventory.length > 0) {
            data.inventory.forEach(item => {
                const div = document.createElement('div');
                div.className = 'interaction-item';
                div.innerHTML = `
                <div style="color: #eee; font-weight: bold;">${item[0]}</div>
                <div style="font-size: 0.8em; color: #888;">Slot: ${item[1]}</div>
            `;
                itemsList.appendChild(div);
            });
        } else {
            itemsList.innerHTML = '<p style="color: #666; font-style: italic;">Your bag is empty.</p>';
        }

        // 3. QUESTS TAB (Mockup/Inferred)
        const questList = document.getElementById('quest-list');
        questList.innerHTML = '';
        let questCount = 0;

        // A. Active Quests from Player State
        // We now use the friendly 'quest_log' processed by backend
        const activeQuests = rawData.player.quest_log || [];
        console.log("DEBUG: Active Quests:", activeQuests);
        if (window.updateLog) window.updateLog("DEBUG: Quests: " + JSON.stringify(activeQuests));


        activeQuests.forEach(quest => {
            const div = document.createElement('div');
            div.className = 'interaction-item';
            div.style.borderLeft = "3px solid #ffd700"; // Gold highlight
            div.innerHTML = `
            <div style="color: #ffd700; font-weight: bold;">${quest.title || quest}</div>
            <div style="font-size: 0.9em; color: #aaa;">${quest.description || "Active Quest"}</div>
        `;
            questList.appendChild(div);
            questCount++;
        });

        // B. Implied Rescue Quests (Legacy)
        if (data.npcs) {
            data.npcs.forEach(npc => {
                if (npc.xyz[2] === 0 && npc.name !== "Dungeon Warden") {
                    const div = document.createElement('div');
                    div.className = 'interaction-item';
                    div.innerHTML = `
                    <div style="color: #ffa500; font-weight: bold;">Rescue ${npc.name}</div>
                    <div style="font-size: 0.9em; color: #aaa;">Trapped in dungeon</div>
                `;
                    questList.appendChild(div);
                    questCount++;
                }
            });
        }

        if (questCount === 0) {
            questList.innerHTML = '<p style="color: #666; font-style: italic;">No active quests.</p>';
        }
    }

    async function interact(action, type, id) {
        if (action === 'talk' && type === 'npc') {
            // Open Chat Interface
            // We need to fetch the name. Usually the id matches the index in data.npcs
            // Ideally we pass name, but layout is simpler:
            // Let's assume the NPC name is what we claimed in the button generation.
            // We'll just pass the ID and let backend identify.
            // But for UI title, we might want to grab it.
            const name = "NPC"; // Placeholder, backend provides real name context
            openChat(name, id);
            return;
        }

        // Call API for real interaction (Loot/Inspect)
        try {
            const response = await fetch('/api/interact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: action, type: type, id: id })
            });
            const data = await response.json();
            if (data.narrative) logMessage(data.narrative);
            fetchState();
        } catch (e) {
            console.error("Interaction failed:", e);
        }
    }

    // --- Chat System ---
    let activeChatNPCId = null;

    async function openChat(name, id) {
        activeChatNPCId = id;
        document.getElementById('chat-modal').style.display = 'flex';
        const hist = document.getElementById('chat-history');
        hist.innerHTML = '<div class="chat-message npc">System: Loading History...</div>';
        document.getElementById('chat-input').focus();

        // Fetch History
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ npc_index: id, message: "__INIT__" })
            });
            const data = await response.json();

            hist.innerHTML = ''; // Clear loading

            if (data.reply && data.reply !== "...") {
                const lines = data.reply.split('\n\n');
                lines.forEach(line => {
                    if (!line.trim()) return;
                    const div = document.createElement('div');

                    if (line.startsWith("Player:")) {
                        div.className = 'chat-message user';
                        div.textContent = line.replace("Player:", "").trim();
                    } else {
                        div.className = 'chat-message npc';
                        // Try to remove "Elara:" prefix if present for cleaner UI
                        const namePrefix = data.npc_name + ":";
                        if (line.startsWith(namePrefix)) {
                            div.textContent = line.replace(namePrefix, "").trim();
                        } else {
                            div.textContent = line;
                            document.getElementById('chat-npc-name').innerText = data.npc_name;
                            // document.getElementById('chat-history').innerHTML = '';

                            // Set Portrait
                            const portraitDiv = document.getElementById('chat-portrait');
                            let imgUrl = 'static/img/player.png'; // Default/Fallback

                            // Simple mapping (Case insensitive check)
                            const lowerName = (data.npc_name || "").toLowerCase();
                            if (lowerName.includes('elara')) imgUrl = 'static/img/Sorceress.jpg';
                            else if (lowerName.includes('gareth')) imgUrl = 'static/img/Warrior.jpg';
                            else if (lowerName.includes('skeleton')) imgUrl = 'static/img/skeleton.png';
                            else if (lowerName.includes('troll')) imgUrl = 'static/img/bones.png'; // Fallback for monsters

                            portraitDiv.style.backgroundImage = `url('${imgUrl}')`;

                            // Initial greeting trigger via backend? 
                            // Usually backend sends greeting upon 'interact' or bumping. 
                            document.getElementById('chat-input').focus(); // Focus input when chat opens
                        }
                        if (div) hist.appendChild(div);
                    } // End Else
                }); // End ForEach
            }
        } catch (e) {
            console.error("Chat Load Error:", e);
        }
    }

    function closeChat() {
        activeChatNPCId = null;
        document.getElementById('chat-modal').style.display = 'none';
    }

    function handleChatKey(e) {
        if (e.key === 'Enter') sendChatMessage();
    }

    async function sendChatMessage(msgOverride) {
        const input = document.getElementById('chat-input');
        const msg = msgOverride || input.value.trim();
        if (!msg) return;

        // Append User Msg
        const hist = document.getElementById('chat-history');
        const userDiv = document.createElement('div');
        userDiv.className = 'chat-message user';
        userDiv.textContent = msg;
        hist.appendChild(userDiv);

        if (!msgOverride) input.value = '';
        hist.scrollTop = hist.scrollHeight;

        // Send to Backend
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ npc_index: activeChatNPCId, message: msg })
            });
            const data = await response.json();

            // Append NPC Response
            if (data.reply) {
                const npcDiv = document.createElement('div');
                npcDiv.className = 'chat-message npc';
                npcDiv.textContent = data.reply;
                hist.appendChild(npcDiv);
                hist.scrollTop = hist.scrollHeight;

                // Update modal title if provided
                if (data.npc_name) {
                    document.getElementById('chat-npc-name').textContent = "Conversing with " + data.npc_name;
                }

                fetchState(); // Refresh map (e.g. Secret Doors)
            }
        } catch (e) {
            console.error("Chat Error:", e);
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

    let isProcessingMove = false;

    async function move(direction) {
        if (isProcessingMove) {
            console.log("Skipping move: Busy");
            return;
        }
        isProcessingMove = true;

        // Safety release: Auto-reset flag after 120ms
        setTimeout(() => { isProcessingMove = false; }, 120);

        try {
            const response = await fetch('/api/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ direction: direction })
            });
            const data = await response.json();
            // console.log("Move Narrative:", data.narrative); 
            if (data.narrative) logMessage(data.narrative);
            else fetchNarrative();
            await fetchState();
        } catch (e) {
            console.error("Move Error:", e);
        } finally {
            isProcessingMove = false;
        }
    }

    let cameraPos = null;

    // Duplicate drawMap removed.

    fetchState().then(async () => {
        fetchNarrative();
    });

    document.addEventListener('keydown', (e) => {
        // Debug why movement might fail
        if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "a", "s", "d"].includes(e.key)) {
            // Allow typing in Chat Input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            e.preventDefault(); // LOCK SCROLL for all move keys

            if (activeChatNPCId !== null) {
                console.warn("Movement blocked: Chat is open. activeChatNPCId:", activeChatNPCId);
                return;
            }

            if (isProcessingMove) {
                console.warn("Movement blocked: Still processing previous move.");
                return;
            }

            if (e.key === 'ArrowUp' || e.key === 'w') move('north');
            if (e.key === 'ArrowDown' || e.key === 's') move('south');
            if (e.key === 'ArrowLeft' || e.key === 'a') move('west');
            if (e.key === 'ArrowRight' || e.key === 'd') move('east');
        }
    });

    // Intro Message
    setTimeout(() => {
        logMessage("You awake with a throbbing headache, the cold stone floor pressing against your cheek. The air smells of damp earth and old iron. You are disoriented, alone, and trapped in the depths of an unknown dungeon...");
    }, 500);

    async function useSkill(skillName) {
        if (skillName === 'investigate') {
            logMessage("Investigating surroundings...");
            try {
                const response = await fetch('/api/action/investigate', { method: 'POST' });
                const data = await response.json();

                if (data.narrative) logMessage(data.narrative);

                // Populate Nearby Tab
                if (data.entities && data.entities.length > 0) {
                    const nearbyList = document.getElementById('state-list'); // ID is technically nearby-list but logic uses ID state-list in HTML? 
                    // Wait, main HTML has `id="nearby-list"` inside `nearby-tab`.
                    // Let's target strictly.
                    const listEl = document.getElementById('nearby-list');
                    if (listEl) {
                        listEl.innerHTML = ''; // Clear "Nothing of interest"
                        // Sort by distance
                        data.entities.sort((a, b) => a.dist - b.dist);

                        data.entities.forEach(ent => {
                            const div = document.createElement('div');
                            div.className = 'item-entry';
                            div.innerHTML = `
                             <strong>${ent.name}</strong> (${ent.dist}m)<br>
                             <span style="font-size:0.8em; color:#aaa;">${ent.status}</span>
                         `;
                            listEl.appendChild(div);
                        });
                        // Auto-switch to Nearby tab
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
} // End useSkill

// Expose functions to global scope for HTML onclick access
window.openChat = openChat;
window.closeChat = closeChat;
window.sendChat = sendChat;
window.useSkill = useSkill;
window.interact = interact; // Defined inside
window.toggleMap = toggleMap;
try { window.resetGame = resetGame; } catch (e) { }

            }); // End Wrapper
