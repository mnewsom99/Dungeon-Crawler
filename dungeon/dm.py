from .database import get_session, Player, MapTile, Monster, InventoryItem, NPC, init_db, WorldObject
from .rules import roll_dice, get_skill_level, award_skill_xp
from .combat import CombatSystem
from .ai_bridge import AIBridge
from .generator import LevelBuilder
from .dialogue import DialogueSystem
from .inventory_system import InventorySystem
from sqlalchemy.orm.attributes import flag_modified
import threading
import queue

class DungeonMaster:
    def __init__(self):
        init_db() # Ensure tables exist
        self.session = get_session()
        self.inventory = InventorySystem(self.session)
        self.prefetch_queue = queue.Queue()
        self.processing = set()
        self.combat = CombatSystem(self)
        self.ai = AIBridge() # Initialize AI Bridge
        self.dialogue = DialogueSystem(self)
        
        self._initialize_world()

    def equip_item(self, item_id):
        return self.inventory.equip_item(self.player, item_id)
        
    def unequip_item(self, item_id):
        return self.inventory.unequip_item(self.player, item_id)

    def use_item(self, item_id):
        return self.inventory.use_item(self.player, item_id)

    def take_loot(self, corpse_id, loot_id):
        return self.inventory.take_loot(self.player, corpse_id, loot_id)

    def get_skill_level(self, skill):
        # Proxy to rules
        return get_skill_level(self.player, skill)

    def award_skill_xp(self, skill, amount):
        # Proxy to rules
        return award_skill_xp(self.player, skill, amount)

    def craft_item(self, recipe_id):
        return self.inventory.craft_item(self.player, recipe_id)

    def buy_item(self, template_id):
        return self.inventory.buy_item(self.player, template_id)

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
            
            # Reveal Starting Area
            self.update_visited(self.player.x, self.player.y, self.player.z)
            
            # --- Spawn Town NPCs ---
            if not self.session.query(NPC).filter_by(name="Gareth").first():
                self.session.add(NPC(
                    name="Gareth",
                    persona_prompt="You are Gareth, a gruff but skilled blacksmith. You sell weapons and armor.",
                    location="Blacksmith",
                    x=8, y=9, z=1
                ))
            
            if not self.session.query(NPC).filter_by(name="Seraphina").first():
                self.session.add(NPC(
                    name="Seraphina",
                    persona_prompt="You are Seraphina, a wise alchemist. You sell potions and magical supplies.",
                    location="Alchemist",
                    x=-8, y=9, z=1
                ))
            
            self.session.commit()

    def reset_game(self):
        """Wipe database and restart."""
        print("DM: RESETTING GAME...")
        # Delete all data
        from .database import CombatEncounter
        self.session.query(InventoryItem).delete()
        self.session.query(Monster).delete()
        self.session.query(MapTile).delete()
        self.session.query(Player).delete()
        self.session.query(NPC).delete()
        self.session.query(CombatEncounter).delete()
        self.session.query(WorldObject).delete()
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
        # Use CombatEncounter check now
        from .database import CombatEncounter
        active_enc = self.session.query(CombatEncounter).filter_by(is_active=True).first()
        if active_enc:
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

        # Resource Gathering
        if tile.tile_type in ["rock", "flower_pot"]:
             from .items import ITEM_TEMPLATES
             from .rules import roll_dice
             
             is_rock = (tile.tile_type == "rock")
             skill = "mining" if is_rock else "herbalism"
             item_key = "iron_ore" if is_rock else "mystic_herb"
             depleted_type = "floor" if is_rock else "grass"
             
             lvl = self.get_skill_level(skill)
             roll = roll_dice(20) + lvl
             dc = 10 
             
             if roll >= dc:
                 template = ITEM_TEMPLATES[item_key]
                 
                 # Stacking Logic
                 existing = self.session.query(InventoryItem).filter_by(
                     player=self.player, name=template['name'], is_equipped=False
                 ).first()
                 
                 if existing and existing.quantity < 50:
                     existing.quantity += 1
                     flag_modified(existing, "quantity")
                 else:
                     self.session.add(InventoryItem(
                        name=template['name'], item_type=template['type'], slot=template['slot'],
                        properties=template['properties'], player=self.player, quantity=1
                     ))
                     
                 tile.tile_type = depleted_type
                 self.session.commit()
                 
                 leveled, new_lvl = self.award_skill_xp(skill, 10)
                 msg = f"Success! Gathered {template['name']}."
                 if leveled: msg += f" ({skill.title()} Level {new_lvl}!)"
                 else: msg += f" (+10 XP)"
             else:
                 leveled, new_lvl = self.award_skill_xp(skill, 2)
                 msg = f"Failed to gather. (Rolled {roll} vs DC {dc})"
                 if leveled: msg += f" ({skill.title()} Level {new_lvl}!)"
                 
             return [self.player.x, self.player.y, self.player.z], msg

        if tile.tile_type not in ["floor", "floor_wood", "door", "open_door", "grass", "bridge"]:
             # Block: wall, wall_house, tree, water, anvil, shelf
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
             # Start new Encounter
             msg_data = self.combat.start_combat(enemy)
             # If complex object return simple string for now, UI will handle state change
             if isinstance(msg_data, dict):
                 return [self.player.x, self.player.y, self.player.z], "Encounter Started!"
             return [self.player.x, self.player.y, self.player.z], msg_data

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

        # Check Town Doors (Z=1)
        if new_z == 1:
            town_doors = {
                (0, 4):  {"name": "Town Hall", "enter": (0, 1)},  # Move South to Enter
                (8, 9):  {"name": "Blacksmith", "enter": (1, 0)}, # Move East to Enter
                (-8, 9): {"name": "Alchemist", "enter": (-1, 0)}  # Move West to Enter
            }
            if (new_x, new_y) in town_doors:
                info = town_doors[(new_x, new_y)]
                edx, edy = info["enter"]
                if dx == edx and dy == edy:
                    desc = f"Entering {info['name']}..."
                elif dx == -edx and dy == -edy:
                    desc = f"Leaving {info['name']}..."
                else:
                    desc = f"Atthe entrance of {info['name']}." # Generic standing
                    
        # Check for proximity events (Greetings)
        # Check adjacent tiles (including diagonals? No, usually Manhattan or Chebyshev 1)
        nearby_npcs = self.session.query(NPC).filter(
            NPC.x.between(new_x-2, new_x+2),
            NPC.y.between(new_y-2, new_y+2),
            NPC.z == new_z
        ).all()
        
        for n in nearby_npcs:
            dist = max(abs(n.x - new_x), abs(n.y - new_y)) # Chebyshev
            if dist <= 4: # Increased range for room entry (Room is 5x5)
                greeting = ""
                if "Elara" in n.name:
                    qs = n.quest_state or {}
                    status = qs.get("status", "captive")
                    
                    if status == "captive":
                        greeting = "Elara calls out: 'Over here! I need your help!'"
                    elif status == "escorting":
                        # Silence is golden when following
                        greeting = "" 
                    elif status == "completed":
                        # In town, maybe only say hi occasionally or silence
                        greeting = ""
                
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
            return None # "Oakhaven Details" - silenced
        else:
            # Dungeon
            return None # "Dungeon Corridor" - silenced

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
        
        # --- HIDDEN DISCOVERY ---
        found_secrets = []
        
        # Check Tiles (Secret Doors)
        nearby_tiles = self.session.query(MapTile).filter(
            MapTile.x.between(x-2, x+2), MapTile.y.between(y-2, y+2), MapTile.z == z
        ).all()
        
        for t in nearby_tiles:
            if t.meta_data and t.meta_data.get("interactable") and t.meta_data.get("hidden") and not t.meta_data.get("discovered"):
                 t.meta_data["discovered"] = True
                 flag_modified(t, "meta_data")
                 found_secrets.append(t.meta_data.get("interact_name", "Something hidden"))
                 
        # Check Objects (Hidden Chests)
        nearby_objs = self.session.query(WorldObject).filter(
             WorldObject.x.between(x-3, x+3), WorldObject.y.between(y-3, y+3), WorldObject.z == z
        ).all()
        for o in nearby_objs:
             props = o.properties or {}
             if props.get("hidden") and not props.get("discovered"):
                 props["discovered"] = True
                 o.properties = props
                 flag_modified(o, "properties")
                 found_secrets.append(o.name)
                 
        self.session.commit()
        
        if found_secrets:
             context.append(f"SECRETS REVEALED: {', '.join(found_secrets)}")
             
        # 3. Call AI
        prompt = f"The player investigates the area at {x},{y}. Describe what they see in vivid detail."
        if found_secrets: prompt += " THEY HAVE FOUND HIDDEN ITEMS! Emphasize this discovery."
        
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
        visited_tiles = self.session.query(MapTile).filter_by(is_visited=True).all()
        map_data = {f"{t.x},{t.y},{t.z}": t.tile_type for t in visited_tiles}
        
        # Enemies
        monsters = self.session.query(Monster).filter_by(is_alive=True, z=pz).all()
        enemy_list = []
        for m in monsters:
            if m.state == "combat":
                 enemy_list.append({"xyz": [m.x, m.y, m.z], "hp": m.hp_current, "max_hp": m.hp_max, "name": m.name, "id": m.id, "state": "combat"})
            else:
                 enemy_list.append({"xyz": [m.x, m.y, m.z], "hp": m.hp_current, "max_hp": m.hp_max, "name": m.name, "id": m.id, "state": "idle"})

        # Corpses
        corpses = self.session.query(Monster).filter_by(is_alive=False, z=pz).all()
        corpse_list = []
        for m in corpses:
             corpse_list.append({"xyz": [m.x, m.y, m.z], "name": f"Dead {m.name}", "id": m.id})

        # NPCs
        npcs = self.session.query(NPC).filter(NPC.x != None, NPC.z == pz).all()
        npc_list = []
        for n in npcs:
            img = "player.png"
            if "Seraphina" in n.name: img = "seraphina.png"
            elif "Elara" in n.name: img = "elara.png"
            elif "Gareth" in n.name: img = "warrior2.png"
            elif "Elder" in n.name: img = "elder.png"
            
            npc_list.append({"xyz": [n.x, n.y, n.z], "name": n.name, "id": n.id, "asset": img})
            
        # Check actual combat state
        from .database import CombatEncounter
        active_enc = self.session.query(CombatEncounter).filter_by(is_active=True).first()
        
        combat_state = {"active": False}
        
        if active_enc:
            current_actor = active_enc.turn_order[active_enc.current_turn_index]
            combat_state = {
                "active": True,
                "current_turn": current_actor["type"], # "player" or "monster"
                "actors": active_enc.turn_order,
                "turn_index": active_enc.current_turn_index
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
                 t.meta_data = {"interactable": True, "interact_name": "Suspicious Wall", "secret_id": "secret_door_1", "hidden": True}
                 flag_modified(t, "meta_data") # Save it
            
            md = t.meta_data or {}
            
            if md.get("interactable"):
                # If it's hidden and not discovered, skip
                if md.get("hidden") and not md.get("discovered"):
                    continue
                
                # If it's a secret door and already open, skip
                if md.get("secret_id") and t.tile_type == "door":
                    continue
                
                secrets.append({
                    "id": md.get("secret_id") or f"tile_{t.x}_{t.y}",
                    "name": md.get("interact_name", "Interesting Object"),
                    "type": "secret" 
                })

        # Fetch Interactive Objects (Chests)
        objs = self.session.query(WorldObject).filter_by(z=self.player.z).all()
        for o in objs:
             # Basic Fog of War for Objects (prevent 'X-Ray' scanning)
             # Only send objects within ~5 tiles, but client will filter closer
             # Actually, let's filter purely by "HIDDEN" status here if needed.
             # User Request: "hidden or secret items... shouldn't show up"
             # We assume normal Chests are NOT hidden, just subject to Fog of War (distance)
             
             # If object has 'hidden' property
             props = o.properties or {}
             if props.get("hidden") and not props.get("discovered"):
                 continue

             secrets.append({
                 "id": f"obj_{o.id}",
                 "name": o.name,
                 "type": "secret", # Render as interact button
                 "obj_type": o.obj_type,
                 "xyz": [o.x, o.y, o.z]
             })

        return {
            "player": {
                "xyz": [self.player.x, self.player.y, self.player.z],
                "stats": self.player.stats,
                "skills": self.player.skills or {},
                "hp": self.player.hp_current,
                "max_hp": self.player.hp_max,
                "gold": self.player.gold or 0,
                "inventory": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "slot": i.slot,
                        "is_equipped": i.is_equipped, 
                        "properties": i.properties,
                        "item_type": i.item_type,
                        "quantity": i.quantity
                    } 
                    for i in self.player.inventory
                ]
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
            px, py, pz = self.player.x, self.player.y, self.player.z
            target = None
            
            # 1. Target by ID if provided
            if target_index:
                 target = self.session.query(Monster).filter_by(id=target_index).first()
            
            # 2. Fallback to Proximity
            if not target:
                corpses = self.session.query(Monster).filter_by(is_alive=False, z=pz).all()
                nearby = [c for c in corpses if abs(c.x - px) <= 1 and abs(c.y - py) <= 1]
                if nearby:
                    target = nearby[0]
            
            if not target:
                return "There is nothing here to loot."
            
            # Return Loot List for UI
            loot_data = target.loot or []
            if not loot_data:
                 return "The corpse is empty."
                 
            return {"type": "loot_window", "loot": loot_data, "corpse_id": target.id, "name": target.name}

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
            # Handle World Objects
            if target_index.startswith("obj_"):
                 oid = int(target_index.split("_")[1])
                 obj = self.session.query(WorldObject).filter_by(id=oid).first()
                 if not obj: return "It's gone."
                 
                 if abs(obj.x - self.player.x) > 1 or abs(obj.y - self.player.y) > 1:
                     return "Too far away."
                     
                 if obj.obj_type == "chest":
                     loot = (obj.properties or {}).get("loot", [])
                     if not loot: return "It's empty."
                     return {"type": "loot_window", "loot": loot, "corpse_id": target_index, "name": obj.name}

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
