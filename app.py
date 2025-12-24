import os
from flask import Flask, render_template, jsonify, request
from dungeon.dm import DungeonMaster

app = Flask(__name__)
dm = DungeonMaster()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    state = dm.get_state_dict()
    return jsonify(state)

@app.route('/api/combat/action', methods=['POST'])
def combat_action():
    data = request.json
    action = data.get('action')
    
    narrative = dm.combat.player_action(action)
    
    # We might need to fetch updated combat state from DM if we want it separately
    # But get_state loop handles it mostly. 
    # For the immediate response:
    state = dm.get_state_dict()
    
    return jsonify({
        "narrative": narrative,
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
    data = request.json
    reply, name = dm.chat_with_npc(data.get("npc_index"), data.get("message"))
    return jsonify({"reply": reply, "npc_name": name})

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
    dx, dy = 0, 0
    if direction == 'north': dy = -1
    elif direction == 'south': dy = 1
    elif direction == 'east': dx = 1
    elif direction == 'west': dx = -1
    
    new_pos, combat_msg = dm.move_player(dx, dy)
    
    narrative = combat_msg
    
    # Return updated stats after move
    state = dm.get_state_dict()
    
    return jsonify({
        "position": new_pos,
        "narrative": narrative,
        "stats": state["player"]
    })

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
        print(f"DEBUG: Source not found: {src_path}")
        return jsonify({"error": f"Source file not found: {source_name}"}), 404
        
    import shutil
    try:
        shutil.copy2(src_path, dest_path)
        return jsonify({"status": "success", "message": f"Assigned {source_name} to {target_role}"})
    except Exception as e:
        print(f"DEBUG: Error copying: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
