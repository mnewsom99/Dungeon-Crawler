from dungeon.database import get_session, Monster, Player
import time

def spawn_goblin():
    session = get_session()
    player = session.query(Player).first()
    
    if not player:
        print("Player not found.")
        return

    print(f"Player at: {player.x}, {player.y}, {player.z}")

    # Spawn Goblin at x+1
    goblin = Monster(
        name="Knife Goblin",
        hp_current=10,
        hp_max=10,
        x=player.x + 1,
        y=player.y,
        z=player.z,
        state="alive",
        family="goblin"
    )
    session.add(goblin)
    session.commit()
    print(f"Spawned Goblin Scout at {goblin.x}, {goblin.y}")

if __name__ == "__main__":
    spawn_goblin()
