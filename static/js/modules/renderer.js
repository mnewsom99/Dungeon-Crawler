
// Main Renderer (renderer.js)
// Orchestrates drawing the map, entities, and lighting.

(function () {
    const BASE_TILE_SIZE = 64;
    const VIS_RADIUS = 7;

    let canvas = null;
    let ctx = null;
    let camOffsetX = 0;
    let camOffsetY = 0;

    function initCanvas() {
        canvas = document.getElementById('map-canvas');
        if (!canvas) return false;
        ctx = canvas.getContext('2d');

        // Attach Input Listeners once
        if (!canvas.dataset.inputAttached) {
            if (window.GraphicsInput) window.GraphicsInput.setup(canvas);
            canvas.dataset.inputAttached = "true";
        }
        return true;
    }

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

    function drawMap(data) {
        if (!canvas && !initCanvas()) return;

        // Resize
        if (canvas.width !== window.innerWidth) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }

        // Clear
        ctx.fillStyle = '#050505';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        if (!data || !data.world || !data.world.map) return;

        // Get State
        const ZOOM_LEVEL = window.GraphicsInput ? window.GraphicsInput.getZoom() : 1.0;
        const images = window.GraphicsAssets ? window.GraphicsAssets.images : {};

        const TILE_SIZE = Math.round(BASE_TILE_SIZE * ZOOM_LEVEL);
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const playerPos = data.player.xyz;

        // Camera Math
        camOffsetX = centerX - playerPos[0] * TILE_SIZE - TILE_SIZE / 2;
        camOffsetY = centerY - playerPos[1] * TILE_SIZE - TILE_SIZE / 2;

        const map = data.world.map;
        ctx.imageSmoothingEnabled = false;

        // 1. Draw Map Tiles
        Object.keys(map).forEach(key => {
            const [x, y, z] = key.split(',').map(Number);
            if (z !== playerPos[2]) return;

            const dx = Math.round(camOffsetX + x * TILE_SIZE);
            const dy = Math.round(camOffsetY + y * TILE_SIZE);

            if (dx < -TILE_SIZE || dy < -TILE_SIZE || dx > canvas.width || dy > canvas.height) return;

            const tileType = map[key];
            const img = images[tileType];

            // Fog Calculation
            const dist = Math.abs(x - playerPos[0]) + Math.abs(y - playerPos[1]);
            const isVisible = dist <= VIS_RADIUS;

            // Render Tile Logic
            if (tileType.startsWith('mtn_') || tileType === 'door_stone') {
                // Grass Underlay
                ctx.fillStyle = '#228b22';
                ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
                if (img) ctx.drawImage(img, dx, dy, TILE_SIZE, TILE_SIZE);
            }
            else if (img) {
                ctx.drawImage(img, dx, dy, TILE_SIZE, TILE_SIZE);
            }
            else {
                // Procedural Rendering
                if (tileType === 'void') {
                    ctx.fillStyle = '#110022';
                    ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
                    if (Math.random() > 0.9) {
                        ctx.fillStyle = '#fff';
                        ctx.fillRect(dx + Math.random() * TILE_SIZE, dy + Math.random() * TILE_SIZE, 1, 1);
                    }
                }
                else if (tileType === 'herb') {
                    ctx.fillStyle = '#228b22';
                    ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
                    ctx.fillStyle = '#FF69B4'; // HotPink
                    ctx.beginPath();
                    ctx.arc(dx + TILE_SIZE * 0.5, dy + TILE_SIZE * 0.5, TILE_SIZE * 0.2, 0, Math.PI * 2);
                    ctx.fill();
                }
                else if (tileType === 'lava') {
                    ctx.fillStyle = '#cf1020';
                    ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
                }
                else {
                    drawFallback(ctx, dx, dy, TILE_SIZE, tileType);
                }
            }

            // Darkness Overlay
            if (!isVisible) {
                ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
                ctx.fillRect(dx, dy, TILE_SIZE, TILE_SIZE);
            }

            // Grid Lines (Low Zoom)
            if (ZOOM_LEVEL > 0.6) {
                ctx.strokeStyle = '#111';
                ctx.strokeRect(dx, dy, TILE_SIZE, TILE_SIZE);
            }
        });

        // 2. Draw Corpses
        if (data.corpses) {
            data.corpses.forEach(c => {
                const [cx, cy, cz] = c.xyz;
                if (cz !== playerPos[2] || !map[`${cx},${cy},${cz}`]) return;

                const dx = Math.round(camOffsetX + cx * TILE_SIZE);
                const dy = Math.round(camOffsetY + cy * TILE_SIZE);

                if (images['bones']) ctx.drawImage(images['bones'], dx, dy, TILE_SIZE, TILE_SIZE);
            });
        }

        // 3. Draw Player
        const pX = centerX - TILE_SIZE / 2;
        const pY = centerY - TILE_SIZE / 2;
        if (images['player']) ctx.drawImage(images['player'], pX, pY, TILE_SIZE, TILE_SIZE);
        else {
            ctx.fillStyle = 'cyan';
            ctx.fillRect(pX + TILE_SIZE / 4, pY + TILE_SIZE / 4, TILE_SIZE / 2, TILE_SIZE / 2);
        }

        // 4. Draw Enemies
        if (data.world.enemies) {
            data.world.enemies.forEach(e => {
                const [ex, ey, ez] = e.xyz;
                if (ez !== playerPos[2] || !map[`${ex},${ey},${ez}`]) return;

                const dist = Math.abs(ex - playerPos[0]) + Math.abs(ey - playerPos[1]);
                if (dist > VIS_RADIUS) return;

                const drawX = Math.round(camOffsetX + ex * TILE_SIZE);
                const drawY = Math.round(camOffsetY + ey * TILE_SIZE);

                // Sprite Selection Logic
                let eImg = images['skeleton']; // Default
                const name = (e.name || "").toLowerCase();

                if (name.includes('bear')) eImg = images['bear'] || eImg;
                else if (name.includes('guardian')) eImg = images['fire_guardian'] || eImg;
                else if (name.includes('wolf')) eImg = images['wolf'] || eImg;
                else if (name.includes('cinder')) eImg = images['cinder_hound'] || eImg;
                else if (name.includes('sentinel')) eImg = images['obsidian_sentinel'] || eImg;
                else if (name.includes('bat')) eImg = images['sulfur_bat'] || eImg;
                else if (name.includes('weaver')) eImg = images['magma_weaver'] || eImg;
                else if (name.includes('knife')) eImg = images['knife_goblin'] || eImg;
                else if (name.includes('goblin')) eImg = images['goblin_scout'] || eImg;

                if (eImg) ctx.drawImage(eImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
                else { ctx.fillStyle = 'red'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }

                // HP Bar (Only if injured)
                if (e.hp < e.max_hp) {
                    const hpPct = e.hp / e.max_hp;
                    ctx.fillStyle = '#500'; ctx.fillRect(drawX, drawY - 6, TILE_SIZE, 4);
                    ctx.fillStyle = '#f00'; ctx.fillRect(drawX, drawY - 6, TILE_SIZE * hpPct, 4);
                }
            });
        }

        // 5. Draw NPCs
        if (data.world.npcs) {
            data.world.npcs.forEach(n => {
                const [nx, ny, nz] = n.xyz;
                if (nz !== playerPos[2] || !map[`${nx},${ny},${nz}`]) return;

                const dist = Math.abs(nx - playerPos[0]) + Math.abs(ny - playerPos[1]);
                if (dist > VIS_RADIUS) return;

                const drawX = Math.round(camOffsetX + nx * TILE_SIZE);
                const drawY = Math.round(camOffsetY + ny * TILE_SIZE);

                let nImg = null;
                if (n.asset && images[n.asset.replace('.png', '')]) nImg = images[n.asset.replace('.png', '')];
                if (!nImg) nImg = images['player']; // Fallback

                if (nImg) ctx.drawImage(nImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
                else { ctx.fillStyle = 'blue'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }

                // Name Tag
                if (ZOOM_LEVEL > 0.8) {
                    ctx.fillStyle = 'white';
                    ctx.font = `${Math.max(10, 12 * ZOOM_LEVEL)}px Arial`;
                    ctx.textAlign = 'center';
                    ctx.fillText(n.name, drawX + TILE_SIZE / 2, drawY - 5);
                    ctx.textAlign = 'start';
                }
            });
        }
    }

    // Export
    window.GraphicsRenderer = {
        drawMap: drawMap,
        getCameraState: () => ({ offsetX: camOffsetX, offsetY: camOffsetY })
    };

    // Global Alias for Game Loop
    window.drawMap = drawMap;

})();
