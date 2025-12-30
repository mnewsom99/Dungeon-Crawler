
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dungeon.database import get_session, MapTile

def move_fire_exit():
    session = get_session()
    print("Moving Fire Dungeon Exit...")
    
    # 1. Remove old door at (0, -1) and restore floor
    old = session.query(MapTile).filter_by(x=0, y=-1, z=3).first()
    if old:
        old.tile_type = "floor_volcanic"
        print("Restored old exit to floor.")
        
    # 2. Add new door at Player's Position (-2, 0)
    # We want it to be a door_stone
    new_x, new_y = -2, 0
    t = session.query(MapTile).filter_by(x=new_x, y=new_y, z=3).first()
    if t:
        t.tile_type = "door_stone"
        t.is_visited = True
        print(f"Moved Exit to ({new_x}, {new_y}).")
    else:
        session.add(MapTile(x=new_x, y=new_y, z=3, tile_type="door_stone", is_visited=True))
        print(f"Created Exit at ({new_x}, {new_y}).")

    session.commit()
    print("Done.")

if __name__ == "__main__":
    move_fire_exit()
