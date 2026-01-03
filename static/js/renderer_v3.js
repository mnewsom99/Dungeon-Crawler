// RENDERER V3 - MINIMAL FALLBACK
// Designed to absolutely guarantee rendering works.
console.log("RENDERER V5 STARTING...");

let TILE_SIZE = 64; // Default Zoom
const MAP_WIDTH = 800;
const MAP_HEIGHT = 600;
let cameraPos = [0, 0];
let playerPos = [0, 0, 0];
let visibleMap = {};

// Images - NOW MANAGED BY spriteCache
const playerImg = new Image(); playerImg.src = "/static/img/player.png";
const floorImg = new Image(); floorImg.src = "/static/img/floor_wood.png"; // Default fallback
// const wallImg = ... REMOVED to prevent conflict with spriteCache['wall']


// Environment Assets
// Environment Assets
const spriteCache = {};
function loadSprite(key, filename) {
    const img = new Image();
    img.src = `/static/img/${filename}`;
    img.onload = () => console.log(`[Assets] Loaded ${key}`);
    img.onerror = () => console.error(`[Assets] FAILED to load ${key} from ${img.src}`);
    spriteCache[key] = img;
}

// GALLERY M APPINGS (From ROLES)
loadSprite("wall", "wall_grey.png"); // Default 'wall' to 'wall_grey'
loadSprite("wall_grey", "wall_grey.png");
loadSprite("wall_house", "wall_house.png");
loadSprite("door", "door.png");
loadSprite("door_wood", "door_wood.png");
loadSprite("stairs_down", "trapdoor_down.png"); // Dungeon Entrance
loadSprite("door_stone", "door_stone.png");
loadSprite("floor_wood", "floor_wood.png");
loadSprite("grass", "grass.png");
loadSprite("water", "water.png");
loadSprite("tree", "tree.png");

// PROPS
loadSprite("anvil", "anvil.png");
loadSprite("shelf", "shelf.png");
loadSprite("barrel", "barrel.png");
loadSprite("crate", "crate.png");
loadSprite("chest", "chest.png");
loadSprite("street_lamp", "street_lamp.png");
loadSprite("fountain", "fountain.png");
loadSprite("flower_pot", "flower_pot.png");
loadSprite("signpost", "signpost.png"); // Replaces manual sign drawing

// ENEMIES
loadSprite("skeleton", "skeleton.png");
loadSprite("knife_goblin", "knife_goblin.png");
loadSprite("goblin", "goblin_scout.png"); // Map generic goblin to scout
loadSprite("goblin_scout", "goblin_scout.png");
loadSprite("cinder_hound", "cinder_hound.png");
loadSprite("fire_guardian", "fire_guardian.png");
loadSprite("magma_weaver", "magma_weaver.png");
loadSprite("obsidian_sentinel", "obsidian_sentinel.png");
loadSprite("sulfur_bat", "sulfur_bat.png");
loadSprite("bear", "bear.png");
loadSprite("wolf", "wolf.png");
loadSprite("herb", "herb.png");

// Dynamic Imports (Mountains/Others)
// Dynamic Imports (Mountains/Others)
loadSprite("rock", "rock.png");
loadSprite("shrine", "shrine_healing.png");
loadSprite("bones", "bones.png");

// Zoom Logic
window.addEventListener('wheel', (e) => {
    e.preventDefault();
    if (e.deltaY < 0) {
        TILE_SIZE += 4; // Zoom In
    } else {
        TILE_SIZE -= 4; // Zoom Out
    }
    // Clamp Zoom
    if (TILE_SIZE < 4) TILE_SIZE = 4;
    if (TILE_SIZE > 128) TILE_SIZE = 128;

    // Force Redraw
    const canvas = document.getElementById('map-canvas');
    if (canvas) fetchAndDraw(canvas.getContext('2d'));
}, { passive: false });


// NPC Images
const npcImages = {};
function loadNpcImage(name, filename) {
    const img = new Image();
    img.src = `/static/img/${filename}`;
    npcImages[name] = img;
}
loadNpcImage("Elder Aethelgard", "elder.png");
loadNpcImage("Seraphina", "Sorceress3.png"); // High-Res Witch
loadNpcImage("Kael", "warrior2.png");
loadNpcImage("Gareth", "warrior2.png");
loadNpcImage("Elara", "elara_transparent.png"); // High-Res Elara

