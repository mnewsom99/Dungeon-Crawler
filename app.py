import os
from flask import Flask, render_template, jsonify, request
from dungeon.dm import DungeonMaster

app = Flask(__name__)
# Force Reload Trigger v37 for Backend Modularization
dm = DungeonMaster()

@app.teardown_appcontext
def shutdown_session(exception=None):
    from dungeon.database import SessionLocal
    SessionLocal.remove()

@app.route('/')
def home():
    print("DEBUG: SERVING index_v2.html")
    return render_template('index_v2.html')

@app.route('/api/state')
def get_state():
    state = dm.get_state_dict()
    return jsonify(state)

@app.route('/api/combat/action', methods=['POST'])
def combat_action():
    data = request.json
    action = data.get('action')
    target_id = data.get('target_id')
    
    narrative_data = dm.combat.player_action(action, target_id=target_id)
    
    # We might need to fetch updated combat state from DM if we want it separately
    # But get_state loop handles it mostly. 
    # For the immediate response:
    state = dm.get_state_dict()
    
    return jsonify({
        "result": narrative_data, # Contains "events" list
        "combat": state.get("combat") 
    })

@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    # action, type, id
    msg = dm.player_interact(data.get("action"), data.get("type"), data.get("id"))
    return jsonify({"narrative": msg})

@app.route('/api/interact_specific', methods=['POST'])
def interact_specific():
    data = request.json
    msg = dm.player_interact(data.get("action"), data.get("target_type"), data.get("target_id"))
    return jsonify({"narrative": msg})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        # dm.chat_with_npc now returns 3 values: reply, name, can_trade_flag
        result = dm.chat_with_npc(data.get("npc_index"), data.get("message"))
        
        # Unpack safely (handle legacy 2-return case if needed, though we updated dm.py)
        if len(result) == 3:
             reply, name, can_trade_flag = result
        else:
             reply, name = result
             can_trade_flag = False
             
        return jsonify({"reply": reply, "npc_name": name, "can_trade": can_trade_flag})
    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"reply": f"(The spirits are confused: {str(e)})", "npc_name": "System", "can_trade": False})

@app.route('/api/narrative')
def get_narrative():
    return jsonify({
        "narrative": dm.describe_current_room()
    })



@app.route('/api/debug/reset', methods=['POST'])
def reset_game():
    dm.reset_game()
    return jsonify({"message": "Game Reset"})

@app.route('/api/action/investigate', methods=['POST'])
def perform_investigate():
    result = dm.investigate_room()
    # result is dict: {"narrative": ..., "entities": ...}
    return jsonify(result)

@app.route('/api/move', methods=['POST'])
def move_player():
    data = request.json
    direction = data.get('direction')
    
    # Check for direct dx/dy first (from mouse)
    if 'dx' in data and 'dy' in data:
         dx = data['dx']
         dy = data['dy']
    else:
        # Fallback to string direction
        dx, dy = 0, 0
        if direction == 'north': dy = -1
        elif direction == 'south': dy = 1
        elif direction == 'east': dx = 1
        elif direction == 'west': dx = -1
    
    new_pos, result = dm.move_player(dx, dy)
    
    narrative = result
    events = []
    
    if isinstance(result, dict):
        if "events" in result:
            events = result["events"]
            narrative = "You move..." # Fallback or look for text in events
            # Try to find a text event to use as narrative
            for e in events:
                if e['type'] == 'text':
                    narrative = e['message']
                    break
    
    # Return updated stats after move
    state = dm.get_state_dict()
    
    return jsonify({
        "position": new_pos,
        "narrative": narrative,
        "events": events,
        "stats": state["player"]
    })

@app.route('/api/inventory/equip', methods=['POST'])
def equip_item():
    data = request.json
    result = dm.equip_item(data.get('item_id'))
    return jsonify({"message": result, "state": dm.get_state_dict()})

@app.route('/api/inventory/unequip', methods=['POST'])
def unequip_item():
    data = request.json
    result = dm.unequip_item(data.get('item_id'))
    return jsonify({"message": result, "state": dm.get_state_dict()})

@app.route('/api/inventory/use', methods=['POST'])
def use_inventory_item():
    data = request.json
    msg = dm.use_item(data.get("item_id"))
    return jsonify({"message": msg})

@app.route('/api/loot/take', methods=['POST'])
def take_loot_item():
    data = request.json
    msg = dm.take_loot(data.get("corpse_id"), data.get("loot_id"))
    return jsonify({"message": msg})

