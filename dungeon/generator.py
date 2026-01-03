import json
import os
import random
from .database import MapTile, Monster, NPC, InventoryItem, WorldObject
from sqlalchemy.orm.attributes import flag_modified
from .rules import roll_dice

class LevelBuilder:
    def __init__(self, session):
        self.session = session
        self.floors = set()
        self.walls = set()

    def _get_level_for_z(self, z):
        """Returns a random level appropriate for the zone depth."""
        if z == 0: return random.randint(1, 2)
        if z == 1: return 1 # Town (Peaceful)
        if z == 2: return random.randint(3, 5) # Forest
        if z == 3: return random.randint(6, 9) # Fire
        if z == 4: return random.randint(10, 14) # Ice
        return 1

    def _scale_monster(self, monster, level):
        """Scales monster stats based on level relative to baseline (Level 1)."""
        monster.level = level
        
        # Scaling Factors per Level
        hp_growth = 5
        
        # Base HP is already set in monster constructor usually.
        # We add bonus HP
        bonus_hp = (level - 1) * hp_growth
        monster.hp_max += bonus_hp
        monster.hp_current = monster.hp_max
        
        # Scale Stats
        stats = dict(monster.stats or {"str": 10, "dex": 10, "int": 10})
        bonus_stat = (level - 1) // 2 # +1 for every 2 levels
        
        for k in stats:
            stats[k] += bonus_stat
            
        monster.stats = stats
        
        # AC Scaling (lighter)
        monster.armor_class = (monster.armor_class or 10) + ((level - 1) // 3)

    def _load_npcs_from_file(self, target_z):
        """Loads NPCs from dungeon/data/npcs.json for a specific Z-level."""
        try:
            # Construct path relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, "data", "npcs.json")
            
            with open(data_path, "r", encoding="utf-8") as f:
                npc_data = json.load(f)
                
            count = 0
            for n in npc_data:
                # Filter by Z level
                if n.get("z") == target_z:
                    new_npc = NPC(
                        name=n["name"],
                        location=n["location"],
                        x=n["x"],
                        y=n["y"],
                        z=n["z"],
                        persona_prompt=n["persona_prompt"],
                        quest_state=n["quest_state"]
                    )
                    self.session.add(new_npc)
                    count += 1
            print(f"Generator: Loaded {count} NPCs for Z={target_z}")
            
        except Exception as e:
            print(f"Generator Error: Could not load NPCs: {e}")

    def generate_tutorial_dungeon(self, player):
        """Generates the initial dungeon floor (Z=0)."""
        print("Generator: Building Tutorial Dungeon...")
        
        # --- Helper Functions ---
        def add_rect(cx, cy, w, h):
            for x in range(cx - w//2, cx + w//2 + 1):
                for y in range(cy - h//2, cy + h//2 + 1):
                    self.floors.add((x, y))

        def add_corridor_v(x, y1, y2):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.floors.add((x, y))
        
        def add_corridor_h(y, x1, x2):
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.floors.add((x, y))

        # 1. Start Room (3x3 at 0,0)
        add_rect(0, 0, 3, 3)
        
        # 2. Main Corridor North (0,2 to 0,8)
        add_corridor_v(0, 2, 8)
        
        # 3. The Grand Hall (7x5 at 0, 11)
        add_rect(0, 11, 7, 5)
        
        # 4. West Wing: Armory (Connected via corridor)
        add_corridor_h(11, -3, -8)  # Hallway West
        add_rect(-10, 11, 5, 5)     # Armory Room
        
        # 5. East Wing: Library
        add_corridor_h(11, 3, 8)    # Hallway East
        add_rect(10, 11, 5, 5)      # Library Room
        
        # 6. North to Barracks
        add_corridor_v(0, 14, 18)
        add_rect(0, 20, 9, 5)       # Barracks (Wide)
        
        # 7. Final Corridor to Jail
        add_corridor_v(0, 23, 28)
        add_rect(0, 30, 5, 5)       # Boss/Jail Room

        # --- Commit Map ---
        # Floors
        for (x, y) in self.floors:
            t_type = "floor"
            if random.random() < 0.05:
                t_type = "rock"
            self.session.add(MapTile(x=x, y=y, z=0, tile_type=t_type, is_visited=False))

        # Walls (Perimeter)
        # Identify walls by checking neighbors of floors
        for (x, y) in self.floors:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = x+dx, y+dy
                    if (nx, ny) not in self.floors:
                        self.walls.add((nx, ny))
        
        for (x, y) in self.walls:
            self.session.add(MapTile(x=x, y=y, z=0, tile_type="wall", is_visited=False))
        
        # --- Populate Enemies (Total: 9 Skeletons + 1 Boss) ---
        enemies = [
            # Hallway / Grand Hall
            ("Decrepit Skeleton", 6, 0, 6),   # Corridor
            ("Skeleton Grunt", 10, -2, 12),   # Grand Hall
            ("Skeleton Grunt", 10, 2, 10),    # Grand Hall
            
            # West Wing (Armory)
            ("Armored Skeleton", 15, -11, 10), # Moved from -10,11 (Chest overlap)
            ("Armored Skeleton", 15, -11, 12),
            
            # East Wing (Library)
            ("Rotted Skeleton", 8, 9, 12),     # Moved from 10,11 (Center room)
            ("Skeleton Mage", 12, 11, 12),
            
            # Barracks (The Horde)
            ("Skeleton Warrior", 18, -2, 20),
            ("Skeleton Warrior", 18, 2, 20),
            
            # Jail Guard (Boss)
            ("Dungeon Warden", 30, 0, 28)      # Guarding the door to cell
        ]
        
        for name, hp, ex, ey in enemies:
            m = Monster(name=name, hp_current=hp, hp_max=hp, x=ex, y=ey, z=0, state="alive")
            # Tutorial Level Logic: 1 for trash, 2 for boss
            lvl = 1
            if "Warden" in name: lvl = 2
            elif "Warrior" in name: lvl = 2
            self._scale_monster(m, lvl)
            self.session.add(m)

        # Load Dungeon NPCs (Z=0)
        self._load_npcs_from_file(0)
        
        # 8. Add Interactive Objects (Chests)
        # Ancient Chest in Boss Room (Center of 5x5 at 0,30) -> 0,30
        cmd_loot = [{"id": "loot_sword_1", "name": "Steel Sword", "item_type": "weapon", "slot": "main_hand", "properties": {"damage": "1d8", "icon": "⚔️"}}]
        self.session.add(WorldObject(
            name="Ancient Chest", 
            obj_type="chest", 
            x=0, y=30, z=0, 
            properties={"loot": cmd_loot, "icon": "🧳"}
        ))
        
        # Armory Crate in West Wing (-10, 11)
        armory_loot = [{"id": "loot_shield_1", "name": "Iron Shield", "item_type": "armor", "slot": "main_hand", "properties": {"defense": 2, "icon": "🛡️"}}]
        self.session.add(WorldObject(
            name="Armory Crate",
            obj_type="chest",
            x=-10, y=11, z=0,
            properties={"loot": armory_loot, "icon": "📦"}
        ))
        
        self.session.commit()

    def generate_town(self, z):
        """Generate the Oakhaven Town map at level Z."""
        print(f"Generator: Building Town at Z={z}...")
        
        # --- Helper: Build House ---
        def build_house(x, y, w, h, door_side="bottom", floor="floor_wood", wall="wall_house"):
            for i in range(x, x+w):
                for j in range(y, y+h):
                    t_type = floor
                    if i == x or i == x+w-1 or j == y or j == y+h-1:
                        t_type = wall
                    
                    self.session.add(MapTile(x=i, y=j, z=z, tile_type=t_type, is_visited=True))
            
            dx, dy = x + w//2, y + h - 1 
            if door_side == "top": dy = y
            elif door_side == "left": dx, dy = x, y + h//2
            elif door_side == "right": dx, dy = x + w-1, y + h//2

        # 1. Base Grass Layer (-20 to 20)
        tiles = {} # (x,y) -> type

        for x in range(-20, 21):
            for y in range(-23, 22): 
                t_type = "grass" 
                # Borders
                if abs(x) == 20 or abs(y) == 20: 
                    t_type = "wall" 
                    
                    # North Gate
                    if y == -20:
                        # Moat
                        if abs(x) <= 6:
                            tiles[(x, -21)] = "water"
                            tiles[(x, -22)] = "water" 

                        # Bridge
                        tiles[(0, -21)] = "bridge"
                        tiles[(0, -22)] = "bridge"

                        # Gate Towers
                        if abs(x) <= 2:
                             if x == 0: t_type = "door"
                             else: t_type = "wall_grey" 

                # North Gate (Inner)
                if y == -19 and abs(x) <= 2:
                    if x == 0: t_type = "floor" 
                    else: t_type = "wall_grey" 

                tiles[(x,y)] = t_type

        # 2. Structures
        
        def place_structure(lx, ly, w, h, floor="floor_wood", wall="wall_house", door_pos=None):
            for i in range(lx, lx+w):
                for j in range(ly, ly+h):
                    tiles[(i,j)] = floor
                    if i == lx or i == lx+w-1 or j == ly or j == ly+h-1:
                        tiles[(i,j)] = wall
            
            if door_pos:
                tiles[door_pos] = "door"

        # Structures
        place_structure(-4, 4, 9, 7, door_pos=(0, 4)) # Town Hall
        place_structure(8, 6, 8, 7, door_pos=(8, 9)) # Smithy
        place_structure(-14, 6, 7, 7, door_pos=(-8, 9)) # Alchemist

        # --- Town Hall Interior (Furniture) ---
        # Back wall shelves
        tiles[(-3, 5)] = "shelf"
        tiles[(-2, 5)] = "shelf"
        tiles[(2, 5)] = "shelf"
        tiles[(3, 5)] = "shelf"
        # Corner Plants
        tiles[(-3, 9)] = "flower_pot"
        tiles[(3, 9)] = "flower_pot"
        # Rug/Carpet Effect (using floor_wood for now if distinct, otherwise relying on structure floor)
        # Adding a "Head Table" approximation with barrels/crates if no table sprite
        tiles[(-1, 5)] = "chest" # Treasure/supplies
        tiles[(1, 5)] = "barrel"

        # --- Decor ---
        tiles[(0, 0)] = "fountain"      
        tiles[(0, -1)] = "stairs_down"  
        
        # Lamps
        tiles[(-2, -2)] = "street_lamp"
        tiles[(2, -2)] = "street_lamp"
        tiles[(-2, 2)] = "street_lamp"
        tiles[(2, 2)] = "street_lamp"
        
        # Flowers
        tiles[(1, 4)] = "flower_pot"
        tiles[(-1, 4)] = "flower_pot"
        tiles[(-8, 8)] = "flower_pot"   
        tiles[(-8, 10)] = "flower_pot"
        
        # Cargo
        tiles[(9, 10)] = "barrel"       
        tiles[(9, 11)] = "crate"
        tiles[(8, 5)] = "barrel"        
        
        # Rocks
        tiles[(12, 8)] = "rock"
        tiles[(13, 9)] = "rock"
        tiles[(12, 10)] = "rock"
        
        # Garden
        tiles[(-10, 5)] = "flower_pot" 
        tiles[(-11, 5)] = "flower_pot"
        tiles[(-10, 4)] = "flower_pot"
        
        # Other
        tiles[(0, -2)] = "signpost"
        tiles[(12, 9)] = "anvil" 
        tiles[(13, 9)] = "anvil" 
        tiles[(-12, 7)] = "shelf"
        tiles[(-11, 7)] = "shelf"
        
        # Pond
        for x in range(10, 16):
            for y in range(-12, -8):
                tiles[(x,y)] = "water"
                
        # Trees 
        for _ in range(30):
            tx = random.randint(-18, 18)
            ty = random.randint(-18, 18)
            if tiles.get((tx,ty)) == "grass":
                tiles[(tx,ty)] = "tree"

        # 4. Commit 
        for (pos, t_type) in tiles.items():
            self.session.add(MapTile(x=pos[0], y=pos[1], z=z, tile_type=t_type, is_visited=True))
        
        # Spawn NPCs from JSON
        self._load_npcs_from_file(z)

    def generate_forest(self, z):
        """Generate the North Forest (Z=2)."""
        print(f"Generator: Building North Forest at Z={z}...")
        
        # 1. Base Grass (Huge Area: 60x60)
        width, height = 60, 60
        tiles = {}
        
        for x in range(-width//2, width//2):
            for y in range(-height//2, height//2):
                tiles[(x,y)] = "grass"
                
                if random.random() < 0.26:
                    tiles[(x,y)] = "tree"
                elif random.random() < 0.02: 
                    tiles[(x,y)] = "rock"
                elif random.random() < 0.03: 
                    tiles[(x,y)] = "herb"
                    # We can't set metadata here easily because we are building a dict of strings.
                    # We must handle this in the Commit step (Line 397 approx)

        # 2. Lake
        cx, cy = 15, -15
        radius = 8
        for x in range(cx - radius, cx + radius):
            for y in range(cy - radius, cy + radius):
                if (x-cx)**2 + (y-cy)**2 <= radius**2:
                    tiles[(x,y)] = "water"

        # 3. Main Road
        for y in range(-25, 30):
            for x in range(-2, 3):
                tiles[(x,y)] = "floor" 
                
        # Town Gate
        tiles[(0, 29)] = "door" 
        tiles[(-1, 29)] = "wall"
        tiles[(1, 29)] = "wall"
        
        # 4. Dungeon Entrances
        def place_entrance(cx, cy, tile_type, decor, name):
            structure = [
                (-1, -2, "mtn_tl"), (0, -2, "mtn_tm"), (1, -2, "mtn_tr"),
                (-1, -1, "mtn_ml"), (0, -1, "mtn_mm"), (1, -1, "mtn_mr"),
                (-1, 0, "mtn_bl"), (0, 0, "door_stone"), (1, 0, "mtn_br")
            ]
            
            for (dx, dy, code) in structure:
                tiles[(cx+dx, cy+dy)] = code
                
            for dx in range(-2, 3):
                for dy in range(-3, 2):
                    if abs(dx) <= 1 and -2 <= dy <= 0: continue
                    if (cx+dx, cy+dy) not in tiles:
                         tiles[(cx+dx, cy+dy)] = decor

            # Ensure Clear Path SOUTH of door
            # If there's a tree or wall at (cx, cy+1), remove it
            path_check = [(0, 1), (0, 2)]
            for pdx, pdy in path_check:
                curr = tiles.get((cx+pdx, cy+pdy))
                if curr == "tree" or curr == "wall":
                    tiles[(cx+pdx, cy+pdy)] = "floor"

        place_entrance(-15, 15, "door", "lava", "Fire Dungeon")
        place_entrance(-15, -20, "door", "ice", "Ice Dungeon")
        place_entrance(20, -20, "door", "rock", "Earth Dungeon")
        place_entrance(20, 15, "door", "void", "Air Dungeon")
        
        # 5. Commit
        game_map = []
        for (pos, t_type) in tiles.items():
            m = MapTile(x=pos[0], y=pos[1], z=z, tile_type=t_type, is_visited=True)
            if t_type == "herb":
                 m.meta_data = {
                     "interactable": True, 
                     "interact_name": "Mystic Herb",
                     "action": "gather",
                     "hidden": False # Visible by default
                 }
            game_map.append(m)
        
        for m in game_map:
            if m.tile_type == "floor": 
                m.is_visited = True
            else:
                m.is_visited = False
            self.session.add(m)
            
        # 6. Spawns
        beasts = ["Dire Wolf", "Forest Bear", "Knife Goblin"]
        occupied_spawns = set()
        
        count = 0
        attempts = 0
        while count < 19 and attempts < 200:
             attempts += 1
             bx = random.randint(-25, 25)
             by = random.randint(-25, 25)
             if (bx, by) in occupied_spawns: continue

             t_type = tiles.get((bx, by))
             if t_type in ["grass", "floor"]:
                 occupied_spawns.add((bx, by))
                 name = random.choice(beasts)
                 hp = 10 if "Goblin" in name else 25
                 m = Monster(name=name, hp_current=hp, hp_max=hp, x=bx, y=by, z=z, state="alive")
                 self._scale_monster(m, self._get_level_for_z(z))
                 self.session.add(m)
                 count += 1

        # 7. Elemental Bosses
        bosses = [
            {"name": "Fire Guardian", "x": -15, "y": 15, "hp": 100},
            {"name": "Ice Guardian", "x": -15, "y": -20, "hp": 100},
            {"name": "Earth Guardian", "x": 20, "y": -20, "hp": 120},
            {"name": "Air Guardian", "x": 20, "y": 15, "hp": 80}
        ]
        
        for b in bosses:
            m = Monster(name=b["name"], hp_current=b["hp"], hp_max=b["hp"], 
                        x=b["x"], y=b["y"], z=z, state="alive", 
                        stats={"str": 14, "dex": 12, "int": 10})
            self._scale_monster(m, 10) 
            self.session.add(m)

        self.session.commit()

    def generate_fire_dungeon(self, z):
        """Generate the Fire Dungeon (Z=3)."""
        print(f"Generator: Building Fire Dungeon at Z={z}...")

        # 1. Base
        floors = set()
        walkers = [(0, 0)]
        
        for x in range(-3, 4):
            for y in range(-3, 4):
                floors.add((x, y))

        for _ in range(400): 
             new_walkers = []
             for wx, wy in walkers:
                 dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                 nx, ny = wx+dx, wy+dy
                 if abs(nx) < 30 and abs(ny) < 30: 
                     floors.add((nx, ny))
                     if random.random() < 0.1: new_walkers.append((nx, ny)) 
                     else: new_walkers.append((nx, ny)) 
             walkers = new_walkers
        
        # 2. Tiles
        for (x, y) in floors:
            t_type = "floor_volcanic"
            if random.random() < 0.05 and abs(x) > 5: t_type = "lava"
            elif random.random() < 0.02 and abs(x) > 5: t_type = "steam_vent"
            
            self.session.add(MapTile(x=x, y=y, z=z, tile_type=t_type, is_visited=False))

        walls = set()
        for x, y in floors:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if (x+dx, y+dy) not in floors:
                        walls.add((x+dx, y+dy))
        
        for x, y in walls:
            self.session.add(MapTile(x=x, y=y, z=z, tile_type="wall_volcanic", is_visited=False))
            
        # 3. Monsters
        valid_floors = list(floors)
        enemies = [
            ("Cinder-Hound", 15, "beast"),
            ("Obsidian Sentinel", 40, "golem"),
            ("Sulfur Bat", 8, "beast")
        ]
        
        for _ in range(15):
             ex, ey = random.choice(valid_floors)
             if abs(ex) < 5 and abs(ey) < 5: continue 
             
             etype = random.choice(enemies)
             m = Monster(name=etype[0], hp_current=etype[1], hp_max=etype[1], 
                         x=ex, y=ey, z=z, state="alive", family=etype[2])
             self._scale_monster(m, self._get_level_for_z(z))
             self.session.add(m)

        # BOSS: Magma Weaver
        boss_x, boss_y = max(valid_floors, key=lambda p: abs(p[0]) + abs(p[1]))
        if boss_x == 0 and boss_y == 0: boss_x, boss_y = 20, 20

        boss = Monster(name="Magma Weaver", hp_current=80, hp_max=80, 
                                 x=boss_x, y=boss_y, z=z, state="alive", family="boss",
                                 stats={"str": 16, "dex": 14, "int": 12})
        self._scale_monster(boss, 12)
        self.session.add(boss)
                                 
        # Boss Chest
        chest_loot = [{"id": "item_core", "name": "Igneous Core", "item_type": "material", "properties": {"icon": "🔥"}}]
        self.session.add(WorldObject(name="Obsidian Chest", obj_type="chest", x=boss_x, y=boss_y-1, z=z, properties={"loot": chest_loot}))

        self.session.commit()

    def generate_ice_dungeon(self, z):
        """Generate the Ice Dungeon (Z=4)."""
        print(f"Generator: Building Ice Dungeon at Z={z}...")

        # 1. Base
        floors = set()
        walls = set()
        hazards = set() 
        
        for x in range(-2, 3):
            for y in range(-2, 3):
                floors.add((x, y))

        width, height = 50, 50
        grid = {}
        for x in range(-width, width):
            for y in range(-width, width):
                grid[(x,y)] = 1 if (random.random() < 0.45) else 0 
        
        for x in range(-3, 4):
            for y in range(-3, 4):
                grid[(x,y)] = 0
                
        for _ in range(4):
            new_grid = grid.copy()
            for x in range(-width+1, width-1):
                for y in range(-width+1, width-1):
                    count = 0
                    for dx in [-1,0,1]:
                        for dy in [-1,0,1]:
                            if dx==0 and dy==0: continue
                            if grid.get((x+dx, y+dy), 1) == 1: count += 1
                    
                    if grid[(x,y)] == 1:
                        if count < 4: new_grid[(x,y)] = 0 
                    else:
                        if count > 5: new_grid[(x,y)] = 1 
            grid = new_grid
            
        accessible = set()
        queue = [(0,0)]
        visited = set([(0,0)])
        while queue:
            cx, cy = queue.pop(0)
            floors.add((cx, cy))
            
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = cx+dx, cy+dy
                if abs(nx) < width and abs(ny) < width:
                    if grid.get((nx, ny)) == 0 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        
        for x, y in floors:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x+dx, y+dy
                    if (nx, ny) not in floors:
                        walls.add((nx, ny))

        # 2. Hazards
        valid_floors = list(floors)
        for _ in range(20):
            cx, cy = random.choice(valid_floors)
            if abs(cx) < 5 and abs(cy) < 5: continue 
            hazards.add((cx, cy))
            for dx in range(-1, 2):
                if random.random() < 0.5:
                     hazards.add((cx+dx, cy))

        # 3. Commit
        for (x, y) in floors:
            t_type = "floor_ice"
            if (x, y) in hazards: t_type = "ice_spikes"
            
            if x == 0 and y == -2: t_type = "door_stone"
            
            self.session.add(MapTile(x=x, y=y, z=z, tile_type=t_type, is_visited=False)) 

        for (x, y) in walls:
            if x == 0 and y == -2: continue 
            self.session.add(MapTile(x=x, y=y, z=z, tile_type="wall_ice", is_visited=False))

        # 4. Monsters
        enemies = [
            ("Frost Wolf", 30, "beast"),    
            ("Ice Golem", 60, "golem"),     
            ("Cryomancer", 25, "undead"),   
            ("Ice Wraith", 20, "undead")    
        ]
        
        enemy_count = 0
        while enemy_count < 25:
             ex, ey = random.choice(valid_floors)
             if (ex, ey) in hazards: continue 
             if abs(ex) < 6 and abs(ey) < 6: continue
             
             etype = random.choice(enemies)
             m = Monster(name=etype[0], hp_current=etype[1], hp_max=etype[1], 
                         x=ex, y=ey, z=z, state="alive", family=etype[2])
             self._scale_monster(m, self._get_level_for_z(z))
             self.session.add(m)
             enemy_count += 1

        # BOSS: Frost Giant
        boss_x, boss_y = max(valid_floors, key=lambda p: abs(p[0]) + abs(p[1]))
        if boss_x == 0 and boss_y == 0: boss_x, boss_y = 20, 20

        boss = Monster(name="Frost Giant Jarl", hp_current=150, hp_max=150, 
                                 x=boss_x, y=boss_y, z=z, state="alive", family="boss",
                                 stats={"str": 20, "dex": 8, "con": 18, "int": 10})
        self._scale_monster(boss, 15)
        self.session.add(boss)
                                 
        # Boss Chest
        chest_loot = [{"id": "item_frost_shard", "name": "Glacial Shard", "item_type": "material", "properties": {"icon": "❄️"}}]
        self.session.add(WorldObject(name="Frozen Chest", obj_type="chest", x=boss_x, y=boss_y-1, z=z, properties={"loot": chest_loot}))

        self.session.commit()
