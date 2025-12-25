console.log("GRAPHICS.JS: Zoom Mode Loading...");

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
    'open_door': 'door.png'
};

// Preload
Object.keys(assets).forEach(key => {
    const img = new Image();
    img.src = `/static/img/${assets[key]}?v=` + Date.now();
    img.onload = () => { images[key] = img; };
    img.onerror = () => { images[key] = null; };
});

// --- Zoom Input ---
document.addEventListener('wheel', (e) => {
    if (e.ctrlKey) return; // Allow browser zoom if ctrl held? No, usually block it.

    e.preventDefault();
    if (e.deltaY < 0) ZOOM_LEVEL = Math.min(ZOOM_LEVEL + 0.1, 3.0);
    else ZOOM_LEVEL = Math.max(ZOOM_LEVEL - 0.1, 0.5);

    // Trigger redraw if we had a manual loop, but main loop handles it
}, { passive: false });


window.drawMap = function (data) {
    canvas = document.getElementById('map-canvas');
    if (!canvas) return;
    ctx = canvas.getContext('2d');

    // 1. Resize & Clear
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

    // 3. Draw Tiles
    ctx.imageSmoothingEnabled = false;

    Object.keys(map).forEach(key => {
        const [x, y, z] = key.split(',').map(Number);
        if (z !== playerPos[2]) return;

        const dx = Math.round(centerX + (x - playerPos[0]) * TILE_SIZE - TILE_SIZE / 2);
        const dy = Math.round(centerY + (y - playerPos[1]) * TILE_SIZE - TILE_SIZE / 2);

        // Cull Off-screen
        if (dx < -TILE_SIZE || dy < -TILE_SIZE || dx > canvas.width || dy > canvas.height) return;

        const tileType = map[key];
        const img = images[tileType];

        // --- FOG OF WAR LOGIC ---
        const dist = Math.abs(x - playerPos[0]) + Math.abs(y - playerPos[1]); // Manhattan
        const isVisible = dist <= VIS_RADIUS;

        // Draw Base Tile
        if (img) {
            ctx.drawImage(img, dx, dy, TILE_SIZE, TILE_SIZE);
        } else {
            drawFallback(ctx, dx, dy, TILE_SIZE, tileType);
        }

        // Overlay Fog Logic
        if (isVisible) {
            // Visible
        } else {
            // Memory (Visited but far): Darken it
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
        }

        // Grid
        if (ZOOM_LEVEL > 0.6) {
            ctx.strokeStyle = '#111';
            ctx.strokeRect(dx, dy, TILE_SIZE, TILE_SIZE);
        }
    });

    // 5. Draw Player (Always visible)
    const pImg = images['player'];
    const half = TILE_SIZE / 2;
    const qtr = TILE_SIZE / 4;

    if (pImg) ctx.drawImage(pImg, centerX - qtr, centerY - qtr, half, half);
    else { ctx.fillStyle = 'cyan'; ctx.fillRect(centerX - qtr, centerY - qtr, half, half); }

    // 6. Draw Entities (Enemies) - ONLY IF VISIBLE
    if (data.world.enemies) {
        data.world.enemies.forEach(e => {
            if (e.xyz[2] !== playerPos[2]) return;

            // --- FOG CHECK ---
            const dist = Math.abs(e.xyz[0] - playerPos[0]) + Math.abs(e.xyz[1] - playerPos[1]);
            if (dist > VIS_RADIUS) return; // Hide enemies in fog

            const ex = Math.round(centerX + (e.xyz[0] - playerPos[0]) * TILE_SIZE - TILE_SIZE / 2);
            const ey = Math.round(centerY + (e.xyz[1] - playerPos[1]) * TILE_SIZE - TILE_SIZE / 2);

            // Scaling logic for sprites (roughly 70% of tile)
            const sprSize = Math.round(TILE_SIZE * 0.7);
            const offset = (TILE_SIZE - sprSize) / 2;

            let eImg = images['skeleton'];
            if (eImg) ctx.drawImage(eImg, ex + offset, ey + offset, sprSize, sprSize);
            else { ctx.fillStyle = 'red'; ctx.fillRect(ex + offset, ey + offset, sprSize, sprSize); }
        });
    }

    // 7. Draw NPCs - ONLY IF VISIBLE
    if (data.world.npcs) {
        data.world.npcs.forEach(n => {
            if (n.xyz[2] !== playerPos[2]) return;

            const dist = Math.abs(n.xyz[0] - playerPos[0]) + Math.abs(n.xyz[1] - playerPos[1]);
            if (dist > VIS_RADIUS) return;

            const nx = Math.round(centerX + (n.xyz[0] - playerPos[0]) * TILE_SIZE - TILE_SIZE / 2);
            const ny = Math.round(centerY + (n.xyz[1] - playerPos[1]) * TILE_SIZE - TILE_SIZE / 2);

            let nImg = null;
            if (n.asset && images[n.asset.replace('.png', '')]) nImg = images[n.asset.replace('.png', '')];
            if (!nImg) nImg = images['player'];

            if (nImg) ctx.drawImage(nImg, nx, ny, TILE_SIZE, TILE_SIZE);
            else { ctx.fillStyle = 'blue'; ctx.fillRect(nx + (TILE_SIZE * 0.25), ny + (TILE_SIZE * 0.25), TILE_SIZE * 0.5, TILE_SIZE * 0.5); }

            // Name Tag
            if (ZOOM_LEVEL > 0.8) {
                ctx.fillStyle = 'white';
                ctx.font = `${Math.max(10, 12 * ZOOM_LEVEL)}px Arial`;
                ctx.fillText(n.name, nx, ny - 5);
            }
        });
    }
};

// Fallback Helper
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

console.log("GRAPHICS.JS: Zoom Ready v24");
