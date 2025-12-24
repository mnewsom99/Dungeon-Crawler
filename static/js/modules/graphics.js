
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
        else if (tileType === 'grass') ctx.drawImage(grassImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'floor_wood') ctx.drawImage(floorWoodImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'water') ctx.drawImage(waterImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'tree') ctx.drawImage(treeImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'wall_house') ctx.drawImage(wallHouseImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'anvil') ctx.drawImage(anvilImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
        else if (tileType === 'shelf') ctx.drawImage(shelfImg, drawX, drawY, TILE_SIZE, TILE_SIZE);
    });

    // Draw Enemies
    if (data.world.enemies) {
        data.world.enemies.forEach(m => {
            const [mx, my, mz] = m.xyz;
            if (mz !== playerPos[2]) return;
            const mDrawX = centerX + (mx - cameraPos[0]) * window.TILE_SIZE - (window.TILE_SIZE / 2);
            const mDrawY = centerY + (my - cameraPos[1]) * window.TILE_SIZE - (window.TILE_SIZE / 2);

            // Draw Monster
            if (m.name.includes("Skeleton") && skeletonImg.complete) {
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

    // Draw NPCs
    if (data.world.npcs) {
        if (!window.npcImages) window.npcImages = {}; // Simple Cache

        data.world.npcs.forEach(n => {
            const [nx, ny, nz] = n.xyz;
            if (nz !== playerPos[2]) return;

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

    // Draw Player
    const pDrawX = centerX + (playerPos[0] - cameraPos[0]) * TILE_SIZE - (TILE_SIZE / 2);
    const pDrawY = centerY + (playerPos[1] - cameraPos[1]) * TILE_SIZE - (TILE_SIZE / 2);
    if (playerImg.complete) ctx.drawImage(playerImg, pDrawX, pDrawY, TILE_SIZE, TILE_SIZE);
    else { ctx.fillStyle = 'green'; ctx.fillRect(pDrawX, pDrawY, TILE_SIZE, TILE_SIZE); }
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
