from dungeon.database import get_session, Player, MapTile

def check_status():
    session = get_session()
    p = session.query(Player).first()
    if not p:
        print("NO PLAYER FOUND!")
        return

    print(f"Player Pos: ({p.x}, {p.y}, {p.z})")
    
    # Check tiles at this Z
    tiles_count = session.query(MapTile).filter_by(z=p.z).count()
    print(f"Total Tiles at Z={p.z}: {tiles_count}")
    
    # Check Visited tiles (Fog of War)
    visited_count = session.query(MapTile).filter_by(z=p.z, is_visited=True).count()
    print(f"VISIBLE Tiles at Z={p.z}: {visited_count}")
    
    if visited_count == 0:
        print("!! ALERT: Player is in PITCH BLACKNESS (0 visited tiles). Fog of War is hiding everything.")

if __name__ == "__main__":
    check_status()
