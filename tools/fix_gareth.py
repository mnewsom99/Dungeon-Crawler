from dungeon.database import get_session, NPC
session = get_session()
gareth = session.query(NPC).filter(NPC.name.like("%Gareth%")).first()
if gareth:
    print(f"Moving Gareth from {gareth.x},{gareth.y} to 10,8")
    gareth.x = 10
    gareth.y = 8
    session.commit()
else:
    print("Gareth not found.")
