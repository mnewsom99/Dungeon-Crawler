import json
import os

DEFAULT_STATE = {
    "player": {
        "hp": 20,
        "max_hp": 20,
        "inventory": [],
        "xyz": [0, 0, 0] # Grid coordinates
    },
    "world": {
        "visited_tiles": [[0,0,0]], # List of visited coordinates
        "map": {}, # Key: "x,y,z", Value: "floor" or "wall"
        "enemies": [], # List of enemy dicts
        "descriptions": {} # Key: "x,y,z", Value: "Narrative text"
    }
}

def load_state(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return DEFAULT_STATE
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return DEFAULT_STATE

def save_state(state: dict, filepath: str):
    with open(filepath, 'w') as f:
        json.dump(state, f, indent=2)
