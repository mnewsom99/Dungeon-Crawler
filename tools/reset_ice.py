from dungeon.database import get_session, MapTile, Monster, Player, WorldObject

def reset_ice_dungeon():
    session = get_session()
    print("Resetting Ice Dungeon (Z=4)...")
    
    # 1. Delete Tiles
    tiles = session.query(MapTile).filter_by(z=4).delete()
    print(f"Deleted {tiles} tiles.")
    
    # 2. Delete Monsters
    monsters = session.query(Monster).filter_by(z=4).delete()
    print(f"Deleted {monsters} monsters.")
    
    # 3. Delete Objects
    objs = session.query(WorldObject).filter_by(z=4).delete()
    print(f"Deleted {objs} objects.")
    
    # 4. Teleport Player to safe start
    player = session.query(Player).first()
    if player:
        # If player is in dungeon, reset then to entry
        if player.z == 4:
            print("Moving Player to Start (0,0,4)...")
            player.x = 0
            player.y = 0
            player.z = 4
        # Or you can move them out? No, let's keep them in so map regens
    
    session.commit()
    print("Done. Next movement or refresh should trigger generation if logic holds.")
    
    # Force Generation Now?
    try:
        from dungeon.generator import LevelBuilder
        builder = LevelBuilder(session)
        print("Forcing Generation...")
        builder.generate_ice_dungeon(4)
        print("Generation Complete.")
    except Exception as e:
        print(f"Generation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_ice_dungeon()
