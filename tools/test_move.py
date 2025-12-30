import sys
import os
sys.path.append(os.getcwd())
from dungeon.dm import DungeonMaster
from dungeon.database import Player

def test_move():
    print("Initializing DM...")
    dm = DungeonMaster()
    
    session = dm.session
    player = session.query(Player).first()
    print(f"Initial Pos: ({player.x}, {player.y}, {player.z})")
    
    print("Attempting Move North (0, -1)...")
    new_pos, msg = dm.move_player(0, -1)
    
    print(f"Move Result: {new_pos}")
    print(f"Message: {msg}")
    
    # Verify DB
    session.expire_all()
    p2 = session.query(Player).first()
    print(f"DB Pos after move: ({p2.x}, {p2.y}, {p2.z})")
    
    if p2.y == player.y - 1:
        print("SUCCESS: Player moved in DB.")
    else:
        print("FAILURE: Player did not move in DB.")

if __name__ == "__main__":
    test_move()
