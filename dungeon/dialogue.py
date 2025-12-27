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
                     
                     # Re-calculate visible options for the NEW node to show them immediately
                     raw_options = current_node.get("options", [])
                     visible_options = []
                     for opt in raw_options:
                        if "req_item" in opt:
                            required = opt["req_item"]
                            has_it = any(i.name == required for i in self.player.inventory)
                            if not has_it:
                                continue
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
