
from dungeon.database import SessionLocal, Monster, Player
from sqlalchemy import func

def check_overlaps():
    session = SessionLocal()
    try:
        # Get player pos
        player = session.query(Player).first()
        if not player:
            print("No player found.")
            return

        print(f"Player at: {player.x}, {player.y}, {player.z}")

        # Check for monsters at the same location
        duplicates = session.query(Monster.x, Monster.y, Monster.z, func.count('*')).\
            filter_by(is_alive=True).\
            group_by(Monster.x, Monster.y, Monster.z).\
            having(func.count('*') > 1).\
            all()

        if duplicates:
            print(f"FOUND {len(duplicates)} LOCATIONS WITH OVERLAPPING MONSTERS!")
            for x, y, z, count in duplicates:
                print(f"Location ({x}, {y}, {z}) has {count} monsters:")
                monsters = session.query(Monster).filter_by(x=x, y=y, z=z, is_alive=True).all()
                for m in monsters:
                    print(f" - ID: {m.id} | Name: '{m.name}' | HP: {m.hp_current}")
        else:
            print("No overlapping monsters found.")

        # Check specifically near player to help debug the "Knife Goblin" spot
        nearby = session.query(Monster).filter(
            Monster.x >= player.x - 5, Monster.x <= player.x + 5,
            Monster.y >= player.y - 5, Monster.y <= player.y + 5,
            Monster.z == player.z,
            Monster.is_alive == True
        ).all()
        
        print("\nNearby Monsters:")
        for m in nearby:
             print(f" - ({m.x}, {m.y}) ID: {m.id} | Name: '{m.name}'")

    finally:
        session.close()

if __name__ == "__main__":
    check_overlaps()
