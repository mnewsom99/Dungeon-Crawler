import shutil
import os

# Source Base Paths
BASE = "static/audio"
SRC_MUSIC = os.path.join(BASE, "Music loops")
SRC_RPG = os.path.join(BASE, "RPG_Audio")
SRC_IMPACT = os.path.join(BASE, "Impact Sounds")

# Destination
DEST = "static/audio"

# Mapping: (Source Subpath, New Name)
files_to_copy = [
    (os.path.join(SRC_MUSIC, "Retro Mystic.ogg"), "bgm_dungeon.ogg"),
    (os.path.join(SRC_RPG, "footstep05.ogg"), "step.ogg"),
    (os.path.join(SRC_RPG, "doorOpen_1.ogg"), "door.ogg"),
    (os.path.join(SRC_RPG, "knifeSlice.ogg"), "attack_sword.ogg"),
    (os.path.join(SRC_IMPACT, "impactPunch_heavy_001.ogg"), "hit_blunt.ogg"),
    (os.path.join(SRC_RPG, "handleCoins.ogg"), "coin.ogg"),
    (os.path.join(SRC_RPG, "clothBelt2.ogg"), "equip.ogg"),
    (os.path.join(SRC_RPG, "bookFlip1.ogg"), "page.ogg"),
    (os.path.join(SRC_RPG, "metalClick.ogg"), "click.ogg"),
    (os.path.join(SRC_IMPACT, "impactMining_000.ogg"), "mining.ogg"),
]

def setup_audio():
    print("Setting up audio files...")
    for src, new_name in files_to_copy:
        dest_path = os.path.join(DEST, new_name)
        if os.path.exists(src):
            shutil.copy2(src, dest_path)
            print(f"Copied {new_name}")
        else:
            print(f"WARNING: Source not found: {src}")

if __name__ == "__main__":
    setup_audio()
