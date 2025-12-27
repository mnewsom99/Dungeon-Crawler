# Dungeon Crawler - Master Plan

## 1. Project Overview
A web-based, turn-based Dungeon Crawler RPG utilizing a Python Flask backend (Dungeon Master) and Vanilla JS Frontend. 
The core hook is the "Agentic DM" - an AI (Ollama/Gemini) that generates dynamic descriptions and handles complex interactions.

## 2. Core Systems Status
- **Backend (Python)**:
    - `dm.py`: Main Game Loop, routing, and world management. [Refactored]
    - `inventory_system.py`: Loot, Equip, Stack, Shop, Craft. [Completed]
    - `combat.py`: Turn-based logic, initiative, attack/damage. [Completed]
    - `generator.py`: Map generation (Tutorial Dungeon + Oakhaven Town). [Completed]
    - `ai_bridge.py`: Interface to LLM. [Completed with Fallback]
- **Frontend (JS)**:
    - `graphics.js`: Canvas rendering, Fog of War, Sprites. [Completed]
    - `ui.js`: React-less UI updates (Inventory, Stats, Chat). [Completed]
    - `main.js`: Input handling, state polling. [Completed]

## 3. Recently Completed (v0.7 - "Combat Update")
- **Combat System v2**: 
    - Moved from flat actions to a **Traditional RPG Menu** (Root -> Submenus: Attack, Skills, Items).
    - Added **Fog of War** logic to target selection (can't target what you can't see).
    - Fixed UI event handling for robust mobile/click support.
- **Interaction Layer**:
    - Fixed `investigate` action to handle structured data (narrative + entity lists).
    - Added popup notifications for Mining/Interacting.
- **Bug Fixes**:
    - Resolved critical UI nesting issues in `ui.js`.
    - Fixed backend/frontend variable mismatches (`enemy_list` vs `world.enemies`).

## 4. Next Steps (Roadmap)
### Short Term
- [ ] **Skills & Magic**: The UI component exists, but the "Skills" menu currently only has hardcoded placeholders. Needs a `SkillManager` backend.
- [ ] **Consumables**: "Items" menu in combat needs to pull from actual Inventory `consumable` items.
- [ ] **Enemy AI**: Make enemies smarter (move towards player, use special attacks).
- [ ] **Save/Load**: Validate the `dm.save()` mechanism robustly across sessions.

### Long Term
- **Quests System**: A dedicated `quest_manager.py` to track multi-stage objectives.
- **New Biomes**: Add Level 2 (The Caverns) or "Forest" area.
- **Multiplayer**: (Stretch Goal) WebSocket integration for real-time coop.

## 5. Development Guidelines
- **Single Responsibility**: Do not bloat `dm.py`. Create new managers.
- **AI Safety**: Always wrap LLM calls in try/except blocks with timeouts.
- **Database**: Use SQLAlchemy for all state persistence.
