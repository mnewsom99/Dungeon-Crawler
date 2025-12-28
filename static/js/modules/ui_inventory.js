// --- INVENTORY MODULE ---
// Extracted from ui.js

// --- Inventory System (Grid & Paperdoll) ---
window.updateInventoryUI = function (player) {
    if (!player || !player.inventory) return;

    const equippedDiv = document.getElementById('equipped-slots');
    const backpackUl = document.getElementById('inventory-list'); // Repurpose this container as grid

    // --- DRAG DATA HELPER ---
    // We attach this to draggable items
    const setDrag = (e, item, source) => {
        e.dataTransfer.setData("text/plain", JSON.stringify({
            id: item.id,
            slot: item.slot, // Target slot needed
            type: source // 'bag' or 'doll'
        }));
        // Visual feedback
        e.target.style.opacity = '0.5';
    };

    // --- 1. Paperdoll Layout ---
    const dollSlots = [
        { key: 'head', icon: 'helm', x: 1, y: 0, label: "Head" },
        { key: 'neck', icon: 'ring', x: 2, y: 0, label: "Neck" },
        { key: 'chest', icon: 'chest', x: 1, y: 1, label: "Chest" },
        { key: 'hands', icon: 'glove', x: 0, y: 1, label: "Hands" },
        { key: 'main_hand', icon: 'sword', x: 0, y: 2, label: "Main Hand" },
        { key: 'off_hand', icon: 'shield', x: 2, y: 2, label: "Off Hand" },
        { key: 'legs', icon: 'legs', x: 1, y: 2, label: "Legs" },
        { key: 'feet', icon: 'boots', x: 1, y: 3, label: "Feet" }
    ];

    const iconMap = {
        'Training Sword': "⚔️", 'Iron Sword': "⚔️",
        'Cloth Tunic': "👕", 'Leather Armor': "👕",
        'Leather Helmet': "🧢", 'Iron Helmet': "🪖",
        'Leather Boots': "👢", 'Healing Potion': "🧪",
        'Iron Ore': "🪨", 'Mystic Herb': "🌿", 'Gold': "💰",
        'Wooden Shield': "🛡️", 'Iron Key': "🔑", 'Ring': "💍", 'Leather Gloves': "🧤"
    };

    equippedDiv.innerHTML = '';

    // Container
    const dollContainer = document.createElement('div');
    dollContainer.style.position = 'relative';
    dollContainer.style.width = '120px';
    dollContainer.style.height = '160px';
    dollContainer.style.margin = '0 auto';
    dollContainer.style.background = '#111';
    dollContainer.style.border = '1px solid #444';

    // Allow dropping ONTO the doll generic area (or slots)
    // Actually better to handle per-slot Drop for validation, 
    // BUT dropping anywhere on doll to 'auto-equip' is nice too.
    // Let's stick to strict Slot Dropping for precision first.

    dollSlots.forEach(slot => {
        const item = player.inventory.find(i => i.is_equipped && i.slot === slot.key);
        const top = slot.y * 36 + 10;
        const left = slot.x * 36 + 6;

        const slotDiv = document.createElement('div');
        slotDiv.className = 'paper-doll-slot';
        slotDiv.style.position = 'absolute';
        slotDiv.style.top = `${top}px`;
        slotDiv.style.left = `${left}px`;
        slotDiv.style.width = '34px';
        slotDiv.style.height = '34px';
        slotDiv.style.border = '1px solid #666';
        slotDiv.style.background = '#222';
        slotDiv.style.cursor = 'default';
        slotDiv.style.display = 'flex';
        slotDiv.style.alignItems = 'center';
        slotDiv.style.justifyContent = 'center';

        // Drag Over (Allow Drop)
        slotDiv.ondragover = (e) => {
            e.preventDefault(); // Necessary to allow drop
            slotDiv.style.borderColor = '#fff';
        };
        slotDiv.ondragleave = () => slotDiv.style.borderColor = '#666';

        slotDiv.ondrop = (e) => {
            e.preventDefault();
            slotDiv.style.borderColor = '#666';
            try {
                const data = JSON.parse(e.dataTransfer.getData("text/plain"));
                if (data.type === 'bag' && data.slot === slot.key) {
                    equipItem(data.id);
                }
            } catch (err) { console.error(err); }
        };

        if (item) {
            slotDiv.draggable = true;
            slotDiv.style.cursor = 'grab';
            slotDiv.title = `${item.name}\n${item.item_type}`;

            let iconStr = item.properties?.icon || iconMap[item.name] || "📦";
            slotDiv.innerHTML = `<div style="font-size:24px;">${iconStr}</div>`;

            // Drag Start (Unequip via Drag)
            slotDiv.ondragstart = (e) => setDrag(e, item, 'doll');
            slotDiv.ondragend = (e) => e.target.style.opacity = '1';

            // Click to Unequip (Legacy/Mobile support)
            slotDiv.onclick = (e) => {
                if (e.ctrlKey || confirm(`Unequip ${item.name}?`)) unequipItem(item.id);
            }
        } else {
            slotDiv.innerHTML = `<div style="opacity:0.2; font-size:10px; pointer-events:none;">${slot.label}</div>`;
        }

        dollContainer.appendChild(slotDiv);
    });
    equippedDiv.appendChild(dollContainer);


    // --- 2. Grid Backpack ---
    const MAX_SLOTS = 20;
    const bagItems = player.inventory.filter(i => !i.is_equipped);

    // Reuse inventory-list but style it as grid
    backpackUl.style.display = 'grid';
    backpackUl.style.gridTemplateColumns = 'repeat(5, 1fr)';
    backpackUl.style.gap = '4px';
    backpackUl.style.listStyle = 'none';
    backpackUl.style.padding = '0';

    // Allow dropping ONTO the backpack (Unequip)
    backpackUl.ondragover = (e) => { e.preventDefault(); backpackUl.style.borderColor = '#fff'; };
    backpackUl.ondragleave = () => backpackUl.style.borderColor = 'transparent'; // Assuming no border usually
    backpackUl.ondrop = (e) => {
        e.preventDefault();
        try {
            const data = JSON.parse(e.dataTransfer.getData("text/plain"));
            if (data.type === 'doll') {
                unequipItem(data.id);
            }
        } catch (err) { console.error(err); }
    };

    backpackUl.innerHTML = '';

    for (let i = 0; i < MAX_SLOTS; i++) {
        const item = bagItems[i];
        const li = document.createElement('li');
        li.style.width = '36px';
        li.style.height = '36px';
        li.style.background = '#1a1a1a';
        li.style.border = '1px solid #333';
        li.style.position = 'relative';
        li.style.display = 'flex';
        li.style.alignItems = 'center';
        li.style.justifyContent = 'center';

        if (item) {
            li.style.cursor = 'grab';
            li.draggable = true;
            li.title = item.name;

            let iconStr = item.properties?.icon || iconMap[item.name] || "📦";

            li.innerHTML = `
                <div style="font-size:24px;">${iconStr}</div>
                ${item.quantity > 1 ? `<span style="position:absolute; bottom:0; right:1px; color:#fff; font-size:10px; text-shadow:1px 1px 0 #000;">${item.quantity || 1}</span>` : ''}
            `;

            // Drag Start
            li.ondragstart = (e) => setDrag(e, item, 'bag');
            li.ondragend = (e) => e.target.style.opacity = '1';

            // Interaction: Equip or Use (Click)
            li.onclick = () => {
                if (item.slot) equipItem(item.id);
                else if (item.item_type === 'consumable') useItem(item.id);
            };
        }

        backpackUl.appendChild(li);
    }

    // Update Gold
    if (document.getElementById('stat-gold')) {
        document.getElementById('stat-gold').innerText = player.gold || 0;
    }
};

