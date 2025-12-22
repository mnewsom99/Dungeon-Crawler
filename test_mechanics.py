from dungeon.rules import roll_dice, calculate_hit
from dungeon.dm import DungeonMaster
import os

def test_dice():
    print("Testing Dice...")
    for _ in range(5):
        r = roll_dice("1d20")
        assert 1 <= r <= 20
        print(f"1d20 rolled: {r}")
    print("Dice OK.")

def test_dm_state():
    print("Testing DM State...")
    if os.path.exists("state.json"):
        os.remove("state.json")
    
    dm = DungeonMaster()
    pos = dm.get_player_position()
    # assert pos == [0,0,0] # Map is generated randomly now
    print(f"Initial Pos: {pos}")
    
    new_pos, msg = dm.move_player(1, 0) # East
    # Check that x increased by 1 OR collision happened
    assert new_pos == [pos[0]+1, pos[1], pos[2]] or new_pos == pos
    print(f"New Pos: {new_pos}")
    
    # Reload to check persistence
    dm2 = DungeonMaster()
    assert dm2.get_player_position() == new_pos
    print("Persistence OK.")

if __name__ == "__main__":
    test_dice()
    test_dm_state()
