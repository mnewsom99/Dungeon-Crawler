from dungeon.database import get_session, Monster, WorldObject

session = get_session()

print("Checking for Overlaps...")

# Check Armory Overlap
chest = session.query(WorldObject).filter_by(x=-10, y=11, z=0).first()
monster = session.query(Monster).filter_by(x=-10, y=11, z=0).first()

if chest and monster:
    print(f"Found overlap at (-10, 11): {monster.name} on {chest.name}")
    monster.x = -11
    monster.y = 10
    session.add(monster)
    print(f"Moved {monster.name} to (-11, 10)")
    session.commit()
else:
    print("No Armory overlap found.")

# Check Library (just in case)
chest_lib = session.query(WorldObject).filter_by(x=10, y=11, z=0).first()
monster_lib = session.query(Monster).filter_by(x=10, y=11, z=0).first()

if chest_lib and monster_lib:
    print(f"Found overlap at (10, 11): {monster_lib.name} on {chest_lib.name}")
    monster_lib.x = 9
    monster_lib.y = 12
    session.add(monster_lib)
    session.commit()
    print("Fixed Library overlap.")

print("Done.")
