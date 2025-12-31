import sys
from dungeon.database import get_session, Player

def teleport(x, y, z):
    session = get_session()
    player = session.query(Player).first()
    print(f"Teleporting {player.name} from ({player.x},{player.y},{player.z}) to ({x},{y},{z})...")
    player.x = x
    player.y = y
    player.z = z
    # Force HP heal too just in case
    player.hp = player.hp_max
    session.commit()
    print("Done.")

if __name__ == "__main__":
    teleport(0, 0, 1)
