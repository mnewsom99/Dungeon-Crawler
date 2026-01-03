from sqlalchemy.orm.attributes import flag_modified
from .database import NPC, MapTile, Player
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
        # Always query fresh to ensure attachment to current thread's session
        return self.session.query(Player).first()

    def chat_with_npc(self, npc_index, message):
        """Handle persistent chat with an NPC using Script Trees."""
        # 1. Lookup by ID
        target = self.session.query(NPC).filter_by(id=npc_index).first()
        
        if not target:
             return "That person does not exist.", "Unknown", False
             
        # 2. Loose Range Check
        dist = abs(target.x - self.player.x) + abs(target.y - self.player.y)
        print(f"DEBUG: Chat Range Check: Player({self.player.x},{self.player.y},{self.player.z}) vs NPC({target.x},{target.y},{target.z}) -> Dist: {dist}")
        
        if target.z != self.player.z or dist > 10: # Relaxed to 10 for debug
             return f"You have wandered too far away. (Dist: {dist}, Z: {target.z}/{self.player.z})", "System", False
             
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
                     action_msg = self.handle_action(selected_opt["action"], target, state)
                     if action_msg:
                         reply += f"\n\n\n**[{action_msg}]**"
                 
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
        if "text_dynamic" in current_node:
            dynamic_text = self.resolve_dynamic_text(current_node["text_dynamic"], target)
            reply += dynamic_text
        else:
            reply += current_node["text"]
        
        if visible_options:
            reply += "\n\n"
            for i, opt in enumerate(visible_options):
                reply += f"{i+1}. {opt['label']}\n"
        else:
             # If we have no options, using dynamic text might imply we need auto-generated options? 
             # For now, assumes scripts provide options or we add a "Bye" default.
            if "text_dynamic" in current_node:
                 reply += "\n\n1. Goodbye." # Fallback for dynamic nodes
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

    def resolve_dynamic_text(self, handler, npc):
        """Generate text based on game state."""
        from .quests import QuestManager, QUEST_DATABASE
        qm = QuestManager(self.session, self.player)
        
        if handler == "elder_status":
            # Check Elemental Balance Quest
            q_id = "elemental_balance"
            status = qm.get_status(q_id)
            
            if status == "available":
                return "Hero! The Elemental Dungeons still block our trade routes. Attempts to enter the forest are met with fire and ice."
            elif status == "completed":
                return "The trade routes are open, and Oakhaven prospers thanks to you. Your home is being built as we speak!"
            elif status == "active":
                # Check specifics
                prog = self.player.quest_state.get("active", {}).get(q_id, {}).get("progress", {})
                
                bosses = {
                    "Magma Weaver": "Fire Dungeon",
                    "Ice Guardian": "Ice Dungeon", 
                    "Earth Guardian": "Earth Dungeon",
                    "Air Guardian": "Air Dungeon"
                }
                
                killed = []
                remaining = []
                
                for boss, loc in bosses.items():
                    if prog.get(boss, 0) >= 1:
                        killed.append(loc)
                    else:
                        remaining.append(loc)
                
                if not killed:
                    return "You have accepted the task, but the Beasts still rule. You must clear the Fire, Ice, Earth, and Air dungeons."
                
                if not remaining:
                    return "Incredible... I can feel the balance returning! You have slain all the Guardians! Speak to me to claim your reward."
                
                msg = f"You are making progress. You have cleared: {', '.join(killed)}."
                msg += f"\nRemains to be cleansed: {', '.join(remaining)}."
                return msg

        elif handler == "seraphina_status":
            # 1. Check Herbal Remedy (Repeatable)
            status_herb = qm.get_status("herbal_remedy")
            
            # Inventory Check
            has_herb = False
            for i in self.player.inventory:
                 if i.name == "Mystic Herb": has_herb = True
            
            if status_herb == "active":
                if has_herb:
                    return "I smell the faint aroma of Mystic Herbs on you! Please, let me put them to use."
                else:
                    return "My potion stocks are running low. Please, if you find any Mystic Herbs in the dungeon, bring them to me."
            
            # 2. Check Elemental Reagents
            status_elem = qm.get_status("elemental_reagents")
            if status_elem == "active":
                has_fire = any(i.name == "Everburning Cinder" for i in self.player.inventory)
                has_ice = any(i.name == "Freezing Spike" for i in self.player.inventory)
                
                if has_fire and has_ice:
                    return "Incredible! I can feel the opposing energies radiating from your pack. You have both reagents!"
                elif has_fire:
                    return "You have the Cinder, good. Now seek the Freezing Spike in the Ice Dungeon."
                elif has_ice:
                    return "The Spike is safe. Now find the Everburning Cinder in the Fire Dungeon."
                else:
                    return "I need a Cinder from the Fire Dungeon and a Spike from the Ice Dungeon to brew this master potion."

            return "Welcome to my shop. The mana currents are stable today. How can I aid you?"

        elif handler == "gareth_status":
             # 1. Check Iron Supply
             status_iron = qm.get_status("iron_supply")
             has_iron = any(i.name == "Iron Ore" for i in self.player.inventory)
             
             if status_iron == "active":
                 if has_iron:
                     return "Hmph. That bag looks heavy. Did you bring the Iron Ore?"
                 else:
                     return "The forge is going cold, lad. I need that Iron Ore from the mines."
             
             # 2. Check Titanium
             status_ti = qm.get_status("titanium_hunt")
             if status_ti == "active":
                 has_ti = any(i.name == "Titanium Fragment" for i in self.player.inventory)
                 if has_ti:
                     return "By the ancestors! Is that shimmneering metal what I think it is? You found the Titanium!"
                 else:
                     return "The Earth Dungeon is treacherous, but I need that Titanium Fragment to forge a masterpiece."
             
             if status_iron == "completed" and status_ti == "available":
                 return "You proved yourself with the iron. But are you ready for a real challenge? I need a rare metal."

             return "Welcome to the Ironhand Smithy. Finest steel in Oakhaven. Need a weapon sharpened?" 
                
        return f"[Dynamic Text Error: {handler}]"


    def handle_action(self, action_name, npc, state):
        """Execute special logic triggers."""
        print(f"DIALOGUE ACTION: {action_name}")
        
        if action_name.startswith("accept_quest:"):
             qid = action_name.split(":")[1]
             from .quests import QuestManager, QUEST_DATABASE
             qm = QuestManager(self.session, self.player)
             if qm.accept_quest(qid):
                 title = QUEST_DATABASE.get(qid, {}).get("title", qid)
                 return f"Quest Accepted: {title}"
             return None

        if action_name.startswith("complete_quest:"):
             qid = action_name.split(":")[1]
             from .quests import QuestManager, QUEST_DATABASE
             qm = QuestManager(self.session, self.player)
             if qm.complete_quest(qid):
                 title = QUEST_DATABASE.get(qid, {}).get("title", qid)
                 return f"Quest Completed: {title}"
             return None
             
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
            return "Elara is following you."
            
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



