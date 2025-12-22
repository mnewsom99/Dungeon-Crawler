from dungeon.database import get_session, MapTile, Player

session = get_session()

print("--- DEBUG DB STATE ---")
p = session.query(Player).first()
if p:
    print(f"Player at: {p.x}, {p.y}, {p.z}")
else:
    print("NO PLAYER FOUND!")

# Check tiles at 0,0
t = session.query(MapTile).filter_by(x=0, y=0, z=0).first()
if t:
    print(f"Tile at 0,0: {t.tile_type} (Visited: {t.is_visited})")
else:
    print("Tile at 0,0: NOT FOUND")

# Count tiles
count = session.query(MapTile).count()
print(f"Total Tiles in DB: {count}")

# List a few
tiles = session.query(MapTile).limit(5).all()
for t in tiles:
    print(f"sample tile: {t.x},{t.y} = {t.tile_type}")

session.close()
