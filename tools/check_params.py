import json
from dungeon.database import get_session, Player, MapTile
from dungeon.dm import DungeonMaster

def check_state():
    session = get_session()
    player = session.query(Player).first()
    print(f"Player: {player.name} at ({player.x}, {player.y}, {player.z})")
    
    # Check Visible Tiles
    # Logic from dm.py _get_state_dict
    # It queries tiles where is_visited is true
    visible_tiles = session.query(MapTile).filter(MapTile.is_visited == True).count()
    print(f"Total Visited Tiles in DB: {visible_tiles}")
    
    visible_z4 = session.query(MapTile).filter_by(z=4, is_visited=True).count()
    print(f"Visited Tiles at Z=4: {visible_z4}")
    
    # Simulate DM State
    dm = DungeonMaster(session, player)
    state = dm.get_game_state()
    
    print("\n--- FRONTEND JSON DUMP (Partial) ---")
    map_data = state['world']['map']
    print(f"Map Keys Count: {len(map_data)}")
    keys = list(map_data.keys())[:5]
    print(f"Sample Keys: {keys}")
    
    if len(map_data) == 0:
        print("WARNING: Frontend is receiving EMPTY MAP.")
    
    # Check Enemies
    enemies = state['world']['enemies']
    print(f"Enemies Count: {len(enemies)}")

if __name__ == "__main__":
    check_state()
