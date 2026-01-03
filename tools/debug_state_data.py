import json
import os

STATE_FILE = "state.json"

try:
    if not os.path.exists(STATE_FILE):
        print("state.json missing")
        exit()

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    world = state.get("world", {})
    map_data = world.get("map", {})
    visited = world.get("visited_tiles", [])
    
    print(f"Total Map Tiles: {len(map_data)}")
    print(f"Total Visited Tiles: {len(visited)}")
    
    visible_count = 0
    void_count = 0
    
    for pos in visited:
        key = f"{pos[0]},{pos[1]},{pos[2]}"
        if key in map_data:
            visible_count += 1
        else:
            void_count += 1
            if void_count < 5:
                print(f"Void tile at: {key}")
                
    print(f"Visible Tiles: {visible_count}")
    print(f"Void Tiles (Visited but not in Map): {void_count}")
    
    player_pos = state["player"]["xyz"]
    print(f"Player Pos: {player_pos}")
    
    p_key = f"{player_pos[0]},{player_pos[1]},{player_pos[2]}"
    print(f"Player Tile Type: {map_data.get(p_key, 'NOT FOUND')}")

except Exception as e:
    print(f"Error: {e}")
