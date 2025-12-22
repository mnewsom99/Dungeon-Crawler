import json
import os
from pathlib import Path
from dungeon.database import init_db, get_session, Player, MapTile, Monster, InventoryItem

STATE_FILE = Path("state.json")

def migrate():
    if not STATE_FILE.exists():
        print("No state.json found. Skipping migration.")
        init_db() # Ensure tables exist anyway
        return

    print("Loading state.json...")
    with open(STATE_FILE, 'r') as f:
        data = json.load(f)

    # Initialize DB
    print("Initializing Database...")
    init_db()
    session = get_session()

    # 1. Migrate Player
    # Check if player exists
    player = session.query(Player).first()
    if not player:
        print("Migrating Player Data...")
        p_data = data.get("player", {})
        pos = p_data.get("position", [0, 0, 0])
        stats = p_data.get("stats", {})
        
        player = Player(
            name="Hero",
            level=p_data.get("level", 1),
            xp=p_data.get("xp", 0),
            hp_current=p_data.get("hp", 20),
            hp_max=p_data.get("max_hp", 20),
            x=pos[0],
            y=pos[1],
            z=pos[2],
            stats=stats
        )
        session.add(player)
        
        # Migrate Inventory (Basic)
        p_inv = p_data.get("inventory", [])
        for item_name in p_inv:
            # Simple assumption: default items
            item = InventoryItem(
                name=item_name,
                item_type="gear", # Placeholder
                is_equipped=False,
                player=player
            )
            session.add(item)
    else:
        print("Player already in DB.")

    # 2. Migrate Map
    # Map data is "x,y,z": "type"
    print("Migrating Map Tiles (this may take a moment)...")
    map_data = data.get("world", {}).get("map", {})
    
    # Get existing coords to avoid duplicates (optional optimization)
    # For now, we'll just wipe and rebuild or check existence. 
    # Checking existence for 1000s of tiles is slow. 
    # Strategy: If map table is empty, bulk insert.
    
    if session.query(MapTile).count() == 0:
        tiles_to_add = []
        for key, tile_type in map_data.items():
            try:
                x, y, z = map(int, key.split(','))
                tiles_to_add.append(MapTile(x=x, y=y, z=z, tile_type=tile_type, is_visited=True))
            except ValueError:
                continue
        
        if tiles_to_add:
            session.bulk_save_objects(tiles_to_add)
            print(f"Added {len(tiles_to_add)} tiles.")
    else:
        print("Map already populated. Skipping bulk insert.")

    # 3. Migrate Enemies/Corpses?
    # Keeping it simple for now. Corpses in state.json "visible_corpses" could be migrated if we had a Corpse table.
    
    session.commit()
    print("Migration Complete! 'dungeon.db' is ready.")
    session.close()

if __name__ == "__main__":
    migrate()
