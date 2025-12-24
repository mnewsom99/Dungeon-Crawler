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

## 3. Recently Completed (v0.5)
- **Refactoring**: Split `dm.py` into modular systems (`inventory_system.py`).
- **Inventory UI**: Grid layout, Paper doll slots, Stacking support.
- **Narrative Fixes**: Fixed NPC positioning (Elara), increased dialogue radius, prevented AI crashes.
- **Graphics**: Added Ore, Bridge, Chest, and Custom Boss sprites.
- **Interaction**: "Inspect" skill reveals hidden doors/chests. "Interact" button usage.

## 4. Next Steps (Roadmap)
### Short Term
- [ ] **Sound Effects**: Add audio for walking, attacking, and ambient tracks.
- [ ] **Save/Load**: Validate the `dm.save()` mechanism robustly across sessions.
- [ ] **More Content**: Add Level 2 (The Caverns) via `generator.py`.

### Long Term
- **Quests System**: A dedicated `quest_manager.py` to track multi-stage objectives.
- **Magic System**: Spells, mana usage, and visual effects.
- **Multiplayer**: (Stretch Goal) WebSocket integration for real-time coop.

## 5. Development Guidelines
- **Single Responsibility**: Do not bloat `dm.py`. Create new managers.
- **AI Safety**: Always wrap LLM calls in try/except blocks with timeouts.
- **Database**: Use SQLAlchemy for all state persistence.
