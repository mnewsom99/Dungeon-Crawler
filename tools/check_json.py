from dungeon.database import get_session, Player
from dungeon.dm import DungeonMaster

def check_json():
    session = get_session()
    player = session.query(Player).first()
    
    # Initialize DM correctly (uses single session arg now?)
    # Checking dm.py init signature in Step 316: def __init__(self): ... self.session = get_session()
    # It takes NO arguments in new version!
    dm = DungeonMaster()
    
    # Mock player for the DM (if needed) or force session player
    # DM uses self.session.query(Player).first() usually.
    
    state = dm.get_game_state()
    
    print("\n--- JSON DEBUG ---")
    pos = state['player']['xyz']
    print(f"Player XYZ: {pos} (Type: {[type(x) for x in pos]})")
    
    map_data = state['world']['map']
    keys = list(map_data.keys())
    print(f"Total Map Keys: {len(keys)}")
    if keys:
        k = keys[0]
        v = map_data[k]
        print(f"Sample Key: '{k}' -> Val: '{v}'")
    else:
        print("MAP IS EMPTY!")

if __name__ == "__main__":
    check_json()
