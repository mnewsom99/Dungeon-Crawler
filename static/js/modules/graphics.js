console.log("GRAPHICS.JS: Advanced Chroma Handler Loading...");

// State
let ZOOM_LEVEL = 1.0;
const BASE_TILE_SIZE = 64;
const VIS_RADIUS = 7;
let canvas, ctx;

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
    'warrior2': 'warrior2.png'
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
        const isMagenta = (r > 240 && g < 20 && b > 240);

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
    const map = data.world.map;

    ctx.imageSmoothingEnabled = false;

    // Draw Map
    Object.keys(map).forEach(key => {
        const [x, y, z] = key.split(',').map(Number);
        if (z !== playerPos[2]) return;

        const dx = Math.round(centerX + (x - playerPos[0]) * TILE_SIZE - TILE_SIZE / 2);
        const dy = Math.round(centerY + (y - playerPos[1]) * TILE_SIZE - TILE_SIZE / 2);

        if (dx < -TILE_SIZE || dy < -TILE_SIZE || dx > canvas.width || dy > canvas.height) return;

        const tileType = map[key];
        const img = images[tileType];

        // Fog
        const dist = Math.abs(x - playerPos[0]) + Math.abs(y - playerPos[1]);
        const isVisible = dist <= VIS_RADIUS;

        if (img) {
            ctx.drawImage(img, dx, dy, TILE_SIZE, TILE_SIZE);
        } else {
            drawFallback(ctx, dx, dy, TILE_SIZE, tileType);
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
            if (nImg) ctx.drawImage(nImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            else { ctx.fillStyle = 'blue'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }

            if (ZOOM_LEVEL > 0.8) {
                ctx.fillStyle = 'white';
                ctx.font = `${Math.max(10, 12 * ZOOM_LEVEL)}px Arial`;
                ctx.textAlign = 'center';
                ctx.fillText(n.name, drawX + TILE_SIZE / 2, drawY - 5);
                ctx.textAlign = 'start';
            }
        });
    }

    // Draw Secrets / World Objects (Chests)
    if (data.world.secrets) {
        data.world.secrets.forEach(s => {
            if (!s.xyz) return; // Some secrets might be tile-based logic only?
            const [sx, sy, sz] = s.xyz;
            if (sz !== playerPos[2]) return;

            if (!map[`${sx},${sy},${sz}`]) return;

            const drawX = Math.round(centerX + (sx - playerPos[0]) * TILE_SIZE - TILE_SIZE / 2);
            const drawY = Math.round(centerY + (sy - playerPos[1]) * TILE_SIZE - TILE_SIZE / 2);

            let sImg = null;
            if (s.obj_type === 'chest') sImg = images['chest'];

            if (sImg) {
                ctx.drawImage(sImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
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
