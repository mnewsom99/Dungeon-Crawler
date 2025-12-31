from dungeon.database import get_session, MapTile

def fix_fog():
    session = get_session()
    print("Revealing Ice Dungeon Entrance area...")
    
    # Reveal radius 5 around 0,0 for Z=4
    tiles = session.query(MapTile).filter_by(z=4).filter(
        MapTile.x >= -5, MapTile.x <= 5,
        MapTile.y >= -5, MapTile.y <= 5
    ).all()
    
    count = 0
    for t in tiles:
        t.is_visited = True
        count += 1
        
    session.commit()
    print(f"Revealed {count} tiles.")

if __name__ == "__main__":
    fix_fog()
