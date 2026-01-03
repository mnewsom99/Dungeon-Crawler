import os
import shutil

BASE_DIR = r"c:/Users/mnews/OneDrive/Documents/AI_Projects/Dungeon-Crawler"
IMG_DIR = os.path.join(BASE_DIR, "static/img")
LIB_DIR = os.path.join(BASE_DIR, "static/asset_library/Found_Assets")

if not os.path.exists(LIB_DIR):
    os.makedirs(LIB_DIR)

files = [f for f in os.listdir(IMG_DIR) if f.startswith("uploaded_image") and f.endswith(".png")]

print(f"Found {len(files)} uploaded images in {IMG_DIR}")

for f in files:
    src = os.path.join(IMG_DIR, f)
    dst = os.path.join(LIB_DIR, f)
    try:
        shutil.move(src, dst)
        print(f"Moved {f} to Library.")
    except Exception as e:
        print(f"Error moving {f}: {e}")

print("Done. Check Gallery.")
