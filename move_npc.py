from dungeon.database import get_session, NPC
from sqlalchemy.orm import sessionmaker

def move_gareth():
    session = get_session()
    gareth = session.query(NPC).filter(NPC.name.like("%Gareth%")).first()
    
    if gareth:
        print(f"Moving Gareth from ({gareth.x}, {gareth.y}) to Smithy (11, 8)")
        gareth.x = 11
        gareth.y = 8
        session.commit()
    else:
        print("Gareth not found!")

if __name__ == "__main__":
    move_gareth()
