import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, '..', 'static', 'img')

TARGETS = ["knife_goblin.png", "goblin_scout.png"]

def repair_images():
    print(f"Checking images in {IMG_DIR}...")
    
    for filename in TARGETS:
        path = os.path.join(IMG_DIR, filename)
        if not os.path.exists(path):
            print(f"Skipping {filename}: Not found.")
            continue
            
        try:
            with Image.open(path) as img:
                w, h = img.size
                print(f"{filename}: Size is {w}x{h}")
                
                if w > 32 or h > 32:
                    print(f" - Resizing {filename} to 32x32...")
                    # Nearest Neighbor for pixel art
                    img_small = img.resize((32, 32), Image.NEAREST)
                    img_small.save(path)
                    print(" - Done.")
                else:
                    print(" - Already correct size.")
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    repair_images()
