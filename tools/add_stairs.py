import sys
import os

# Add parent directory to path so we can import 'dungeon'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dungeon.dm import DungeonMaster
from dungeon.database import MapTile

def main():
    print("Initializing DM...")
    dm = DungeonMaster()
    session = dm.session

    print("Checking for Stairs at (0, 1, 1)...")
    tile = session.query(MapTile).filter_by(x=0, y=1, z=1).first()

    if tile:
        print(f"Old Tile: {tile.tile_type}")
        tile.tile_type = "stairs_down"
        tile.is_visited = True
        session.add(tile)
        session.commit()
        print("Updated tile (0, 1, 1) to 'stairs_down'.")
    else:
        print("Tile not found! Creating...")
        new_tile = MapTile(x=0, y=1, z=1, tile_type="stairs_down", is_visited=True)
        session.add(new_tile)
        session.commit()
        print("Created new tile 'stairs_down' at (0, 1, 1).")

    print("Done.")

if __name__ == "__main__":
    main()