window.updateSkillsUI = function (player) {
    const list = document.getElementById('skills-list');
    if (!list) return;

    list.innerHTML = '';
    const skills = player.skills || {};

    if (Object.keys(skills).length === 0) {
        list.innerHTML = '<span style="color:#666; font-style:italic;">No skills learnt.</span>';
        return;
    }

    for (const [key, val] of Object.entries(skills)) {
        let level = 0;
        let xp = 0;

        if (typeof val === 'object') {
            level = val.level;
            xp = val.xp;
        } else {
            level = val;
        }

        const nextThreshold = level * 50;
        const pct = Math.min(100, (xp / nextThreshold) * 100);

        const div = document.createElement('div');
        div.style.background = '#222';
        div.style.padding = '5px';
        div.style.borderRadius = '4px';
        div.style.border = '1px solid #444';

        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                <span style="font-weight:bold; text-transform:capitalize;">${key}</span>
                <span style="color:#8f8;">Lvl ${level}</span>
            </div>
            <div style="background:#000; height:4px; width:100%; border-radius:2px;">
                <div style="background:#0f0; width:${pct}%; height:100%; border-radius:2px; transition: width 0.3s;"></div>
            </div>
            <div style="font-size:0.7em; color:#888; text-align:right;">${xp} / ${nextThreshold} XP</div>
        `;
        list.appendChild(div);
    }
};

window.equipItem = async function (id) {
    try {
        const res = await fetch('/api/inventory/equip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();

        audioSystem.play('equip');

        // State update happens in main loop usually, but we can force it
        // Or await next fetchState
        window.fetchState(); // from main.js (global)
    } catch (e) { console.error(e); }
};

window.unequipItem = async function (id) {
    try {
        const res = await fetch('/api/inventory/unequip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();
        audioSystem.play('equip');
        window.fetchState();
    } catch (e) { console.error(e); }
};

// --- Shop System ---
// --- Shop System (Dual Grid + Drag&Drop) ---
window.openShop = async function (merchantName) {
    const modal = document.getElementById('shop-modal');
    // Sanity check: if it was minimized, closing and re-opening might not reset position if we don't clear it.
    // The draggable logic uses internal closures for restoreX/Y, which are per-element but scoped to the `makeDraggable` call.
    // We can't access those closures easily. 
    // However, we can simply force the modal to center screen style here.

    modal.style.top = '10%';
    modal.style.left = '50%';
    modal.style.transform = 'translateX(-50%)';
    modal.style.width = '700px';
    modal.style.height = '500px';

    // Ensure content is visible (un-minimize)
    const content = modal.querySelector('.panel-content');
    if (content) content.style.display = 'flex'; // It uses flex layout now
    const minBtn = modal.querySelector('.minimize-btn');
    if (minBtn) minBtn.innerText = 'X'; // Use X as close, or _ if we supported minimize

    const title = document.getElementById('shop-merchant-name');
    const goldDisplay = document.getElementById('shop-player-gold');
    const merchantList = document.getElementById('shop-list');
    const playerList = document.getElementById('player-shop-inv');

    title.innerText = merchantName;
    if (window.gameState && window.gameState.player) {
        goldDisplay.innerText = window.gameState.player.gold || 0;
    }

    merchantList.innerHTML = '<div style="color:#aaa;">Loading...</div>';
    playerList.innerHTML = '<div style="color:#aaa;">Loading...</div>';

    modal.style.display = 'block';

    try {
        const res = await fetch('/api/shop/list');
        const data = await res.json();

        // Render Function for reuse
        const renderGrid = (container, items, source) => {
            container.innerHTML = '';

            if (items.length === 0) {
                container.innerHTML = '<div style="grid-column:1/-1; color:#555; font-style:italic; padding:10px;">Empty</div>';
                return;
            }

            items.forEach(item => {
                const slot = document.createElement('div');
                slot.draggable = true;
                slot.className = 'shop-slot';
                // Inline styles for grid box
                slot.style.width = '42px';
                slot.style.height = '42px';
                slot.style.background = '#1a1a1a';
                slot.style.border = '1px solid #444';
                slot.style.borderRadius = '4px';
                slot.style.display = 'flex';
                slot.style.alignItems = 'center';
                slot.style.justifyContent = 'center';
                slot.style.fontSize = '24px';
                slot.style.cursor = 'grab';
                slot.style.position = 'relative';

                // Data
                const cost = source === 'merchant' ? item.value : Math.max(1, Math.floor((item.value || 0) / 2));
                const itemIcon = (item.properties && item.properties.icon) ? item.properties.icon : '📦';

                slot.innerHTML = itemIcon;

                // Tooltip
                slot.title = `${item.name}\n${source === 'merchant' ? 'Buy for ' : 'Sell for '} ${cost}g\n${item.description || ''}`;

                // Drag Events
                slot.ondragstart = (e) => {
                    e.dataTransfer.setData("text/plain", JSON.stringify({
                        source: source,
                        id: item.id || item.template_id, // Merchant items use template_id logic probably?
                        cost: cost,
                        name: item.name
                    }));
                    slot.style.opacity = '0.5';
                };

                slot.ondragend = () => {
                    slot.style.opacity = '1';
                };

                // Click fallback
                slot.onclick = () => {
                    if (confirm(source === 'merchant' ? `Buy ${item.name} for ${cost}g?` : `Sell ${item.name} for ${cost}g?`)) {
                        if (source === 'merchant') buyItem(item.id || item.template_id, cost); // logic expects template_id usually
                        else sellItem(item.id);
                    }
                };

                container.appendChild(slot);
            });
        };

        // 1. Merchant Items
        const merchInvIds = data.shops[merchantName] || [];
        const merchItems = merchInvIds.map(id => {
            let t = data.items[id];
            if (t) t.template_id = id; // Ensure ID is passed
            return t;
        }).filter(x => x);

        renderGrid(merchantList, merchItems, 'merchant');

        // 2. Player Items
        // We rely on global gameState
        const playerItems = window.gameState.player.inventory || [];
        // Filter out equipped items? Usually yes
        renderGrid(playerList, playerItems.filter(i => !i.is_equipped), 'player');


        // Setup Drop Zones
        // Drop on Player List = BUY
        playerList.ondragover = (e) => e.preventDefault(); // Allow drop
        playerList.ondrop = (e) => {
            e.preventDefault();
            const raw = e.dataTransfer.getData("text/plain");
            if (!raw) return;
            const d = JSON.parse(raw);

            if (d.source === 'merchant') {
                buyItem(d.id, d.cost);
            }
        };

        // Drop on Merchant List = SELL
        merchantList.ondragover = (e) => e.preventDefault();
        merchantList.ondrop = (e) => {
            e.preventDefault();
            const raw = e.dataTransfer.getData("text/plain");
            if (!raw) return;
            const d = JSON.parse(raw);

            if (d.source === 'player') {
                sellItem(d.id);
            }
        };


    } catch (e) {
        console.error(e);
        merchantList.innerHTML = 'Error loading shop.';
    }
};

window.buyItem = async function (templateId, cost) {
    // Check Gold First
    const currentGold = window.gameState.player.gold || 0;
    if (currentGold < cost) {
        alert("Not enough gold!");
        return;
    }

    try {
        const res = await fetch('/api/shop/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: templateId })
        });
        const data = await res.json();

        // Refresh
        await window.fetchState();
        document.getElementById('shop-player-gold').innerText = window.gameState.player.gold;

        // Re-open/Refresh shop visuals?
        // simple way: just re-call openShop with current name
        const name = document.getElementById('shop-merchant-name').innerText;
        window.openShop(name);

        audioSystem.play('coin');

    } catch (e) { console.error(e); }
};

window.sellItem = async function (itemId) {
    try {
        const res = await fetch('/api/shop/sell', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await res.json();

        // Refresh
        await window.fetchState();
        document.getElementById('shop-player-gold').innerText = window.gameState.player.gold;

        const name = document.getElementById('shop-merchant-name').innerText;
        window.openShop(name); // Refresh inventory lists

        audioSystem.play('coin');

    } catch (e) { console.error(e); }
};

// --- Tab Switching ---
window.switchCharTab = function (tabName) {
    audioSystem.play('page');
    // Buttons
    document.querySelectorAll('#char-sheet .tab-btn').forEach(b => b.classList.remove('active'));
    // Content
    document.querySelectorAll('#char-sheet .tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('#char-sheet .tab-content').forEach(c => c.style.display = 'none'); // Ensure hidden

    // Activate
    const btn = document.querySelector(`#char-sheet .tab-btn[onclick="switchCharTab('${tabName}')"]`);
    if (btn) btn.classList.add('active');

    const content = document.getElementById(`${tabName}-char-tab`);
    if (content) {
        content.classList.add('active');
        content.style.display = 'block'; // force show

        if (tabName === 'hero') content.style.display = 'flex'; // Hero tab uses flex
    }
};

window.switchTab = function (tabName) {
    document.querySelectorAll('#interaction-panel .tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('#interaction-panel .tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('#interaction-panel .tab-content').forEach(c => c.style.display = 'none');

    const btn = document.querySelector(`#interaction-panel .tab-btn[onclick="switchTab('${tabName}')"]`);
    if (btn) btn.classList.add('active');

    const content = document.getElementById(`${tabName}-tab`);
    if (content) {
        content.classList.add('active');
        content.style.display = 'block';
    }
};

window.lootBody = async function (corpseId) {
    try {
        const res = await fetch('/api/interact_specific', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: "loot", target_type: "corpse", target_id: corpseId })
        });
        const data = await res.json();

        // Check payload type
        let payload = data.narrative;
        if (typeof payload === 'object' && payload.type === 'loot_window') {
            renderLootModal(payload);
        } else {
            // Fallback text
            alert(payload);
        }

        window.fetchState();
    } catch (e) { console.error(e); }
};

