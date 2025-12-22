from dungeon.database import get_session, NPC, MapTile

session = get_session()

# 1. Define Oakhaven NPCs
npcs = [
    {
        "name": "elara",
        "location": "Dungeon Cell",
        "persona_prompt": "You are Elara, a frightened but brave young girl lost in the dungeon. You want to go home to Oakhaven. You trust the hero.",
        "quest_state": {"status": "lost", "dialogue_stage": 0}
    },
    {
        "name": "brogun",
        "location": "Smithy",
        "persona_prompt": "You are Brogun, a grumpy Irish Dwarf Blacksmith. You sell weapons. You hate elves. You respect strength.",
        "quest_state": {"status": "vendor", "inventory": ["Iron Sword", "Chainmail"]}
    },
    {
        "name": "dredge",
        "location": "Tavern",
        "persona_prompt": "You are Dredge, the Tavern Keeper. You are cynical and sell rumors/ale. You know everyone in Oakhaven.",
        "quest_state": {"status": "vendor", "rumors": ["The rats are getting bigger.", "Someone saw a ghost in the crypt."]}
    }
]

print("Seeding NPCs...")
for n_data in npcs:
    # Check if exists
    existing = session.query(NPC).filter_by(name=n_data["name"]).first()
    if not existing:
        npc = NPC(
            name=n_data["name"],
            location=n_data["location"],
            persona_prompt=n_data["persona_prompt"],
            quest_state=n_data["quest_state"]
        )
        session.add(npc)
        print(f"Added {n_data['name']}")
    else:
        print(f"Update/Confirm {n_data['name']}")
        existing.persona_prompt = n_data["persona_prompt"]
        existing.quest_state = n_data["quest_state"]

# 2. Add the "Lost Girl" to the Map (as a special tile or just logic? 
# For now, let's put her on a specific tile near the start (e.g., 5,5)
# We can represent her being "on" a tile by metadata or valid NPC entity pos.
# Since NPC table is separate, we'll just conceptually say she is at 5,5.
# But let's verify map exists there.

target_x, target_y = 5, 5
tile = session.query(MapTile).filter_by(x=target_x, y=target_y).first()
if not tile:
    # Create a room for her
    print("Creating Cell for Elara...")
    for dx in range(4, 7):
        for dy in range(4, 7):
            t = MapTile(x=dx, y=dy, z=0, tile_type="floor", is_visited=True)
            session.add(t)
            
    # Add explicit marker
    center = session.query(MapTile).filter_by(x=target_x, y=target_y).first()
    if not center: 
        center = MapTile(x=target_x, y=target_y, z=0, tile_type="floor", is_visited=True)
        session.add(center)
    
    center.meta_data = {"description": "A damp, mossy cell. You hear soft weeping from the corner.", "npc": "elara"}
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(center, "meta_data") # Import needed? yes.
else:
    print(f"Adding Elara to existing tile {target_x},{target_y}")
    if not tile.meta_data: tile.meta_data = {}
    tile.meta_data["npc"] = "elara"
    tile.meta_data["description"] = "A damp cell. Elara is here, huddled in the corner."
    # We need to flag modified if using SQLA json mutable... or just reassign
    # Since we are using basic JSON, reassign is safer usually or use flag_modified
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(tile, "meta_data")

session.commit()
print("NPCs Seeded and Elara placed at 5,5.")
session.close()
