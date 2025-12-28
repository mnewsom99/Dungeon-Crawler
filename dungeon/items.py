ITEM_TEMPLATES = {
    # Weapons
    "iron_sword": {
        "name": "Iron Sword",
        "type": "weapon",
        "slot": "main_hand",
        "properties": {"damage": "1d6", "icon": "⚔️"},
        "value": 50,
        "description": "A standard soldier's blade."
    },
    "dagger": {
        "name": "Steel Dagger",
        "type": "weapon",
        "slot": "main_hand",
        "properties": {"damage": "1d4", "icon": "🗡️"},
        "value": 25,
        "description": "Fast and light."
    },
    "greatsword": {
        "name": "Greatsword",
        "type": "weapon",
        "slot": "main_hand",
        "properties": {"damage": "2d6", "icon": "🗡️"},
        "value": 150,
        "description": "Requires two hands, but hits hard."
    },
    
    # Armor
    "leather_armor": {
        "name": "Leather Armor",
        "type": "armor",
        "slot": "chest",
        "properties": {"defense": 2, "icon": "👕"},
        "value": 40,
        "description": "Standard protective gear."
    },
    "chainmail": {
        "name": "Chainmail",
        "type": "armor",
        "slot": "chest",
        "properties": {"defense": 5, "icon": "⛓️"},
        "value": 200,
        "description": "Heavy interlocking rings."
    },
    
    # Consumables
    "healing_potion": {
        "name": "Healing Potion",
        "type": "consumable",
        "slot": None,
        "properties": {"heal": 2, "icon": "🧪"},
        "value": 25,
        "description": "Restores health."
    },
    
    # Quest Items
    "iron_ore": {
        "name": "Iron Ore",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "🪨"},
        "value": 0,
        "description": "Raw iron mined from a rock."
    },
    "mystic_herb": {
        "name": "Mystic Herb",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "🌿"},
        "value": 0,
        "description": "A fragrant herb needed by the Alchemist."
    },
    # New Quest Materials
    "titanium_fragment": {
        "name": "Titanium Fragment",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "💎"},
        "value": 200,
        "description": "An incredibly hard metal shard."
    },
    "everburning_cinder": {
        "name": "Everburning Cinder",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "🔥"},
        "value": 150,
        "description": "It feels warm to the touch."
    },
    "freezing_spike": {
        "name": "Freezing Spike",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "❄️"},
        "value": 150,
        "description": "It never melts."
    },
    # Rewards
    "potion_of_power": {
        "name": "Potion of Power",
        "type": "consumable",
        "slot": None,
        "properties": {"heal": 50, "buff": "str+2", "icon": "🍷"},
        "value": 500,
        "description": "A legendary brew that grants immense strength."
    }
}

SHOPS = {
    "Gareth Ironhand": ["iron_sword", "dagger", "greatsword", "leather_armor", "chainmail"],
    "Seraphina": ["healing_potion"]
}
