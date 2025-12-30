import json
import os
from .database import MapTile, Monster, NPC, InventoryItem, WorldObject
from sqlalchemy.orm.attributes import flag_modified

class LevelBuilder:
    def __init__(self, session):
        self.session = session
        self.floors = set()
        self.walls = set()

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
        import random
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
            self.session.add(Monster(name=name, hp_current=hp, hp_max=hp, x=ex, y=ey, z=0, state="alive"))

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
            # Walls & Floor
            for i in range(x, x+w):
                for j in range(y, y+h):
                    t_type = floor
                    # Walls
                    if i == x or i == x+w-1 or j == y or j == y+h-1:
                        t_type = wall
                    
                    self.session.add(MapTile(x=i, y=j, z=z, tile_type=t_type, is_visited=True))
            
            # Door
            dx, dy = x + w//2, y + h - 1 # Default bottom
            if door_side == "top": dy = y
            elif door_side == "left": dx, dy = x, y + h//2
            elif door_side == "right": dx, dy = x + w-1, y + h//2
            
            # Ensure door is walkable (find existing wall and replace/mark)
            # Actually, we rely on DB upsert or just overwrite logic in session.add if not unique constraint?
            # session.add will fail if PK exists unless we merge.
            # For simplicity in this generator, we assume we aren't overlapping yet or use merge.
            # But we are using session.add which might duplicate if we aren't careful? 
            # Actually sqlite primary key is composite? No, id is PK. (x,y,z) is unique constraint usually.
            
            # Better approach: We query first or we rely on the fact we haven't built there.
            # But the base "grass" loop runs first. So we need to update existing tiles.
            
            # Since we iterate distinct ranges, let's just do an UPSERT style logic or query-update.
            pass # We'll do logic in main loop

        # 1. Base Grass Layer (-20 to 20)
        # We'll use a dictionary to track tiles before committing to DB to handle layers/updates easily.
        tiles = {} # (x,y) -> type

        for x in range(-20, 21):
            for y in range(-23, 22): # Expanded Range for Moat (-22)
                t_type = "grass" # Explicitly grass type for frontend rendering
                # Borders
                if abs(x) == 20 or abs(y) == 20: 
                    t_type = "wall" # Town border
                    
                    # North Gate (Fortified Gatehouse)
                    if y == -20:
                        # Moat (Outer)
                        if abs(x) <= 6:
                            tiles[(x, -21)] = "water"
                            tiles[(x, -22)] = "water" # Double wide moat

                        # Bridge
                        tiles[(0, -21)] = "bridge"
                        tiles[(0, -22)] = "bridge"

                        # Gate Towers
                        if abs(x) <= 2:
                             if x == 0: t_type = "door"
                             else: t_type = "wall_grey" # Heavy Towers

                # North Gate (Inner Keep - "Massive" feel)
                if y == -19 and abs(x) <= 2:
                    if x == 0: t_type = "floor" 
                    else: t_type = "wall_grey" 

                tiles[(x,y)] = t_type

        # 2. Structures
        
        # Helper to apply structure to 'tiles' dict
        def place_structure(lx, ly, w, h, floor="floor_wood", wall="wall_house", door_pos=None):
            for i in range(lx, lx+w):
                for j in range(ly, ly+h):
                    tiles[(i,j)] = floor
                    if i == lx or i == lx+w-1 or j == ly or j == ly+h-1:
                        tiles[(i,j)] = wall
            
            if door_pos:
                tiles[door_pos] = "door"

        # Town Hall (North Center) - Elder's Home
        # 8x6 building
        place_structure(-4, 4, 9, 7, door_pos=(0, 4)) 
        
        # Blacksmith (East) - Gareth (7x8)
        place_structure(8, 6, 8, 7, door_pos=(8, 9))
        
        # Alchemist (West) - Seraphina (6x6)
        place_structure(-14, 6, 7, 7, door_pos=(-8, 9))

        # --- New Decorations ---
        tiles[(0, 0)] = "fountain"      # Centerpiece
        
        # Lamps
        tiles[(-2, -2)] = "street_lamp"
        tiles[(2, -2)] = "street_lamp"
        tiles[(-2, 2)] = "street_lamp"
        tiles[(2, 2)] = "street_lamp"
        
        # Flowers
        tiles[(1, 4)] = "flower_pot"
        tiles[(-1, 4)] = "flower_pot"
        tiles[(-8, 8)] = "flower_pot"   # Alchemist door side
        tiles[(-8, 10)] = "flower_pot"
        
        # Cargo (Barrels/Crates)
        tiles[(9, 10)] = "barrel"       # Blacksmith
        tiles[(9, 11)] = "crate"
        tiles[(8, 5)] = "barrel"        # Corner
        
        # Quest Resources: Rocks (East Outskirts)
        tiles[(12, 8)] = "rock"
        tiles[(13, 9)] = "rock"
        tiles[(12, 10)] = "rock"
        
        # Quest Resources: Alchemist Garden (West)
        tiles[(-10, 5)] = "flower_pot" # Side garden
        tiles[(-11, 5)] = "flower_pot"
        tiles[(-10, 4)] = "flower_pot"
        
        # Signpost
        tiles[(0, -2)] = "signpost"

        # Interiors
        tiles[(12, 9)] = "anvil" 
        tiles[(13, 9)] = "anvil" 

        # Alchemist (West) - Seraphina
        # 6x6 building
        place_structure(-14, 6, 7, 7, door_pos=(-8, 9)) # Door on Right
        tiles[(-12, 7)] = "shelf"
        tiles[(-11, 7)] = "shelf"
        
        # 3. Decor
        # Pond
        for x in range(10, 16):
            for y in range(-12, -8):
                tiles[(x,y)] = "water"
                
        # Trees (Random scatter)
        import random
        for _ in range(30):
            tx = random.randint(-18, 18)
            ty = random.randint(-18, 18)
            # Only put trees on grass
            if tiles.get((tx,ty)) == "grass":
                tiles[(tx,ty)] = "tree"

        # 4. Commit to DB
        for (pos, t_type) in tiles.items():
            self.session.add(MapTile(x=pos[0], y=pos[1], z=z, tile_type=t_type, is_visited=True))
        
        # Update NPC Locations to match new interiors
        # Elder -> Town Hall (0, 7)
        # Gareth -> Smithy (11, 8)  <-- Moved next to Forge (12,9)
        # Seraphina -> Alchemist (-11, 9)
        # This is handled in npcs.json primarily, but if I modified it here I'd need to update json.
        # Update NPC Locations to match new interiors
        # ...
        
        # Spawn NPCs from JSON
        self._load_npcs_from_file(z)

    def generate_forest(self, z):
        """Generate the North Forest (Z=2)."""
        print(f"Generator: Building North Forest at Z={z}...")
        
        # 1. Base Grass (Huge Area: 60x60)
        width, height = 60, 60
        tiles = {}
        
        import random
        from .rules import roll_dice
        
        for x in range(-width//2, width//2):
            for y in range(-height//2, height//2):
                tiles[(x,y)] = "grass"
                
                # Heavy Forest Density (Updated: Reduced by 25% -> ~0.26)
                if random.random() < 0.26:
                    tiles[(x,y)] = "tree"

                # Ore Deposits (Iron)
                elif random.random() < 0.02: # 2% chance for free rock
                    tiles[(x,y)] = "rock"

                # Herb Deposits (Mystic Herbs)
                elif random.random() < 0.03: # 3% chance
                    tiles[(x,y)] = "herb"

        # 2. The Lake (North East)
        # Circle at (15, -15) radius 8
        cx, cy = 15, -15
        radius = 8
        for x in range(cx - radius, cx + radius):
            for y in range(cy - radius, cy + radius):
                if (x-cx)**2 + (y-cy)**2 <= radius**2:
                    tiles[(x,y)] = "water"

        # 3. Main Road (South to North)
        # From (0, 30) aka South Entrance to (0, -25)
        for y in range(-25, 30):
            for x in range(-2, 3):
                tiles[(x,y)] = "floor" # Dirt path
                
        # Town Gate (South Exit)
        tiles[(0, 29)] = "door" 
        tiles[(-1, 29)] = "wall"
        tiles[(1, 29)] = "wall"
        
        # 4. Dungeon Entrances (Elemental)
        
        # Helper for themed entrance
        def place_entrance(cx, cy, tile_type, decor, name):
            # 3x3 Mountain Structure with door at bottom-center (cx, cy)
            # Grid relative to Door (0,0):
            # Top Row: y-2
            # Mid Row: y-1
            # Bot Row: y (Door)
            
            structure = [
                # Top Row
                (-1, -2, "mtn_tl"), (0, -2, "mtn_tm"), (1, -2, "mtn_tr"),
                # Mid Row
                (-1, -1, "mtn_ml"), (0, -1, "mtn_mm"), (1, -1, "mtn_mr"),
                # Bot Row
                (-1, 0, "mtn_bl"), (0, 0, "door_stone"), (1, 0, "mtn_br")
            ]
            
            for (dx, dy, code) in structure:
                tiles[(cx+dx, cy+dy)] = code
                
            # Surround with decor (slightly wider radius to blend)
            for dx in range(-2, 3):
                for dy in range(-3, 2):
                    # Skip the structure itself
                    if abs(dx) <= 1 and -2 <= dy <= 0: continue
                    
                    if (cx+dx, cy+dy) not in tiles:
                         tiles[(cx+dx, cy+dy)] = decor

        # Fire Dungeon (South West - Volcanic Patch)
        place_entrance(-15, 15, "door", "lava", "Fire Dungeon")
        
        # Ice Dungeon (North West - Frozen Patch)
        place_entrance(-15, -20, "door", "ice", "Ice Dungeon")
        
        # Earth Dungeon (North East - Rocky/Muddy)
        place_entrance(20, -20, "door", "rock", "Earth Dungeon")
        
        # Air Dungeon (South East - Cloudy/Void?)
        place_entrance(20, 15, "door", "void", "Air Dungeon")
        
        # 5. Commit to DB
        game_map = []
        for (pos, t_type) in tiles.items():
            game_map.append(MapTile(x=pos[0], y=pos[1], z=z, tile_type=t_type, is_visited=True)) # Forest is open, auto-visited? Or Fog of War?
            # Let's keep it Fog of War: is_visited=False
            # But the path should be visible?
        
        # Auto-visit the starting path for convenience
        for m in game_map:
            if m.tile_type == "floor": 
                m.is_visited = True
            else:
                m.is_visited = False
            self.session.add(m)
            
        # 6. Spawns (Wolves, Bears)
        beasts = ["Dire Wolf", "Forest Bear", "Knife Goblin"]
        occupied_spawns = set()
        
        # Increased by 25%: 15 -> ~19
        count = 0
        attempts = 0
        while count < 19 and attempts < 200:
             attempts += 1
             bx = random.randint(-25, 25)
             by = random.randint(-25, 25)
             if (bx, by) in occupied_spawns: continue

             # Valid spawn logic: Grass or Floor (road ambushes)
             t_type = tiles.get((bx, by))
             if t_type in ["grass", "floor"]:
                 occupied_spawns.add((bx, by))
                 name = random.choice(beasts)
                 hp = 10 if "Goblin" in name else 25
                 self.session.add(Monster(name=name, hp_current=hp, hp_max=hp, x=bx, y=by, z=z, state="alive"))
                 count += 1

        # 7. Elemental Bosses (Guardians)
        bosses = [
            {"name": "Fire Guardian", "x": -15, "y": 15, "hp": 100},
            {"name": "Ice Guardian", "x": -15, "y": -20, "hp": 100},
            {"name": "Earth Guardian", "x": 20, "y": -20, "hp": 120},
            {"name": "Air Guardian", "x": 20, "y": 15, "hp": 80}
        ]
        
        for b in bosses:
            self.session.add(Monster(name=b["name"], hp_current=b["hp"], hp_max=b["hp"], 
                                     x=b["x"], y=b["y"], z=z, state="alive", 
                                     stats={"str": 14, "dex": 12, "int": 10})) # Boost str for bosses

        self.session.commit()

    def generate_fire_dungeon(self, z):
        """Generate the Fire Dungeon (Z=3)."""
        print(f"Generator: Building Fire Dungeon at Z={z}...")
        import random

        # 1. Base: Volcanic Floor
        # Irregular Cave Shape using Random Walk
        floors = set()
        walkers = [(0, 0)]
        
        # Entrance Room
        for x in range(-3, 4):
            for y in range(-3, 4):
                floors.add((x, y))

        # Dig Tunnels
        for _ in range(400): # Steps
             new_walkers = []
             for wx, wy in walkers:
                 dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                 nx, ny = wx+dx, wy+dy
                 if abs(nx) < 30 and abs(ny) < 30: # Bounds
                     floors.add((nx, ny))
                     if random.random() < 0.1: new_walkers.append((nx, ny)) # Branch
                     else: new_walkers.append((nx, ny)) # Move
             walkers = new_walkers
        
        # 2. Convert to MapTiles
        for (x, y) in floors:
            t_type = "floor_volcanic"
            # Lava Pools
            if random.random() < 0.05 and abs(x) > 5: t_type = "lava"
            # Steam Vents
            elif random.random() < 0.02 and abs(x) > 5: t_type = "steam_vent"
            
            self.session.add(MapTile(x=x, y=y, z=z, tile_type=t_type, is_visited=False)) # Fog of war

        # Walls (Surround floors)
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
             if abs(ex) < 5 and abs(ey) < 5: continue # Safe zone
             
             etype = random.choice(enemies)
             self.session.add(Monster(name=etype[0], hp_current=etype[1], hp_max=etype[1], 
                                      x=ex, y=ey, z=z, state="alive", family=etype[2]))

        # BOSS: Magma Weaver (at end of longest path approx)
        boss_x, boss_y = max(valid_floors, key=lambda p: abs(p[0]) + abs(p[1]))
        self.session.add(Monster(name="Magma Weaver", hp_current=80, hp_max=80, 
                                 x=boss_x, y=boss_y, z=z, state="alive", family="boss",
                                 stats={"str": 16, "dex": 14, "int": 12}))
                                 
        # Boss Chest
        chest_loot = [{"id": "item_core", "name": "Igneous Core", "item_type": "material", "properties": {"icon": "🔥"}}]
        self.session.add(WorldObject(name="Obsidian Chest", obj_type="chest", x=boss_x, y=boss_y-1, z=z, properties={"loot": chest_loot}))

        self.session.commit()
