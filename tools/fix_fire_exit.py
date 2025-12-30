
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dungeon.database import get_session, MapTile, Player

def fix_fire_exit():
    session = get_session()
    print("Adding Fire Dungeon Exit...")
    
    # 1. Ensure Player is safe (opt)
    # 2. Add Door at (0, -1, 3)
    
    t = session.query(MapTile).filter_by(x=0, y=-1, z=3).first()
    if t:
        t.tile_type = "door_stone"
        t.is_visited = True
        print("Updated existing tile to door_stone.")
    else:
        session.add(MapTile(x=0, y=-1, z=3, tile_type="door_stone", is_visited=True))
        print("Created new door_stone exit.")
        
    session.commit()
    print("Fire Dungeon Exit Added.")

if __name__ == "__main__":
    fix_fire_exit()
