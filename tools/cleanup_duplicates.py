from dungeon.database import get_session, WorldObject
from sqlalchemy import func

session = get_session()

# Find duplicates
subq = session.query(
    WorldObject.x, WorldObject.y, WorldObject.z,
    func.count('*').label('count')
).group_by(
    WorldObject.x, WorldObject.y, WorldObject.z
).having(func.count('*') > 1).subquery()

duplicates = session.query(WorldObject).join(
    subq, 
    (WorldObject.x == subq.c.x) & 
    (WorldObject.y == subq.c.y) & 
    (WorldObject.z == subq.c.z)
).all()

print(f"Found {len(duplicates)} objects involved in duplication.")

deleted_count = 0
# Keep one, delete rest
processed_locs = set()

for obj in duplicates:
    loc = (obj.x, obj.y, obj.z)
    if loc in processed_locs:
        # We already kept one for this loc, delete this one
        session.delete(obj)
        deleted_count += 1
    else:
        # First one we see, keep it (mark as processed)
        processed_locs.add(loc)

session.commit()
print(f"Deleted {deleted_count} duplicate objects.")
