from .database import MapTile, NPC, Monster, CombatEncounter, InventoryItem
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
        player = self.dm.player
        
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

        if tile.tile_type not in ["floor", "floor_wood", "door", "open_door", "grass", "bridge"]:
             # Block: wall, wall_house, tree, water, anvil, shelf
             if not tile.is_visited:
                 tile.is_visited = True
                 self.session.commit()
             return [player.x, player.y, player.z], "You bump into a wall."

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
                    
        # Check for proximity events (Greetings)
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

        player = self.dm.player
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
        tiles = self.session.query(MapTile).filter(
            MapTile.x.between(cx-2, cx+2),
            MapTile.y.between(cy-2, cy+2),
            MapTile.z == cz
        ).all()
        
        for t in tiles:
            if not t.is_visited:
                t.is_visited = True
        self.session.commit()
