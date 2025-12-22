from dungeon.dm import DungeonMaster

print("Initializing DM...")
dm = DungeonMaster()

print(f"Player Start: {dm.get_player_position()}")

# Move North (should hit something or expand map)
print("Moving North...")
pos, msg = dm.move_player(0, 1)
print(f"New Pos: {pos}")
print(f"Message: {msg}")

# Move again
print("Moving North Again...")
pos, msg = dm.move_player(0, 1)
print(f"New Pos: {pos}")
print(f"Message: {msg}")

# Wall hit test?
print("Trying to walk into a known wall/void...")
# Assuming (0,0) is floor, let's try (100,100)
# Actually, let's just inspect the surroundings.
state = dm.get_state_dict()
print(f"Stat Check - HP: {state['player']['hp']}")
print(f"Tiles Known: {len(state['world']['map'])}")
