from sqlalchemy.orm.attributes import flag_modified
from .database import NPC, MapTile
from .ai_bridge import AIBridge

class DialogueSystem:
    def __init__(self, dm):
        self.dm = dm

    @property
    def session(self):
        return self.dm.session

    @property
    def ai(self):
        return self.dm.ai

    @property
    def player(self):
        return self.dm.player

    def get_npc_greeting(self, npc):
        """Generates or retrieves the initial greeting for an NPC."""
        state = npc.quest_state or {}
        
        # 1. Check for Pre-written greeting (Fast Path)
        if state.get("greeting"):
            return state["greeting"]
            
        # 2. Generate via LLM (Slow Path)
        print(f"Dialogue: Generating greeting for {npc.name}...")
        prompt = f"The player has just approached {npc.name} ({npc.location}, {npc.persona_prompt}). {npc.name} speaks a desperate or hopeful greeting line."
        greeting = self.ai.chat(prompt, persona="npc")
        return greeting

    def chat_with_npc(self, npc_index, message):
        """Handle persistent chat with an NPC."""
        # 1. Lookup by ID
        target = self.session.query(NPC).filter_by(id=npc_index).first()
        
        if not target:
             return "That person does not exist.", "Unknown"
             
        # 2. Loose Range Check
        dist = abs(target.x - self.player.x) + abs(target.y - self.player.y)
        if target.z != self.player.z or dist > 3:
             return "You have wandered too far away.", "System"
             
        # Get History
        state = target.quest_state or {}
        history = state.get("history", [])
        
        if message == "__INIT__":
            # Return existing history for UI
            full_log = "\n\n".join(history[-10:])
            if not full_log: full_log = "..."
            return full_log, target.name
        
        # Append User Message
        history.append(f"Player: {message}")
        
        # Generate Response (Limit context)
        context = "\n".join(history[-6:])
        prompt = f"""
        You are {target.name}. Location: {target.location}.
        Persona: {target.persona_prompt}
        
        Conversation So Far:
        {context}
        
        Reply to the player's last message naturally. Keep it concise (1-2 sentences).
        """
        
        reply = self.ai.chat(prompt, persona="npc")
        
        # QUEST TRIGGER CHECK (Specific to Elara/Tutorial for now)
        # We might move this to a QuestManager later, but for now we keep it close to the dialogue interaction.
        current_status = state.get("status", "trapped")
        
        p_low = message.lower()
        player_wants_to_go = "lead" in p_low or "guide" in p_low or "go" in p_low or "passage" in p_low or "out" in p_low
        
        if target.name == "Elara" and current_status == "trapped" and player_wants_to_go:
            state["status"] = "escorting"
            
            # Reveal Door
            door_tile = self.session.query(MapTile).filter_by(x=2, y=30, z=0).first()
            if door_tile:
                door_tile.tile_type = "door"
                door_tile.is_visited = True 
                flag_modified(door_tile, "tile_type")
            else:
                door_tile = MapTile(x=2, y=30, z=0, tile_type="door", is_visited=True)
                self.session.add(door_tile)
            
            # Move Elara
            target.x = 1
            target.y = 30
            
            reply += "\n\n(Elara nods with determination. She rushes to the stone wall, feels for a loose brick, and suddenly a hidden door grinds open!)"
        
        # --- Gareth Rescue Logic ---
        elif target.name == "Gareth Ironhand" and current_status == "trapped" and (player_wants_to_go or "save" in p_low):
             state["status"] = "rescued"
             target.x = 8
             target.y = 8
             target.z = 1 # Oakhaven
             target.location = "Gareth's Smithy (Oakhaven)"
             reply += "\n\n(Gareth lets out a hearty laugh.) 'Right then! I'll meet you top-side. Beers are on me!'"

        # --- Seraphina Rescue Logic ---
        elif target.name == "Seraphina" and current_status == "trapped" and (player_wants_to_go or "save" in p_low):
             state["status"] = "rescued"
             target.x = -8
             target.y = 8
             target.z = 1 # Oakhaven
             target.location = "Seraphina's Alchemy Shop (Oakhaven)"
             reply += "\n\n(Seraphina gathers her scrolls.) 'Finally! The mana down here was giving me a headache. See you in town!'"

        # --- Shop Quests (Town) ---
        can_trade = False
        hint = ""
        
        if target.name == "Gareth":
            shop_status = state.get("shop_status", "closed")
            
            if shop_status == "open":
                can_trade = True
            else:
                # Check for Ore
                has_ore = any(i.name == "Iron Ore" for i in self.player.inventory)
                if has_ore:
                    # Unlock!
                    state["shop_status"] = "open"
                    can_trade = True
                    hint = "(SYSTEM: The player has brought the Iron Ore! Thank them heartily and declare the shop OPEN!)"
                    
                    # Remove Ore
                    ore = next(i for i in self.player.inventory if i.name == "Iron Ore")
                    self.session.delete(ore)
                else:
                    hint = "(SYSTEM: The player wants to trade. Tell them you need **Iron Ore** first. Mention some rocks to the EAST.)"

        elif target.name == "Seraphina":
            shop_status = state.get("shop_status", "closed")
            
            if shop_status == "open":
                can_trade = True
            else:
                # Check for Herbs
                has_herb = any(i.name == "Mystic Herb" for i in self.player.inventory)
                if has_herb:
                    # Unlock!
                    state["shop_status"] = "open"
                    can_trade = True
                    hint = "(SYSTEM: The player has brought the Mystic Herb! Thank them and open the apothecary!)"
                    
                    # Remove Herb
                    herb = next(i for i in self.player.inventory if i.name == "Mystic Herb")
                    self.session.delete(herb)
                else:
                    hint = "(SYSTEM: The shop is closed. Tell the player you need a **Mystic Herb** from the garden behind your shop (WEST).)"

        if hint:
            prompt += f"\n{hint}"
        
        reply = self.ai.chat(prompt, persona="npc")
        
        # ... (Rescue logic can remain, though less relevant in Town) ...

        # Append Reply
        history.append(f"{target.name}: {reply}")
        
        # Save State
        state["history"] = history
        target.quest_state = state
        flag_modified(target, "quest_state")
        self.session.commit()
        
        return reply, target.name, can_trade
