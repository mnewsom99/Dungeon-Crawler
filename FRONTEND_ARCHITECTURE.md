# Frontend Architecture & Rendering Pipeline

## Overview
The frontend has been refactored to use a modular architecture, replacing the previous monolithic `graphics.js` and legacy `game_v3.js`.

## Core Modules
1.  **`modules/assets.js`**: 
    *   **Responsibility**: Loads all images, handles transparency (chroma keying), and exposes a global `window.GraphicsAssets` object.
    *   **Key Data**: `assets` dictionary mapping Logical Keys -> Filenames.
    *   **Usage**: To add sprites, edit the `assets` object here.

2.  **`modules/input.js`**: 
    *   **Responsibility**: Handles Mouse (Click/Movement) and Keyboard (Zoom) inputs.
    *   **Global**: Exposes `window.GraphicsInput`.

3.  **`modules/renderer.js`**: 
    *   **Responsibility**: Main pure function `window.drawMap(data)` that renders the state to the Canvas.
    *   **Dependencies**: Uses `GraphicsAssets.images` and `GraphicsInput` state.

## How to Add New Enemies
1.  **Backend**: Add the monster to `generator.py` (and `gamedata.py` if stats are needed).
2.  **Asset**: Upload the image to `static/img`.
3.  **Frontend (`assets.js`)**:
    *   Add the key/file pair to the `assets` object: `'my_enemy': 'my_enemy.png'`.
4.  **Frontend (`renderer.js`)**:
    *   Update the Sprite Selection Logic in `drawMap` (under "4. Draw Enemies") to map the entity name to your new asset key.
    *   Example: `else if (name.includes('dragon')) eImg = images['my_enemy'];`

## File Structure
- `static/js/modules/main.js`: Main Game Loop and Network Logic.
- `static/js/modules/renderer.js`: **ACTIVE RENDERER**.
- `static/js/modules/assets.js`: Asset Registry.
- `static/js/modules/ui.js`: DOM-based UI (Inventory, Chat, Panels).
