
// Map & Rendering Logic

// Image Assets
const floorImg = new Image(); floorImg.src = 'static/img/grey_black_floor_tile.png';
const wallImg = new Image(); wallImg.src = 'static/img/wall_grey.png';
const doorImg = new Image(); doorImg.src = 'static/img/door.png';
const playerImg = new Image(); playerImg.src = 'static/img/player.png';
const skeletonImg = new Image(); skeletonImg.src = 'static/img/skeleton.png';

// Town Assets
const grassImg = new Image(); grassImg.src = 'static/img/grass.png?v=4';
const floorWoodImg = new Image(); floorWoodImg.src = 'static/img/floor_wood.png';
const waterImg = new Image(); waterImg.src = 'static/img/water.png';
const treeImg = new Image(); treeImg.src = 'static/img/tree.png';
const wallHouseImg = new Image(); wallHouseImg.src = 'static/img/wall_house.png';
const anvilImg = new Image(); anvilImg.src = 'static/img/anvil.png';
const shelfImg = new Image(); shelfImg.src = 'static/img/shelf.png';
const barrelImg = new Image(); barrelImg.src = 'static/img/barrel.png';
const crateImg = new Image(); crateImg.src = 'static/img/crate.png';
const lampImg = new Image(); lampImg.src = 'static/img/street_lamp.png';
const fountainImg = new Image(); fountainImg.src = 'static/img/fountain.png';
const flowerImg = new Image(); flowerImg.src = 'static/img/flower_pot.png';
const signImg = new Image(); signImg.src = 'static/img/signpost.png';

// Dungeon Assets
const rockImg = new Image(); rockImg.src = 'static/img/rock.png';
const bridgeImg = new Image(); bridgeImg.src = 'static/img/bridge.png';
const chestImg = new Image(); chestImg.src = 'static/img/chest.png';
const wardenImg = new Image(); wardenImg.src = 'static/img/warden.png';

