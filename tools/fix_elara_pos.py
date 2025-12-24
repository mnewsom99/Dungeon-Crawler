from dungeon.database import get_session, NPC

session = get_session()
elara = session.query(NPC).filter(NPC.name == "Elara").first()
if elara:
    print(f"Moving Elara from ({elara.x}, {elara.y}) to (1, 30)")
    elara.x = 1
    elara.y = 30
    session.commit()
    print("Elara moved.")
else:
    print("Elara not found.")
