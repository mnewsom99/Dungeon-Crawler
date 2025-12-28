
# Quest Definitions and Logic

QUEST_DATABASE = {
    "elemental_balance": {
        "title": "Elemental Balance",
        "giver": "Elder Aethelgard",
        "description": "The North Forest is blocked. Clear the 4 Elemental Dungeons to open trade routes.",
        "objectives": [
            {"type": "kill_boss", "target": "Fire Guardian", "count": 1},
            {"type": "kill_boss", "target": "Ice Guardian", "count": 1},
            {"type": "kill_boss", "target": "Earth Guardian", "count": 1},
            {"type": "kill_boss", "target": "Air Guardian", "count": 1}
        ],
        "prevent_turn_in": True, # Cannot turn in until objectives complete
        "rewards": {
             "special": "tax_free_house_plot"
        }
    },
    
    "iron_supply": {
        "title": "Iron Supply",
        "giver": "Gareth Ironhand",
        "description": "Gareth needs raw Iron Ore to restock the smithy.",
        "objectives": [
            {"type": "item", "target": "Iron Ore", "count": 1}
        ],
        "repeatable": True,
        "rewards": {
            "gold": 50
        }
    },

    "titanium_hunt": {
        "title": "The Legendary Metal",
        "giver": "Gareth Ironhand",
        "description": "Find a Titanium Fragment in the Earth Dungeon.",
        "objectives": [
            {"type": "item", "target": "Titanium Fragment", "count": 1}
        ],
        "rewards": {
            "gold": 500,
            "items": ["Titanium Greatsword"]
        }
    },
    
    "herbal_remedy": {
        "title": "Herbal Remedy",
        "giver": "Seraphina",
        "description": "Collect Mystic Herbs for Seraphina's potions.",
        "objectives": [
            {"type": "item", "target": "Mystic Herb", "count": 1}
        ],
        "repeatable": True,
        "rewards": {
            "gold": 30
        }
    },

    "elemental_reagents": {
        "title": "Fire and Ice",
        "giver": "Seraphina",
        "description": "Retrieve an Everburning Cinder and a Freezing Spike for a master potion.",
        "objectives": [
            {"type": "item", "target": "Everburning Cinder", "count": 1},
            {"type": "item", "target": "Freezing Spike", "count": 1}
        ],
        "rewards": {
            "items": ["Potion of Power"]
        }
    }
}

class QuestManager:
    def __init__(self, session, player):
        self.session = session
        self.player = player
        # Ensure quest state structure exists
        if not self.player.quest_state:
            self.player.quest_state = {"active": {}, "completed": []}
            
    def get_status(self, quest_id):
        qs = self.player.quest_state
        if quest_id in qs.get("completed", []): return "completed"
        if quest_id in qs.get("active", {}): return "active"
        return "available"

    def accept_quest(self, quest_id):
        if quest_id not in QUEST_DATABASE: return False
        
        q_data = QUEST_DATABASE[quest_id]
        
        # Check Requirements
        reqs = q_data.get("requirements", {})
        if "min_level" in reqs and self.player.level < reqs["min_level"]:
            return False # Too low level
        if "max_level" in reqs and self.player.level > reqs["max_level"]:
            return False # Too high level (e.g. tutorial quest)
        
        qs = self.player.quest_state
        # Init structure if missing
        if "active" not in qs: qs["active"] = {}
        
        # Add to active
        qs["active"][quest_id] = {"progress": {}}
        
        # Save
        self.player.quest_state = qs
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self.player, "quest_state")
        
        print(f"Quest Accepted: {QUEST_DATABASE[quest_id]['title']}")
        return True

    def can_complete(self, quest_id):
        """Check if player has required items/kills."""
        if quest_id not in QUEST_DATABASE: return False
        
        q_data = QUEST_DATABASE[quest_id]
        qs_active = self.player.quest_state.get("active", {}).get(quest_id, {})
        progress = qs_active.get("progress", {})

        # Check all objectives
        for obj in q_data.get("objectives", []):
            if obj["type"] == "item":
                # Check inventory
                required_name = obj["target"]
                count_needed = obj.get("count", 1)
                
                found_count = 0
                for item in self.player.inventory:
                    if item.name == required_name:
                        found_count += 1
                
                if found_count < count_needed:
                    return False
            
            elif obj["type"] == "kill_boss":
                 target = obj["target"]
                 count_needed = obj.get("count", 1)
                 current = progress.get(target, 0)
                 if current < count_needed:
                     return False
                     
        return True

    def record_kill(self, enemy_name):
        """Update progress for kill objectives."""
        if not self.player.quest_state: return
        
        qs = self.player.quest_state
        changed = False
        
        # Check all active quests
        for qid, q_data in qs.get("active", {}).items():
            db_data = QUEST_DATABASE.get(qid)
            if not db_data: continue
            
            for obj in db_data.get("objectives", []):
                if obj["type"] == "kill_boss" and obj["target"] == enemy_name:
                    # Update Progress
                    prog = q_data.get("progress", {})
                    old_val = prog.get(enemy_name, 0)
                    if old_val < obj.get("count", 1):
                         prog[enemy_name] = old_val + 1
                         q_data["progress"] = prog
                         changed = True
                         print(f"Quest Update: {db_data['title']} - Killed {enemy_name} ({prog[enemy_name]}/{obj.get('count', 1)})")
        
        if changed:
            self.player.quest_state = qs
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(self.player, "quest_state")
            self.session.commit()

    def complete_quest(self, quest_id):
        """Deduct items, grant rewards, move to completed."""
        if not self.can_complete(quest_id): return False
        
        q_data = QUEST_DATABASE[quest_id]
        
        # 1. Deduct Items
        from .inventory_system import InventorySystem
        inv_sys = InventorySystem(self.session)
        
        for obj in q_data.get("objectives", []):
            if obj["type"] == "item":
                inv_sys.remove_item_by_name(obj["target"], obj.get("count", 1))

        # 2. Grant Rewards
        rewards = q_data.get("rewards", {})
        
        # XP Reward
        if "xp" in rewards:
            self.player.xp = (self.player.xp or 0) + rewards["xp"]
            print(f"Awarded {rewards['xp']} XP.")
            # Simple Level Up Logic could go here (call rules.check_level_up)
            
        if "gold" in rewards:
            self.player.gold += rewards["gold"]
            
        if "items" in rewards:
            from .items import ITEM_TEMPLATES
            from .database import InventoryItem
            
            for item_name_or_key in rewards["items"]:
                # Try finding key in templates
                # Normalize key? We stored "Titanium Greatsword" as name in Quest, 
                # but template might be keys. Ideally Quest DB uses Template Keys.
                # For now, let's assume we look up by name match or key match.
                template = None
                for k, v in ITEM_TEMPLATES.items():
                    if v["name"] == item_name_or_key or k == item_name_or_key:
                        template = v
                        break
                        
                if template:
                     self.session.add(InventoryItem(
                         name=template['name'], 
                         item_type=template['type'], 
                         slot=template['slot'],
                         properties=template['properties'], 
                         player=self.player
                     ))

        # 3. Update State
        qs = self.player.quest_state
        if quest_id in qs["active"]:
            del qs["active"][quest_id]
        
        if "completed" not in qs: qs["completed"] = []
        if not q_data.get("repeatable"):
            qs["completed"].append(quest_id)
            
        self.player.quest_state = qs
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self.player, "quest_state")
        self.session.commit()
        
        print(f"Quest Completed: {q_data['title']}")
        return True
