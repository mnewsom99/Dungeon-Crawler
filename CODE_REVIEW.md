# Dungeon Crawler Code Review & Architecture Report

**Date:** 2025-12-30
**Reviewer:** Antigravity (Staff Engineer)
**Scope:** Full Stack (Backend Python/Flask, Frontend JS, Database)

---

## 1. Executive Summary
The `Dungeon-Crawler` project demonstrates a solid prototype architecture with a clear separation of concerns in the backend (facade pattern). However, the frontend suffers from significant technical debt due to file overrides and monolithic scripts. The database schema lacks critical performance indexes for spatial lookups, which will cause degradation as the map grows.

---

## 2. Refactoring Opportunities (Modularity & SRP)

### High Severity
*   **Frontend Logic Override Conflict (`game_v3.js` vs `graphics.js`)**:
    *   **Issue**: `game_v3.js` is loaded but its core `drawMap` function is completely silently overridden by `modules/graphics.js`. This creates a "Ghost Code" scenario where changes to the manifest game logic file have no effect.
    *   **Proposal**: Delete the rendering logic from `game_v3.js` entirely. Rename `graphics.js` to `renderer.js` and strict import it.
*   **Monolithic Frontend Renderer (`graphics.js`)**:
    *   **Issue**: This file handles Asset Loading, Chroma Key Processing, Canvas Drawing, Input Handling (Mouse), and Game Loop Logic.
    *   **Proposal**: Split into:
        *   `assets.js`: Image loading and processing.
        *   `input.js`: Mouse/Keyboard event listeners.
        *   `renderer.js`: Pure `draw(state)` function.

### Medium Severity
*   **Hardcoded World Initialization (`dm.py::_initialize_world`)**:
    *   **Issue**: `DungeonMaster` contains specific NPC placement logic ("Gareth", "Seraphina") and hardcoded hacks (`if gareth: gareth.x...`).
    *   **Proposal**: Move all entity placement logic to `dungeon/generator.py` or a `WorldLoader` class. DM should only coordinate, not script the plot.
*   **Dead Code Retention (`dm.py::_dead_move_player`)**:
    *   **Issue**: An entire method meant for deletion is still present, cluttering the class.
    *   **Proposal**: Delete immediately.

---

## 3. Database Performance & Integrity

### High Severity (Critical Bottlenecks)
*   **Missing Composite Index on Map Tiles**:
    *   **Context**: The game queries `MapTile` by `(x, y, z)` on **every single movement step** and **every viewport render**.
    *   **Current State**: Indexes exist on `x` and `y` separately. `z` is unindexed.
    *   **Impact**: high latency as table grows.
    *   **Fix**: `CREATE INDEX idx_maptile_z_x_y ON map_tiles (z, x, y);`
*   **Missing Spatial Indexes on Entities**:
    *   **Context**: `Monster`, `NPC`, and `WorldObject` tables are queried by location but have **zero indexes** on coordinates.
    *   **Impact**: Checking "is there a monster here?" becomes a sequential table scan.
    *   **Fix**: Add composite index `(z, x, y)` to `monsters`, `npcs`, and `world_objects`.

### Medium Severity (N+1 Risks)
*   **Inventory Loading**:
    *   **Context**: `Player.inventory` is a relationship. By default, accessing `player.inventory` triggers a lazy load.
    *   **Issue**: If we loop through 100 players (multiplayer future?) and access inventory, that is 101 queries.
    *   **Fix**: Use `joinedload` in SQLAlchemy queries: `session.query(Player).options(joinedload(Player.inventory)).first()`.

---

## 4. Proposed Database Migration

To address the performance issues, the following schema changes are required.

```python
# In database.py

class MapTile(Base):
    # ...
    # Replace individual indexes with Composite
    __table_args__ = (
        Index('idx_maptile_location', 'z', 'x', 'y'),
    )

class Monster(Base):
    # ...
    __table_args__ = (
        Index('idx_monster_location', 'z', 'x', 'y'),
        Index('idx_monster_alive', 'is_alive'), # For filtering dead bodies vs active threats
    )
```

## 5. Security & Threading (Staff Note)
*   **Session Management**: `dm.py` uses a single `self.session` protected by a `threading.RLock()`. In Flask, requests run in separate threads. While the lock prevents corruption, it serializes all DB access, killing concurrency.
    *   **Recommendation**: Switch to `scoped_session` from `sqlalchemy.orm`. Let each Flask request have its own thread-local session. Remove the `RLock`.

---

**Action Plan**:
1.  Apply Database Indexes immediately.
2.  Purge dead code in `dm.py` and `game_v3.js`.
3.  Refactor `graphics.js` into modules.
