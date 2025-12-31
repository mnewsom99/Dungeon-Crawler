from .database import get_session, Player, MapTile, Monster, InventoryItem, NPC, init_db, WorldObject, CombatEncounter
from .rules import roll_dice, get_skill_level, award_skill_xp
from .combat import CombatSystem
from .generator import LevelBuilder
from .dialogue import DialogueSystem
from .inventory_system import InventorySystem
from .world_sim import WorldSimulation
from .movement import MovementSystem
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import joinedload
from .gamedata import NPC_START_CONFIG, PLAYER_START_CONFIG
import threading
import queue

class DungeonMaster:
    def __init__(self):
        # self.lock removed; using scoped_session
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
        player = self.session.query(Player).first()
        return self.inventory.equip_item(player, item_id)
        
    def unequip_item(self, item_id):
        player = self.session.query(Player).first()
        return self.inventory.unequip_item(player, item_id)

    def use_item(self, item_id):
        player = self.session.query(Player).first()
        return self.inventory.use_item(player, item_id)

    def take_loot(self, corpse_id, loot_id):
        player = self.session.query(Player).first()
        return self.inventory.take_loot(player, corpse_id, loot_id)

    def get_skill_level(self, skill):
        # Proxy to rules
        player = self.session.query(Player).first()
        return get_skill_level(player, skill)

    def award_skill_xp(self, skill, amount):
        # Proxy to rules
        player = self.session.query(Player).first()
        return award_skill_xp(player, skill, amount)

    def craft_item(self, recipe_id):
        player = self.session.query(Player).first()
        return self.inventory.craft_item(player, recipe_id)

    def buy_item(self, template_id):
        player = self.session.query(Player).first()
        return self.inventory.buy_item(player, template_id)

    def sell_item(self, item_id):
        player = self.session.query(Player).first()
        return self.inventory.sell_item(player, item_id)

    def _initialize_world(self):
        # Ensure player exists
        self.player = self.session.query(Player).options(joinedload(Player.inventory)).first()
        if not self.player:
            print(f"DM: Creating new Hero '{PLAYER_START_CONFIG['name']}'...")
            cfg = PLAYER_START_CONFIG
            self.player = Player(
                name=cfg['name'],
                hp_current=cfg['hp_current'], hp_max=cfg['hp_max'],
                stats=cfg['stats'],
                x=cfg['start_pos']['x'], 
                y=cfg['start_pos']['y'], 
                z=cfg['start_pos']['z'],
                quest_state={"active_quests": []}
            )
            
            # Add default gear
            for item in cfg['inventory']:
                self.session.add(InventoryItem(
                    name=item['name'], 
                    slot=item['slot'], 
                    is_equipped=item['is_equipped'], 
                    player=self.player
                ))
            
            self.session.add(self.player)
            
            # --- Generate Maps ---
            builder = LevelBuilder(self.session)
            builder.generate_tutorial_dungeon(self.player)
            builder.generate_town(1) # Force Generate Town
            
            # Reveal Starting Area
            self.update_visited(self.player.x, self.player.y, self.player.z)
            
            # --- DEBUG: Auto-Rescue NPCs for Testing ---
            # Move everyone to town immediately based on config
            for npc_key, coords in NPC_START_CONFIG.items():
                npc = self.session.query(NPC).filter(NPC.name.like(f"%{npc_key}%")).first()
                if npc:
                    npc.x = coords['x']
                    npc.y = coords['y']
                    npc.z = coords['z']
            
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

    def player_interact(self, action, target_type, target_index):
        return self.interactions.handle_interaction(action, target_type, target_index)

    def chat_with_npc(self, npc_index, message):
        return self.dialogue.chat(npc_index, message)











        


    def update_visited(self, cx, cy, cz):
        return self.movement.update_visited(cx, cy, cz)



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
        
        elif z == 4:
            if x==0 and y==0: return "Frozen Entrance"
            return "Glacial Cavern"

        return None

    def investigate_room(self):
        """Active Skill: Analyze location for hidden secrets."""
        from .rules import roll_dice
        from .database import Monster, WorldObject
        from sqlalchemy.orm.attributes import flag_modified
        
        
        pl = self.session.query(Player).first()
        skill_bonus = self.get_skill_level("investigation")
        roll = roll_dice(20) + skill_bonus
        
        # Room Description
        x, y, z = pl.x, pl.y, pl.z
        
        # 0. Force Update Visited (Clear Fog of War)
        self.movement.update_visited(x, y, z)
        
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
        # Use fresh query to avoid DetachedInstanceError across threads
        player = self.session.query(Player).first()
        if not player: return {} # Should not happen

        map_data = {}
        px, py, pz = player.x, player.y, player.z
        
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

        from .quests import QuestManager, QUEST_DATABASE
        qm = QuestManager(self.session, player)

        # NPCs
        npcs = self.session.query(NPC).filter(NPC.x != None, NPC.z == pz).all()
        npc_list = []
        for n in npcs:
            img = "player.png"
            if "Seraphina" in n.name: img = "seraphina.png"
            elif "Elara" in n.name: img = "elara.png"
            elif "Gareth" in n.name: img = "warrior2.png"
            elif "Elder" in n.name: img = "elder.png"
            
            # Quest Indicator Logic
            q_status = "none"
            # 1. Check for Turn Ins
            for qid, q_data in QUEST_DATABASE.items():
                if q_data.get("giver") in n.name: # Flexible Match
                    # Is it active?
                    status = qm.get_status(qid)
                    if status == "active":
                        if qm.can_complete(qid):
                            q_status = "turn_in"
                            break
            
            # 2. Check for New Quests (only if no turn in found)
            if q_status == "none":
                 for qid, q_data in QUEST_DATABASE.items():
                    if q_data.get("giver") in n.name:
                        status = qm.get_status(qid)
                        if status == "available":
                            # Check Requirements if defined in QUEST_DATABASE
                            reqs = q_data.get("requirements", {})
                            blocked = False
                            
                            # Level Check
                            if "min_level" in reqs and self.player.level < reqs["min_level"]: blocked = True
                            
                            # Prerequisite Quest Check (Custom logic needed as it's not standard in DB yet?)
                            # Actually let's just check the "active" list vs specific logic
                            if qid == "titanium_hunt":
                                # Gareth's second quest requires Iron Supply done
                                if "iron_supply" not in self.player.quest_state.get("completed", []):
                                    blocked = True
                            
                            if qid == "elemental_reagents":
                                # Seraphina's second quest requires Herbal Remedy done
                                if "herbal_remedy" not in self.player.quest_state.get("completed", []):
                                    blocked = True

                            if not blocked:
                                 q_status = "available"
                                 break
            
            # DEBUG
            if q_status != "none":
                print(f"DEBUG: NPC {n.name} has quest status: {q_status}")

            npc_list.append({
                "xyz": [n.x, n.y, n.z], 
                "name": n.name, 
                "id": n.id, 
                "asset": img,
                "quest_status": q_status 
            })
            
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
        # 1. Fetch nearby tiles
        nearby_tiles = self.session.query(MapTile).filter(
            MapTile.x.between(player.x - 1, player.x + 1),
            MapTile.y.between(player.y - 1, player.y + 1),
            MapTile.z == player.z
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
        objs = self.session.query(WorldObject).filter_by(z=player.z).all()
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
            qs = player.quest_state or {}
            
            # 1. New Dictionary System
            active_q = qs.get("active", {})
            with open("debug_quest_log.txt", "w") as f:
                 f.write(f"Active: {active_q}\n")
                 f.write(f"DB Keys: {list(QUEST_DATABASE.keys())}\n")
            
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
                "xyz": [player.x, player.y, player.z],
                "stats": player.stats,
                "skills": player.skills or {},
                "hp": player.hp_current,
                "max_hp": player.hp_max,
                "level": player.level or 1,
                "xp": player.xp or 0,
                "gold": player.gold or 0,
                "quest_state": player.quest_state or {},
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
                    for i in player.inventory if i
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



    def _generate_town(self, z):
        """Generate the Oakhaven Town map."""
        builder = LevelBuilder(self.session)
        builder.generate_town(z)

    def upgrade_stat(self, stat_name):
        """Spend a point to upgrade a stat."""
        from sqlalchemy.orm.attributes import flag_modified
        
        pl = self.session.query(Player).first()
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

    def choose_skill(self, skill_id):
        """Learn a level-up feat."""
        from sqlalchemy.orm.attributes import flag_modified
        
        valid_skills = ["cleave", "heavy_strike", "kick", "rage"]
        if skill_id not in valid_skills:
            return "Invalid skill."
            
        pl = self.session.query(Player).first()
        current_skills = dict(pl.skills or {})
        
        # 1. Check Capacity (1 feat per 4 levels)
        allowed_feats = pl.level // 4
        if allowed_feats < 1:
            return "You are not high enough level to learn a feat."
            
        # Count currently known feats
        known_feats_count = sum(1 for s in valid_skills if s in current_skills)
        
        if known_feats_count >= allowed_feats:
             return "You have no unspent feat points."
             
        # 2. Check if already known
        if skill_id in current_skills:
            return "You already know this skill."
            
        # Add Skill
        current_skills[skill_id] = 1
        pl.skills = current_skills
        flag_modified(pl, "skills")
        self.session.commit()
        
        return f"Learned {skill_id.replace('_', ' ').title()}!"
