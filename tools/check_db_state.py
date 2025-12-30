
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dungeon.database import get_session, Player, Monster, MapTile

def check():
    session = get_session()
    
    # Check Player
    p = session.query(Player).first()
    if not p:
        print("No Player found!")
        return
        
    print(f"Player: {p.name} at ({p.x}, {p.y}, {p.z})")
    
    # Check Monsters at this level
    monsters = session.query(Monster).filter_by(z=p.z, is_alive=True).all()
    print(f"Monsters at Z={p.z}: {len(monsters)}")
    for m in monsters:
        print(f"  - {m.name} at ({m.x}, {m.y})")
        
    # Check Tiles around Player
    print("Tiles:")
    tiles = session.query(MapTile).filter(
        MapTile.x.between(p.x-2, p.x+2),
        MapTile.y.between(p.y-2, p.y+2),
        MapTile.z == p.z
    ).all()
    
    t_map = {(t.x, t.y): t.tile_type for t in tiles}
    
    for y in range(p.y-2, p.y+3):
        row = ""
        for x in range(p.x-2, p.x+3):
            tt = t_map.get((x,y), "VOID")
            sym = ".."
            if tt == "floor": sym = "fl"
            elif tt == "floor_volcanic": sym = "fv"
            elif tt == "wall": sym = "##"
            elif tt == "wall_volcanic": sym = "WV"
            elif tt == "lava": sym = "~~"
            elif tt == "door": sym = "DR"
            elif tt == "door_stone": sym = "DS"
            
            if x == p.x and y == p.y: sym = "PL"
            
            row += f"[{sym}]"
        print(f"y={y}: {row}")

if __name__ == "__main__":
    check()
