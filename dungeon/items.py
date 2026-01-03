ITEM_TEMPLATES = {
    # Weapons
    "iron_sword": {
        "name": "Iron Sword",
        "type": "weapon",
        "slot": "main_hand",
        "properties": {"damage": "1d6", "icon": "iron_sword.png"},
        "value": 50,
        "description": "A standard soldier's blade."
    },
    "dagger": {
        "name": "Steel Dagger",
        "type": "weapon",
        "slot": "main_hand",
        "properties": {"damage": "1d4", "icon": "dagger.png"},
        "value": 25,
        "description": "Fast and light."
    },
    "greatsword": {
        "name": "Greatsword",
        "type": "weapon",
        "slot": "main_hand",
        "properties": {"damage": "2d6", "icon": "greatsword.png"},
        "value": 150,
        "description": "Requires two hands, but hits hard."
    },
    "titanium_greatsword": {
        "name": "Titanium Greatsword",
        "type": "weapon",
        "slot": "main_hand",
        "properties": {"damage": "2d8", "icon": "titanium_greatsword.png", "rarity": "legendary"},
        "value": 1000,
        "description": "A legendary blade forged from star metal. Incredible power."
    },
    
    # Armor
    "leather_armor": {
        "name": "Leather Armor",
        "type": "armor",
        "slot": "chest",
        "properties": {"defense": 2, "icon": "leather_armor.png"},
        "value": 40,
        "description": "Standard protective gear."
    },
    "chainmail": {
        "name": "Chainmail",
        "type": "armor",
        "slot": "chest",
        "properties": {"defense": 5, "icon": "chainmail.png"},
        "value": 200,
        "description": "Heavy interlocking rings."
    },
    
    # Consumables
    "healing_potion": {
        "name": "Healing Potion",
        "type": "consumable",
        "slot": None,
        "properties": {"heal": 2, "icon": "healing_potion.png"},
        "value": 25,
        "description": "Restores health."
    },
    
    # Quest Items
    "iron_ore": {
        "name": "Iron Ore",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "rock.png"},
        "value": 0,
        "description": "Raw iron mined from a rock."
    },
    "mystic_herb": {
        "name": "Mystic Herb",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "herb.png"},
        "value": 0,
        "description": "A fragrant herb needed by the Alchemist."
    },
    # New Quest Materials
    "titanium_fragment": {
        "name": "Titanium Fragment",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "titanium_fragment.png"},
        "value": 200,
        "description": "An incredibly hard metal shard."
    },
    "everburning_cinder": {
        "name": "Everburning Cinder",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "everburning_cinder.png"},
        "value": 150,
        "description": "It feels warm to the touch."
    },
    "freezing_spike": {
        "name": "Freezing Spike",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "freezing_spike.png"},
        "value": 150,
        "description": "It never melts."
    },
    # Rewards
    "potion_of_power": {
        "name": "Potion of Power",
        "type": "consumable",
        "slot": None,
        "properties": {"heal": 50, "buff": "str+2", "icon": "potion_of_power.png"},
        "value": 500,
        "description": "A legendary brew that grants immense strength."
    },
    
    # Fire Dungeon Loot
    "phoenix_shield": {
        "name": "Phoenix Down Shield",
        "type": "armor",
        "slot": "off_hand",
        "properties": {"defense": 3, "effect": "fire_resist", "icon": "phoenix_shield.png"},
        "value": 450,
        "description": "Grants immunity to fire when blocking."
    },
    "cryo_flask": {
        "name": "Cryo-Flask",
        "type": "consumable",
        "slot": None,
        "properties": {"icon": "cryo_flask.png", "effect": "freeze_lava"},
        "value": 150,
        "description": "Freezes lava or steam to create safe passage."
    },
    "item_core": {
        "name": "Igneous Core",
        "type": "material",
        "slot": None,
        "properties": {"icon": "item_core.png"},
        "value": 300,
        "description": "The pulsating heart of a molten creature."
    },
    "charred_ledger": {
        "name": "Charred Ledger",
        "type": "quest",
        "slot": None,
        "properties": {"icon": "charred_ledger.png"},
        "value": 0,
        "description": "A burnt book detailing the experiments of the Magma Weaver."
    },
    
    # New Standard Items
    "torch": {
        "name": "Torch",
        "type": "misc",
        "slot": "off_hand",
        "properties": {"icon": "torch.png", "light": 6},
        "value": 5,
        "description": "Provides light in dark places."
    },
    
    # Ice Dungeon Loot
    "frost_brand": {
        "name": "Frost Brand",
        "type": "weapon",
        "slot": "main_hand",
        "properties": {"damage": "1d8+1d6", "icon": "frost_brand.png", "effect": "slow"},
        "value": 600,
        "description": "A magical sword that deals extra cold damage."
    },
    "item_frost_shard": {
        "name": "Glacial Shard",
        "type": "material",
        "slot": None,
        "properties": {"icon": "item_frost_shard.png"},
        "value": 300,
        "description": "A shard of eternal ice."
    }
}

SHOPS = {
    "Gareth Ironhand": ["iron_sword", "dagger", "greatsword", "leather_armor", "chainmail"],
    "Seraphina": ["healing_potion"]
}
