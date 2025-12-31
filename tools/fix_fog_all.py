from dungeon.database import get_session, MapTile

def fix_fog_all():
    session = get_session()
    print("Revealing ALL Ice Dungeon tiles (Z=4)...")
    
    # Just update all
    try:
        updated = session.query(MapTile).filter_by(z=4).update({MapTile.is_visited: True})
        session.commit()
        print(f"Revealed {updated} tiles.")
    except Exception as e:
        print(f"Update failed: {e}")
        # Manual iter
        tiles = session.query(MapTile).filter_by(z=4).all()
        print(f"Manual Count: {len(tiles)}")
        for t in tiles:
            t.is_visited = True
        session.commit()
        print("Manual Commit done.")

if __name__ == "__main__":
    fix_fog_all()
