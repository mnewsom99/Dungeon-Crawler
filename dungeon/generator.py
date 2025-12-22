
import random

def generate_dungeon(width=50, height=50, num_rooms=10):
    """
    Generates a simple dungeon with rooms and corridors.
    Returns a dict of coordinate strings "x,y,z" mapped to tile types "floor" or "wall".
    """
    tiles = {}
    rooms = []

    # Initialize all as walls (implied). We only store "floor" for now.
    # Actually, let's store everything explicitly for now to be safe, or just floors.
    # Storing just floors is easier for collision: if not in dict, it's a wall.

    def create_room(x, y, w, h):
        for i in range(x, x + w):
            for j in range(y, y + h):
                tiles[f"{i},{j},0"] = "floor"
        return {"x": x, "y": y, "w": w, "h": h, "center": (x + w // 2, y + h // 2)}

    def create_h_tunnel(x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            tiles[f"{x},{y},0"] = "floor"

    def create_v_tunnel(y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            tiles[f"{x},{y},0"] = "floor"

    for _ in range(num_rooms):
        w = random.randint(5, 10)
        h = random.randint(5, 10)
        x = random.randint(1, width - w - 1)
        y = random.randint(1, height - h - 1)

        new_room = create_room(x, y, w, h)
        
        if rooms:
            # Connect to previous room
            prev_room = rooms[-1]
            new_x, new_y = new_room["center"]
            prev_x, prev_y = prev_room["center"]

            if random.choice([True, False]):
                create_h_tunnel(prev_x, new_x, prev_y)
                create_v_tunnel(prev_y, new_y, new_x)
            else:
                create_v_tunnel(prev_y, new_y, prev_x)
                create_h_tunnel(prev_x, new_x, new_y)
        
        rooms.append(new_room)

    # Add walls around floors
    floor_keys = list(tiles.keys())
    for key in floor_keys:
        x, y, z = map(int, key.split(','))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                neighbor_key = f"{x+dx},{y+dy},{z}"
                if neighbor_key not in tiles:
                    tiles[neighbor_key] = "wall"

    start_pos = [rooms[0]["center"][0], rooms[0]["center"][1], 0]
    
    # Generate Enemies
    enemies = []
    # Skip first room (start room)
    for room in rooms[1:]:
        # Spawn 1 skeleton at random spot in room
        ex = random.randint(room["x"], room["x"] + room["w"] - 1)
        ey = random.randint(room["y"], room["y"] + room["h"] - 1)
        enemies.append({
            "xyz": [ex, ey, 0],
            "type": "skeleton",
            "hp": 10,
            "max_hp": 10,
            "ac": 12,
            "xp": 50
        })

    return tiles, start_pos, enemies