// RESIZE HANDLER FOR HIGH DPI / FULLSCREEN
function resizeCanvas() {
    const canvas = document.getElementById('map-canvas');
    if (!canvas) return;

    // Match internal resolution to display size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Re-apply context settings lost on resize
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;

    // Redraw immediately
    fetchAndDraw(ctx);
}
window.addEventListener('resize', resizeCanvas);

// Main Game Loop
window.onload = function () {
    console.log("Window Onload - V3");
    resizeCanvas(); // Set initial size

    const canvas = document.getElementById('map-canvas');
    if (!canvas) { console.error("No Canvas Found"); return; }
    const ctx = canvas.getContext('2d');

    // Start Fetch Loop
    setInterval(() => fetchAndDraw(ctx), 500);
};

async function fetchAndDraw(ctx) {
    try {
        const canvas = ctx.canvas;
        // FORCE PIXELATION via CSS
        if (canvas.style.imageRendering !== 'pixelated') {
            canvas.style.imageRendering = 'pixelated';
        }

        ctx.imageSmoothingEnabled = false;
        ctx.mozImageSmoothingEnabled = false;
        ctx.webkitImageSmoothingEnabled = false;
        ctx.msImageSmoothingEnabled = false;

        const res = await fetch(`/api/state?t=${Date.now()}`);
        const data = await res.json();

        // UI UPDATE HOOK
        if (window.updateDashboard) window.updateDashboard(data);

        if (!data.world || !data.world.map) return;

        visibleMap = data.world.map;
        playerPos = data.player.xyz;
        cameraPos = [...playerPos]; // Lock camera

        // DRAW
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Background
        ctx.fillStyle = "#111";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;

        const playerZ = playerPos[2];

        // --- TILE RENDERING ---
        for (let key in visibleMap) {
            const [x, y, z] = key.split(',').map(Number);
            if (z !== playerZ) continue;

            const drawX = centerX + (x - cameraPos[0]) * TILE_SIZE - TILE_SIZE / 2;
            const drawY = centerY + (y - cameraPos[1]) * TILE_SIZE - TILE_SIZE / 2;

            // GRID OVERLAY
            ctx.strokeStyle = "rgba(0,0,0,0.15)";
            ctx.lineWidth = 1;
            ctx.strokeRect(drawX, drawY, TILE_SIZE, TILE_SIZE);

            const tileType = visibleMap[key];

            // FOG OF WAR: Distance Dimming
            const dist = Math.sqrt(Math.pow(x - playerPos[0], 2) + Math.pow(y - playerPos[1], 2));
            const isVisible = dist < 7;

            // Dim "Memory" tiles
            ctx.globalAlpha = isVisible ? 1.0 : 0.4;

            // RENDER LOGIC V5 - SPRITE FIRST
            const typeValue = (tileType || "").toLowerCase();

            // 1. Base Layer (Grass/Floor)
            if (playerZ === 1 || playerZ === 2) {
                if (spriteCache['grass'] && spriteCache['grass'].complete)
                    ctx.drawImage(spriteCache['grass'], drawX, drawY, TILE_SIZE, TILE_SIZE);
            } else {
                if (spriteCache['floor_wood'] && spriteCache['floor_wood'].complete && (typeValue.includes('wood') || typeValue.includes('residence')))
                    ctx.drawImage(spriteCache['floor_wood'], drawX, drawY, TILE_SIZE, TILE_SIZE);
                else if (floorImg.complete)
                    ctx.drawImage(floorImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            }

            // 2. Object Layer - Check SpriteCache Direct Match First
            // Handle aliases/mappings
            let renderKey = typeValue;
            if (renderKey === 'sign') renderKey = 'signpost';
            if (renderKey === 'road' || renderKey === 'path') renderKey = 'street';

            // DOOR LOGIC: Differentiate Town vs Dungeon
            if (renderKey === 'door') {
                if (playerZ === 1 && spriteCache['door_wood']) {
                    renderKey = 'door_wood';
                }
            }

            // Explicit check for door_stone if not caught by generic loader (SAFETY)
            if (renderKey === 'door_stone' && spriteCache['door_stone']) {
                ctx.drawImage(spriteCache['door_stone'], drawX, drawY, TILE_SIZE, TILE_SIZE);
            }
            else if (spriteCache[renderKey] && spriteCache[renderKey].complete) {
                ctx.drawImage(spriteCache[renderKey], drawX, drawY, TILE_SIZE, TILE_SIZE);
            }
            // 3. Fallback / Special Logic for Procedural IDs (walls) or Missing Sprites
            else if (typeValue.includes('wall')) {
                if (typeValue.includes('house') && spriteCache['wall_house']) {
                    ctx.drawImage(spriteCache['wall_house'], drawX, drawY, TILE_SIZE, TILE_SIZE);
                } else if (spriteCache['wall'] && spriteCache['wall'].complete) {
                    ctx.drawImage(spriteCache['wall'], drawX, drawY, TILE_SIZE, TILE_SIZE);
                } else {
                    ctx.fillStyle = "#555"; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                }
            }
            else if (typeValue.includes('street')) {
                // Fallback if street sprite texturing failed, but we want the brown path
                ctx.fillStyle = "#5d4037"; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = "#4e342e"; ctx.fillRect(drawX + 5, drawY + 5, 4, 4);
            }
            else if (typeValue.includes('water')) {
                // Animation could go here
                if (spriteCache['water']) ctx.drawImage(spriteCache['water'], drawX, drawY, TILE_SIZE, TILE_SIZE);
                else ctx.fillStyle = "blue"; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
            }
            else if (typeValue === 'herb') {
                if (spriteCache['herb'] && spriteCache['herb'].complete) {
                    ctx.drawImage(spriteCache['herb'], drawX, drawY, TILE_SIZE, TILE_SIZE);
                } else {
                    ctx.fillStyle = "magenta"; ctx.fillRect(drawX + 8, drawY + 8, 16, 16);
                }
            }
            else if (typeValue.startsWith('mtn')) {
                if (!spriteCache[tileType]) loadSprite(tileType, tileType + '.png');
                if (spriteCache[tileType] && spriteCache[tileType].complete)
                    ctx.drawImage(spriteCache[tileType], drawX, drawY, TILE_SIZE, TILE_SIZE);
            }
            else if (renderKey === 'door' || renderKey.includes('floor')) {
                // Handled by base or sprite check usually. 
                // If special door needed:
                // ctx.fillStyle = "brown"; ...
            }
            // UNKNOWN
            else if (!typeValue.includes('grass')) {
                // Only show purple if it's REALLY unknown
                if (!typeValue.includes('floor')) {
                    ctx.fillStyle = "purple";
                    ctx.fillRect(drawX + TILE_SIZE / 4, drawY + TILE_SIZE / 4, TILE_SIZE / 2, TILE_SIZE / 2);
                }
            }

            // RESET ALPHA
            ctx.globalAlpha = 1.0;
        }

        // --- ENTITY RENDERING (Enable Smoothing for High Res Sprites) ---
        ctx.imageSmoothingEnabled = true;

        // --- CORPSE RENDERING ---
        if (data.corpses) {
            data.corpses.forEach(c => {
                const [cx, cy, cz] = c.xyz;
                if (cz !== playerZ) return;
                // Fog of War Check
                if (!visibleMap[`${cx},${cy},${cz}`]) return;

                const drawX = centerX + (cx - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
                const drawY = centerY + (cy - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

                if (spriteCache['bones'] && spriteCache['bones'].complete) {
                    ctx.drawImage(spriteCache['bones'], drawX, drawY, TILE_SIZE, TILE_SIZE);
                } else {
                    ctx.fillStyle = "#ccc";
                    ctx.beginPath();
                    ctx.arc(drawX + TILE_SIZE / 2, drawY + TILE_SIZE / 2, TILE_SIZE / 4, 0, 2 * Math.PI);
                    ctx.fill();
                }
            });
        }

        if (data.world.npcs) {
            data.world.npcs.forEach(npc => {
                const [nx, ny, nz] = npc.xyz;
                if (nz !== playerZ) return;

                // Fog of War Check
                const tileKey = `${nx},${ny},${nz}`;
                if (!visibleMap[tileKey]) return;

                const drawX = centerX + (nx - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
                const drawY = centerY + (ny - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

                // Draw NPC Image if Available
                let drawn = false;

                // Backend provided asset (e.g. "warrior2.png")
                let assetKey = npc.asset;

                // Fallback for legacy
                if (!assetKey) {
                    // Try name match (Legacy)
                    for (let nameKey in npcImages) {
                        if (npc.name.includes(nameKey)) {
                            // We found a partial match in our legacy list
                            // But wait, npcImages values are Image objects, not keys.
                            // Let's just draw it if found.
                            ctx.drawImage(npcImages[nameKey], drawX, drawY, TILE_SIZE, TILE_SIZE);
                            drawn = true;
                            break;
                        }
                    }
                } else {
                    // Modern Path: Use asset filename
                    // check if loaded in npcImages (we'll store by filename now too) or spriteCache

                    // Lazy Load if missing
                    if (!npcImages[assetKey]) {
                        console.log(`[Renderer] Lazy Loading NPC Asset: ${assetKey}`);
                        loadNpcImage(assetKey, assetKey);
                    }

                    const img = npcImages[assetKey];
                    if (img && img.complete) {
                        ctx.drawImage(img, drawX, drawY, TILE_SIZE, TILE_SIZE);
                        drawn = true;
                    }
                }

                if (!drawn) {
                    ctx.fillStyle = "cyan";
                    ctx.fillRect(drawX + 4, drawY + 4, TILE_SIZE - 8, TILE_SIZE - 8);
                }

                ctx.fillStyle = "white"; ctx.font = "10px monospace"; ctx.textAlign = "center";
                ctx.fillText(npc.name, drawX + 16, drawY - 5);
            });
        }

        if (data.world.enemies) {
            data.world.enemies.forEach(enemy => {
                const [ex, ey, ez] = enemy.xyz;
                if (ez !== playerZ) return;

                // Fog of War Check
                const tileKey = `${ex},${ey},${ez}`;
                if (!visibleMap[tileKey]) return; // HIDDEN if not in visible/visited map

                const drawX = centerX + (ex - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
                const drawY = centerY + (ey - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

                // Sprite Mapping
                const name = (enemy.name || "").toLowerCase();
                let assetKey = "skeleton"; // Default
                if (name.includes("goblin")) assetKey = "goblin";
                if (name.includes("knife")) assetKey = "knife_goblin";
                if (name.includes("wolf")) assetKey = "wolf";
                if (name.includes("bear")) assetKey = "bear";
                if (name.includes("cinder")) assetKey = "cinder_hound";
                if (name.includes("sentinel")) assetKey = "obsidian_sentinel";
                if (name.includes("bat")) assetKey = "sulfur_bat";
                if (name.includes("weaver")) assetKey = "magma_weaver";
                if (name.includes("guard")) assetKey = "fire_guardian";

                if (spriteCache[assetKey] && spriteCache[assetKey].complete) {
                    ctx.drawImage(spriteCache[assetKey], drawX, drawY, TILE_SIZE, TILE_SIZE);
                } else {
                    // Fallback Square
                    if (name.includes("goblin")) ctx.fillStyle = "green";
                    else if (name.includes("giant")) ctx.fillStyle = "blue";
                    else ctx.fillStyle = "red";
                    ctx.fillRect(drawX + 2, drawY + 2, TILE_SIZE - 4, TILE_SIZE - 4);
                }

                // HP Bar
                const hpPct = (enemy.hp / enemy.max_hp) || 1;
                ctx.fillStyle = "red"; ctx.fillRect(drawX, drawY - 6, TILE_SIZE, 4);
                ctx.fillStyle = "lime"; ctx.fillRect(drawX, drawY - 6, TILE_SIZE * hpPct, 4);
                ctx.fillStyle = "lime"; ctx.fillRect(drawX, drawY - 6, TILE_SIZE * hpPct, 4);
            });
        }

        // --- OBJECTS (Crates, Chests) ---
        // --- OBJECTS (Crates, Chests, Secrets) ---
        if (data.world && data.world.secrets) {
            data.world.secrets.forEach(obj => {
                if (!obj.xyz) return;

                const [ox, oy, oz] = obj.xyz;
                if (oz !== playerZ) return;

                // Fog of War Check
                const tileKey = `${ox},${oy},${oz}`;
                if (!visibleMap[tileKey]) return;

                const drawX = centerX + (ox - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
                const drawY = centerY + (oy - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

                let assetKey = "crate"; // Default
                const name = (obj.name || "").toLowerCase();
                const type = (obj.obj_type || "").toLowerCase(); // Check obj_type from DM

                // Use chest sprite if applicable
                if (type === "chest" || name.includes("chest")) assetKey = "chest";

                const img = spriteCache[assetKey];
                if (img && img.complete && img.naturalWidth > 0) {
                    ctx.drawImage(img, drawX, drawY, TILE_SIZE, TILE_SIZE);
                } else {
                    // Fallback
                    ctx.fillStyle = "#8B4513";
                    ctx.fillRect(drawX + 8, drawY + 8, TILE_SIZE - 16, TILE_SIZE - 16);
                    ctx.strokeStyle = "#D2691E";
                    ctx.lineWidth = 2;
                    ctx.strokeRect(drawX + 8, drawY + 8, TILE_SIZE - 16, TILE_SIZE - 16);
                }
            });
        }

        // Draw Player
        const pX = centerX - TILE_SIZE / 2;
        const pY = centerY - TILE_SIZE / 2;
        if (playerImg.complete) ctx.drawImage(playerImg, pX, pY, TILE_SIZE, TILE_SIZE);
        else { ctx.fillStyle = "red"; ctx.fillRect(pX, pY, TILE_SIZE, TILE_SIZE); }

        // Debug Text - DISABLED FOR PRODUCTION
        // ctx.fillStyle = "yellow";
        // ctx.font = "16px monospace";
        // ctx.fillText(`Pos: ${playerPos}`, 10, 20);
        // ctx.fillText(`Tiles: ${Object.keys(visibleMap).length}`, 10, 40);

    } catch (e) {
        console.error("V3 Error:", e);
    }
}

// --- CONTROLS ---
let lastInputTime = 0;
let inputDebug = "None";

window.addEventListener('keydown', (e) => {
    if (Date.now() - lastInputTime < 100) return; // Debounce slightly
    lastInputTime = Date.now();

    let dx = 0, dy = 0;
    if (e.key === 'w' || e.key === 'ArrowUp') dy = -1;
    if (e.key === 's' || e.key === 'ArrowDown') dy = 1;
    if (e.key === 'a' || e.key === 'ArrowLeft') dx = -1;
    if (e.key === 'd' || e.key === 'ArrowRight') dx = 1;

    if (dx !== 0 || dy !== 0) {
        inputDebug = `Key Code: ${e.code} -> Move ${dx},${dy}`;
        movePlayer(dx, dy);
    }
});

// --- MOUSE CONTROLS ---
window.addEventListener('mousedown', (e) => {
    const canvas = document.getElementById('map-canvas');
    if (e.target !== canvas) return;

    const rect = canvas.getBoundingClientRect();

    // Scale Factors (Internal Resolution / Displayed Size)
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    // Mouse Posiiton in Canvas Coordinates (0-800, 0-600)
    const canvasX = (e.clientX - rect.left) * scaleX;
    const canvasY = (e.clientY - rect.top) * scaleY;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // Relative to Player (Center)
    const relX = canvasX - centerX;
    const relY = canvasY - centerY;

    // Calculate Tile Difference
    // TILE_SIZE is current zoom level
    const tileDx = relX / TILE_SIZE;
    const tileDy = relY / TILE_SIZE;

    console.log(`Click Debug: Canvas(${canvasX.toFixed(0)},${canvasY.toFixed(0)}) Center(${centerX},${centerY}) Rel(${relX.toFixed(0)},${relY.toFixed(0)}) TileD(${tileDx.toFixed(1)},${tileDy.toFixed(1)})`);

    let dx = 0;
    let dy = 0;

    // Simple Directional Logic
    // Threshold to prevent accidental moves near center?
    // Let's just use largest axis
    if (Math.abs(relX) > Math.abs(relY)) {
        // Horizontal
        dx = relX > 0 ? 1 : -1;
    } else {
        // Vertical
        dy = relY > 0 ? 1 : -1;
    }

    if (dx !== 0 || dy !== 0) {
        movePlayer(dx, dy);
    }
});

async function movePlayer(dx, dy) {
    // Optimistic Update
    playerPos[0] += dx;
    playerPos[1] += dy;

    // Force immediate redraw to show movement
    const canvas = document.getElementById('map-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        fetchAndDraw(ctx); // Re-draw with new optimistic pos
    }

    try {
        const res = await fetch('/api/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dx, dy })
        });
        const json = await res.json();

        // Immediate UI Update
        if (json.state && window.updateDashboard) {
            window.updateDashboard(json.state);
        }

        if (json.narrative && window.logMessage) {
            window.logMessage(json.narrative);
        }
    } catch (e) {
        console.error("Move Failed", e);
        // Revert on failure (simple)
        playerPos[0] -= dx;
        playerPos[1] -= dy;
    }
}

// Draw Input Debug
function drawInputDebug(ctx) {
    ctx.fillStyle = "white";
    ctx.font = "14px monospace";
    ctx.fillText(`Last Input: ${inputDebug}`, 10, 60);
}

// Modify fetchAndDraw to include this:
// ... inside fetchAndDraw ...
// ctx.fillText(`Tiles: ${Object.keys(visibleMap).length}`, 10, 40);
// drawInputDebug(ctx); 
// ...


// Global Exposes for HTML Buttons (Empty for now to prevent errors)
window.interact = function () { };
window.openChat = function () { };
window.useSkill = function () { };
window.toggleMap = function () { };