window.renderLootModal = function (data) {
    const list = document.getElementById('loot-list');
    list.innerHTML = '';

    document.getElementById('loot-title').innerText = "LOOT: " + data.name;
    document.getElementById('loot-modal').style.display = 'block';

    window.activeLootCorpseId = data.corpse_id;

    if (data.loot.length === 0) {
        list.innerHTML = '<div style="font-style:italic">Empty...</div>';
        return;
    }

    data.loot.forEach(item => {
        const div = document.createElement('div');
        div.style.padding = '5px';
        div.style.borderBottom = '1px solid #444';
        div.style.display = 'flex';
        div.style.justifyContent = 'space-between';
        div.style.alignItems = 'center';

        div.innerHTML = `
            <div style="display:flex; align-items:center;">
                <span style="font-size:20px; margin-right:10px;">${item.icon || '📦'}</span>
                <span>${item.name}</span>
            </div>
            <button onclick="takeLoot('${item.id}')" style="cursor:pointer; background:#522; border:1px solid #844; color:#fcc; padding:2px 8px;">Take</button>
        `;
        list.appendChild(div);
    });
};

window.takeLoot = async function (lootId) {
    try {
        const res = await fetch('/api/loot/take', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ corpse_id: window.activeLootCorpseId, loot_id: lootId })
        });
        const data = await res.json();

        // Popup Notification for Loot
        if (data.message && !data.message.includes("Nothing left") && !data.message.includes("removed")) {
            showTurnNotification("ACQUIRED", data.message, 1500, "rgba(0, 100, 0, 0.8)");
            if (window.audioSystem) window.audioSystem.play('coin');
        }

        // If corpse is gone (empty), close modal. Otherwise refresh it.
        if (data.message === "Corpse removed." || data.message === "Nothing left.") {
            document.getElementById('loot-modal').style.display = 'none';
            window.fetchState();
        } else {
            lootBody(window.activeLootCorpseId);
        }

    } catch (e) { console.error(e); }
};