@app.route('/api/craft/list')
def list_recipes():
    from dungeon.gamedata import RECIPES
    return jsonify(RECIPES)

@app.route('/api/craft/make', methods=['POST'])
def perform_craft():
    data = request.json
    msg = dm.craft_item(data.get("recipe_id"))
    return jsonify({"message": msg})

@app.route('/api/shop/list')
def list_shops():
    from dungeon.items import SHOPS, ITEM_TEMPLATES
    return jsonify({"shops": SHOPS, "items": ITEM_TEMPLATES})

@app.route('/api/shop/buy', methods=['POST'])
def buy_item():
    data = request.json
    result = dm.buy_item(data.get('item_id')) # item_id here is actually template_id string
    return jsonify({"message": result, "state": dm.get_state_dict()})

@app.route('/api/shop/sell', methods=['POST'])
def sell_item():
    data = request.json
    result = dm.sell_item(data.get('item_id')) # item_id here is Player's InventoryItem ID (int)
    return jsonify({"message": result, "state": dm.get_state_dict()})

@app.route('/api/action', methods=['POST'])
def perform_action():
    data = request.json
    action = data.get('action')
    
    if action == "investigate":
        print(f"DEBUG: Player investigating at {dm.player.x},{dm.player.y}")
        result = dm.investigate_room()
        # result is now a dict {narrative, entities}
        narrative = result.get("narrative") if isinstance(result, dict) else result
        return jsonify({"narrative": narrative, "state": dm.get_state_dict()})
        
    return jsonify({"message": "Unknown action"}), 400

@app.route('/api/stats/upgrade', methods=['POST'])
def upgrade_stat():
    data = request.json
    msg = dm.upgrade_stat(data.get("stat"))
    return jsonify({"message": msg, "state": dm.get_state_dict()})

@app.route('/api/skills/choose', methods=['POST'])
def choose_skill():
    data = request.json
    msg = dm.choose_skill(data.get("skill_id"))
    return jsonify({"message": msg, "state": dm.get_state_dict()})

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/api/assets/list')
@app.route('/api/assets/list')
def list_assets():
    """List all images in static/asset_library recursively"""
    base_folder = os.path.join(app.root_path, 'static', 'asset_library')
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
    
    image_files = []
    for root, dirs, files in os.walk(base_folder):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Get path relative to asset_library
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, base_folder)
                # Ensure forward slashes for web
                rel_path = rel_path.replace('\\', '/')
                image_files.append(rel_path)
                
    return jsonify({"files": sorted(image_files)})

@app.route('/api/assets/assign', methods=['POST'])
def assign_asset():
    """Rename or Copy a library asset to a game asset"""
    data = request.json
    source_name = data.get('source') # e.g. "tile_0042.png"
    target_role = data.get('role')   # e.g. "wall_grey"
    
    if not source_name or not target_role:
        return jsonify({"error": "Missing info"}), 400
        
    src_path = os.path.join(app.root_path, 'static', 'asset_library', source_name)
    src_path = os.path.normpath(src_path) # Fix mixed slashes
    
    # Target is static/img/target_role.png
    dest_path = os.path.join(app.root_path, 'static', 'img', f"{target_role}.png")

    if not os.path.exists(src_path):
        return jsonify({"error": f"Source file not found: {source_name}"}), 404

    try:
        # Auto-resize if possible
        try:
            from PIL import Image
            with Image.open(src_path) as img:
                # Resize to 32x32 using Nearest Neighbor (preserves pixel art)
                img_resized = img.resize((32, 32), Image.NEAREST)
                img_resized.save(dest_path)
        except ImportError:
            # Fallback if PIL not installed
            import shutil
            shutil.copy2(src_path, dest_path)
            
        return jsonify({"status": "success", "message": f"Assigned {source_name} to {target_role}"})
    except Exception as e:
        print(f"DEBUG: Error copying: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug/reset', methods=['POST', 'GET'])
def debug_reset():
    """Resets the game state (DB cleanup handled by DM init usually or we force it)."""
    # For SQLite, deleting the file is one way, or dropping tables.
    # DM logic usually handles creating if missing.
    # Let's drop all tables and init.
    from dungeon.database import Base, engine
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    global dm
    dm = DungeonMaster() # Re-init
    return jsonify({"message": "World Reset Completed", "state": dm.get_state_dict()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
