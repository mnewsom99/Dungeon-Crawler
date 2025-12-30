import sqlite3
import os

DB_PATH = "dungeon.db"

def apply_indexes():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("applying high-performance indexes...")

    # 1. Map Tiles Composite Index
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maptile_location ON map_tiles (z, x, y)")
        print("[OK] Created idx_maptile_location")
    except Exception as e:
        print(f"[FAIL] Failed to create idx_maptile_location: {e}")

    # 2. World Objects Composite Index
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wobj_location ON world_objects (z, x, y)")
        print("[OK] Created idx_wobj_location")
    except Exception as e:
        print(f"[FAIL] Failed to create idx_wobj_location: {e}")

    # 3. Monster Location Index
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_monster_location ON monsters (z, x, y)")
        print("[OK] Created idx_monster_location")
    except Exception as e:
        print(f"[FAIL] Failed to create idx_monster_location: {e}")

    # 4. Monster Alive Index
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_monster_alive ON monsters (is_alive)")
        print("[OK] Created idx_monster_alive")
    except Exception as e:
        print(f"[FAIL] Failed to create idx_monster_alive: {e}")

    # 5. NPC Location Index
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_location ON npcs (z, x, y)")
        print("[OK] Created idx_npc_location")
    except Exception as e:
        print(f"[FAIL] Failed to create idx_npc_location: {e}")

    conn.commit()
    conn.close()
    print("Database indexing complete.")

if __name__ == "__main__":
    apply_indexes()
