# Dungeon Crawler - Master Plan

## 1. Vision
> **Code Quality Rules**:
> 1. **File Size Limit**: Files must stay under 600 lines.
> 2. **Modularity**: If a feature (e.g., Spells, Inventory) grows large, create a new module in the appropriate sub-folder (e.g., `dungeon/spells.py`).
> 3. **Clean Main**: Never put business logic inside `app.py` or entry points; use them only for initialization.

An immersive, AI-driven dungeon crawler where a "Dungeon Master" (DM) AI narrates the adventure, while strict Python-based rules govern the mechanics (combat, checks).

## 2. Architectural Requirements

### A. DM Logic (`dungeon/dm.py`)
- **Central Class**: `DungeonMaster`
- **Responsibilities**:
  - Handle narration (bridging to AI).
  - Manage Game State.
  - Execute dice rolls and rule checks.

### B. Rulebook (`dungeon/rules.py`)
- **Modules**:
  - Dice Roller (`d20`, `d6`, etc.).
  - Combat Logic: `is_hit(roll, armor_class)`.
  - Damage Calculation.

### C. AI Narrative Integration
- **Engine**: Gemini 3 API.
- **Function**: Describe rooms, generate NPC dialogue, and respond to player creativity.
- **Constraint**: Must adhere to the physical state enforced by `rules.py`.

### D. Persistence (`state.json`)
- **File**: `state.json`
- **Data**:
  - Player Stats (HP, Inventory, XP).
  - Current Location/Room.
  - World State (Defeated enemies, unlocked doors).
  - **Map Data**: Visited tiles, known layout.

### F. Graphics & Audio
- **Visual Style**: Retro "block pattern" or pixel art.
- **Implementation**: Tile-based rendering (walls, floors, entities).

### E. Interface (Web UI)
- **Tech**: Flask (Backend) + HTML5/JavaScript (Frontend).
- **Visuals**:
  - **Map View**: A grid-based "block pattern" map rendered on an HTML Canvas.
  - **Narrative View**: Text log for the DM's descriptions.
  - **Controls**: Command input or buttons for actions.

## 3. Workflow & tasks

### Phase 1: Core Foundation
- [x] Set up file structure.
- [x] Implement `rules.py` (Math & Mechanics).
- [x] Implement `state` management (Save/Load).

### Phase 2: The Dungeon Master
- [x] Create `DungeonMaster` class.
- [x] Connect DM to `rules.py`.
- [x] Connect DM to `state.json`.

### Phase 3: The Voice (AI)
- [x] Design Prompt Engineering for DM persona.
- [x] Integrate Gemini API logic (Migrated to `google-genai`).

### Phase 4: The Interface
- [x] Build Flask App.
- [x] Connect UI input to DM functions.
- [x] Add Basic Graphics (Sprite rendering).

### Phase 5: Technical Foundation & Core Systems
- [x] **SQLite Migration**: Move from `state.json` to `dungeon.db`.
  - Tables: `Players` (Level, Class, HP, Mana, Stamina), `Inventory` (Properties JSON), `Quests`.
  - Tables: `NPCs` (Name, Persona, QuestState).
- [x] **Core Engine Shift**: Transition to Local AI (Ollama/Llama3).
  - Create `dungeon/ai_bridge.py`: Handle context switching (DM Narration vs. NPC Dialogue vs. Enemy Banter).
- [x] **Refactor `app.py`**: Add `/chat` (NPC interaction) and `/use_skill` routes.

### Phase 5.5: The Beginning (New User Flow)
- [ ] **Tutorial Dungeon**:
  - Spawn generic Hero in specific "Tutorial Dungeon" zone.
  - Slay skeletons -> Find "Lost Girl" (NPC).
- [ ] **Town Arrival**:
  - Escort Girl -> Unlocks "Oakhaven".
  - **Class Selection**: Talk to Trainer/Mayor to pick Archetype (Class & Race) -> Update Player DB.
  - **Quest Hub**: Receive first real quest.

### Phase 6: The Living World (Towns & Environment)
- [ ] **Oakhaven (Safe Zone)**:
  - **Brogun (Blacksmith)**: Weapon upgrades/crafting (Irish Dwarf persona).
  - **Dredge (Tavern)**: Rumor-monger and quest giver.
  - **Store/Alchemist**: Consumables (Potions, Torches).
- [ ] **Procedural Dungeon**:
  - **Dynamic Lighting**: Torch system ($R=5$ tiles) with durability cost.
  - Generative Rooms/Corridors.
- [ ] **Time System**: Track turns for resource consumption and events.

### Phase 7: RPG Depth (Classes & Equipment)
- [ ] **5 Archetypes**: Rogue, Warrior, Mage, Ranger, Paladin.
- [ ] **Skill Trees**:
  - *Passive*: Sneak (Aggro reduction), Sprint (Multi-tile move).
  - *Active*: Class Skills (Mana Bolt, Backstab).
  - **Resource Bars**: HP, Mana, Stamina.
- [ ] **Equipment Manager**:
  - Slots: Head, Chest, Main Hand, Off-Hand, Boots.
  - Stat Weighting: Heavy armor affects Stealth/Speed.

### Phase 8: Enhanced Immersion (Combat & Audio)
- [ ] **Combat Banter**: Random enemy taunts/puns via Ollama.
- [ ] **Narrative Strikes**: AI describes hits based on damage rolls.
- [ ] **Death Rattles**: Unique last words for enemies.
- [ ] **Frontend Polish**:
  - **Animations**: Sprite-sheet support.
  - **Audio**: Footsteps, hits, combat music.
  - **Visuals**: Radial gradient masking for torches.

## 4. Immediate Next Steps / Agent Tasks
1. **Refactor/Migration**: Build `database.py` tables (NPCs, Skills, Equipment) and clean up `app.py`.
2. **Asset Setup**: Create `/static/assets` structure for sprites/audio.
3. **Ollama Bridge**: Implement the system prompt logic to switch between DM and NPCs.
