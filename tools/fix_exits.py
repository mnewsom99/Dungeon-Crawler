
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dungeon.database import get_session, MapTile, Player
from sqlalchemy.orm.attributes import flag_modified

def fix_exits():
    session = get_session()
    print("Checking Dungeon Exits...")

    # 1. Start Exit (North of Start Room) at (0, -1)
    # Actually, let's put it at (0, -2) outside the room? 
    # Logic in movement.py checks y <= -1. 
    # If 0,-1 is floor, and they are there, they might trigger it instantly if they spawn there?
    # Start pos is usually 0,0.
    # So moving to 0,-1 (Floor) is fine.
    # I will change 0,-1 to door_stone.
    
    t_start = session.query(MapTile).filter_by(x=0, y=-1, z=0).first()
    if t_start:
        t_start.tile_type = "door_stone"
        t_start.is_visited = True
        print(f"Updated Start Exit at (0, -1)")
    else:
        # Create it if missing
        session.add(MapTile(x=0, y=-1, z=0, tile_type="door_stone", is_visited=True))
        print("Created Start Exit at (0, -1)")

    # 2. End Exit (South/Back of Boss Room) at (0, 32)
    t_end = session.query(MapTile).filter_by(x=0, y=32, z=0).first()
    if t_end:
        t_end.tile_type = "door_stone" # or "door"
        t_end.is_visited = True
        print(f"Updated End Exit at (0, 32)")
    else:
        session.add(MapTile(x=0, y=32, z=0, tile_type="door_stone", is_visited=True))
        print("Created End Exit at (0, 32)")

    session.commit()
    print("Exits Fixed.")

if __name__ == "__main__":
    fix_exits()
