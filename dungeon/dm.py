from .database import get_session, Player, MapTile, Monster, InventoryItem, NPC, init_db
from .rules import roll_dice
from .combat import CombatSystem
from .ai_bridge import AIBridge
from sqlalchemy.orm.attributes import flag_modified
import threading
import queue

class DungeonMaster:
    def __init__(self):
        init_db() # Ensure tables exist
        self.session = get_session()
        self.prefetch_queue = queue.Queue()
        self.processing = set()
        self.combat = CombatSystem(self)
        self.ai = AIBridge() # Initialize AI Bridge
        
        self._initialize_world()

        # Start background worker
        threading.Thread(target=self._worker, daemon=True).start()
        print("DM: Connected to SQLite. Systems Online.")

    def _initialize_world(self):
        # Ensure player exists
        self.player = self.session.query(Player).first()
        if not self.player:
            print("DM: Creating new Hero...")
            self.player = Player(
                name="Generic Hero", 
                hp_current=20, hp_max=20,
                stats={"str": 14, "dex": 14, "con": 14, "int": 10, "wis": 10, "cha": 10},
                x=0, y=0, z=0
            )
            # Add default gear
            self.session.add(InventoryItem(name="Training Sword", slot="main_hand", is_equipped=True, player=self.player))
            self.session.add(InventoryItem(name="Cloth Tunic", slot="chest", is_equipped=True, player=self.player))
            self.session.add(self.player)
            
            # --- Tutorial Dungeon Generation ---
            floors = set()
            
            def add_rect(cx, cy, w, h):
                for x in range(cx - w//2, cx + w//2 + 1):
                    for y in range(cy - h//2, cy + h//2 + 1):
                        floors.add((x, y))

            def add_corridor_v(x, y1, y2):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    floors.add((x, y))
            
            def add_corridor_h(y, x1, x2):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    floors.add((x, y))

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
            for (x, y) in floors:
                self.session.add(MapTile(x=x, y=y, z=0, tile_type="floor", is_visited=True))

            # Walls (Perimeter)
            walls = set()
            for (x, y) in floors:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nx, ny = x+dx, y+dy
                        if (nx, ny) not in floors:
                            walls.add((nx, ny))
            
            for (x, y) in walls:
                self.session.add(MapTile(x=x, y=y, z=0, tile_type="wall", is_visited=True))
            
            # --- Populate Enemies (Total: 9 Skeletons + 1 Boss) ---
            enemies = [
                # Hallway / Grand Hall
                ("Decrepit Skeleton", 6, 0, 6),   # Corridor
                ("Skeleton Grunt", 10, -2, 12),   # Grand Hall
                ("Skeleton Grunt", 10, 2, 10),    # Grand Hall
                
                # West Wing (Armory)
                ("Armored Skeleton", 15, -10, 11), 
                ("Armored Skeleton", 15, -11, 12),
                
                # East Wing (Library)
                ("Rotted Skeleton", 8, 10, 11),
                ("Skeleton Mage", 12, 11, 12),
                
                # Barracks (The Horde)
                ("Skeleton Warrior", 18, -2, 20),
                ("Skeleton Warrior", 18, 2, 20),
                
                # Jail Guard (Boss)
                ("Dungeon Warden", 30, 0, 28)      # Guarding the door to cell
            ]
            
            for name, hp, ex, ey in enemies:
                self.session.add(Monster(name=name, hp_current=hp, hp_max=hp, x=ex, y=ey, z=0, state="alive"))

            # Elara is at 0, 30 (Back of Jail Room)
            self.session.add(NPC(
                name="Elara", 
                location="Dungeon Cell", 
                x=0, y=30, z=0,
                persona_prompt="You are Elara, a scared but hopeful villager girl locked in a cage."
            ))

            self.session.commit()

    def reset_game(self):
        """Wipe database and restart."""
        print("DM: RESETTING GAME...")
        # Delete all data
        self.session.query(InventoryItem).delete()
        self.session.query(Monster).delete()
        self.session.query(MapTile).delete()
        self.session.query(Player).delete()
        self.session.query(NPC).delete() 
        self.session.commit()
        
        # Re-init
        self._initialize_world()
        print("DM: Game Reset Complete.")


    def save(self):
        """Commit current transaction."""
        try:
            self.session.commit()
        except Exception as e:
            print(f"DM Save Error: {e}")
            self.session.rollback()

    def get_player_position(self):
        return [self.player.x, self.player.y, self.player.z]

    def move_player(self, dx, dy):
        # 0. Check Combat
        active_combat = self.session.query(Monster).filter_by(state="combat", is_alive=True).first()
        if active_combat:
             return [self.player.x, self.player.y, self.player.z], "Combat is active! You must fight or flee."

        new_x = self.player.x + dx
        new_y = self.player.y + dy
        new_z = self.player.z
        
        # 1. Collision Check (DB Query)
        tile = self.session.query(MapTile).filter_by(x=new_x, y=new_y, z=new_z).first()
        if not tile or tile.tile_type != "floor":
            # Auto-generate wall if unknown
            if not tile:
                tile = MapTile(x=new_x, y=new_y, z=new_z, tile_type="wall", is_visited=True)
                self.session.add(tile)
                self.session.commit()
            elif not tile.is_visited:
                tile.is_visited = True
                self.session.commit()
            
            return [self.player.x, self.player.y, self.player.z], "You bump into a wall."

        # 1.5 Occupied Check (Enemies)
        enemy = self.session.query(Monster).filter_by(x=new_x, y=new_y, z=new_z, is_alive=True).first()
        if enemy:
             pass # Stay at current pos
        else:
            # Move
            self.player.x = new_x
            self.player.y = new_y
            self.update_visited(new_x, new_y, new_z)
            self.save()

        # 2. Check for Combat Trigger
        target_pos = [new_x, new_y, new_z] if not enemy else [self.player.x, self.player.y, self.player.z]
        
        if enemy:
             msg = self.combat.start_combat(enemy)
             return target_pos, msg
        
        return [self.player.x, self.player.y, self.player.z], None

    def update_visited(self, cx, cy, cz):
        tiles = self.session.query(MapTile).filter(
            MapTile.x.between(cx-2, cx+2),
            MapTile.y.between(cy-2, cy+2),
            MapTile.z == cz
        ).all()
        
        for t in tiles:
            if not t.is_visited:
                t.is_visited = True
        self.session.commit()

    def prefetch_surroundings(self, center_pos):
        # Optimization: User requested to stop prefetching empty tiles
        pass 

    def _worker(self):
        worker_session = get_session() # Dedicated session
        while True:
            xyz = self.prefetch_queue.get()
            try:
                x, y, z = xyz
                self._generate_description(x, y, z, session=worker_session)
            except Exception as e:
                print(f"Worker Error: {e}")
                worker_session.rollback()
            finally:
                self.prefetch_queue.task_done()
                pos_key = f"{x},{y},{z}"
                if pos_key in self.processing:
                    self.processing.remove(pos_key)

    def _generate_description(self, x, y, z, session=None):
        sess = session if session else self.session
        
        # 1. Fetch Tile
        tile = sess.query(MapTile).filter_by(x=x, y=y, z=z).first()
        if not tile: return "Void."
        
        # 2. Check Cache
        if tile.meta_data and tile.meta_data.get("description"):
            return tile.meta_data["description"]

        # 3. Check for Interesting Things (Monsters/Corpses)
        # Lazy import to ensure availability in this scope if needed
        from .database import Monster 
        
        has_monster = sess.query(Monster).filter_by(x=x, y=y, z=z, is_alive=True).first()
        has_corpse = sess.query(Monster).filter_by(x=x, y=y, z=z, is_alive=False).first()

        text = "A cold, damp corridor of hewn stone."
        
        if has_monster or has_corpse:
             # Generated unique description only for interactions
            entity_name = has_monster.name if has_monster else (f"dead {has_corpse.name}" if has_corpse else "something")
            prompt = f"The player is at ({x}, {y}). There is a {entity_name} here. Describe the scene briefly and ominously."
            text = self.ai.chat(prompt, persona="dm")
        
        # 4. Save to DB
        if not tile.meta_data: tile.meta_data = {}
        tile.meta_data["description"] = text
        flag_modified(tile, "meta_data")
        sess.commit()
            
        return text

    def describe_current_room(self):
        x, y, z = self.player.x, self.player.y, self.player.z
        self.prefetch_surroundings([x,y,z])
        return self._generate_description(x, y, z)
    
    def get_state_dict(self):
        """Return the JSON-serializable state for the frontend."""
        visited_tiles = self.session.query(MapTile).filter_by(is_visited=True).all()
        map_data = {f"{t.x},{t.y},{t.z}": t.tile_type for t in visited_tiles}
        
        monsters = self.session.query(Monster).all()
        enemy_list = []
        corpse_list = []
        for m in monsters:
            if m.is_alive:
                enemy_list.append({"xyz": [m.x, m.y, m.z], "hp": m.hp_current, "max_hp": m.hp_max, "name": m.name})
            else:
                 corpse_list.append({"xyz": [m.x, m.y, m.z], "name": f"Dead {m.name}"})

        # NPCs
        npcs = self.session.query(NPC).filter(NPC.x != None).all()
        npc_list = []
        for n in npcs:
            npc_list.append({"xyz": [n.x, n.y, n.z], "name": n.name})

        # Check actual combat state
        active_combat = self.session.query(Monster).filter_by(state="combat", is_alive=True).first()
        combat_state = {"active": False}
        if active_combat:
            combat_state = {
                "active": True,
                "enemy_name": active_combat.name,
                "enemy_hp": active_combat.hp_current
            }

        return {
            "player": {
                "xyz": [self.player.x, self.player.y, self.player.z],
                "stats": self.player.stats,
                "hp": self.player.hp_current,
                "max_hp": self.player.hp_max,
                "inventory": [[i.name, i.slot] for i in self.player.inventory]
            },
            "world": {
                "map": map_data,
                "enemies": enemy_list,
                "npcs": npc_list
            },
            "corpses": corpse_list,
            "combat": combat_state 
        }
