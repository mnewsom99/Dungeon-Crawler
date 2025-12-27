from .database import MapTile, WorldObject, Monster, NPC
from sqlalchemy.orm.attributes import flag_modified

class InteractionManager:
    def __init__(self, dm):
        self.dm = dm
        self.session = dm.session
        # self.player is accessed dynamically via self.dm.player

    def handle_interaction(self, action, target_type, target_index):
        """Dispatches interaction handling based on action type."""
        
        # Ensure player state is fresh
        self.player = self.dm.player 

        if action == "loot" and target_type == "corpse":
            return self._handle_loot(target_index)
            
        elif action == "talk" and target_type == "npc":
            # Just return a simple message, actual chat is handled by dialogue system or 'chat' endpoint
            # But the 'interact' button calls this.
            return self._handle_generic_talk()
            
        elif action == "inspect" and target_type == "secret":
             return self._handle_inspect(target_index)
             
        return "Invalid action."

    def _handle_loot(self, target_index):
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
        
        loot_data = target.loot or []
        if not loot_data:
                self.session.delete(target)
                self.session.commit()
                return "The corpse is empty."
                
        return {"type": "loot_window", "loot": loot_data, "corpse_id": target.id, "name": target.name}

    def _handle_generic_talk(self):
        px, py, pz = self.player.x, self.player.y, self.player.z
        nearby = self.session.query(NPC).filter(
            NPC.x.between(px-1, px+1),
            NPC.y.between(py-1, py+1),
            NPC.z == pz
        ).all()
        
        if not nearby:
            return "No one to talk to."
        
        target = nearby[0]
        
        # Note: We aren't doing the LLM chat generation here anymore for the 'click' 
        # because the new Chat Window UI handles it via /api/chat. 
        # But if this is legacy fallback:
        return f"You greet {target.name}. (Open Chat to talk)"

    def _handle_inspect(self, target_index):
        if target_index.startswith("obj_"):
                oid = int(target_index.split("_")[1])
                obj = self.session.query(WorldObject).filter_by(id=oid).first()
                if not obj: return "It's gone."
                
                if abs(obj.x - self.player.x) > 1 or abs(obj.y - self.player.y) > 1:
                    return "Too far away."
                    
                if obj.obj_type == "chest":
                    loot = (obj.properties or {}).get("loot", [])
                    if not loot: 
                        self.session.delete(obj)
                        self.session.commit()
                        return "It's empty."
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
        
        return "Nothing interesting found."
