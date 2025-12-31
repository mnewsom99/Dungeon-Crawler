from dungeon.database import get_session, Player, MapTile
from dungeon.dm import DungeonMaster

def check_json_fixed():
    session = get_session()
    player = session.query(Player).first()
    
    # Manually mimic get_state_dict since the class wrapper is tricky to verify 
    # without instantiating full engine env
    
    # 1. Fetch player
    print(f"Player Pos: {player.x}, {player.y}, {player.z}")
    
    # 2. Fetch Map Data (mimic dm.py line 430)
    visited_tiles = session.query(MapTile).filter_by(is_visited=True).all()
    map_data = {f"{t.x},{t.y},{t.z}": t.tile_type for t in visited_tiles}
    
    print(f"Map Data Count: {len(map_data)}")
    if len(map_data) > 0:
        first_key = list(map_data.keys())[0]
        # Validate Key format
        print(f"Sample Key: '{first_key}'")
        parts = first_key.split(',')
        print(f"Split Parts: {parts} (Type: {[type(p) for p in parts]})")
        
        # Validate Z Logic
        z_str = parts[2]
        p_z = player.z
        
        print(f"Comparisons:")
        print(f"z_str ({z_str}) == p_z ({p_z}) ? {z_str == p_z}") # False (str vs int)
        print(f"int(z_str) ({int(z_str)}) == p_z ({p_z}) ? {int(z_str) == p_z}") # True
        print(f"z_str ({z_str}) == str(p_z) ({str(p_z)}) ? {z_str == str(p_z)}") # True

if __name__ == "__main__":
    check_json_fixed()
