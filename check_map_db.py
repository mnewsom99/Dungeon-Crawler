from dungeon.database import get_session, MapTile, Player

session = get_session()

# Check Player
p = session.query(Player).first()
print(f"Player Pos: {p.x}, {p.y}, {p.z}")

# Check Tile at Player Pos
tile = session.query(MapTile).filter_by(x=p.x, y=p.y, z=p.z).first()
if tile:
    print(f"Tile at Player: {tile.tile_type}, Visited: {tile.is_visited}")
else:
    print("Tile at Player: NONE (Void)")

# Check any surroundings
surroundings = session.query(MapTile).filter(
    MapTile.x.between(p.x-5, p.x+5),
    MapTile.y.between(p.y-5, p.y+5)
).all()
print(f"Total tiles in 5x5 radius: {len(surroundings)}")
for t in surroundings:
    print(f" - {t.x},{t.y}: {t.tile_type}")
