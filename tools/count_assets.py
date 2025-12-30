import os

base_dir = r"c:/Users/mnews/OneDrive/Documents/AI_Projects/Dungeon-Crawler/static/asset_library"
count = 0
extensions = ('.png', '.jpg', '.jpeg')

for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.lower().endswith(extensions):
            count += 1

print(f"Total images found: {count}")
