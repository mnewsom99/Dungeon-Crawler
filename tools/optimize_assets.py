from PIL import Image
import os

TARGET_SIZE = (32, 32)
IMG_DIR = 'static/img'

def optimize_images():
    print("Optimization Report:")
    for f in os.listdir(IMG_DIR):
        if not f.lower().endswith('.png'): continue
        
        path = os.path.join(IMG_DIR, f)
        try:
            with Image.open(path) as img:
                w, h = img.size
                
                # If image is significantly larger than 32x32 (e.g. > 64x64), resize.
                # Pixel art usually needs Nearest Neighbor to stay crisp.
                if w > 64 or h > 64:
                    print(f"Resizing {f} ({w}x{h}) -> 32x32")
                    
                    # Resize using Nearest Neighbor for pixel art look
                    # But if the source IS NOT pixel art (high res gen), Bicubic might be better?
                    # The prompt said "Pixel art style", so Nearest is safest to avoid blur.
                    # Or 'Box' / 'Lanczos' if it's actually high res.
                    # Let's try Nearest first.
                    
                    new_img = img.resize(TARGET_SIZE, Image.NEAREST)
                    new_img.save(path)
                    print(f"  Saved {f}")
                else:
                    # It's already small enough
                    pass
                    
        except Exception as e:
            print(f"Error processing {f}: {e}")

if __name__ == '__main__':
    optimize_images()
