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
            for y in range(-20, 21):
                t_type = "grass" # Explicitly grass type for frontend rendering
                if abs(x) == 20 or abs(y) == 20: 
                    t_type = "wall" # Town border
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
        # For now, current JSON coords might be slightly off (Elder is at 2,2 which is now grass).
        # JSON needs update to match these new building locations.

