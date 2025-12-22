import sqlalchemy
from sqlalchemy import func
from dungeon.database import get_session, MapTile, Player

session = get_session()
player = session.query(Player).first()

if not player:
    print("No player found!")
    exit()

count = session.query(MapTile).count()
print(f"Total Tiles: {count}")

current_tile = session.query(MapTile).filter_by(x=player.x, y=player.y, z=player.z).first()

if not current_tile or current_tile.tile_type != 'floor':
    print("Player is on INVALID tile (Void/Wall). Searching for floor...")
    # Find ANY floor tile
    target = session.query(MapTile).filter_by(tile_type='floor').first()
    if target:
        player.x = target.x
        player.y = target.y
        player.z = target.z
        session.commit()
        print(f"TELEPORT SUCCESS: Moved to {target.x}, {target.y}")
    else:
        print("CRITICAL: No floor tiles found in entire DB!")
else:
    print("Player is on valid floor.")

session.close()
