console.log("GRAPHICS.JS: Advanced Chroma Handler Loading...");

// State
let ZOOM_LEVEL = 1.0;
const BASE_TILE_SIZE = 64;
const VIS_RADIUS = 7;
let canvas, ctx;
let camOffsetX = 0; // New Global
let camOffsetY = 0; // New Global

// --- Asset Loader ---
const images = {};
const assets = {
    // Basic
    'floor': 'floor.png',
    'floor_wood': 'floor_wood.png',
    'wall': 'wall_grey.png',
    'wall_grey': 'wall_grey.png',
    'wall_house': 'wall_house.png',
    'door': 'door.png',
    'grass': 'grass.png',
    'water': 'water.png',
    'rock': 'rock.png',
    'tree': 'tree.png',
    'fountain': 'fountain.png',
    'flower_pot': 'flower_pot.png',
    'street_lamp': 'street_lamp.png',
    'signpost': 'signpost.png',
    'barrel': 'barrel.png',
    'crate': 'crate.png',
    'anvil': 'anvil.png',
    'shelf': 'shelf.png',

    // Entities
    'player': 'player.png',
    'skeleton': 'Skeleton.png',
    'chest': 'chest.png',
    'chest': 'chest.png',
    'open_door': 'door.png',
    'bones': 'bones.png',

    // NPCs
    'elara': 'elara_transparent.png',
    'seraphina': 'seraphina.png',
    'elder': 'elder.png',
    'warrior2': 'warrior2.png',
    'herb': 'herb.png',
    'bear': 'bear.png',
    'wolf': 'wolf.png',
    'mountain_entrance': 'mountain_entrance.png',
    'fire_guardian': 'fire_guardian.png'
};

// --- Advanced Chroma/Transparency Processor ---
function processTransparency(img) {
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = img.width;
    tempCanvas.height = img.height;
    const tCtx = tempCanvas.getContext('2d');
    tCtx.drawImage(img, 0, 0);

    const imgData = tCtx.getImageData(0, 0, img.width, img.height);
    const data = imgData.data;

    for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];

        // 1. Pure White (Backgrounds)
        const isWhite = (r > 240 && g > 240 && b > 240);

        // 2. Checkerboard/Flat Grey (Backgrounds)
        // We lower the floor to 150 to catch darker editor backgrounds
        // BUT we tighten the spread (<3) to ensure we don't delete "Stone" textures (which have color noise)
        const isGrey = (r > 150 && r < 240) &&
            (Math.abs(r - g) < 3) &&
            (Math.abs(g - b) < 3) &&
            (Math.abs(r - b) < 3);

        // 3. Magic Pink (Magenta) - Legacy support
        // Only if pure magenta to avoid deleting pink flowers
        const isMagenta = (r > 250 && g < 5 && b > 250);

        if (isWhite || isGrey || isMagenta) {
            data[i + 3] = 0; // Alpha = 0
        }
    }

    tCtx.putImageData(imgData, 0, 0);
    const newImg = new Image();
    newImg.src = tempCanvas.toDataURL();
    return newImg;
}

// Preload
Object.keys(assets).forEach(key => {
    const rawImg = new Image();
    rawImg.crossOrigin = "Anonymous";
    rawImg.src = `/static/img/${assets[key]}?v=` + Date.now();

    rawImg.onload = () => {
        // Only process Entities/NPCs
        // We include 'elara' specifically to catch the checkerboard
        if (key === 'floor' || key.includes('wall') || key.includes('grass')) {
            images[key] = rawImg;
        } else {
            // Apply Chroma Key
            images[key] = processTransparency(rawImg);
        }
    };
    rawImg.onerror = () => { images[key] = null; };
});

// --- Zoom Input ---
document.addEventListener('wheel', (e) => {
    if (e.ctrlKey) return;
    e.preventDefault();
    if (e.deltaY < 0) ZOOM_LEVEL = Math.min(ZOOM_LEVEL + 0.1, 3.0);
    else ZOOM_LEVEL = Math.max(ZOOM_LEVEL - 0.1, 0.5);
}, { passive: false });


