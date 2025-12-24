from dungeon.database import get_session, NPC, MapTile
from dungeon.dm import DungeonMaster

def fix_seraphina():
    print("Fixing Seraphina...")
    session = get_session()
    
    # 1. Find Seraphina
    seraphina = session.query(NPC).filter(NPC.name.like("%Seraphina%")).first()
    if seraphina:
        print(f"Found Seraphina at ({seraphina.x}, {seraphina.y}, {seraphina.z})")
        
        # If she is in Town (z=1) or Dungeon (z=0), move her to center of Alchemist Shop
        # Alchemist Shop is in Town (-14 to -8, 6 to 12). Center ~ (-11, 9)
        # If user says she is "in a wall" in town, she is likely at -8.
        
        # Force move to Alchemist Interior (Town)
        seraphina.x = -11
        seraphina.y = 9
        seraphina.z = 1 # Update to Town
        seraphina.location = "Alchemist Shop"
        
        print(f"Moved Seraphina to (-11, 9, 1).")
        session.commit()
    else:
        print("Seraphina not found!")

def split_assets():
    try:
        from PIL import Image
        import os
        
        src = "static/img/town_assets.png"
        if not os.path.exists(src):
            print("town_assets.png not found.")
            return

        img = Image.open(src)
        print(f"Loaded {src} ({img.size})")
        
        # Assuming grid. 32x32.
        # We'll just define some crops if we know them, or just split a 2x3 grid.
        # Let's guess it's a grid since I asked for it.
        w, h = 32, 32
        
        assets = ["barrel", "crate", "street_lamp", "fountain", "flower_pot", "signpost"]
        
        # Auto-crop simple grid
        cols = img.width // w
        rows = img.height // h
        
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= len(assets): break
                
                left = c * w
                top = r * h
                # Refine crop later if needed
                tile = img.crop((left, top, left+w, top+h))
                
                name = assets[idx]
                out_path = f"static/img/{name}.png"
                tile.save(out_path)
                print(f"Saved {out_path}")
                idx += 1
                
    except ImportError:
        print("PIL not installed. Cannot split images. Please run 'pip install Pillow'")
    except Exception as e:
        print(f"Error splitting: {e}")

if __name__ == "__main__":
    fix_seraphina()
    split_assets()
