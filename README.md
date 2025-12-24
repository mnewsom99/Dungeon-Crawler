# Dungeon Crawler

A new dungeon crawler game project.

## Status
- **Phase**: Alpha (Playable Tutorial + Town)
- **Tech Stack**: Python (Flask) + SQLite + HTML5/JS (Canvas)
- **AI**: Local LLM Integration (Ollama / Llama 3)

## How to Run (Local)
1. Install dependencies: `pip install -r requirements.txt`
2. Ensure you have the `static/img` assets populated (or use the included Texture Pack).
3. Run app: `python app.py`
4. Visit: `http://localhost:5000`

## Features
- **Immersive Interface**: Retro pixel-art style with drag-and-drop UI panels.
- **Dungeon Master AI**: Procedural narration and descriptions powered by Local LLM.
- **Combat System**: Turn-based battles with initiative, attack rolls, and enemy AI.
- **Interactive World**:
  - Talk to NPCs (Elara, Gareth, Elder) with dynamic dialogue.
  - Search for secrets, loot corpses, and interact with objects.
  - Travel between zones (Dungeon ↔ Oakhaven Town).
- **Asset Manager**: Built-in `/gallery` tool to easily swap and assign game textures.
- **Persistence**: SQLite database saves player state, inventory, and world changes automatically.
