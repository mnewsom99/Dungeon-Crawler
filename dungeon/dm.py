from .database import get_session, Player, MapTile, Monster, InventoryItem, NPC, init_db, WorldObject, CombatEncounter
from .rules import roll_dice, get_skill_level, award_skill_xp
from .combat import CombatSystem
from .generator import LevelBuilder
from .dialogue import DialogueSystem
from .inventory_system import InventorySystem
from .world_sim import WorldSimulation
from .movement import MovementSystem
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
        # self.ai = AIBridge() # Removed LLM
        self.dialogue = DialogueSystem(self)
        from .interactions import InteractionManager
        self.interactions = InteractionManager(self)
        self.world_sim = WorldSimulation(self)
        self.movement = MovementSystem(self)
        
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

    def sell_item(self, item_id):
        return self.inventory.sell_item(self.player, item_id)

    def _initialize_world(self):
        # Ensure player exists
        self.player = self.session.query(Player).first()
        if not self.player:
            print("DM: Creating new Hero...")
            self.player = Player(
                name="Generic Hero", 
                hp_current=20, hp_max=20,
                stats={"str": 14, "dex": 14, "con": 14, "int": 10, "wis": 10, "cha": 10},
                x=0, y=0, z=1, # DEBUG: Start in Town
                quest_state={"active_quests": []}
            )
            # Add default gear
            self.session.add(InventoryItem(name="Training Sword", slot="main_hand", is_equipped=True, player=self.player))
            self.session.add(InventoryItem(name="Cloth Tunic", slot="chest", is_equipped=True, player=self.player))
            self.session.add(self.player)
            
            # --- Generate Maps ---
            builder = LevelBuilder(self.session)
            builder.generate_tutorial_dungeon(self.player)
            builder.generate_town(1) # Force Generate Town
            
            # Reveal Starting Area
            self.update_visited(self.player.x, self.player.y, self.player.z)
            
            # --- DEBUG: Auto-Rescue NPCs for Testing ---
            # Move everyone to town immediately
            gareth = self.session.query(NPC).filter(NPC.name.like("%Gareth%")).first()
            if gareth: gareth.x, gareth.y, gareth.z = 10, 8, 1
            
            seraphina = self.session.query(NPC).filter(NPC.name.like("%Seraphina%")).first()
            if seraphina: seraphina.x, seraphina.y, seraphina.z = -11, 9, 1
            
            elara = self.session.query(NPC).filter(NPC.name.like("%Elara%")).first()
            if elara: elara.x, elara.y, elara.z = -11, 8, 1 # Home
            
            elder = self.session.query(NPC).filter(NPC.name.like("%Elder%")).first()
            if elder: elder.x, elder.y, elder.z = 0, 7, 1 # Town Hall
            
            self.session.commit()
            
            # --- Spawn Town NPCs ---
            # --- Spawn Town NPCs ---
            # LEGACY FIX: Check for "Gareth Ironhand" specifically.
            # If he exists (even in dungeon), DO NOT spawn the town placeholder.
            gareth_exists = self.session.query(NPC).filter(NPC.name.like("%Gareth%")).first()
            # Clean up duplicates (Migration)
            # If we have "Gareth" (town) AND "Gareth Ironhand" (dungeon), delete "Gareth".
            generic_gareth = self.session.query(NPC).filter_by(name="Gareth").first()
            true_gareth = self.session.query(NPC).filter_by(name="Gareth Ironhand").first()
            
            if generic_gareth and true_gareth:
                print("DM: Fixing Duplicate Gareth. Removing town placeholder.")
                self.session.delete(generic_gareth)
                self.session.commit()
            
            # Note: We rely on Generator to load Seraphina/Elder now.
            # No manual add here.
            
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
        """Clean robust movement logic (Delegated)."""
        return self.movement.move_player(dx, dy)

    def _dead_move_player(self, dx, dy):
        """Legacy code to be removed."""
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
            if new_z == 1:
                # North Gate check
                # Town is approx -20 to 20 range.
                if new_y < -20: 
                    # Transition to North Forest (Z=2)
                    self.teleport_player(0, 29, 2) # South end of Forest
                    return [0, 29, 2], "*** You enter the North Forest ***"

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
            # Hacky Secret Door check (Dungeon -> Town)
            print("DM: Door interaction")
            if new_z == 0 and abs(new_x) <= 2 and new_y >= 28: # Dungeon Exit Range
                self.teleport_player(0, 0, 1) # Town
                
                # --- TRIGGER: Elara Returns Home ---
                # 1. Find Elara (likely following us or just in DB at Z=0)
                elara = self.session.query(NPC).filter(NPC.name.like("%Elara%")).first()
                if elara:
                    # Teleport close to entrance
                    elara.x = 1
                    elara.y = 1
                    elara.z = 1
                    
                    # Set Schedule (Alchemist Shop Interior: -11, 8)
                    qs = elara.quest_state or {}
                    qs["status"] = "walking_home"
                    qs["target_x"] = -11
                    qs["target_y"] = 8
                    elara.quest_state = qs
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(elara, "quest_state")
                    self.session.add(elara)
                
                # --- TRIGGER: Auto-Rescue Others ---
                # If player beat the dungeon, others escape too
                
                # Gareth -> Blacksmith (10, 8)
                gareth = self.session.query(NPC).filter(NPC.name.like("%Gareth%")).first()
                if gareth and gareth.z == 0:
                    gareth.x, gareth.y, gareth.z = 1, 0, 1 # Start at town square
                    qs = gareth.quest_state or {}
                    qs["status"] = "walking_home"
                    qs["target_x"] = 10
                    qs["target_y"] = 8
                    gareth.quest_state = qs
                    flag_modified(gareth, "quest_state")
                    self.session.add(gareth)

                # Seraphina -> Alchemist (-11, 9)
                seraphina = self.session.query(NPC).filter(NPC.name.like("%Seraphina%")).first()
                if seraphina and seraphina.z == 0:
                    seraphina.x, seraphina.y, seraphina.z = -1, 0, 1 # Start at town square
                    qs = seraphina.quest_state or {}
                    qs["status"] = "walking_home"
                    qs["target_x"] = -11
                    qs["target_y"] = 9
                    seraphina.quest_state = qs
                    flag_modified(seraphina, "quest_state")
                    self.session.add(seraphina)

                self.session.commit()
                return [0, 0, 1], "*** You emerge into Oakhaven! ***"
             
            # Normal door (open it?)
            tile.tile_type = "open_door" # Visual change?
            # Treat as floor for now
        
        # 3b. Check Zone Transitions (Edges)
        # Forest (Z=2) -> Town (Z=1) : South Edge (y > 28)
        if new_z == 2 and new_y >= 29:
             self.teleport_player(0, -18, 1) # North Gate of Town
             return [0, -18, 1], "You travel south back to Oakhaven."
             
        # Town (Z=1) -> Forest (Z=2) : North Edge (y < -20)
        # (Assuming town map allows walking north)
        if new_z == 1 and new_y <= -19:
             self.teleport_player(0, 28, 2) # South Road of Forest
             return [0, 28, 2], "You head north into the deep forest."
        
        # 4. Check Monsters (Combat Trigger)
        enemy = self.session.query(Monster).filter_by(x=new_x, y=new_y, z=new_z, is_alive=True).first()
        if enemy:
             # Start new Encounter
             msg_data = self.combat.start_combat(enemy)
             # If complex object return simple string for now, UI will handle state change
             if isinstance(msg_data, dict):
                 return [self.player.x, self.player.y, self.player.z], "Encounter Started!"
             return [self.player.x, self.player.y, self.player.z], msg_data

        if self.combat.is_active():
            # Combat Movement Logic
            # 1. Check Turn & Moves
            encounter = self.session.query(CombatEncounter).filter_by(is_active=True).first()
            if not encounter:
                 pass
            elif encounter.turn_order[encounter.current_turn_index]["type"] != "player":
                 return [self.player.x, self.player.y, self.player.z], "<b>It is not your turn!</b>"
            elif encounter.moves_left <= 0:
                 return [self.player.x, self.player.y, self.player.z], "No movement remaining!"
            
            # 2. Update Position (We know it's valid/empty from checks above)
            self.player.x = new_x
            self.player.y = new_y
            self.player.z = new_z
            self.update_visited(new_x, new_y, new_z) # Fog of war updates
            
            # 3. Decrement Counter (via combat)
            res = self.combat.player_action("move") # returns {events: []}
            self.session.commit()
            
            # Return events so frontend can play them (Enemy AI turns - actually no, enemy turns happen on End Phase now)
            return [new_x, new_y, new_z], res # res has simple "Moved" message usually

        # 5. Check NPCs (Blocking? Or Chat Trigger?)
        npc = self.session.query(NPC).filter_by(x=new_x, y=new_y, z=new_z).first()
        if npc:
             # Attempt to displace NPC to make room
             candidates = [(new_x+1, new_y), (new_x-1, new_y), (new_x, new_y+1), (new_x, new_y-1)]
             moved_npc = False
             
             for cx, cy in candidates:
                 if cx == self.player.x and cy == self.player.y: continue # Don't swap immediately
                 
                 # Check Wall/Void
                 ct = self.session.query(MapTile).filter_by(x=cx, y=cy, z=new_z).first()
                 if not ct or ct.tile_type in ["wall", "water", "void"]: continue
                 
                 # Check Occupancy
                 occ = self.session.query(NPC).filter_by(x=cx, y=cy, z=new_z).first()
                 if occ: continue
                 occ_m = self.session.query(Monster).filter_by(x=cx, y=cy, z=new_z).first()
                 if occ_m: continue
                 
                 # Move NPC
                 npc.x = cx
                 npc.y = cy
                 moved_npc = True
                 self.session.add(npc)
                 break
                 
             if moved_npc:
                 pass # NPC moved, but let's effectively Block the player for this turn so they see the push
                 # OR: allow player to enter? "You squeeze past".
                 # Let's Move Player INTO the tile since it's now free.
             else:
                 return [self.player.x, self.player.y, self.player.z], f"You bump into {npc.name}. (Blocked)"

        # 6. Success - Commit Move
        old_x, old_y, old_z = self.player.x, self.player.y, self.player.z
        
        self.player.x = new_x
        self.player.y = new_y
        
        # --- NPC AMBIENT MOVEMENT ---
        try:
             self.world_sim.process_npc_schedules()
             
             # --- MONSTER ROAMING & AGGRO ---
             if new_z != 1: # Not in Safe Town
                env_msg = self.world_sim.process_environment_turn()
                if env_msg: 
                    pass
        except Exception as e:
             print(f"Error processing NPCs/Env: {e}")
        
        self.session.commit() # Commit positions so NPC updates see new player pos
        self.update_visited(new_x, new_y, new_z)
        
        narrative = "You move forward."
        if new_z == 2: narrative = "You are wandering the North Forest."
        if new_z == 0: narrative = "You step through the dungeon."
        
        # Check active combat again in case environment turn started it
        if self.combat.is_active():
            narrative = "Ambushed! Combat Started."
            # Retrieve initial combat events to show
            return [new_x, new_y, new_z], narrative

        # --- NPC AI (Followers & Returning Home) ---
        npcs = self.session.query(NPC).filter_by(z=old_z).all()
        for f in npcs:
            qs = f.quest_state or {}
            status = qs.get("status")
            
            # A. Follower Logic
            if status == "following":
                dist = abs(f.x - old_x) + abs(f.y - old_y)
                # Only move if not already at old pos (avoid stacking if multiple)
                # And check reasonable distance (don't teleport across map)
                if dist <= 5 and (f.x != old_x or f.y != old_y):
                     # Check if old spot is empty (it should be, player just left)
                     f.x = old_x
                     f.y = old_y
                     self.session.add(f)
            
            # B. Return Home Logic
            elif "home" in qs and status != "following":
                 hx, hy, hz = qs["home"]
                 if f.z == hz and (f.x != hx or f.y != hy):
                      # Determine direction
                      dx = 0
                      dy = 0
                      if f.x < hx: dx = 1
                      elif f.x > hx: dx = -1
                      
                      if f.y < hy: dy = 1
                      elif f.y > hy: dy = -1
                      
                      # Try moving X then Y (Manhattan)
                      # Check collision for next step
                      target_x, target_y = f.x + dx, f.y
                      if dx == 0: target_x, target_y = f.x, f.y + dy
                      
                      # Simple collision check
                      # Avoid player
                      if target_x == self.player.x and target_y == self.player.y: continue 
                      
                      # Avoid Walls
                      ct = self.session.query(MapTile).filter_by(x=target_x, y=target_y, z=f.z).first()
                      if ct and ct.tile_type not in ["wall", "water", "void"]:
                           f.x = target_x
                           f.y = target_y
                           self.session.add(f)

        # 7. Update Visibility
        self.update_visited(new_x, new_y, new_z)
        self.save()
        
        # 8. Return Narrative (Static + Dynamic Events)
        old_room = self._generate_description(old_x, old_y, old_z)
        new_room = self._generate_description(new_x, new_y, new_z)
        
        desc = ""
        if new_room and new_room != old_room:
             desc = f"You enter {new_room}."
        elif new_room == "Dungeon Entrance" and not desc:
             # Always show entrance name if just lingering? No, prevent spam.
             pass

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
                    desc = f"At the entrance of {info['name']}." # Generic standing
        
        elif new_z == 2:
             desc = "You are wandering the North Forest."
                    
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

        return [new_x, new_y, new_z], desc

    def update_visited(self, cx, cy, cz):
        return self.movement.update_visited(cx, cy, cz)

    def _dead_update_visited_legacy(self, cx, cy, cz):
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
        
        # Room Definitions
        # Helper to check bounds
        def in_rect(rx, ry, w, h):
            # Centered rect logic from generator?
            # Generator used: range(cx - w//2, cx + w//2 + 1)
            # So bounds are [cx - w//2, cx + w//2] inclusive
            
            # Let's just define explicit ranges based on known generator logic
            pass

        if z == 1:
            # Town
            if -8 <= x <= 0 and 1 <= y <= 7: return "Town Hall"
            if 8 <= x <= 15 and 6 <= y <= 12: return "The Smithy"
            if -14 <= x <= -8 and 6 <= y <= 12: return "Alchemist's Shop"
            if abs(x) <= 20 and abs(y) <= 20: return "Town Square"
            return "Wilderness"
        elif z == 0:
            # Dungeon
            # 1. Start Room (0,0, 3x3) -> -1 to 1
            if -1 <= x <= 1 and -1 <= y <= 1: return "Dungeon Entrance"
            
            # 2. Corridor (0, 2-8)
            if x == 0 and 2 <= y <= 8: return "Dark Corridor"
            
            # 3. Grand Hall (0, 11, 7x5) -> -3 to 3, 9 to 13
            if -3 <= x <= 3 and 9 <= y <= 13: return "Grand Hall"
            
            # 4. Armory (-10, 11, 5x5) -> -12 to -8, 9 to 13
            if -12 <= x <= -8 and 9 <= y <= 13: return "Old Armory"
            
            # 5. Library (10, 11, 5x5) -> 8 to 12, 9 to 13
            if 8 <= x <= 12 and 9 <= y <= 13: return "Dusty Library"
            
            # 6. Barracks (0, 20, 9x5) -> -4 to 4, 18 to 22
            if -4 <= x <= 4 and 18 <= y <= 22: return "Guard Barracks"
            
            # 7. Jail (0, 30, 5x5) -> -2 to 2, 28 to 32
            if -2 <= x <= 2 and 28 <= y <= 32: return "High Security Jail"
            
            return "Dungeon Tunnels"

        elif z == 2:
            return "North Forest"

        return None

    def investigate_room(self):
        """Active Skill: Analyze location for hidden secrets."""
        from .rules import roll_dice
        from .database import Monster, WorldObject
        from sqlalchemy.orm.attributes import flag_modified
        
        pl = self.player
        skill_bonus = self.get_skill_level("investigation")
        roll = roll_dice(20) + skill_bonus
        
        # Room Description
        x, y, z = pl.x, pl.y, pl.z
        room_name = self._generate_description(x, y, z) or "Unknown Area"
        
        found = []
        
        # 1. Scan Tiles - VISIBILITY FLOOD FILL (Radius 6)
        # Instead of simple box, we do a BFS/FloodFill that stops at walls to simulate Line of Sight
        
        revealed_count = 0
        queue_pos = [(x, y)]
        visited_bfs = set([(x, y)])
        max_dist = 6
        
        # We need to fetch the local map for efficient checking
        local_tiles = self.session.query(MapTile).filter(
            MapTile.x.between(x-6, x+6),
            MapTile.y.between(y-6, y+6),
            MapTile.z == z
        ).all()
        
        # Convert to dict for fast lookup
        tile_map = {(t.x, t.y): t for t in local_tiles}
        
        idx = 0
        while idx < len(queue_pos):
            cx, cy = queue_pos[idx]
            idx += 1
            
            # Check distance
            dist = max(abs(cx - x), abs(cy - y))
            if dist > max_dist: continue
            
            # Reveal this tile
            if (cx, cy) in tile_map:
                t = tile_map[(cx, cy)]
                
                # REVEAL FOG OF WAR
                if not t.is_visited:
                    t.is_visited = True
                    revealed_count += 1
                
                # REVEAL HIDDEN SECRETS (Check Roll)
                md = t.meta_data or {}
                if md.get("hidden"):
                    dc = md.get("dc", 15)
                    if roll >= dc:
                        md["hidden"] = False
                        md["discovered"] = True
                        t.meta_data = md
                        flag_modified(t, "meta_data")
                        found.append(f"Hidden {md.get('interact_name', 'Feature')}")

                # PROPAGATE?
                # Stop at walls/doors (Vision blockers)
                if t.tile_type in ["wall", "wall_grey", "wall_house", "void", "door"]:
                     continue # Don't look past walls
                
                # Add neighbors
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) not in visited_bfs:
                        visited_bfs.add((nx, ny))
                        queue_pos.append((nx, ny))
            else:
                # Void/Unmapped -> treat as wall, stop
                pass

        # 2. Scan Objects
        objs = self.session.query(WorldObject).filter_by(z=z).all()
        for o in objs:
            dist = abs(o.x - x) + abs(o.y - y)
            if dist <= 3:
                props = o.properties or {}
                if props.get("hidden"):
                    dc = props.get("dc", 15)
                    if roll >= dc:
                        props["hidden"] = False
                        props["discovered"] = True
                        o.properties = props
                        flag_modified(o, "properties")
                        found.append(f"Hidden {o.name}")

        # 3. Scan Visible Entities (for observation)
        monsters = self.session.query(Monster).filter(
            Monster.x.between(x-5, x+5),
            Monster.y.between(y-5, y+5),
            Monster.z == z,
            Monster.is_alive == True
        ).all()
        
        visible_threats = [m.name for m in monsters]

        self.session.commit()
        
        narrative = f"You carefully investigate the {room_name}. (Rolled {roll})"
        if found:
            narrative += f"<br><span style='color:#55ff55'>You revealed: {', '.join(found)}!</span>"
        elif revealed_count > 0:
             narrative += f"<br>You map out more of the area ({revealed_count} tiles)."
        else:
            narrative += "<br>You find nothing hidden."
            
        entities = []
        if monsters:
             narrative += f"<br><span style='color:#ff8888'>You spot: {', '.join(visible_threats)}.</span>"
             for m in monsters:
                 dist = int(abs(m.x - x) + abs(m.y - y))
                 entities.append({"name": m.name, "dist": dist, "status": "Hostile"})

        return {"narrative": narrative, "entities": entities}


    def describe_current_room(self):
        # Legacy fallback or quick look
        return self._generate_description(self.player.x, self.player.y, self.player.z)

    def get_state_dict(self):
        try:
             return self._get_state_dict_impl()
        except Exception as e:
             self.session.rollback() # CRITICAL: Reset session on error!
             import traceback
             print("CRITICAL ERROR IN GET_STATE:")
             traceback.print_exc()
             return { "error": str(e) }

    def _get_state_dict_impl(self):
        """Return a JSON-serializable state for the frontend."""
        map_data = {}
        px, py, pz = self.player.x, self.player.y, self.player.z
        
        # 1. Fetch visible tiles
        try:
             visited_tiles = self.session.query(MapTile).filter_by(is_visited=True).all()
        except:
             self.session.rollback()
             visited_tiles = self.session.query(MapTile).filter_by(is_visited=True).all()
             
        map_data = {f"{t.x},{t.y},{t.z}": t.tile_type for t in visited_tiles}
        
        # Enemies
        try:
            monsters = self.session.query(Monster).filter_by(is_alive=True, z=pz).all()
        except:
             self.session.rollback()
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
            
            # --- FAILSAFE: DEADLOCK PREVENTION ---
            # If we are fetching state (passive) but it is the Enemy/NPC turn,
            # it means the Turn Processor failed to auto-continue previously.
            # We force it to run now to unblock the UI.
            if current_actor["type"] != "player":
                print(f"DEBUG: Found stuck AI turn ({current_actor['name']}). Forcing Turn Process.")
                try:
                    self.combat._process_turn_queue(active_enc)
                    # Refresh active_enc state after processing
                    self.session.expire(active_enc)
                    if not active_enc.is_active:
                         # Combat ended during catch-up
                         combat_state = {"active": False}
                    else:
                         # Re-read actor
                         current_actor = active_enc.turn_order[active_enc.current_turn_index]
                except Exception as e:
                    print(f"CRITICAL: Failed to process stuck turn: {e}")

            # Check if STILL active after potential auto-resolve
            if active_enc.is_active:
                combat_state = {
                    "active": True,
                    "current_turn": current_actor["type"], # "player" or "monster"
                    "actors": active_enc.turn_order,
                    "turn_index": active_enc.current_turn_index,
                    "phase": active_enc.phase,
                    "moves_left": active_enc.moves_left,
                    "actions_left": active_enc.actions_left,
                    "bonus_actions_left": active_enc.bonus_actions_left
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

        # Prepare Quest Log for Frontend
        quest_log = []
        try:
            from .quests import QUEST_DATABASE
            qs = self.player.quest_state or {}
            
            # 1. New Dictionary System
            active_q = qs.get("active", {})
            if isinstance(active_q, dict):
                for qid in active_q:
                    if qid in QUEST_DATABASE:
                        quest_log.append({
                            "id": qid,
                            "title": QUEST_DATABASE[qid]["title"],
                            "description": QUEST_DATABASE[qid]["description"],
                            "status": "active"
                        })
                    else:
                        quest_log.append({"title": qid, "status": "active"}) # Fallback

            # 2. Legacy List System (Migration/Compat)
            legacy_q = qs.get("active_quests", [])
            if isinstance(legacy_q, list):
                for q_title in legacy_q:
                    quest_log.append({
                        "title": q_title,
                        "description": "Active Quest (Legacy)",
                        "status": "active"
                    })
                    
        except Exception as e:
            print(f"Quest Log Error state: {e}")

        return {
            "player": {
                "xyz": [self.player.x, self.player.y, self.player.z],
                "stats": self.player.stats,
                "skills": self.player.skills or {},
                "hp": self.player.hp_current,
                "max_hp": self.player.hp_max,
                "level": self.player.level or 1,
                "xp": self.player.xp or 0,
                "gold": self.player.gold or 0,
                "quest_state": self.player.quest_state or {},
                "quest_log": quest_log, # NEW friendliness
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
                    for i in self.player.inventory if i
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
        """Handle interactions like looting. Delegated to InteractionManager."""
        return self.interactions.handle_interaction(action, target_type, target_index)

    def chat_with_npc(self, npc_index, message):
        """Handle persistent chat with an NPC."""
        return self.dialogue.chat_with_npc(npc_index, message)

    def teleport_player(self, x, y, z):
        return self.movement.teleport_player(x, y, z)

    def _dead_update_visited(self, cx, cy, cz):
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

    def upgrade_stat(self, stat_name):
        """Spend a point to upgrade a stat."""
        from sqlalchemy.orm.attributes import flag_modified
        
        pl = self.player
        stats = dict(pl.stats or {})
        points = stats.get('unspent_points', 0)
        
        if points <= 0: return "No points available."
        
        valid_stats = ['str', 'dex', 'int', 'con', 'cha', 'isd', 'wis', 'agility', 'strength', 'intelligence', 'constitution'] 
        s_lower = stat_name.lower()
        
        # Normalize
        if s_lower == 'strength': s_lower = 'str'
        if s_lower == 'agility': s_lower = 'dex'
        if s_lower == 'intelligence': s_lower = 'int'
        if s_lower == 'constitution': s_lower = 'con'
        
        current = stats.get(s_lower, 10)
        stats[s_lower] = current + 1
        stats['unspent_points'] = points - 1
        
        pl.stats = stats
        flag_modified(pl, "stats")
        self.session.commit()
        
        if s_lower == 'con':
            pl.hp_max += 2
            pl.hp_current += 2
            
        # Recalculate derived stats (AC from DEX)
        from .inventory_system import InventorySystem
        inv_sys = InventorySystem(self.session)
        inv_sys.recalculate_stats(pl)
        self.session.commit()
            
        return f"Upgraded {s_lower.upper()} to {stats[s_lower]}."
