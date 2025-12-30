from dungeon.database import SessionLocal, Player

session = SessionLocal()
player = session.query(Player).first()

print(f"Current: Lvl {player.level}, XP {player.xp}")

# Manual Level Up Calculation if stuck
if player.level == 1 and (player.xp or 0) >= 150:
    print("Fixing stuck level...")
    player.xp -= 150
    player.level = 2
    
    # Apply stats for Lvl 2
    player.hp_max += 5
    player.hp_current = player.hp_max
    
    stats = dict(player.stats or {})
    if 'unspent_points' not in stats: stats['unspent_points'] = 0
    stats['unspent_points'] += 1
    player.stats = stats
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(player, "stats")
    
    session.commit()
    print(f"Fixed! New: Lvl {player.level}, XP {player.xp}")
else:
    print("No fix needed.")

session.close()
