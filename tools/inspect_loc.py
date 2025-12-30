import sys
import os
sys.path.append(os.getcwd())
from dungeon.database import get_session, Player, MapTile

def inspect_player_loc():
    session = get_session()
    player = session.query(Player).first()
    if not player:
        print("No player found.")
        return

    print(f"Player Location: ({player.x}, {player.y}, {player.z})")
    
    # Check current tile
    current_tile = session.query(MapTile).filter_by(x=player.x, y=player.y, z=player.z).first()
    print(f"Current Tile: {current_tile.tile_type if current_tile else 'None'}")
    
    # Check neighbors
    neighbors = [
        (player.x, player.y - 1, "North"),
        (player.x, player.y + 1, "South"),
        (player.x - 1, player.y, "West"),
        (player.x + 1, player.y, "East")
    ]
    
    print("\nSurrounding Tiles:")
    for x, y, label in neighbors:
        tiles = session.query(MapTile).filter_by(x=x, y=y, z=player.z).all()
        if tiles:
            print(f"{label} ({x}, {y}):")
            for t in tiles:
                print(f"  - ID: {t.id}, Type: {t.tile_type}, Visited: {t.is_visited}")
        else:
            print(f"{label} ({x}, {y}): VOID")

if __name__ == "__main__":
    inspect_player_loc()
