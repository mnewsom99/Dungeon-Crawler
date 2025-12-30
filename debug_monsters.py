from dungeon.database import get_session, Monster

def check_monsters():
    session = get_session()
    monsters = session.query(Monster).filter_by(is_alive=True).all()
    
    print(f"Found {len(monsters)} alive monsters.")
    for m in monsters:
        print(f"ID: {m.id} | Name: {m.name} | HP: {m.hp_current}/{m.hp_max} | Pos: ({m.x}, {m.y}) | State: {m.state}")

if __name__ == "__main__":
    check_monsters()
