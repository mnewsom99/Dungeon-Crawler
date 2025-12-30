
// Asset Manager (assets.js)
// Handles image loading, transparency processing, and caching.

(function () {
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
        'fire_guardian': 'fire_guardian.png',

        // Dungeon Entrance Tiles
        'door_stone': 'door_stone.png',
        'mtn_tl': 'mtn_tl.png',
        'mtn_tm': 'mtn_tm.png',
        'mtn_tr': 'mtn_tr.png',
        'mtn_ml': 'mtn_ml.png',
        'mtn_mm': 'mtn_mm.png',
        'mtn_mr': 'mtn_mr.png',

        // Goblin
        'knife_goblin': 'knife_goblin.png',
        'goblin_scout': 'goblin_scout.png',

        // Fire Dungeon
        'floor_volcanic': 'floor_volcanic.png',
        'wall_volcanic': 'wall_volcanic.png',
        'steam_vent': 'steam_vent.png',
        'cinder_hound': 'cinder_hound.png',
        'obsidian_sentinel': 'obsidian_sentinel.png',
        'sulfur_bat': 'sulfur_bat.png',
        'magma_weaver': 'magma_weaver.png',
        'mtn_bl': 'mtn_bl.png',
        'mtn_br': 'mtn_br.png'
    };

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
            const isGrey = (r > 150 && r < 240) &&
                (Math.abs(r - g) < 3) &&
                (Math.abs(g - b) < 3) &&
                (Math.abs(r - b) < 3);

            // 3. Magic Pink (Magenta) - Legacy support
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

    function loadAssets(onLoadCallback) {
        Object.keys(assets).forEach(key => {
            const rawImg = new Image();
            rawImg.crossOrigin = "Anonymous";
            rawImg.src = `/static/img/${assets[key]}?v=` + Date.now();

            rawImg.onload = () => {
                if (key === 'floor' || key.includes('wall') || key.includes('grass')) {
                    images[key] = rawImg;
                } else {
                    images[key] = processTransparency(rawImg);
                }
            };
            rawImg.onerror = () => { images[key] = null; };
        });
    }

    // Initialize Global Namespace
    window.GraphicsAssets = {
        images: images,
        load: loadAssets
    };

    // Auto-load on script execution
    loadAssets();

})();
