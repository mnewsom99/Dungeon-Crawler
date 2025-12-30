from .database import Monster, MapTile, NPC
from sqlalchemy.orm.attributes import flag_modified
import random

class WorldSimulation:
    def __init__(self, dm):
        self.dm = dm
        self.session = dm.session

    def process_environment_turn(self):
        """Handle overworld monster AI (Roaming & Aggro)."""
        if self.dm.combat.is_active(): return None
        
        # Get local monsters (simple bounding box for optimization?)
        # For now, fetch all on level.
        from .database import Player
        player = self.session.query(Player).first()
        if not player: return None
        monsters = self.session.query(Monster).filter_by(z=player.z, is_alive=True).all()
        
        # Cache MapTiles for collision (optimization could be done here, but query is safe enough for <20 monsters)
        
        def is_blocked(tx, ty, tz):
             # Check Wall/Water/Void
             t = self.session.query(MapTile).filter_by(x=tx, y=ty, z=tz).first()
             if not t: return True
             # Allow: floor, grass, floor_wood, open_door, bridge
             allow_list = ["floor", "floor_wood", "grass", "open_door", "bridge"]
             if t.tile_type not in allow_list: return True
             
             # Check Other Monster
             occ = self.session.query(Monster).filter_by(x=tx, y=ty, z=tz, is_alive=True).first()
             if occ: return True
             return False

        alerts = []
        
        for m in monsters:
            dist = max(abs(m.x - player.x), abs(m.y - player.y))
            moved = False
            
            # 1. Aggro Check (Vision Range: 5)
            if dist <= 5:
                # Chase Player
                dx = 0
                dy = 0
                if m.x < player.x: dx = 1
                elif m.x > player.x: dx = -1
                
                if m.y < player.y: dy = 1
                elif m.y > player.y: dy = -1
                
                # Check for "Touching" PLAYER -> Combat Trigger
                # If we are 1 tile away and move closer, we might hit them.
                # Actually, check projected position.
                tx, ty = m.x + dx, m.y + dy
                if tx == player.x and ty == player.y:
                     self.dm.combat.start_combat(m)
                     return "Ambush"
                     
                # Try Move (Manhattan-ish)
                if not is_blocked(tx, ty, m.z):
                    m.x, m.y = tx, ty
                    moved = True
                else:
                    # Try Axis only
                    if dx != 0 and not is_blocked(m.x + dx, m.y, m.z) and (m.x + dx != player.x):
                         m.x += dx
                         moved = True
                    elif dy != 0 and not is_blocked(m.x, m.y + dy, m.z) and (m.y + dy != player.y):
                         m.y += dy
                         moved = True
                         
            # 2. Random Roam (15% Chance)
            elif dist < 20: 
                if random.random() < 0.15:
                    rx = random.randint(-1, 1)
                    ry = random.randint(-1, 1)
                    if rx == 0 and ry == 0: continue
                    
                    tx, ty = m.x + rx, m.y + ry
                    if not is_blocked(tx, ty, m.z) and (tx != player.x or ty != player.y):
                        m.x, m.y = tx, ty
                        moved = True

            if moved:
                self.session.add(m)
                self.session.flush() # Ensure next monster sees this move
                # Final Proximity Check
                new_dist = max(abs(m.x - player.x), abs(m.y - player.y))
                if new_dist <= 1:
                     self.dm.combat.start_combat(m)
                     return "Ambushed by " + m.name

        return None

    def process_npc_schedules(self):
        """Moves NPCs that have a target destination."""
        # Find all NPCs on player's level with a target
        # We rely on quest_state JSON for target_x, target_y
        npcs = self.session.query(NPC).filter_by(z=self.dm.player.z).all() # Only process current level for visuals
        
        for npc in npcs:
            qs = npc.quest_state or {}
            if "status" in qs and qs["status"] == "walking_home" and "target_x" in qs and "target_y" in qs:
                tx = qs["target_x"]
                ty = qs["target_y"]
                
                # Check arrival
                dist = max(abs(npc.x - tx), abs(npc.y - ty))
                if dist <= 0:
                    # Arrived
                    del qs["target_x"]
                    del qs["target_y"]
                    qs["status"] = "completed"
                    npc.quest_state = qs # Trigger flag_modified
                    flag_modified(npc, "quest_state")
                    continue
                
                # Move towards target (Simple step)
                dx = 0
                dy = 0
                if npc.x < tx: dx = 1
                elif npc.x > tx: dx = -1
                
                if npc.y < ty: dy = 1
                elif npc.y > ty: dy = -1
                
                # Collision Check (Basic) - Prioritize X then Y
                # This is a simplified version of _move_actor_towards
                candidates = []
                # Ideal Diagonal
                if dx != 0 and dy != 0: candidates.append((dx, dy))
                # Straight
                if dx != 0: candidates.append((dx, 0))
                if dy != 0: candidates.append((0, dy))
                
                moved = False
                for cdx, cdy in candidates:
                    nx, ny = npc.x + cdx, npc.y + cdy
                    
                    # Avoid Player
                    if nx == self.dm.player.x and ny == self.dm.player.y: continue
                    
                    # Avoid Walls
                    tile = self.session.query(MapTile).filter_by(x=nx, y=ny, z=npc.z).first()
                    if not tile or tile.tile_type in ["wall", "water", "void", "tree"]: continue
                    
                    # Move
                    npc.x = nx
                    npc.y = ny
                    moved = True
                    self.session.add(npc)
                    break 
                
                if moved: pass
