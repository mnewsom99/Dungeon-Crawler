
import json
from dungeon.state import load_state

STATE_FILE = "state.json"
state = load_state(STATE_FILE)

player_pos = state["player"]["xyz"]
enemies = state["world"]["enemies"]
combat = state.get("combat", {})

print(f"Player Pos: {player_pos} (Type: {[type(x) for x in player_pos]})")
print(f"Combat State: {combat}")
print("-" * 20)
print("Enemies:")
for e in enemies:
    ex, ey, ez = e["xyz"]
    dist_x = abs(ex - player_pos[0])
    dist_y = abs(ey - player_pos[1])
    dist_z = abs(ez - player_pos[2])
    
    is_close = dist_x <= 1 and dist_y <= 1 and dist_z == 0
    print(f"  - {e['type']} at {e['xyz']} (Type: {[type(x) for x in e['xyz']]})")
    print(f"    Dist: dx={dist_x}, dy={dist_y}. Engaged? {is_close}")

print("-" * 20)
if not enemies:
    print("NO ENEMIES FOUND!")

print("-" * 20)
print("Map Check (Surroundings):")
cx, cy, cz = player_pos
full_map = state["world"].get("map", {})

for dy in range(-2, 3):
    row = ""
    for dx in range(-2, 3):
        x, y = cx + dx, cy + dy
        key = f"{x},{y},{cz}"
        tile = full_map.get(key, "VOID")
        
        # Mark player and enemies
        marker = " "
        if x == cx and y == cy: marker = "P"
        for e in enemies:
            if e["xyz"] == [x, y, cz]: marker = "E"
            
        row += f"[{marker}{tile[:1]}] " 
    print(f"y={cy+dy}: {row}")
print("(f=floor, w=wall, V=VOID/None)")
