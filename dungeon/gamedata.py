"""
Static Game Data Definitions.
This module serves as the central repository for static game rules, tables, and definitions,
keeping the database focused on state and the DM logic focused on execution.
"""

SKILLS = {
    "mining": {
        "name": "Mining", 
        "desc": "Ability to extract ore from rocks.",
        "icon": "⛏️"
    },
    "herbalism": {
        "name": "Herbalism", 
        "desc": "Ability to gather herbs.",
        "icon": "🌿"
    },
    "stealth": {
        "name": "Stealth", 
        "desc": "Avoid detection by enemies.",
        "icon": "🥷"
    },
    "smithing": {
        "name": "Smithing",
        "desc": "Craft weapons and armor.",
        "icon": "🔨"
    }
}

RECIPES = {
    "health_potion": {
        "id": "health_potion_recipe",
        "name": "Health Potion", 
        "ingredients": {"mystic_herb": 2}, 
        "result": "healing_potion", 
        "skill_req": {"herbalism": 1},
        "station": "alchemy_lab"
    },
    "iron_ingot": {
        "id": "iron_ingot_recipe",
        "name": "Iron Ingot",
        "ingredients": {"iron_ore": 2},
        "result": "iron_ingot",
        "skill_req": {"smithing": 1},
        "station": "forge"
    }
}

LOOT_TABLES = {
    "undead_basic": [
        {"code": "gold", "chance": 1.0, "qty_range": (2, 8)},
        {"code": "bone", "chance": 0.4, "qty_range": (1, 2)},
        {"code": "dagger", "chance": 0.1, "qty_range": (1, 1)}
    ],
    "beast_basic": [
        {"code": "gold", "chance": 0.3, "qty_range": (1, 3)},
        {"code": "meat", "chance": 0.6, "qty_range": (1, 1)}
    ]
}

MONSTER_VARIANTS = {
    "skeleton": {
        "name": "Skeleton",
        "family": "undead",
        "level": 1,
        "hp_range": (8, 12),
        "ac": 10,
        "stats": {"str": 10, "dex": 12},
        "loot_table": "undead_basic",
        "abilities": []
    },
    "skeleton_warrior": {
        "name": "Skeleton Warrior",
        "family": "undead",
        "level": 3,
        "hp_range": (15, 25),
        "ac": 14,
        "stats": {"str": 14, "dex": 10},
        "loot_table": "undead_basic",
        "abilities": ["power_strike"]
    }
}

ABILITIES = {
    "power_strike": {
        "name": "Power Strike",
        "desc": "Deals 1.5x damage but has -2 to hit.",
        "mana_cost": 0,
        "cooldown": 3
    },
    "fireball": {
        "name": "Fireball",
        "desc": "Deals 3d6 fire damage in an area.",
        "mana_cost": 5,
        "cooldown": 0
    }
}