window.drawMap = function (data) {
    canvas = document.getElementById('map-canvas');
    if (!canvas) return;
    ctx = canvas.getContext('2d');

    if (canvas.width !== window.innerWidth) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    ctx.fillStyle = '#050505';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!data || !data.world || !data.world.map) return;

    const TILE_SIZE = Math.round(BASE_TILE_SIZE * ZOOM_LEVEL);
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const playerPos = data.player.xyz;

    // Update Globals for Click Handler
    // Player is at Center.
    // ScreenX = CenterX + (WorldX - PlayerX) * TILE_SIZE - TILE_SIZE/2
    // Implies: WorldX = (ScreenX - CenterX + TILE_SIZE/2) / TILE_SIZE + PlayerX

    // Let's store the base offsets for the formula: ScreenX = OffsetX + WorldX * TILE_SIZE
    // OffsetX = CenterX - PlayerX * TILE_SIZE - TILE_SIZE/2
    camOffsetX = centerX - playerPos[0] * TILE_SIZE - TILE_SIZE / 2;
    camOffsetY = centerY - playerPos[1] * TILE_SIZE - TILE_SIZE / 2;

    const map = data.world.map;

    ctx.imageSmoothingEnabled = false;

    // Draw Map
    Object.keys(map).forEach(key => {
        const [x, y, z] = key.split(',').map(Number);
        if (z !== playerPos[2]) return;

        // Use Global Offsets for Drawing too to ensure consistency
        const dx = Math.round(camOffsetX + x * TILE_SIZE);
        const dy = Math.round(camOffsetY + y * TILE_SIZE);

        if (dx < -TILE_SIZE || dy < -TILE_SIZE || dx > canvas.width || dy > canvas.height) return;

        const tileType = map[key];
        const img = images[tileType];

        // Fog
        const dist = Math.abs(x - playerPos[0]) + Math.abs(y - playerPos[1]);
        const isVisible = dist <= VIS_RADIUS;

        if (img) {
            ctx.drawImage(img, dx, dy, TILE_SIZE, TILE_SIZE);
        } else {
            // Procedural Fallbacks for detailed types
            if (tileType === 'void') {
                // Starfield
                ctx.fillStyle = '#110022';
                ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = '#fff';
                // Random stars (static based on coord hash would be better but random is okay for now if redrawn)
                // actually random flickers which is nice
                if (Math.random() > 0.9) ctx.fillRect(dx + Math.random() * TILE_SIZE, dy + Math.random() * TILE_SIZE, 1, 1);
            }
            else if (tileType === 'herb') {
                if (images['herb']) {
                    ctx.drawImage(images['herb'], dx, dy, TILE_SIZE, TILE_SIZE);
                } else {
                    // Grass Base
                    ctx.fillStyle = '#228b22';
                    ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
                    // Flower Cluster
                    ctx.fillStyle = '#FF69B4'; // HotPink Flowers
                    ctx.beginPath();
                    ctx.arc(dx + TILE_SIZE * 0.25, dy + TILE_SIZE * 0.25, TILE_SIZE * 0.1, 0, Math.PI * 2);
                    ctx.arc(dx + TILE_SIZE * 0.75, dy + TILE_SIZE * 0.75, TILE_SIZE * 0.1, 0, Math.PI * 2);
                    ctx.arc(dx + TILE_SIZE * 0.25, dy + TILE_SIZE * 0.75, TILE_SIZE * 0.1, 0, Math.PI * 2);
                    ctx.arc(dx + TILE_SIZE * 0.75, dy + TILE_SIZE * 0.25, TILE_SIZE * 0.1, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
            else if (tileType === 'rock') {
                // Grass Base (Forest) or Floor Base (Dungeon)? 
                // Mostly forest for now.
                ctx.fillStyle = '#228b22';
                ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
                // Rock
                ctx.fillStyle = '#555';
                ctx.beginPath();
                ctx.arc(dx + TILE_SIZE / 2, dy + TILE_SIZE / 2, TILE_SIZE * 0.3, 0, Math.PI * 2);
                ctx.fill();
                // Highlight
                ctx.fillStyle = '#777';
                ctx.beginPath();
                ctx.arc(dx + TILE_SIZE * 0.4, dy + TILE_SIZE * 0.4, TILE_SIZE * 0.1, 0, Math.PI * 2);
                ctx.fill();
            }
            else if (tileType === 'lava') {
                ctx.fillStyle = '#cf1020';
                ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
                ctx.fillStyle = '#ff8c00';
                ctx.fillRect(dx + Math.random() * TILE_SIZE, dy + Math.random() * TILE_SIZE, TILE_SIZE * 0.2, TILE_SIZE * 0.2);
            }
            else {
                drawFallback(ctx, dx, dy, TILE_SIZE, tileType);
            }
        }

        if (!isVisible) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
        }

        if (ZOOM_LEVEL > 0.6) {
            ctx.strokeStyle = '#111';
            ctx.strokeRect(dx, dy, TILE_SIZE, TILE_SIZE);
        }
    });

    // Initial Draw
    // draw(); // This line is commented out as 'draw' is not defined in the original context.

    // Click Handler (Movement / Selection)
    // This block is placed here as per the user's instruction, but it contains references
    // to 'camOffsetX', 'camOffsetY', 'window.gameState', and a call to 'draw()'
    // which are not defined in the provided document.
    // The `})();` at the end also suggests it was part of an IIFE, which is not present.
    // To maintain syntactical correctness, the IIFE closing brace and the 'draw()' call are commented out.
    // The undefined variables 'camOffsetX' and 'camOffsetY' will cause runtime errors if not defined elsewhere.
    // 'window.gameState' is assumed to be globally available.
    // Click Handler (Movement / Selection)
    // Move this listener OUTSIDE of draw() or any recurring function if it isn't already.
    // Ensure we don't bind multiple times.
    if (!canvas.dataset.listenerAttached) {
        canvas.addEventListener('mousedown', (e) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // Recalculate TILE_SIZE as it might change with zoom
            const currentTileSize = Math.round(BASE_TILE_SIZE * ZOOM_LEVEL);

            // Convert to World Coords
            const tX = Math.floor((mouseX - camOffsetX) / currentTileSize);
            const tY = Math.floor((mouseY - camOffsetY) / currentTileSize);

            // Simple adjacent check for movement
            if (window.gameState && window.gameState.player) {
                const pX = window.gameState.player.xyz[0];
                const pY = window.gameState.player.xyz[1];

                const dx = tX - pX;
                const dy = tY - pY;

                console.log(`Click at ${tX},${tY} (Player: ${pX},${pY}) Delta: ${dx},${dy}`); // Debug

                if (Math.abs(dx) + Math.abs(dy) === 1) {
                    if (window.movePlayerCmd) {
                        window.movePlayerCmd({ dx, dy });
                    }
                }
            }
        });
        canvas.dataset.listenerAttached = "true";
    }

    // })(); // This closing IIFE brace is commented out as the original code is not an IIFE.
    // Draw Corpses
    if (data.corpses) {
        data.corpses.forEach(c => {
            const [cx, cy, cz] = c.xyz;
            if (cz !== playerPos[2]) return;

            // Visibility Check
            if (!map[`${cx},${cy},${cz}`]) return;

            const dx = Math.round(centerX + (cx - playerPos[0]) * TILE_SIZE - TILE_SIZE / 2);
            const dy = Math.round(centerY + (cy - playerPos[1]) * TILE_SIZE - TILE_SIZE / 2);

            let img = images['bones'];
            if (img) ctx.drawImage(img, dx, dy, TILE_SIZE, TILE_SIZE);
        });
    }

    // Draw Player
    const pImg = images['player'];
    const pSize = TILE_SIZE; // Use full tile size for player usually, or crop
    // Let's standardise sprite drawing centered
    const pX = centerX - TILE_SIZE / 2;
    const pY = centerY - TILE_SIZE / 2;

    if (pImg) ctx.drawImage(pImg, pX, pY, TILE_SIZE, TILE_SIZE);
    else { ctx.fillStyle = 'cyan'; ctx.fillRect(pX + TILE_SIZE / 4, pY + TILE_SIZE / 4, TILE_SIZE / 2, TILE_SIZE / 2); }

    // Draw Enemies
    if (data.world.enemies) {
        data.world.enemies.forEach(e => {
            const [ex, ey, ez] = e.xyz;
            if (ez !== playerPos[2]) return;

            // Visibility Check: Must be on a visible/revealed tile
            // The map only contains discovered tiles. If it's not in the map, it's in the void.
            if (!map[`${ex},${ey},${ez}`]) return;

            const dist = Math.abs(ex - playerPos[0]) + Math.abs(ey - playerPos[1]);
            if (dist > VIS_RADIUS) return;

            const drawX = Math.round(centerX + (ex - playerPos[0]) * TILE_SIZE - TILE_SIZE / 2);
            const drawY = Math.round(centerY + (ey - playerPos[1]) * TILE_SIZE - TILE_SIZE / 2);

            let eImg = images['skeleton'];
            if (e.name && e.name.toLowerCase().includes('bear')) {
                if (images['bear']) eImg = images['bear'];
            }
            else if (e.name && e.name.toLowerCase().includes('guardian')) {
                if (images['fire_guardian']) eImg = images['fire_guardian'];
            }
            else if (e.name && e.name.toLowerCase().includes('wolf')) {
                if (images['wolf']) eImg = images['wolf'];
            }

            if (eImg) ctx.drawImage(eImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            else { ctx.fillStyle = 'red'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }
        });
    }

    // Draw NPCs
    if (data.world.npcs) {
        data.world.npcs.forEach(n => {
            const [nx, ny, nz] = n.xyz;
            if (nz !== playerPos[2]) return;

            // Visibility Check
            if (!map[`${nx},${ny},${nz}`]) return;

            const dist = Math.abs(nx - playerPos[0]) + Math.abs(ny - playerPos[1]);
            while (dist > VIS_RADIUS) return; // Wait, this should be an if. Fixed below in replacement.
            if (dist > VIS_RADIUS) return;

            const drawX = Math.round(centerX + (nx - playerPos[0]) * TILE_SIZE - TILE_SIZE / 2);
            const drawY = Math.round(centerY + (ny - playerPos[1]) * TILE_SIZE - TILE_SIZE / 2);

            let nImg = null;
            if (n.asset && images[n.asset.replace('.png', '')]) nImg = images[n.asset.replace('.png', '')];
            if (!nImg) nImg = images['player'];

            // Sprites often have whitespace, so drawing full tile is fine
            if (nImg) {
                ctx.drawImage(nImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            } else {
                ctx.fillStyle = 'blue'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE);
            }

            if (ZOOM_LEVEL > 0.8) {
                ctx.fillStyle = 'white';
                ctx.font = `${Math.max(10, 12 * ZOOM_LEVEL)}px Arial`;
                ctx.textAlign = 'center';
                ctx.fillText(n.name, drawX + TILE_SIZE / 2, drawY - 5);
                ctx.textAlign = 'start';
            }
        });
    }
};

function drawFallback(ctx, x, y, size, type) {
    if (type.includes('floor')) ctx.fillStyle = '#444';
    else if (type.includes('wall')) ctx.fillStyle = '#888';
    else if (type === 'door') ctx.fillStyle = '#852';
    else if (type === 'grass') ctx.fillStyle = '#282';
    else if (type === 'water') ctx.fillStyle = '#22d';
    else if (type === 'rock') ctx.fillStyle = '#555';
    else if (type === 'tree') ctx.fillStyle = '#0f0';
    else ctx.fillStyle = '#a0a';
    ctx.fillRect(x, y, size, size);
}

console.log("GRAPHICS.JS: Advanced Chroma Ready v29");
