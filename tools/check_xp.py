from dungeon.database import SessionLocal, Player, CombatEncounter, Monster

session = SessionLocal()
player = session.query(Player).first()
print(f"Player Level: {player.level}")
print(f"Player XP: {player.xp}")

encounter = session.query(CombatEncounter).filter_by(is_active=True).first()
if encounter:
    print(f"Active Encounter ID: {encounter.id}")
    monsters = session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).all()
    print(f"Alive Monsters: {len(monsters)}")
    for m in monsters:
        print(f" - {m.name} (HP: {m.hp_current}/{m.hp_max})")
else:
    print("No active encounter.")
    
session.close()
