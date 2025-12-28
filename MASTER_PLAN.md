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

## 3. Recently Completed (v0.8 - "Flexible Combat Update")
- **Flexible Combat System**:
    - **Tabbed Interface**: Separated actions into Move (Green), Action (Red), and Bonus (Yellow) tabs.
    - **Flexible Turn Order**: Players can Move, Attack, and use Bonus actions in *any order*.
    - **Explicit End Turn**: Added a dedicated button to end the turn, removing confusing auto-end logic.
- **Combat Logic Refactor**:
    - **Enemy AI**: Enemies now perform pathfinding to move towards the player if out of range.
    - **Victory Check**: Combat automatically ends when the last enemy falls (even if killed by an NPC).
    - **Code Cleanup**: Refactored `combat.py` to use shared helper methods for movement and victory checks.
- **Bug Fixes**:
    - Fixed "Double Move" on click issue.
    - Fixed Combat UI filtering (only showing visible enemies).

## 4. Next Steps (Roadmap)
### Short Term
- [ ] **Skills & Magic**: The UI component exists, but the "Skills" menu currently only has hardcoded placeholders (Second Wind). Needs a `SkillManager` backend.
- [ ] **Consumables**: "Items" menu in combat needs to pull from actual Inventory `consumable` items rather than just a hardcoded Potion button.
- [ ] **Save/Load**: Validate the `dm.save()` mechanism robustly across sessions.


### Long Term
- **Quests System**: A dedicated `quest_manager.py` to track multi-stage objectives.
- **New Biomes**: Add Level 2 (The Caverns) or "Forest" area.
- **Multiplayer**: (Stretch Goal) WebSocket integration for real-time coop.

## 5. Development Guidelines
- **Single Responsibility**: Do not bloat `dm.py`. Create new managers.
- **AI Safety**: Always wrap LLM calls in try/except blocks with timeouts.
- **Database**: Use SQLAlchemy for all state persistence.
