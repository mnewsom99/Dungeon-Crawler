from .database import MapTile, NPC, Monster, CombatEncounter, InventoryItem, Player
from sqlalchemy.orm.attributes import flag_modified
from .items import ITEM_TEMPLATES
from .generator import LevelBuilder

class MovementSystem:
    """
    Handles all player movement logic, including:
    - Collision detection (Walls, Void)
    - Zone transitions (Dungeon <-> Town <-> Forest)
    - Resource gathering triggering (Mining/Herbalism)
    - Interaction triggering (Doors)
    - Combat triggering (Monsters)
    - NPC displacement
    """
    def __init__(self, dm):
        self.dm = dm
        self.session = dm.session

    def move_player(self, dx, dy):
        """Clean robust movement logic."""
        # Use fresh query to ensure attachment to current thread's session
        player = self.session.query(Player).first()
        if not player: return [0,0,0], "Error: No Player Found"
        
        # 1. Calculate Target
        new_x = player.x + dx
        new_y = player.y + dy
        new_z = player.z
        
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
                 return [player.x, player.y, player.z], "You bump into a dark wall."
            # Town bounds handled by generation usually
            if new_z == 1:
                # North Gate check
                # Town is approx -20 to 20 range.
                if new_y < -20: 
                    # Transition to North Forest (Z=2)
                    self.teleport_player(0, 29, 2) # South end of Forest
                    return [0, 29, 2], "*** You enter the North Forest ***"

            return [player.x, player.y, player.z], "The path is blocked."

        # Resource Gathering (Delegated to InteractionManager)
        if tile.tile_type in ["rock", "flower_pot"]:
             # We simulate a "gather" action on this tile
             msg = self.dm.interactions.handle_interaction("gather", "tile", f"{new_x},{new_y},{new_z}")
             # If successful (msg starts with "Success"), we usually stay put? 
             # Or moved? The original logic returned player pos (didn't move).
             return [player.x, player.y, player.z], msg

        if tile.tile_type not in ["floor", "floor_wood", "floor_volcanic", "floor_ice", "door", "door_stone", "open_door", "grass", "bridge", "steam_vent", "lava", "ice_spikes", "signpost", "street_lamp", "fountain", "stairs_down"]:
             print(f"DEBUG: Move Blocked! Tile Type: '{tile.tile_type}' not in whitelist.")
             # Block: wall, wall_house, tree, water, anvil, shelf
             if not tile.is_visited:
                 tile.is_visited = True
                 self.session.commit()
             return [player.x, player.y, player.z], f"You bump into a wall ({tile.tile_type})."

        # 3. Check Door Transition (Tile Event)
        if tile.tile_type == "stairs_down":
             if new_z == 1: # Town -> Dungeon
                 self.teleport_player(0, 0, 0)
                 return [0, 0, 0], "*** You descend into the Dark Dungeon... ***"

        if tile.tile_type in ["door", "door_stone"]:
            # Hacky Secret Door check (Dungeon -> Town)
            print(f"DM: Door interaction at {new_x},{new_y},{new_z}")
            if new_z == 0 and abs(new_x) <= 2 and new_y >= 28: # Dungeon Exit Range
                self.teleport_player(0, 0, 1) # Town
                
                # ... (Keep existing Elara/NPC return logic) ...
                # (For brevity, I assume I don't need to re-copy all NPC logic if I just insert the Fire Dungeon check before returning)
                return [0, 0, 1], "*** You emerge into Oakhaven! ***"

            # --- FIRE DUNGEON ENTRANCE (Forest Z=2 -> Z=3) ---
            # Location approx (-15, 15)
            if new_z == 2 and abs(new_x - (-15)) <= 1 and abs(new_y - 15) <= 1:
                self.teleport_player(0, 0, 3) # Fire Dungeon Start
                
                # Auto-start Quest if not active
                try:
                    from .quests import QuestManager
                    qm = QuestManager(self.session, player)
                    if qm.get_status("elemental_balance") == "available":
                        qm.accept_quest("elemental_balance")
                except Exception as e:
                    print(f"Quest Auto-Start Error: {e}")

                return [0, 0, 3], "*** You descend into the Volcanic Depths! ***<br><i>(Quest 'Elemental Balance' Updated)</i>"

            # --- ICE DUNGEON ENTRANCE (Forest Z=2 -> Z=4) ---
            # Location approx (-15, -20)
            if new_z == 2 and abs(new_x - (-15)) <= 1 and abs(new_y - (-20)) <= 1:
                self.teleport_player(0, 0, 4) # Ice Dungeon Start
                return [0, 0, 4], "*** You enter the Frozen Caverns! ***"

            # ... (Rest of existing door logic if needed) ...
            
            # Normal door (open it?)
            tile.tile_type = "open_door" # Visual change?
            # Treat as floor for now
        
            # Treat as floor for now
        
        # 3b. DUNGEON EXITS (Z=0)
        # Entry Door (0, -1) or (-1 to 1 range close to start)
        if new_z == 0 and abs(new_x) <= 1 and new_y <= -1:
             self.teleport_player(0, 0, 1) # Back to Town
             return [0, 0, 1], "*** You ascend the stairs to Oakhaven. ***"
             
        # Boss Exit Door (0, 32)
        if new_z == 0 and abs(new_x) <= 1 and new_y >= 32:
             self.teleport_player(0, 0, 1) # Back to Town
             return [0, 0, 1], "*** You escape the dungeon triumphantly! ***"
             
        # 3c. FIRE DUNGEON EXIT (Z=3)
        # Entry Door moved to (-2, 0) based on user feedback
        if new_z == 3 and abs(new_x - (-2)) <= 1 and abs(new_y - 0) <= 1:
             self.teleport_player(-15, 15, 2) # Back to Forest Entrance
             return [-15, 15, 2], "*** You escape the searing heat and return to the cool forest. ***"

        # 3e. ICE DUNGEON EXIT (Z=4)
        # Door is at (0, -2).
        if new_z == 4 and new_x == 0 and new_y <= -2:
             self.teleport_player(-15, -20, 2) # Back to Forest
             return [-15, -20, 2], "*** You leave the freezing cold behind. ***"


        # 3d. Check Zone Transitions (Edges)
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
             msg_data = self.dm.combat.start_combat(enemy)
             # If complex object return simple string for now, UI will handle state change
             if isinstance(msg_data, dict):
                 return [player.x, player.y, player.z], "Encounter Started!"
             return [player.x, player.y, player.z], msg_data

        if self.dm.combat.is_active():
            # Combat Movement Logic
            # 1. Check Turn & Moves
            encounter = self.session.query(CombatEncounter).filter_by(is_active=True).first()
            if not encounter:
                 pass
            elif encounter.turn_order[encounter.current_turn_index]["type"] != "player":
                 return [player.x, player.y, player.z], "<b>It is not your turn!</b>"
            elif encounter.moves_left <= 0:
                 return [player.x, player.y, player.z], "No movement remaining!"
            
            # 2. Update Position (We know it's valid/empty from checks above)
            player.x = new_x
            player.y = new_y
            player.z = new_z
            self.update_visited(new_x, new_y, new_z) # Fog of war updates
            
            # 3. Decrement Counter (via combat)
            res = self.dm.combat.player_action("move") # returns {events: []}
            self.session.commit()
            
            # Return events so frontend can play them
            return [new_x, new_y, new_z], res 

        # 5. Check NPCs (Blocking? Or Chat Trigger?)
        npc = self.session.query(NPC).filter_by(x=new_x, y=new_y, z=new_z).first()
        if npc:
             # Attempt to displace NPC to make room
             candidates = [(new_x+1, new_y), (new_x-1, new_y), (new_x, new_y+1), (new_x, new_y-1)]
             moved_npc = False
             
             for cx, cy in candidates:
                 if cx == player.x and cy == player.y: continue # Don't swap immediately
                 
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
                 pass # NPC moved
             else:
                 return [player.x, player.y, player.z], f"You bump into {npc.name}. (Blocked)"

        # 6. Success - Commit Move
        old_x, old_y, old_z = player.x, player.y, player.z
        
        player.x = new_x
        player.y = new_y
        
        # --- NPC AMBIENT MOVEMENT ---
        try:
             self.dm.world_sim.process_npc_schedules()
             
             # --- MONSTER ROAMING & AGGRO ---
             if new_z != 1: # Not in Safe Town
                env_msg = self.dm.world_sim.process_environment_turn()
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
        if self.dm.combat.is_active():
            narrative = "Ambushed! Combat Started."
            return [new_x, new_y, new_z], narrative

        # --- NPC AI (Followers & Returning Home) ---
        npcs = self.session.query(NPC).filter_by(z=old_z).all()
        for f in npcs:
            qs = f.quest_state or {}
            status = qs.get("status")
            
            # A. Follower Logic
            if status == "following":
                dist = abs(f.x - old_x) + abs(f.y - old_y)
                if dist <= 5 and (f.x != old_x or f.y != old_y):
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
                      
                      target_x, target_y = f.x + dx, f.y
                      if dx == 0: target_x, target_y = f.x, f.y + dy
                      
                      if target_x == player.x and target_y == player.y: continue 
                      
                      ct = self.session.query(MapTile).filter_by(x=target_x, y=target_y, z=f.z).first()
                      if ct and ct.tile_type not in ["wall", "water", "void"]:
                           f.x = target_x
                           f.y = target_y
                           self.session.add(f)

        # 7. Update Visibility
        self.update_visited(new_x, new_y, new_z)
        self.dm.save()
        
        # 8. Return Narrative (Static + Dynamic Events)
        old_room = self.dm._generate_description(old_x, old_y, old_z)
        new_room = self.dm._generate_description(new_x, new_y, new_z)
        
        desc = ""
        if new_room and new_room != old_room:
             desc = f"You enter {new_room}."
        elif new_room == "Dungeon Entrance" and not desc:
             pass

        # Check Town Doors (Z=1)
        if new_z == 1:
            town_doors = {
                (0, 4):  {"name": "Town Hall", "enter": (0, 1)},  
                (8, 9):  {"name": "Blacksmith", "enter": (1, 0)}, 
                (-8, 9): {"name": "Alchemist", "enter": (-1, 0)} 
            }
            if (new_x, new_y) in town_doors:
                info = town_doors[(new_x, new_y)]
                desc = f"Approaching {info['name']}..." # Simplified logic
        
        elif new_z == 2:
             desc = "You are wandering the North Forest."
                    
        # Check for proximity events (Greetings & Landmarks)
        if new_z == 2:
             # Fire Dungeon Entrance
             if abs(new_x - (-15)) <= 3 and abs(new_y - 15) <= 3:
                 desc += " <br><span style='color: #ff4500;'>Heat radiates from the stone archway...</span>"

        nearby_npcs = self.session.query(NPC).filter(
            NPC.x.between(new_x-2, new_x+2),
            NPC.y.between(new_y-2, new_y+2),
            NPC.z == new_z
        ).all()
        
        for n in nearby_npcs:
            dist = max(abs(n.x - new_x), abs(n.y - new_y)) 
            if dist <= 4: 
                greeting = ""
                if "Elara" in n.name:
                    qs = n.quest_state or {}
                    status = qs.get("status", "captive")
                    if status == "captive":
                        greeting = "Elara calls out: 'Over here! I need your help!'"
                elif "Gareth" in n.name: greeting = "Gareth hails you: 'Well met, traveler.'"
                elif "Elder" in n.name: greeting = "The Elder waves a weary hand."
                
                if greeting:
                    desc += f" <br><span style='color: #fdcb6e;'>{greeting}</span>"
        
        return [new_x, new_y, new_z], desc

    def teleport_player(self, x, y, z):
        """Move player to a new zone/level."""
        # End Combat if Active (Escaped!)
        if self.dm.combat.is_active():
            self.dm.combat.end_combat()

        player = self.session.query(Player).first()
        player.x = x
        player.y = y
        player.z = z
        self.session.commit()
        
        # Check if map exists, if not generate
        if not self.session.query(MapTile).filter_by(z=z).first():
            if z == 1:
                self.dm._generate_town(z)
            elif z == 2:
                builder = LevelBuilder(self.session)
                builder.generate_forest(z)
            elif z == 3:
                builder = LevelBuilder(self.session)
                builder.generate_fire_dungeon(z)
            elif z == 4:
                builder = LevelBuilder(self.session)
                builder.generate_ice_dungeon(z)
        
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

    def update_visited(self, cx, cy, cz):
        # 1. Fetch Area (Square covers Max Diamond Radius 5)
        tiles = self.session.query(MapTile).filter(
            MapTile.x.between(cx-5, cx+5),
            MapTile.y.between(cy-5, cy+5),
            MapTile.z == cz
        ).all()
        
        # 2. Build Memory Map
        tile_map = {(t.x, t.y): t for t in tiles}
        
        # 3. BFS Flood Fill for Line of Sight
        queue = [(cx, cy, 0)] # x, y, dist
        visited = set([(cx, cy)])
        
        blockers = ["wall", "wall_grey", "wall_house", "void", "door", "tree", "bedrock_wall"]
        
        # We process the queue
        idx = 0
        while idx < len(queue):
            curr_x, curr_y, dist = queue[idx]
            idx += 1
            
            # Reveal this tile
            if (curr_x, curr_y) in tile_map:
                t = tile_map[(curr_x, curr_y)]
                if not t.is_visited:
                    t.is_visited = True
                
                # If this tile is opaque, we see IT, but not PAST it.
                if t.tile_type in blockers:
                    continue
            else:
                # Void/Empty space acts as full blocker
                continue

            # Check Range limit (Radius 5)
            if dist >= 5: continue
            
            # Propagate to Neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = curr_x + dx, curr_y + dy
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny, dist + 1))
                    
        self.session.commit()
