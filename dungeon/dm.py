from .database import get_session, Player, MapTile, Monster, InventoryItem, NPC, init_db
from .rules import roll_dice
from .combat import CombatSystem
from .ai_bridge import AIBridge
from .generator import LevelBuilder
from .dialogue import DialogueSystem
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
        self.dialogue = DialogueSystem(self)
        
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
            builder = LevelBuilder(self.session)
            builder.generate_tutorial_dungeon(self.player)

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
        """Clean robust movement logic."""
        # 0. Check Combat
        active_combat = self.session.query(Monster).filter_by(state="combat", is_alive=True).first()
        if active_combat:
             return [self.player.x, self.player.y, self.player.z], "Combat is active! You must fight or flee."

        # 1. Calculate Target
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        new_z = self.player.z
        
        print(f"DM: Move Request -> ({new_x}, {new_y}, {new_z})")

        # 2. Check Map Collision
        tile = self.session.query(MapTile).filter_by(x=new_x, y=new_y, z=new_z).first()
        
        # Auto-create wall if void (safety)
        if not tile:
            # If we are in 'void', assume wall? Or allow generation hook?
            # For now, simplistic wall.
            if new_z == 0: # Dungeon
                 tile = MapTile(x=new_x, y=new_y, z=new_z, tile_type="wall", is_visited=True)
                 self.session.add(tile)
                 self.session.commit()
                 return [self.player.x, self.player.y, self.player.z], "You bump into a dark wall."
            # Town bounds handled by generation usually
            return [self.player.x, self.player.y, self.player.z], "The path is blocked."

        if tile.tile_type != "floor" and tile.tile_type != "floor_wood" and tile.tile_type != "door" and tile.tile_type != "open_door":
             # Mark visited so user sees the wall they hit
             if not tile.is_visited:
                 tile.is_visited = True
                 self.session.commit()
             return [self.player.x, self.player.y, self.player.z], "You bump into a wall."

        # 3. Check Door Transition (Tile Event)
        if tile.tile_type == "door":
             # Hacky Secret Door check
             print("DM: Door interaction")
             if new_z == 0 and new_x == 2 and new_y == 30:
                 self.teleport_player(0, 0, 1) # Town
                 return [0, 0, 1], "*** You emerge into Oakhaven! ***"
             
             # Normal door (open it?)
             tile.tile_type = "open_door" # Visual change?
             # Treat as floor for now
        
        # 4. Check Monsters (Combat Trigger)
        enemy = self.session.query(Monster).filter_by(x=new_x, y=new_y, z=new_z, is_alive=True).first()
        if enemy:
             msg = self.combat.start_combat(enemy)
             return [self.player.x, self.player.y, self.player.z], msg

        # 5. Check NPCs (Blocking? Or Chat Trigger?)
        # Let's interact on bump for now, or just block
        npc = self.session.query(NPC).filter_by(x=new_x, y=new_y, z=new_z).first()
        if npc:
             return [self.player.x, self.player.y, self.player.z], f"You bump into {npc.name}."

        # 6. Success - Commit Move
        self.player.x = new_x
        self.player.y = new_y
        
        # 7. Update Visibility
        self.update_visited(new_x, new_y, new_z)
        self.save()
        
        # 8. Return Narrative (Static + Dynamic Events)
        desc = self._generate_description(new_x, new_y, new_z) or ""
        
        # Check for proximity events (Greetings)
        # Check adjacent tiles (including diagonals? No, usually Manhattan or Chebyshev 1)
        nearby_npcs = self.session.query(NPC).filter(
            NPC.x.between(new_x-2, new_x+2),
            NPC.y.between(new_y-2, new_y+2),
            NPC.z == new_z
        ).all()
        
        for n in nearby_npcs:
            dist = max(abs(n.x - new_x), abs(n.y - new_y)) # Chebyshev
            if dist <= 2: # "Close" range
                greeting = ""
                if "Elara" in n.name: greeting = "Elara calls out: 'Over here! I need your help!'"
                elif "Gareth" in n.name: greeting = "Gareth hails you: 'Well met, traveler.'"
                elif "Elder" in n.name: greeting = "The Elder waves a weary hand."
                
                if greeting:
                    desc += f" <br><span style='color: #fdcb6e;'>{greeting}</span>"
        
        return [new_x, new_y, new_z], desc

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
        
        # Standard Static Descriptions
        if z == 1:
            if x == 0 and y == 0: return "Town Square"
            return "Oakhaven Details"
        else:
            # Dungeon
            return "Dungeon Corridor"

    def investigate_room(self):
        """Active Skill: Analyze the current location in detail using AI."""
        x, y, z = self.player.x, self.player.y, self.player.z
        
        # 1. Fetch Context & Nearby Entities (Radius 5)
        # We want to return these to the frontend to populate the "Nearby" tab
        nearby_entities = []
        
        # Monsters
        from .database import Monster
        monsters = self.session.query(Monster).filter(
            Monster.x.between(x-5, x+5),
            Monster.y.between(y-5, y+5),
            Monster.z == z,
            Monster.is_alive == True
        ).all()
        
        for m in monsters:
            dist = abs(m.x - x) + abs(m.y - y)
            nearby_entities.append({
                "name": m.name, 
                "type": "monster", 
                "dist": dist,
                "status": f"HP: {m.hp_current}/{m.hp_max}"
            })
            
        # Corpses
        corpses = self.session.query(Monster).filter(
            Monster.x.between(x-5, x+5),
            Monster.y.between(y-5, y+5),
            Monster.z == z,
            Monster.is_alive == False
        ).all()
        for c in corpses:
             nearby_entities.append({"name": f"Dead {c.name}", "type": "corpse", "dist": abs(c.x-x)+abs(c.y-y), "status": "Lootable"})

        # 2. Build Prompt
        context = []
        if z == 1: context.append("Location: Oakhaven Town (Outdoors, Night)")
        else: context.append("Location: Dungeon (Underground, Dark)")
        
        if monsters: context.append(f"Threats: {', '.join([m.name for m in monsters])}")
        if corpses: context.append(f"Objects: {', '.join([c.name for c in corpses])}")
        
        # 3. Call AI
        prompt = f"The player investigates the area at {x},{y}. Describe what they see in vivid detail, focusing on the threats or objects found."
        desc = self.ai.chat(prompt, persona="dm", context=", ".join(context))
        
        return {"narrative": desc, "entities": nearby_entities}

    def describe_current_room(self):
        # Legacy fallback or quick look
        return self._generate_description(self.player.x, self.player.y, self.player.z)
    
    def get_state_dict(self):
        """Return a JSON-serializable state for the frontend."""
        map_data = {}
        px, py, pz = self.player.x, self.player.y, self.player.z
        
        # 1. Fetch visible tiles
        # ... (Assuming tile fetching handles Z via player.z, wait, 'visibleMap' logic uses Z?)
        # Let's trust tile fetching for now.
        visited_tiles = self.session.query(MapTile).filter_by(is_visited=True).all()
        map_data = {f"{t.x},{t.y},{t.z}": t.tile_type for t in visited_tiles}
        
        # Enemies
        # Filter by current Z
        monsters = self.session.query(Monster).filter_by(is_alive=True, z=pz).all()
        enemy_list = []
        for m in monsters:
            if m.state == "combat":
                 enemy_list.append({"xyz": [m.x, m.y, m.z], "hp": m.hp_current, "max_hp": m.hp_max, "name": m.name})
            else:
                 enemy_list.append({"xyz": [m.x, m.y, m.z], "hp": m.hp_current, "max_hp": m.hp_max, "name": m.name})

        # Corpses
        # Filter by current Z
        # Note: Original code might have iterated monsters and checked IS_ALIVE=False? 
        # Let's check original logic.
        # It iterated `monsters` logic.
        # Actually standard query was `query(Monster).filter(Monster.is_alive == True)`.
        # I need to separate corpse query if it was separate.
        # Checking existing code:
        # It had `corpse_list`?
        
        corpses = self.session.query(Monster).filter_by(is_alive=False, z=pz).all()
        corpse_list = []
        for m in corpses:
             corpse_list.append({"xyz": [m.x, m.y, m.z], "name": f"Dead {m.name}"})

        # NPCs
        npcs = self.session.query(NPC).filter(NPC.x != None, NPC.z == pz).all()
        npc_list = []
        for n in npcs:
            # Simple Image Mapping
            img = "player.png"
            if "Seraphina" in n.name: img = "seraphina.png"
            elif "Elara" in n.name: img = "elara.png"
            elif "Gareth" in n.name: img = "warrior2.png"
            elif "Elder" in n.name: img = "elder.png"
            
            npc_list.append({"xyz": [n.x, n.y, n.z], "name": n.name, "id": n.id, "asset": img})
            
        # Check actual combat state
        active_combat = self.session.query(Monster).filter_by(state="combat", is_alive=True).first()
        # Ensure combat target is on same level? Or reset combat if changing level?
        # If I flee to town, combat breaks.
        # Logic for fleeing: `teleport_player` should probably clear combat.
        
        combat_state = {"active": False}
        if active_combat and active_combat.z == pz:
            combat_state = {
                "active": True,
                "enemy_name": active_combat.name,
                "enemy_hp": active_combat.hp_current
            }

        # Interactables (Generic)
        secrets = []
        
        # 1. Fetch nearby tiles
        nearby_tiles = self.session.query(MapTile).filter(
            MapTile.x.between(self.player.x - 1, self.player.x + 1),
            MapTile.y.between(self.player.y - 1, self.player.y + 1),
            MapTile.z == self.player.z
        ).all()
        
        # 2. Check for Interactables
        for t in nearby_tiles:
            # Legacy/Hardcoded fix for our secret door at (2, 30)
            if t.x == 2 and t.y == 30 and not t.meta_data:
                 t.meta_data = {"interactable": True, "interact_name": "Suspicious Wall", "secret_id": "secret_door_1"}
                 flag_modified(t, "meta_data") # Save it
            
            md = t.meta_data or {}
            
            if md.get("interactable"):
                # If it's a secret door and already open, skip
                if md.get("secret_id") and t.tile_type == "door":
                    continue
                
                secrets.append({
                    "id": md.get("secret_id") or f"tile_{t.x}_{t.y}",
                    "name": md.get("interact_name", "Interesting Object"),
                    "type": "secret" 
                })

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
                "npcs": npc_list,
                "secrets": secrets
            },
            "corpses": corpse_list,
            "combat": combat_state 
        }

    def player_interact(self, action, target_type, target_index):
        """Handle interactions like looting."""
        if action == "loot" and target_type == "corpse":
            # 1. Find the corpse (We need to map index to DB ID, or closest corpse)
            # For simplicity, we assume target_index corresponds to the SORTED list of dead monsters.
            # But relying on index is risky if list changes.
            # Better: Find closest corpse.
            
            px, py, pz = self.player.x, self.player.y, self.player.z
            corpses = self.session.query(Monster).filter_by(is_alive=False, z=pz).all()
            
            # Filter by proximity (Radius 1)
            nearby = [c for c in corpses if abs(c.x - px) <= 1 and abs(c.y - py) <= 1]
            
            if not nearby:
                return "There is nothing here to loot."
            
            # Loot the first one found
            target = nearby[0]
            
            if target.state == "looted":
                return "The corpse is empty."
            
            # Generate Loot
            loot_roll = roll_dice(20)
            item_name = "Rusty Dagger"
            slot = "main_hand"
            
            if loot_roll > 15:
                item_name = "Steel Longsword"
                slot = "main_hand"
            elif loot_roll > 10:
                item_name = "Health Potion"
                slot = "consumable"
            elif loot_roll > 5:
                item_name = "Leather Cap"
                slot = "head"
            
            # Add to Inventory
            self.session.add(InventoryItem(name=item_name, slot=slot, player=self.player))
            
            # Mark Looted
            target.state = "looted"
            self.session.commit()
            
            return f"You search the {target.name} and find a {item_name}!"

        elif action == "talk" and target_type == "npc":
            # 1. Find NPC
            px, py, pz = self.player.x, self.player.y, self.player.z
            nearby = self.session.query(NPC).filter(
                NPC.x.between(px-1, px+1),
                NPC.y.between(py-1, py+1),
                NPC.z == pz
            ).all()
            
            if not nearby:
                return "No one to talk to."
            
            target = nearby[0] # Assume interacting with first
            
            # Generate AI Dialogue
            prompt = f"The player says hello to {target.name} ({target.location}, {target.persona_prompt}). Respond in character."
            response = self.ai.chat(prompt, persona="npc")
            
            # Save interaction state? (Optional, maybe increment 'talk_count')
            
            
            return f"{target.name} says: \"{response}\""
            
        elif action == "inspect" and target_type == "secret":
            if target_index == "secret_door_1":
                 # Trigger Door Reveal at (2, 30)
                 door_tile = self.session.query(MapTile).filter_by(x=2, y=30, z=0).first()
                 if door_tile:
                     door_tile.tile_type = "door"
                     door_tile.is_visited = True
                     flag_modified(door_tile, "tile_type")
                 else:
                     # Create it
                     new_door = MapTile(x=2, y=30, z=0, tile_type="door", is_visited=True)
                     self.session.add(new_door)

                 # Elara Comment & State Update
                 elara = self.session.query(NPC).filter(NPC.name.like("%Elara%")).first()
                 elara_msg = ""
                 if elara:
                      elara_msg = "\n\nElara: 'You found it! Quick, let's go!'"
                      q_state = elara.quest_state or {}
                      q_state["status"] = "escorting"
                      elara.quest_state = q_state
                      flag_modified(elara, "quest_state")
                 
                 self.session.commit()
                 return f"You investigate the crack and find a hidden latch. The wall grinds open!{elara_msg}"

        return "Invalid action."

    def chat_with_npc(self, npc_index, message):
        """Handle persistent chat with an NPC."""
        return self.dialogue.chat_with_npc(npc_index, message)

    def teleport_player(self, x, y, z):
        """Move player to a new zone/level."""
        self.player.x = x
        self.player.y = y
        self.player.z = z
        self.session.commit()
        
        # Check if map exists, if not generate
        if not self.session.query(MapTile).filter_by(z=z).first():
            if z == 1:
                self._generate_town(z)
        
        # Force visit surrounding
        self.update_visited(x, y, z)
        
        # Handle Followers (Elara)
        if z == 1:
             elara = self.session.query(NPC).filter(NPC.name.like("%Elara%")).first()
             if elara:
                  qs = elara.quest_state or {}
                  if qs.get("status") == "escorting":
                       elara.x = x + 1
                       elara.y = y
                       elara.z = z
                       elara.location = "Oakhaven Town"
                       qs["status"] = "completed"
                       elara.quest_state = qs
                       flag_modified(elara, "quest_state")
                       self.session.commit()

    def _generate_town(self, z):
        """Generate the Oakhaven Town map."""
        builder = LevelBuilder(self.session)
        builder.generate_town(z)