window.useItem = async function (id) {
    try {
        const res = await fetch('/api/inventory/use', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: id })
        });
        const data = await res.json();

        alert(data.message);
        window.fetchState();
    } catch (e) { console.error(e); }
};

// --- Crafting System ---
window.refreshCraftingList = async function () {
    const list = document.getElementById('crafting-list');
    if (!list) return;
    list.innerHTML = '<div style="padding:10px; color:#aaa;">Loading recipes...</div>';
    try {
        const res = await fetch('/api/craft/list');
        const recipes = await res.json();
        list.innerHTML = '';

        if (Object.keys(recipes).length === 0) {
            list.innerHTML = '<div style="padding:10px;">No recipes known.</div>';
            return;
        }

        for (const [key, r] of Object.entries(recipes)) {
            let ingredients = [];
            for (let [k, v] of Object.entries(r.ingredients)) ingredients.push(`${v}x ${k}`);

            const div = document.createElement('div');
            div.style.background = '#222';
            div.style.padding = '8px';
            div.style.marginBottom = '4px';
            div.style.border = '1px solid #444';

            div.innerHTML = `
                <div style="color:#d4af37; font-weight:bold;">${r.name}</div>
                <div style="font-size:0.8em; color:#aaa; margin-bottom:4px;">Needs: ${ingredients.join(', ')}</div>
                <button onclick="craftItem('${key}')" style="background:#400; color:#faa; border:1px solid #800; width:100%; cursor:pointer; padding:4px;">Craft</button>
             `;
            list.appendChild(div);
        }
    } catch (e) { console.error(e); }
};