function drawMap(data) {
    const canvas = document.getElementById('map-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const TILE_SIZE = window.TILE_SIZE;



    // Auto-Resize Canvas to Full Window
    if (canvas.width !== window.innerWidth || canvas.height !== window.innerHeight) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#111'; // Dark background for empty space
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!data || !data.world || !data.world.map) return;

    // Update Globals from State
    playerPos = data.player.xyz;
    if (!cameraPos) cameraPos = [...playerPos];
    else {
        // Simple Lock
        cameraPos[0] = playerPos[0];
        cameraPos[1] = playerPos[1];
    }

    // Calculate Viewport
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    const visibleMap = data.world.map;

    Object.keys(visibleMap).forEach(key => {
        const [x, y, z] = key.split(',').map(Number);
        const tileType = visibleMap[key];

        // Z-Level Check
        if (z !== playerPos[2]) return;

        const drawX = centerX + (x - cameraPos[0]) * window.TILE_SIZE - (window.TILE_SIZE / 2);
        const drawY = centerY + (y - cameraPos[1]) * window.TILE_SIZE - (window.TILE_SIZE / 2);

        // Z-Level 1 (Town): Draw base grass layer for transparant props
        if (z === 1 && tileType !== 'water' && tileType !== 'grass' && tileType !== 'wall_house') {
            ctx.drawImage(grassImg, drawX, drawY, window.TILE_SIZE, window.TILE_SIZE);
        }



        // Render Tile
        if (tileType === 'floor') {
            if (floorImg.complete) ctx.drawImage(floorImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            else { ctx.fillStyle = '#333'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }
        }
        else if (tileType === 'wall') {
            if (wallImg.complete) ctx.drawImage(wallImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            else { ctx.fillStyle = '#888'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }
        }
        else if (tileType === 'door' || tileType === 'open_door') {
            if (doorImg.complete) ctx.drawImage(doorImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
            else { ctx.fillStyle = 'brown'; ctx.fillRect(drawX, drawY, TILE_SIZE, TILE_SIZE); }
        }
        // Special Tiles
        else if (tileType === 'rock') ctx.drawImage(rockImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'bridge') ctx.drawImage(bridgeImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'grass') ctx.drawImage(grassImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'floor_wood') ctx.drawImage(floorWoodImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'water') ctx.drawImage(waterImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'tree') ctx.drawImage(treeImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'wall_house') ctx.drawImage(wallHouseImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'anvil') ctx.drawImage(anvilImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'shelf') ctx.drawImage(shelfImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'barrel') ctx.drawImage(barrelImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'crate') ctx.drawImage(crateImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'street_lamp') ctx.drawImage(lampImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'fountain') ctx.drawImage(fountainImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'flower_pot') ctx.drawImage(flowerImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'signpost') ctx.drawImage(signImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
    });

    // Draw Enemies (Only if within vision radius)
    if (data.world.enemies) {
        data.world.enemies.forEach(m => {
            const [mx, my, mz] = m.xyz;
            if (mz !== playerPos[2]) return;

            // Fog of War Check: Hide if too far
            const dist = Math.sqrt(Math.pow(mx - playerPos[0], 2) + Math.pow(my - playerPos[1], 2));
            if (dist > 4.0) return;

            const mDrawX = centerX + (mx - cameraPos[0]) * window.TILE_SIZE - (window.TILE_SIZE / 2);
            const mDrawY = centerY + (my - cameraPos[1]) * window.TILE_SIZE - (window.TILE_SIZE / 2);

            // Draw Monster
            if (m.name.includes("Warden") && wardenImg.complete) {
                ctx.drawImage(wardenImg, mDrawX, mDrawY, window.TILE_SIZE, window.TILE_SIZE);
            } else if (m.name.includes("Skeleton") && skeletonImg.complete) {
                ctx.drawImage(skeletonImg, mDrawX, mDrawY, window.TILE_SIZE, window.TILE_SIZE);
            } else {
                ctx.fillStyle = 'red';
                ctx.fillRect(mDrawX, mDrawY, window.TILE_SIZE, window.TILE_SIZE);
            }

            // HP Bar
            ctx.fillStyle = 'red';
            ctx.fillRect(mDrawX, mDrawY - 5, window.TILE_SIZE, 3);
            ctx.fillStyle = 'green';
            const hpPct = m.hp / m.max_hp;
            ctx.fillRect(mDrawX, mDrawY - 5, window.TILE_SIZE * hpPct, 3);
        });
    }

    // Draw NPCs (Only if within vision radius)
    if (data.world.npcs) {
        if (!window.npcImages) window.npcImages = {}; // Simple Cache

        data.world.npcs.forEach(n => {
            const [nx, ny, nz] = n.xyz;
            if (nz !== playerPos[2]) return;

            // Fog of War Check
            const dist = Math.sqrt(Math.pow(nx - playerPos[0], 2) + Math.pow(ny - playerPos[1], 2));
            if (dist > 4.0) return;

            const nDrawX = centerX + (nx - cameraPos[0]) * window.TILE_SIZE - (window.TILE_SIZE / 2);
            const nDrawY = centerY + (ny - cameraPos[1]) * window.TILE_SIZE - (window.TILE_SIZE / 2);

            // Asset Loading
            const assetName = n.asset || "player.png";
            if (!window.npcImages[assetName]) {
                const img = new Image();
                img.src = 'static/img/' + assetName;
                window.npcImages[assetName] = img;
            }

            const img = window.npcImages[assetName];
            if (img.complete) {
                ctx.drawImage(img, nDrawX, nDrawY, window.TILE_SIZE, window.TILE_SIZE);
            } else {
                // Placeholder
                ctx.fillStyle = 'gold';
                ctx.fillRect(nDrawX, nDrawY, window.TILE_SIZE, window.TILE_SIZE);
                ctx.fillStyle = '#000';
                ctx.font = '10px Arial';
                ctx.fillText("NPC", nDrawX, nDrawY + 10);
            }
        });
    }




    // Draw Corpses
    if (data.corpses) {
        if (!window.corpseImg) {
            window.corpseImg = new Image();
            window.corpseImg.src = 'static/img/bones.png';
        }
        data.corpses.forEach(c => {
            const [cx, cy, cz] = c.xyz;
            if (cz !== playerPos[2]) return;

            // Fog check
            const dist = Math.sqrt(Math.pow(cx - playerPos[0], 2) + Math.pow(cy - playerPos[1], 2));
            if (dist > 4.0) return;

            const cDrawX = centerX + (cx - cameraPos[0]) * window.TILE_SIZE - (window.TILE_SIZE / 2);
            const cDrawY = centerY + (cy - cameraPos[1]) * window.TILE_SIZE - (window.TILE_SIZE / 2);

            if (window.corpseImg.complete) {
                ctx.drawImage(window.corpseImg, cDrawX, cDrawY, window.TILE_SIZE, window.TILE_SIZE);
            } else {
                ctx.fillStyle = '#444';
                ctx.fillRect(cDrawX + 10, cDrawY + 10, 10, 10);
            }
        });
    }

    // Draw Secrets / World Objects
    if (data.world.secrets) {
        data.world.secrets.forEach(s => {
            // Only draw if it has coordinates (physically present objects)
            if (!s.xyz) return;
            const [sx, sy, sz] = s.xyz;
            if (sz !== playerPos[2]) return;

            const dist = Math.sqrt(Math.pow(sx - playerPos[0], 2) + Math.pow(sy - playerPos[1], 2));
            if (dist > 4.0) return;

            const sDrawX = centerX + (sx - cameraPos[0]) * window.TILE_SIZE - (window.TILE_SIZE / 2);
            const sDrawY = centerY + (sy - cameraPos[1]) * window.TILE_SIZE - (window.TILE_SIZE / 2);

            // Select Image
            let imgToDraw = crateImg;
            if (s.obj_type === 'chest') imgToDraw = chestImg;
            else if (s.obj_type === 'crate') imgToDraw = crateImg;

            if (imgToDraw.complete) {
                ctx.drawImage(imgToDraw, sDrawX, sDrawY, window.TILE_SIZE, window.TILE_SIZE);
            } else {
                ctx.fillStyle = 'gold';
                ctx.fillRect(sDrawX + 5, sDrawY + 5, window.TILE_SIZE - 10, window.TILE_SIZE - 10);
            }
        });
    }


    // Draw Fog / Vision Radius (15ft ~= 3-4 tiles radius)
    // We mask the visible area
    ctx.save();
    // We want to darken everything EXCEPT the circle around the player.
    // We achieve this by drawing a rectangle covering the screen, with a circular HOLE cut out.
    // The 'hole' is achieved by drawing the circle counter-clockwise in the same path.

    const pFogX = centerX + (playerPos[0] - cameraPos[0]) * TILE_SIZE;
    const pFogY = centerY + (playerPos[1] - cameraPos[1]) * TILE_SIZE;
    const fogRadius = TILE_SIZE * 3.5;

    ctx.fillStyle = "rgba(0, 0, 0, 0.65)"; // The darkness level of visited-but-not-active areas
    ctx.shadowColor = "rgba(0, 0, 0, 1)"; // Shadow to soften the edge
    ctx.shadowBlur = 30;                 // Softness radius

    ctx.beginPath();
    // 1. Outer Box (Clockwise)
    ctx.rect(0, 0, canvas.width, canvas.height);

    // 2. Inner Circle (Counter-Clockwise = Hole)
    ctx.arc(pFogX, pFogY, fogRadius, 0, Math.PI * 2, true);

    ctx.closePath();
    ctx.fill();

    ctx.restore();

    // Draw Player (on top of fog? No, affected by fog slightly? Actually player should be fully bright)
    // Re-calculate pDraw positions for sprite drawing which is top-left based
    const pSpriteX = centerX + (playerPos[0] - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
    const pSpriteY = centerY + (playerPos[1] - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);

    if (playerImg.complete) ctx.drawImage(playerImg, pSpriteX, pSpriteY, TILE_SIZE, TILE_SIZE);
    else { ctx.fillStyle = 'green'; ctx.fillRect(pSpriteX, pSpriteY, TILE_SIZE, TILE_SIZE); }
}

function toggleMap() {
    const modal = document.getElementById('map-modal');
    if (modal.style.display === 'none') {
        modal.style.display = 'flex';
        // Need to refetch full map data if implemented
        // For now, just show what we have
    } else {
        modal.style.display = 'none';
    }
}

// Click to Move Logic
const mapCanvas = document.getElementById('map-canvas');
if (mapCanvas) {
    mapCanvas.addEventListener('mousedown', (e) => {
        // Only left click
        if (e.button !== 0) return;

        // Calculate clicked tile coordinates
        const rect = mapCanvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;
        const centerX = mapCanvas.width / 2;
        const centerY = mapCanvas.height / 2;

        if (!cameraPos) return;

        const rawX = (clickX - centerX + (window.TILE_SIZE / 2)) / window.TILE_SIZE;
        const rawY = (clickY - centerY + (window.TILE_SIZE / 2)) / window.TILE_SIZE;

        const tileX = Math.floor(rawX + cameraPos[0]);
        const tileY = Math.floor(rawY + cameraPos[1]);

        // Simple Adjacent Movement
        const dx = tileX - playerPos[0];
        const dy = tileY - playerPos[1];

        if (Math.abs(dx) + Math.abs(dy) === 1) {
            // Adjacent
            if (dy === -1) move('north');
            if (dy === 1) move('south');
            if (dx === -1) move('west');
            if (dx === 1) move('east');
        } else {
            if (dx === 0 && dy === 0) logMessage("You represent your current position.");
        }
    });
}
