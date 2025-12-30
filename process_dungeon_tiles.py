from PIL import Image
import os

# Paths
source_path = "C:/Users/mnews/.gemini/antigravity/brain/a2f4a45e-c958-4eae-904e-7ba98617cc92/stone_dungeon_entrance_3x3_1766960355085.png"
dest_dir = "c:/Users/mnews/OneDrive/Documents/AI_Projects/Dungeon-Crawler/static/img/"

# Load
img = Image.open(source_path)

# Resize to 120x120 (3x3 grid of 40x40 tiles)
# We use Nearest Neighbor to keep pixel art crisp
img = img.resize((120, 120), Image.NEAREST)

# Slice and Save
tile_size = 40
grid_map = [
    ["mtn_tl", "mtn_tm", "mtn_tr"],
    ["mtn_ml", "mtn_mm", "mtn_mr"],
    ["mtn_bl", "door_stone", "mtn_br"]
]

for row in range(3):
    for col in range(3):
        # Crop
        left = col * tile_size
        upper = row * tile_size
        right = left + tile_size
        lower = upper + tile_size
        
        tile = img.crop((left, upper, right, lower))
        
        # Save
        filename = f"{grid_map[row][col]}.png"
        save_path = os.path.join(dest_dir, filename)
        tile.save(save_path)
        print(f"Saved {filename}")
