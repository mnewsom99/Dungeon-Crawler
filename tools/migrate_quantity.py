from dungeon.database import get_session, engine
from sqlalchemy import text

# Add quantity column to inventory table if it doesn't exist
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE inventory ADD COLUMN quantity INTEGER DEFAULT 1"))
        print("Migrated: Added 'quantity' column.")
    except Exception as e:
        print(f"Skipping migration (might already exist): {e}")

session = get_session()
session.commit()
print("Migration check complete.")
