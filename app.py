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

@app.route('/api/narrative')
def get_narrative():
    return jsonify({
        "narrative": dm.describe_current_room()
    })

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/api/debug/reset', methods=['POST'])
def reset_game():
    dm.reset_game()
    return jsonify({"message": "Game Reset"})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
