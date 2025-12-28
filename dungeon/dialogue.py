from sqlalchemy.orm.attributes import flag_modified
from .database import NPC, MapTile
# from .ai_bridge import AIBridge # Removed LLM
from .scripts import NPC_SCRIPTS

class DialogueSystem:
    def __init__(self, dm):
        self.dm = dm

    @property
    def session(self):
        return self.dm.session

    @property
    def player(self):
        return self.dm.player

    def chat_with_npc(self, npc_index, message):
        """Handle persistent chat with an NPC using Script Trees."""
        # 1. Lookup by ID
        target = self.session.query(NPC).filter_by(id=npc_index).first()
        
        if not target:
             return "That person does not exist.", "Unknown", False
             
        # 2. Loose Range Check
        dist = abs(target.x - self.player.x) + abs(target.y - self.player.y)
        if target.z != self.player.z or dist > 3:
             return "You have wandered too far away.", "System", False
             
        # 3. Get / Init State
        state = target.quest_state or {}
        
        # Determine Script Key
        script_key = target.name
        # Handle variations or defaults
        if "Gareth" in target.name: script_key = "Gareth Ironhand"
        if "Elder" in target.name: script_key = "Elder Aethelgard"
        
        script = NPC_SCRIPTS.get(script_key)
        if not script:
            return f"{target.name} has nothing to say.", target.name, False

        # Current Node
        current_node_id = state.get("current_node")
        
        # Special: Check if we should switch to "town_start"
        # If NPC is in Town (z=1) but node is still Dungeon defaults
        if target.z == 1 and (not current_node_id or current_node_id == "end_rescue"):
             if "town_start" in script["nodes"]:
                  current_node_id = "town_start"
                  state["current_node"] = current_node_id

        if not current_node_id: 
            current_node_id = script["start_node"]
            
        # 3b. Auto-Reset if stuck at end node (Leaf node reset)
        # If we are initializing and the current node is "end" or has no options, reset.
        if message == "__INIT__":
             node_data = script["nodes"].get(current_node_id)
             if not node_data or not node_data.get("options") or current_node_id == "end":
                 # Reset Logic
                 current_node_id = "town_start" if target.z == 1 and "town_start" in script["nodes"] else script["start_node"]
                 state["current_node"] = current_node_id
        
        current_node = script["nodes"].get(current_node_id)
        
        # 4b. Dynamic Option Filtering via Quest Manager
        from .quests import QuestManager
        qm = QuestManager(self.session, self.player)
        
        # 4. Filter Options (Pre-Process)
        # We need to filter options BEFORE processing input idx to ensure indices match visible list
        raw_options = current_node.get("options", [])
        visible_options = []
        
        for opt in raw_options:
            # Check Item Requirement
            if "req_item" in opt:
                required = opt["req_item"]
                has_it = any(i.name == required for i in self.player.inventory)
                if not has_it:
                    continue
            
            # Check Quest Requirement (e.g. "req_quest_active": "titanium_hunt")
            if "req_quest_active" in opt:
                 status = qm.get_status(opt["req_quest_active"])
                 if status != "active": continue

            if "req_quest_complete" in opt:
                 status = qm.get_status(opt["req_quest_complete"])
                 if status != "completed": continue
                 
            # Action Hook: Check "complete_quest" ability
            # If an action is 'complete_quest:titanium_hunt', check if we can actually complete it
            if "action" in opt and opt["action"].startswith("complete_quest:"):
                qid = opt["action"].split(":")[1]
                if not qm.can_complete(qid):
                    continue
            
            visible_options.append(opt)

        # 5. Process Input (If message matches an option)
        # We expect message to be an Index (1-based) OR text
        reply = ""
        
        if message == "__INIT__":
             # Just show current node text
             pass
        else:
             # Check if message maps to a VISIBLE option
             selected_opt = None
             
             # Try Integer match
             if message.isdigit():
                 idx = int(message) - 1
                 if 0 <= idx < len(visible_options):
                     selected_opt = visible_options[idx]
             
             # If valid selection
             if selected_opt:
                 # Execute Action Hook
                 if "action" in selected_opt:
                     self.handle_action(selected_opt["action"], target, state)
                 
                 # Advance Node
                 next_id = selected_opt.get("next")
                 if next_id:
                     current_node_id = next_id
                     current_node = script["nodes"].get(current_node_id)
                     state["current_node"] = current_node_id
                     
                     # Re-calculate visible options for the NEW node
                     # (Refactor this duplication later or loop it)
                     # For now, simplistic re-filter
                     raw_options = current_node.get("options", [])
                     visible_options = []
                     for opt in raw_options:
                        if "req_item" in opt:
                            required = opt["req_item"]
                            found = any(i.name == required for i in self.player.inventory)
                            if not found: continue
                        if "action" in opt and opt["action"].startswith("complete_quest:"):
                            qid = opt["action"].split(":")[1]
                            if not qm.can_complete(qid): continue
                        visible_options.append(opt)
 
             else:
                 reply += "(Invalid option. Please type the number.)\n"

        # 6. Render Output
        # Text + Options List
        reply += current_node["text"]
        
        if visible_options:
            reply += "\n\n"
            for i, opt in enumerate(visible_options):
                reply += f"{i+1}. {opt['label']}\n"
        else:
             # If we have no options, but we just completed a quest, maybe we should offer a 'Back' button?
             # For now, just end.
            reply += "\n(End of conversation)"

        # Save State
        state["history"] = [reply] # Minimal history needed now
        target.quest_state = state
        flag_modified(target, "quest_state")
        self.session.commit()
        
        # Check Trade Status (Simple logic: if node is 'shop_info' -> enable trade?)
        # Or just use the old logic?
        # Let's say if we are in town, we enable trade.
        can_trade = (target.z == 1) 
        
        return reply, target.name, can_trade


    def handle_action(self, action_name, npc, state):
        """Execute special logic triggers."""
        print(f"DIALOGUE ACTION: {action_name}")
        
        if action_name.startswith("accept_quest:"):
             qid = action_name.split(":")[1]
             from .quests import QuestManager
             qm = QuestManager(self.session, self.player)
             qm.accept_quest(qid)
             return

        if action_name.startswith("complete_quest:"):
             qid = action_name.split(":")[1]
             from .quests import QuestManager
             qm = QuestManager(self.session, self.player)
             qm.complete_quest(qid)
             return
             
        if action_name == "rescue_elara":
            state["status"] = "escorting"
            # Unlock Secret Door
            door_tile = self.session.query(MapTile).filter_by(x=2, y=30, z=0).first()
            if door_tile:
                door_tile.tile_type = "door"
                door_tile.is_visited = True 
                flag_modified(door_tile, "tile_type")
            # Move Elara closer
            npc.x = 2
            
        elif action_name == "rescue_gareth":
            state["status"] = "rescued"
            npc.x = 8
            npc.y = 8
            npc.z = 1 # Town
            npc.location = "Smithy"
            
        elif action_name == "rescue_seraphina":
            state["status"] = "rescued"
            npc.x = -8
            npc.y = 8
            npc.z = 1 # Town
            npc.location = "Alchemy Shop"

        elif action_name == "follow_me":
             state["status"] = "following"
             if "home" not in state:
                 state["home"] = [npc.x, npc.y, npc.z]
             
        elif action_name == "stay_here":
             state["status"] = "waiting"

        elif action_name == "give_ore":
            # Remove 1 Iron Ore
            from .inventory_system import InventorySystem
            inv_sys = InventorySystem(self.dm.session)
            # Find item
            item = next((i for i in self.player.inventory if i.name == "Iron Ore"), None)
            if item:
                inv_sys.remove_item(item.id, 1)
                self.player.gold += 50
                state["has_ore"] = True # Remember we gave it
                print("Action: Gave Ore. +50 Gold.")

        elif action_name == "give_herb":
            from .inventory_system import InventorySystem
            inv_sys = InventorySystem(self.dm.session)
            item = next((i for i in self.player.inventory if i.name == "Mystic Herb"), None)
            if item:
                inv_sys.remove_item(item.id, 1)
                self.player.gold += 30
                print("Action: Gave Herb. +30 Gold.")
                
        elif action_name == "start_elemental_quest":
             # We need a proper Quesy system, but for now we put it in the Player's quest_state or similar
             # Or we attach it to the Elder's state which the UI reads?
             # The UI reads 'data.npcs' to infer quests.
             # Let's set a global flag on the player!
             qs = self.player.quest_state or {}
             qs["active_quests"] = qs.get("active_quests", [])
             if "Elemental Dungeons" not in qs["active_quests"]:
                 qs["active_quests"].append("Elemental Dungeons")
                 flag_modified(self.player, "quest_state")
                 self.session.add(self.player)
                 self.session.commit()
                 print("Quest Started: Elemental Dungeons")

        elif action_name == "start_gareth_quest":
             qs = self.player.quest_state or {}
             qs["active_quests"] = qs.get("active_quests", [])
             if "Titanium Hunt" not in qs["active_quests"]:
                 qs["active_quests"].append("Titanium Hunt")
                 flag_modified(self.player, "quest_state")
                 self.session.add(self.player)
                 self.session.commit()
                 
        elif action_name == "start_seraphina_quest":
             qs = self.player.quest_state or {}
             qs["active_quests"] = qs.get("active_quests", [])
             if "Elemental Reagents" not in qs["active_quests"]:
                 qs["active_quests"].append("Elemental Reagents")
                 flag_modified(self.player, "quest_state")
                 self.session.add(self.player)
                 self.session.commit()
                 
        elif action_name == "give_reagents":
             # Remove Cinder and Spike
             from .inventory_system import InventorySystem
             inv_sys = InventorySystem(self.dm.session)
             cinder = next((i for i in self.player.inventory if i.name == "Everburning Cinder"), None)
             spike = next((i for i in self.player.inventory if i.name == "Freezing Spike"), None)
             
             if cinder and spike:
                 inv_sys.remove_item(cinder.id, 1)
                 inv_sys.remove_item(spike.id, 1)
                 
                 # Grant Reward: Potion of Power
                 from .database import InventoryItem
                 from .items import ITEM_TEMPLATES
                 t = ITEM_TEMPLATES["potion_of_power"]
                 self.session.add(InventoryItem(
                     name=t['name'], item_type=t['type'], slot=t['slot'],
                     properties=t['properties'], player=self.player
                 ))
                 self.session.commit()
                 
                 # Complete Quest
                 qs = self.player.quest_state or {}
                 if "Elemental Reagents" in qs.get("active_quests", []):
                     qs["active_quests"].remove("Elemental Reagents")
                     qs["completed_quests"] = qs.get("completed_quests", []) + ["Elemental Reagents"]
                     flag_modified(self.player, "quest_state")
                     self.session.commit()
                     print("Quest Complete: Elemental Reagents")

        elif action_name == "give_titanium":
             from .inventory_system import InventorySystem
             inv_sys = InventorySystem(self.dm.session)
             item = next((i for i in self.player.inventory if i.name == "Titanium Fragment"), None)
             
             if item:
                 inv_sys.remove_item(item.id, 1)
                 self.player.gold += 500
                 
                 from .database import InventoryItem
                 from .items import ITEM_TEMPLATES
                 t = ITEM_TEMPLATES["greatsword"]
                 self.session.add(InventoryItem(
                     name="Titanium Greatsword", item_type=t['type'], slot=t['slot'],
                     properties={"damage": "2d8", "icon": "⚔️"}, player=self.player
                 ))
                 self.session.commit()
                 
                 qs = self.player.quest_state or {}
                 if "Titanium Hunt" in qs.get("active_quests", []):
                     qs["active_quests"].remove("Titanium Hunt")
                     qs["completed_quests"] = qs.get("completed_quests", []) + ["Titanium Hunt"]
                     flag_modified(self.player, "quest_state")
                     self.session.commit()
                     print("Quest Complete: Titanium Hunt")

