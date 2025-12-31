from dungeon.database import get_session, MapTile, Monster

def debug_ice():
    session = get_session()
    print("Checking Z=4 Data...")
    
    # 1. Tiles
    tiles = session.query(MapTile).filter_by(z=4).limit(5).all()
    print(f"Sample Tiles (Z=4):")
    for t in tiles:
        print(f" - ({t.x}, {t.y}): {t.tile_type}")
        
    # Check Counts
    floor_ice = session.query(MapTile).filter_by(z=4, tile_type="floor_ice").count()
    wall_ice = session.query(MapTile).filter_by(z=4, tile_type="wall_ice").count()
    other = session.query(MapTile).filter_by(z=4).count() - floor_ice - wall_ice
    print(f"Counts: floor_ice={floor_ice}, wall_ice={wall_ice}, other={other}")
    
    # 2. Monsters
    monsters = session.query(Monster).filter_by(z=4).all()
    print(f"Monsters (Z=4) [{len(monsters)}]:")
    for m in monsters:
        print(f" - {m.name} at ({m.x}, {m.y})")

if __name__ == "__main__":
    debug_ice()
