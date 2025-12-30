# Fire Dungeon Implementation Plan

## 1. Zone Management (Z-Level 3)
We will dedicate **Z=3** to the Fire Dungeon (The "Volcanic Depths").

### Entrance Logic (`movement.py`)
- Modify `move_player` to detect when entering the specific `door_stone` at the Fire Dungeon location in the Forest (approx `-15, 15`).
- Trigger teleport to `(0, 0, 3)`.
- **Nearby Description:** Update checks to identify the distinctive "Heat radiating from the stone archway" when standing near the entrance.

## 2. Map Generation (`generator.py`)
Create `generate_fire_dungeon(z=3)`:
- **Layout:** Irregular cave system using Cellluar Automata or random walks, similar to the Forest but tighter.
- **Tiles:**
    - `floor_volcanic`: Dark basalt/rock.
    - `lava`: Hazard tiles (damage on step).
    - `steam_vent`: Interactive traps/mechanics.
- **Boss Room:** A large central chamber for the Magma Weaver.

## 3. Monsters (The Inhabitants)
Implement special behaviors in `combat.py`:
- **Cinder-Hound**:
    - *Passive:* `Fire Trail` (Does not need complex grid logic yet, mostly flavor/stat block).
    - *Mechanic:* High Speed/Dodge.
- **Obsidian Sentinel**:
    - *Passive:* `Fire Absorb` (Heals from fire damage).
    - *Weakness:* High Armor, lowered if adjacent to `Steam Vent` (or hit by Cryo-Flask).
- **Sulfur Bat**:
    - *Deathrattle:* `Explosion` (Deals 1d6 Fire to player on death).
- **Magma Weaver (Boss)**:
    - *Ability:* `Molten Web` (Stuns player, prevents movement for 1 turn).

## 4. Items & Loot (`items.py` & `interaction.py`)
- **Phoenix Down Shield**:
    - Type: Shield.
    - Effect: Active ability or passive checks in combat.
- **Cryo-Flask**:
    - Type: Consumable (or Cooldown Tool).
    - Effect: Turns target `lava` tile into `obsidian` (safe walk).
- **Igneous Core**: Crafting Mat.

## 5. Assets
We need to generate pixel art for:
- Monsters: `cinder_hound`, `obsidian_sentinel`, `sulfur_bat`, `magma_weaver`.
- Tiles: `floor_volcanic` (dark rock), `steam_vent`.
- Items: `cryo_flask`, `phoenix_shield`.

## Execution Order
1.  **Generate Assets**: Create the visual styling.
2.  **Update Generator**: Build the map level.
3.  **Update Movement**: Link the door.
4.  **Update Combat**: Add the monster mechanics.