window.craftItem = async function (id) {
    try {
        const res = await fetch('/api/craft/make', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipe_id: id })
        });
        const d = await res.json();
        alert(d.message);
        window.fetchState();
    } catch (e) { console.error(e); }
};

// Overwrite switchCharTab to support crafting
window.switchCharTab = function (tabName) {
    const tabs = ['hero', 'equipment', 'skills', 'crafting'];
    tabs.forEach(t => {
        const pane = document.getElementById(`${t}-char-tab`);
        if (pane) {
            const isActive = (t === tabName);
            pane.classList.toggle('active', isActive);
            pane.style.display = isActive ? 'block' : 'none';
        }
    });

    // Update Button Styles using querySelector
    // We assume buttons are siblings in .tab-header. 
    // This is purely visual.
    const btns = document.querySelectorAll('#char-sheet .tab-btn');
    btns.forEach(btn => {
        if (btn.innerText.toLowerCase().includes(tabName.substring(0, 4))) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    if (tabName === 'crafting') {
        window.refreshCraftingList();
    }
};

window.updateRightPanelItems = function (player) {
    const list = document.getElementById('items-list');
    if (!list) return;

    list.innerHTML = '';

    // Icon Mapping for Box Display
    const iconMap = {
        'Training Sword': "⚔️", 'Iron Sword': "⚔️", 'Steel Sword': "⚔️", 'Rusty Dagger': "🗡️", 'Steel Dagger': "🗡️",
        'Cloth Tunic': "👕", 'Leather Armor': "👕", 'Chainmail': "⛓️",
        'Leather Helmet': "🧢", 'Iron Helmet': "🪖",
        'Leather Boots': "👢",
        'Healing Potion': "🧪",
        'Iron Ore': "🪨",
        'Mystic Herb': "🌿",
        'Gold': "💰",
        'Wooden Shield': "🛡️", 'Iron Shield': "🛡️",
        'Iron Key': "🔑",
        'Ring': "💍",
        'Leather Gloves': "🧤"
    };

    // 1. Gold Display
    let gold = player.gold || 0;
    const goldDiv = document.createElement('div');
    goldDiv.className = 'item-entry'; // Reuse class for styling if needed, or override
    goldDiv.style.color = '#ffd700';
    goldDiv.style.fontWeight = 'bold';
    goldDiv.style.borderBottom = '1px solid #444';
    goldDiv.style.marginBottom = '10px';
    goldDiv.style.paddingBottom = '5px';
    goldDiv.style.background = 'none'; // Clear default
    goldDiv.style.border = 'none';
    goldDiv.style.borderBottom = '1px solid #444';
    goldDiv.innerText = `Gold: ${gold}g`;
    list.appendChild(goldDiv);

    // 2. Items Grid Container
    const grid = document.createElement('div');
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(40px, 1fr))';
    grid.style.gap = '8px';

    const items = player.inventory || [];

    if (items.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; color:#666; font-style:italic;">Bag is empty.</div>';
    } else {
        items.forEach(item => {
            const slot = document.createElement('div');
            // Style Box
            slot.style.width = '42px';
            slot.style.height = '42px';
            slot.style.background = '#1a1a1a';
            slot.style.border = '1px solid #444';
            slot.style.borderRadius = '6px';
            slot.style.position = 'relative';
            slot.style.cursor = 'help'; // Shows it has info
            slot.style.display = 'flex';
            slot.style.alignItems = 'center';
            slot.style.justifyContent = 'center';
            slot.style.fontSize = '24px';
            slot.style.transition = 'all 0.1s';

            // Hover Effect
            slot.onmouseover = () => { slot.style.borderColor = '#888'; slot.style.background = '#222'; };
            slot.onmouseout = () => {
                slot.style.borderColor = item.is_equipped ? '#0f0' : '#444';
                slot.style.background = '#1a1a1a';
            };

            // Highlight equipped
            if (item.is_equipped) {
                slot.style.borderColor = '#0f0';
                slot.style.boxShadow = '0 0 5px rgba(0, 255, 0, 0.3)';
            }

            // Icon
            let iconStr = "📦";
            if (item.properties && item.properties.icon) iconStr = item.properties.icon;
            else if (iconMap[item.name]) iconStr = iconMap[item.name];

            slot.innerText = iconStr;

            // Tooltip (Description on Hover)
            let desc = `${item.name}`;
            if (item.is_equipped) desc += " (Equipped)";
            if (item.quantity > 1) desc += ` x${item.quantity}`;

            // Add Stats if available
            const props = item.properties || {};
            if (props.damage) desc += `\nDamage: ${props.damage}`;
            if (props.defense) desc += `\nDefense: +${props.defense}`;
            if (props.heal) desc += `\nHeals: ${props.heal}`;
            if (item.item_type) desc += `\nType: ${item.item_type}`;

            slot.title = desc;

            // Quantity Badge
            if (item.quantity > 1) {
                const badge = document.createElement('span');
                badge.style.position = 'absolute';
                badge.style.bottom = '1px';
                badge.style.right = '3px';
                badge.style.fontSize = '10px';
                badge.style.color = '#fff';
                badge.style.fontWeight = 'bold';
                badge.style.textShadow = '1px 1px 0 #000';
                badge.innerText = item.quantity;
                slot.appendChild(badge);
            }

            // Optional: Click to equip/use?
            // The user just asked for display, but interaction makes sense.
            slot.onclick = () => {
                if (confirm(`Interact with ${item.name}?`)) {
                    if (item.is_equipped) unequipItem(item.id);
                    else if (item.slot) equipItem(item.id);
                    else if (item.item_type === 'consumable') useItem(item.id);
                }
            };

            grid.appendChild(slot);
        });
    }
    list.appendChild(grid);
};
