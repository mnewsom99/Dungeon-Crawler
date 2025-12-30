import sqlite3

def patch():
    try:
        conn = sqlite3.connect('dungeon.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(players)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'skills' not in columns:
            print("Patching DB: Adding skills column to players table...")
            # SQLite doesn't strictly support JSON type in ADD COLUMN, use TEXT (which JSON is stored as)
            cursor.execute("ALTER TABLE players ADD COLUMN skills TEXT DEFAULT '{}'")
            conn.commit()
            print("Success.")
        else:
            print("DB already has skills column.")
            
        conn.close()
    except Exception as e:
        print(f"Error patching DB: {e}")

if __name__ == "__main__":
    patch()
