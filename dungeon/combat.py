import math
import random
from sqlalchemy.orm.attributes import flag_modified
from .rules import roll_dice
from .database import Monster, Player, CombatEncounter

class CombatSystem:
    def __init__(self, dm_instance):
        self.dm = dm_instance
        self.session = dm_instance.session

    def _award_xp(self, player, amount):
        """Awards XP and handles Level Ups."""
        player.xp = (player.xp or 0) + amount
        
        # Level Up Logic
        next_level_xp = (player.level or 1) * 150
        events = []
        
        while player.xp >= next_level_xp:
            player.xp -= next_level_xp
            player.level = (player.level or 1) + 1
            
            # Growth
            player.hp_max += 5
            player.hp_current = player.hp_max
            
            # Stat Point
            stats = dict(player.stats or {})
            stats['unspent_points'] = stats.get('unspent_points', 0) + 1
            player.stats = stats
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(player, "stats")
            
            # Add Level Up Event
            events.append({"type": "popup", "title": "LEVEL UP!", "content": f"Level {player.level}!", "color": "#00ff00", "duration": 3000})
            events.append({"type": "text", "message": f"<span style='color:#0f0'><b>LEVEL UP!</b></span> You are now Level {player.level}. (+1 Stat Point, +5 HP)"})
            
            next_level_xp = player.level * 150
            
        return events

    def _get_modifier(self, score):
        return math.floor((score - 10) / 2)

    def is_active(self):
        """Check if there is an active combat encounter."""
        return self.session.query(CombatEncounter).filter_by(is_active=True).first() is not None

    def end_combat(self):
        """Force end the active combat encounter."""
        active = self.session.query(CombatEncounter).filter_by(is_active=True).first()
        if active:
            active.is_active = False
            for m in active.monsters:
                m.state = "idle"
            self.session.commit()



    def start_combat(self, target_enemy):


        """Initialize a new combat encounter with all nearby enemies."""
        # 1. Check for existing active encounter
        active = self.session.query(CombatEncounter).filter_by(is_active=True).first()
        if active:
            return "Combat is already active!"
            
        # 2. Find all enemies in range (e.g., same room/radius 5)
        # For now, just the target + any within 5 tiles
        room_monsters = self.session.query(Monster).filter(
            Monster.z == target_enemy.z,
            Monster.is_alive == True,
            Monster.x.between(target_enemy.x - 3, target_enemy.x + 3),
            Monster.y.between(target_enemy.y - 3, target_enemy.y + 3)
        ).all()
        
        # 3. Roll Initiatives
        participants = []
        
        # Player Init
        player = self.session.query(Player).first()
        p_stats = player.stats or {"dex": 10}
        p_init = roll_dice(20) + self._get_modifier(p_stats.get("dex", 10))
        participants.append({"type": "player", "id": player.id, "init": p_init, "name": "You"})
        
        # Enemy Init
        for m in room_monsters:
            e_stats = m.stats or {"dex": 10}
            e_init = roll_dice(20) + self._get_modifier(e_stats.get("dex", 10))
            m.initiative = e_init
            m.state = "combat"
            participants.append({"type": "monster", "id": m.id, "init": e_init, "name": m.name})

        # Check for Followers (NPCs with status='following')
        from .database import NPC
        followers = self.session.query(NPC).all() # Simple grab, filter in python for quest_state
        for f in followers:
            qs = f.quest_state or {}
            if qs.get("status") == "following" and f.z == target_enemy.z:
                # Calculate Distance (must be close enough to help)
                dist = abs(f.x - target_enemy.x) + abs(f.y - target_enemy.y)
                if dist < 10:
                    # Generic NPC Init
                    n_init = roll_dice(20) + 1 # +1 Dex assumed
                    participants.append({"type": "npc", "id": f.id, "init": n_init, "name": f.name})
            
        # 4. Sort Turn Order (High to Low)
        participants.sort(key=lambda x: x["init"], reverse=True)
        
        # 5. Create Encounter
        encounter = CombatEncounter(
            turn_order=participants,
            current_turn_index=0,
            is_active=True,
            phase="move",
            moves_left=6,
            actions_left=1,
            bonus_actions_left=1
        )
        self.session.add(encounter)
        self.session.commit()
        
        # Link monsters and REVEAL them
        from .database import MapTile
        for m in room_monsters:
            m.encounter_id = encounter.id
            m.state = "combat"
            
            # Reveal Monster Position
            tile = self.session.query(MapTile).filter_by(x=m.x, y=m.y, z=m.z).first()
            if tile and not tile.is_visited:
                tile.is_visited = True
                
        self.session.commit()
        
        # 6. Initial Turn Check
        # If player is NOT first, we need to process turns until player
        events = [{"type": "text", "message": f"<b>Encounter Started!</b> {len(room_monsters)} Enemies engage!"}]
        
        first_actor = participants[0]
        events.append({"type": "text", "message": f"Initiative Winner: {first_actor['name']} ({first_actor['init']})"})
        
        if first_actor["type"] != "player":
            # Auto-run enemies
             ai_events = self._process_turn_queue(encounter)
             events.extend(ai_events)
             
        return {"events": events}

    def _get_nearest_enemy(self, encounter):
        """Helper to find nearest enemy in encounter."""
        monsters = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).all()
        if not monsters: return None
        
        # Sort by distance
        player = self.session.query(Player).first()
        monsters.sort(key=lambda m: max(abs(m.x - player.x), abs(m.y - player.y)))
        return monsters[0]

    def player_action(self, action_type, target_id=None):
        """Wrapper for player action."""
        # No lock needed (scoped_session)
        try:
            return self._player_action_impl(action_type, target_id)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"events": [{"type": "text", "message": f"Error: {str(e)}"}]}

    def _dist(self, a, b):
        return max(abs(a.x - b.x), abs(a.y - b.y))

    def _player_action_impl(self, action_type, target_id=None):
        """Execute player turn phase-step."""
        player = self.session.query(Player).first()

        encounter = self.session.query(CombatEncounter).filter_by(is_active=True).first()
        if not encounter:
            return {"events": [{"type": "text", "message": "No active combat."}]}

        idx = encounter.current_turn_index
        current_actor = encounter.turn_order[idx]
        
        if current_actor["type"] != "player":
            return {"events": [{"type": "text", "message": "It is not your turn!"}]}

        events = []
        
        # --- FLEXIBLE TURN LOGIC ---
        if action_type == "end_turn":
            # Decrement Rage
            props = dict(player.properties or {})
            if props.get("rage_turns", 0) > 0:
                props["rage_turns"] -= 1
                if props["rage_turns"] == 0:
                    events.append({"type": "text", "message": "<b>Your rage subsides.</b>"})
                player.properties = props
                flag_modified(player, "properties")

            events.append({"type": "text", "message": "Ending Turn..."})
            events.extend(self._cycle_turn(encounter))
            return {"events": events}

        # --- ACTION LOGIC ---
        if action_type == 'attack':
            if encounter.actions_left <= 0:
                return {"events": [{"type": "text", "message": "No actions left."}]}
            
            # Target specific or nearest
            target = None
            if target_id:
                try:
                    t_id = int(target_id)
                    target = next((m for m in encounter.monsters if m.id == t_id and m.is_alive), None)
                except ValueError:
                    target = None
            
            if not target:
                target = self._get_nearest_enemy(encounter)
            
            if not target: return {"events": [{"type": "text", "message": "No enemy in range."}]}
                
            dist = self._dist(player, target)
            if dist > 1.5:
                 return {"events": [{"type": "text", "message": "Target is too far away."}]}
                 
            encounter.actions_left -= 1
            result_events = self._resolve_player_attack(target)
            
            # Check Victory
            is_win, v_events = self._check_victory(encounter)
            result_events.extend(v_events)
            
            self.session.commit()
            return {"events": result_events}

        elif action_type == "move":
            if encounter.moves_left <= 0:
                return {"events": [{"type": "text", "message": "No movement remaining!"}]}
            
            encounter.moves_left -= 1
            # Note: Coordinate update is in DM.py
            pass 

        elif action_type == 'heavy_strike':
             if encounter.actions_left <= 0:
                 return {"events": [{"type": "text", "message": "No actions left."}]}
             
             # Target specific or nearest
             target = None
             target = None
             if target_id:
                 try:
                     t_id = int(target_id)
                     target = next((m for m in encounter.monsters if m.id == t_id and m.is_alive), None)
                 except ValueError:
                     target = None
             
             if not target:
                 target = self._get_nearest_enemy(encounter)
                 
             if not target: return {"events": [{"type": "text", "message": "No enemy in range."}]}
             
             # Heavy Strike Logic
             encounter.actions_left -= 1
             events.append({"type": "text", "message": f"You wind up for a HEAVY STRIKE against {target.name}!"})
             
             p_stats = player.stats or {"str": 10}
             str_mod = self._get_modifier(p_stats.get("str", 10))
             prof_bonus = 2 # Assuming player proficiency bonus is 2
             
             # Rage Check
             props = player.properties or {}
             range_bonus = 2 if props.get("rage_turns", 0) > 0 else 0

             # Roll to Hit: Heavy Strike has -2 penalty, but Rage adds +2
             hit_roll = roll_dice(20) + str_mod + prof_bonus - 2 + range_bonus
             if hit_roll >= target.armor_class:
                 dmg = roll_dice(8) + roll_dice(8) + int(str_mod * 1.5) # 2d8 + 1.5x STR
                 
                 # Rage Bonus (20% Scale)
                 props = player.properties or {}
                 if props.get("rage_turns", 0) > 0:
                     dmg = int(dmg * 1.2)
                     
                 target.hp_current -= dmg
                 events.append({"type": "anim", "actor": "player", "anim": "attack"})
                 events.append({"type": "popup", "title": f"SMASH! {dmg} DMG", "content": "Critical Impact!", "duration": 1500})
                 events.append({"type": "text", "message": f"You CRUSH {target.name} for {dmg} damage!"})
                 
                 if target.hp_current <= 0:
                     target.is_alive = False
                     target.state = "dead"
                     
                     # XP & Loot
                     xp_gain = (target.hp_max or 10) * 4
                     events.extend(self._award_xp(player, xp_gain))
                     events.append({"type": "popup", "title": "VICTORY", "content": f"+{xp_gain} XP", "color": "gold", "duration": 2000})

                     self._generate_loot(target)
                     events.append({"type": "text", "message": f"{target.name} is obliterated!"})
                     
                     is_win, v_events = self._check_victory(encounter)
                     events.extend(v_events)
             else:
                 events.append({"type": "popup", "title": "MISS!", "content": "Swung too wide!", "color": "#aa0", "duration": 1000})
                 events.append({"type": "text", "message": f"You miss {target.name} with the heavy swing."})
                 
             self.session.commit()
             return {"events": events}

        elif action_type == 'cleave':
             if encounter.actions_left <= 0: return {"events": [{"type": "text", "message": "No actions left."}]}
             
             encounter.actions_left -= 1
             events.append({"type": "text", "message": "You sweep your weapon in a wide arc! (Cleave)"})
             
             p_stats = player.stats or {"str": 10}
             str_mod = self._get_modifier(p_stats.get("str", 10))
             prof_bonus = 2 # Assuming player proficiency bonus is 2

             # Find all adjacent (within 1.5 units, effectively adjacent squares)
             enemies = [m for m in encounter.monsters if m.is_alive and self._dist(player, m) <= 1.5]
             
             # Rage Check
             props = player.properties or {}
             range_bonus = 2 if props.get("rage_turns", 0) > 0 else 0

             if not enemies:
                 events.append({"type": "text", "message": "You hit nothing but air."})
             else:
                 for target in enemies:
                     # Cleave: High Accuracy (+2) + Rage (+2), Low Damage (d6)
                     hit = roll_dice(20) + str_mod + prof_bonus + 2 + range_bonus
                     if hit >= target.armor_class:
                         dmg = roll_dice(6) + str_mod
                         # Rage Bonus Damage (20%)
                         if range_bonus > 0: dmg = int(dmg * 1.2)
                         
                         target.hp_current -= dmg
                         events.append({"type": "text", "message": f"Hit {target.name} for {dmg}."})
                         if target.hp_current <= 0:
                             target.is_alive = False
                             target.state = "dead"
                             player.xp += 50 # Assuming XP gain for cleave kill
                             self._generate_loot(target)
                             events.append({"type": "text", "message": f"{target.name} falls!"})
                     else:
                         events.append({"type": "text", "message": f"Missed {target.name}."})
                 
                 # Victory Check once after sweep
                 events.extend(self._check_victory(encounter))
                 
             self.session.commit()
             return {"events": events}

        elif action_type == 'kick':
             if encounter.bonus_actions_left <= 0: return {"events": [{"type": "text", "message": "No bonus actions left."}]}
             
             target = None
             if target_id:
                 try:
                     t_id = int(target_id)
                     target = next((m for m in encounter.monsters if m.id == t_id and m.is_alive), None)
                 except ValueError:
                     target = None
                 
             if not target:
                 target = self._get_nearest_enemy(encounter)
                 
             if not target or self._dist(player, target) > 1.5: # Must be adjacent
                 return {"events": [{"type": "text", "message": "No enemy close enough to kick."}]}
             
             encounter.bonus_actions_left -= 1
             
             p_stats = player.stats or {"str": 10}
             str_mod = self._get_modifier(p_stats.get("str", 10))

             # Contest: Player STR (Athletics) vs DC 12
             athletics = roll_dice(20) + str_mod # +STR mod
             dc = 12 # Fixed DC for simplicity or Target STR? Let's use Fixed DC + Target Size Mod if we had it.
             
             if athletics >= dc:
                 # Success
                 events.append({"type": "text", "message": f"You KICK {target.name}! <span style='color:orange'>STUNNED!</span> <span style='font-size:0.8em; color:#888'>(Rolled {athletics} vs DC {dc})</span>"})
                 events.append({"type": "popup", "title": "KNOCKDOWN!", "content": "Enemy Stunned", "duration": 1500, "color": "#fa0"})
                 
                 # Apply Stun
                 # We need a way to track status. Assuming simple "stunned" state or properties?
                 # Monster doesn't have "properties" column in models shown.
                 # Re-use 'state'? 'combat' is default.
                 # Let's use 'abilities' list to add 'stunned'? No, that's static capabilities.
                 # Let's add to 'metadata' if it existed? No.
                 # Let's use 'state' = 'stunned'.
                 target.state = 'stunned'
                 # Note: Need to handle 'stunned' in enemy turn logic to skip turn.
             else:
                 events.append({"type": "text", "message": f"You try to kick {target.name}, but they hold firm."})
                 
             self.session.commit()
             return {"events": events}

        elif action_type == 'rage':
             if encounter.bonus_actions_left <= 0: return {"events": [{"type": "text", "message": "No bonus actions left."}]}
             encounter.bonus_actions_left -= 1
             
             events.append({"type": "text", "message": "You ROAR with primal fury! (+20% DMG, +2 HIT, Vuln +20%)"})
             events.append({"type": "anim", "actor": "player", "anim": "buff"}) # visual?
             
             props = dict(player.properties or {})
             props["rage_turns"] = 3
             player.properties = props
             flag_modified(player, "properties")
             
             self.session.commit()
             return {"events": events}

        elif action_type == "attack":
            if encounter.actions_left <= 0:
                return {"events": [{"type": "text", "message": "Action already spent!"}]}

            encounter.actions_left -= 1
            
            # Resolve Target
            target = None
            if target_id: target = self.session.query(Monster).filter_by(id=target_id).first()
            else: target = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).first()
            
            if not target:
                # Fallback: If target died or ID is wrong, target FIRST living enemy
                target = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).first()
            
            if not target: 
                # If still no target, we might have won already?
                events.extend(self._check_victory(encounter))
                if encounter.is_active:
                        events.append({"type": "text", "message": "No valid target found."})
            else: 
                events.extend(self._resolve_player_attack(target))
                # Check Victory Condition
                events.extend(self._check_victory(encounter))
            
        elif action_type in ["use_potion", "second_wind"]:
            if encounter.bonus_actions_left <= 0:
                return {"events": [{"type": "text", "message": "Bonus action already spent!"}]}
            
            encounter.bonus_actions_left -= 1
            
            if action_type == "use_potion":
                heal = roll_dice(4) + roll_dice(4) + 2
                player.hp_current = min(player.hp_max, player.hp_current + heal)
                events.append({"type": "anim", "actor": "player", "anim": "heal"})
                events.append({"type": "text", "message": f"You drink a potion and recover <b>{heal} HP</b>."})
            elif action_type == "second_wind":
                events.extend(self._resolve_second_wind())

        elif action_type == "flee":
             active = self.session.query(CombatEncounter).filter_by(is_active=True).first()
             if active:
                 # 1. Calculate Escape Vector (Average Enemy Position)
                 avg_x, avg_y, count = 0, 0, 0
                 for m in active.monsters:
                     avg_x += m.x; avg_y += m.y; count += 1
                 
                 target_x, target_y = player.x, player.y
                 if count > 0:
                     avg_x /= count; avg_y /= count
                     dx = player.x - avg_x
                     dy = player.y - avg_y
                     mag = max(abs(dx), abs(dy), 0.1) # Avoid div0
                     
                     # Push 5 tiles away
                     push_dist = 5
                     target_x = int(player.x + (dx/mag * push_dist))
                     target_y = int(player.y + (dy/mag * push_dist))

                 # 2. Apply Teleport (Force)
                 # Note: Ideally we check walls, but for 'scrambling away' we might clip.
                 # Let's try to map-check or just do it.
                 # Safe Clamp?
                 player.x = target_x
                 player.y = target_y
                 
                 # 3. End Combat
                 active.is_active = False
                 for m in active.monsters: m.state = "idle"
                 
                 self.session.commit()
                 
                 # 4. Update Fog of War at new location
                 self.dm.movement.update_visited(player.x, player.y, player.z)

                 return {"events": [
                     {"type": "text", "message": "You scrambled away from the battle!"},
                     {"type": "popup", "title": "ESCAPED!", "content": "Battle Ended", "color": "#aaf"}
                 ]}

        # No Auto-Advance. Player must click End Turn.
        self.session.commit()
        return {"events": events}

    def _advance_phase(self, encounter):
        """Move to next phase or end turn."""
        events = []
        if encounter.phase == "move":
            encounter.phase = "action"
            events.append({"type": "popup", "title": "ACTION PHASE", "content": "Choose your action!", "duration": 1000})
        elif encounter.phase == "action":
            encounter.phase = "bonus"
            events.append({"type": "popup", "title": "BONUS PHASE", "content": "Bonus actions available.", "duration": 1000})
        elif encounter.phase == "bonus":
            events.append({"type": "text", "message": "Ending Turn..."})
            events.extend(self._cycle_turn(encounter))
        
        self.session.commit()
        return events

    def _cycle_turn(self, encounter):
        # Safety Check: Are we already victorious?
        if self._check_victory_quiet(encounter):
             return [{"type": "text", "message": "Combat Over."}]

        encounter.current_turn_index = (encounter.current_turn_index + 1) % len(encounter.turn_order)
        
        # Reset Stats for New Actor
        encounter.phase = "move"
        encounter.moves_left = 6
        encounter.actions_left = 1
        encounter.bonus_actions_left = 1
        
        self.session.commit()
        return self._process_turn_queue(encounter)

    def _process_turn_queue(self, encounter):
        """Loop through turn order until it is the Player's turn."""
        events = []
        max_loops = 20 # Safety break
        loops = 0
        
        while loops < max_loops:
            idx = encounter.current_turn_index
            actor_data = encounter.turn_order[idx]
            
            # 1. Stop if Player
            if actor_data["type"] == "player":
                events.append({"type": "popup", "title": "PLAYER TURN", "content": "Choose your action!", "duration": 1500})
                return events
                
            # 2. Process Enemy
            monster = self.session.query(Monster).filter_by(id=actor_data["id"]).first()
            npc = None
            if actor_data["type"] == "npc":
                 from .database import NPC
                 npc = self.session.query(NPC).filter_by(id=actor_data["id"]).first()
            
            if monster and monster.is_alive:
                events.append({"type": "turn_switch", "actor": "enemy", "title": f"{monster.name}'s Turn", "content": "Attacking..."})
                # Simulate Phases
                # Phase 1: Move
                encounter.phase = "move"
                # Phase 2: Action
                encounter.phase = "action"
                # Phase 3: Bonus
                encounter.phase = "bonus"
                # Do Logic
                events.extend(self._enemy_turn(monster))
                
            elif npc:
                events.append({"type": "turn_switch", "actor": "npc", "title": f"{npc.name}'s Turn", "content": "Acting..."})
                events.extend(self._npc_turn(npc, encounter))
            else:
                pass # Skip dead
                
            # 3. Advance Index
            encounter.current_turn_index = (idx + 1) % len(encounter.turn_order)
            
            # Reset for next
            encounter.phase = "move"
            encounter.moves_left = 6
            encounter.actions_left = 1
            encounter.bonus_actions_left = 1
            
            self.session.commit() # Save progress
            loops += 1
            
        return events

    def _resolve_second_wind(self):
        player = self.session.query(Player).first()
        heal = roll_dice(10) + 1
        player.hp_current = min(player.hp_max, player.hp_current + heal)
        return [
            {"type": "anim", "actor": "player", "anim": "heal"},
            {"type": "text", "message": f"<span style='color:gold'>Second Wind!</span> You recover <b>{heal} HP</b>."}
        ]

    def _resolve_player_attack(self, enemy):
        events = []
        # Stats
        player = self.session.query(Player).first()
        p_stats = player.stats or {"str": 10}
        str_mod = self._get_modifier(p_stats.get("str", 10))
        prof_bonus = 2
        
        # Attack Roll
        # Attack Roll: Regular Attack gets +1 Accuracy
        # Rage Bonus: +2 Hit
        props = player.properties or {}
        is_raging = props.get("rage_turns", 0) > 0
        rage_hit_mod = 2 if is_raging else 0
        
        roll = roll_dice(20)
        hit_mod = str_mod + prof_bonus + 1 + rage_hit_mod
        total_hit = roll + hit_mod
        
        events.append({"type": "popup", "title": "ATTACK", "content": f"You attack {enemy.name}!", "duration": 1000})
        events.append({"type": "anim", "actor": "player", "anim": "attack"})
        
        if total_hit >= enemy.armor_class:
            dmg = roll_dice(8) + str_mod
            if is_raging: dmg = int(dmg * 1.2) # Rage 20% Bonus
            
            # OBSIDIAN SENTINEL: High Defense
            if enemy.name == "Obsidian Sentinel":
                dmg = max(1, dmg // 2)
                events.append({"type": "text", "message": "<i style='color:#777'>Your weapon glances off the obsidian armor!</i>"})

            print(f"DEBUG: Applying {dmg} damage to {enemy.name} (ID: {enemy.id}). HP before: {enemy.hp_current}")
            enemy.hp_current -= dmg
            print(f"DEBUG: HP after: {enemy.hp_current}")
            flag_modified(enemy, "hp_current") # Force SQLAlchemy to notice (paranoid)
            
            # Check Death
            if enemy.hp_current <= 0:
                enemy.is_alive = False
                enemy.state = "dead"
                
                # Dynamic XP
                xp_gain = (enemy.hp_max or 10) * 4
                events.extend(self._award_xp(player, xp_gain))
                events.append({"type": "popup", "title": "VICTORY", "content": f"+{xp_gain} XP", "color": "gold", "duration": 2000})
                
                # SULFUR BAT: Volatile Explosion (Death Rattle)
                if enemy.name == "Sulfur Bat":
                     expl_dmg = roll_dice(6)
                     player.hp_current = max(0, player.hp_current - expl_dmg)
                     events.append({"type": "anim", "actor": "enemy", "anim": "attack"}) # Explosion anim?
                     events.append({"type": "text", "message": f"The <span style='color:yellow'>Sulfur Bat</span> EXPLODES for <b>{expl_dmg}</b> fire damage!"})

                # --- QUEST HOOK ---
                try:
                    from .quests import QuestManager
                    qm = QuestManager(self.session, self.dm.player)
                    qm.record_kill(enemy.name)
                except Exception as e:
                    print(f"Quest Hook Error: {e}")
                # ------------------
                
                # Generate Loot
                self._generate_loot(enemy)
                flag_modified(enemy, "loot")
                
                events.append({"type": "text", "message": f"You slash the {enemy.name} for <b>{dmg}</b> damage. <span style='color:red'>It falls dead!</span> <span style='color:#ccc; font-size:0.9em'>(Roll {roll}+{hit_mod}={total_hit})</span>"})
            else:
                events.append({"type": "text", "message": f"You hit {enemy.name} for <b>{dmg}</b> damage! <span style='color:#ccc; font-size:0.9em'>(Roll {roll}+{hit_mod}={total_hit})</span>"})
                events.append({"type": "popup", "title": "HIT!", "content": f"{dmg} Damage", "color": "#ff3333", "duration": 1200})
        else:
            events.append({"type": "text", "message": f"You swing at {enemy.name} but miss. <span style='color:#ccc; font-size:0.9em'>(Roll {roll}+{hit_mod}={total_hit} vs AC {enemy.armor_class})</span>"})
            events.append({"type": "popup", "title": "MISS", "content": "You missed!", "color": "#ffd700", "duration": 1000})
            
        return events

    # --- HELPER METHODS ---
    def _move_actor_towards(self, actor, target_x, target_y, max_steps=6):
        """Standardized pathfinding - moves actor towards target."""
        # Simple Pathfinding: Move towards target one tile at a time
        from .database import MapTile, NPC, Monster
        
        start_dist = max(abs(actor.x - target_x), abs(actor.y - target_y))
        current_dist = start_dist
        steps = 0
        moved = False
        
        # Valid Tile Cache (optional optimization could go here)
        
        while steps < max_steps and current_dist > 1.5: # 1.5 is melee range
            dx = 0
            dy = 0
            if actor.x < target_x: dx = 1
            elif actor.x > target_x: dx = -1
            
            if actor.y < target_y: dy = 1
            elif actor.y > target_y: dy = -1
            
            new_x = actor.x + dx
            new_y = actor.y + dy
            
            # blocked?
            blocked = False
            
            # 1. Wall Check
            # We should query the map. For now, we trust the generator's open space or check known obstacles.
            # Ideally: tile = self.session.query(MapTile).filter_by(x=new_x, y=new_y, z=actor.z).first()
            # This is expensive in a loop.
            # Simplified: Check if occupied by another entity
            
            if self.session.query(Monster).filter_by(x=new_x, y=new_y, z=actor.z, is_alive=True).first(): blocked = True
            if self.session.query(NPC).filter_by(x=new_x, y=new_y, z=actor.z).first(): blocked = True
            player = self.session.query(Player).first()
            if new_x == player.x and new_y == player.y: blocked = True
            
            if not blocked:
                actor.x = new_x
                actor.y = new_y
                moved = True
                steps += 1
                current_dist = max(abs(actor.x - target_x), abs(actor.y - target_y))
            else:
                # Try only ONE axis if diagonal blocked, OR try alternate axis if straight blocked
                alt_moves = []
                if dx != 0 and dy != 0:
                     alt_moves.append((dx, 0)) # Try X only
                     alt_moves.append((0, dy)) # Try Y only
                elif dx != 0:
                     alt_moves.append((0, 1))
                     alt_moves.append((0, -1))
                elif dy != 0:
                     alt_moves.append((1, 0))
                     alt_moves.append((-1, 0))
                
                found_alt = False
                for adx, ady in alt_moves:
                     anx, any_ = actor.x + adx, actor.y + ady
                     
                     # Simple Block Check (Copy of above)
                     ablocked = False
                     player = self.session.query(Player).first()
                     if anx == player.x and any_ == player.y: ablocked = True
                     elif self.session.query(Monster).filter_by(x=anx, y=any_, z=actor.z, is_alive=True).first(): ablocked = True
                     
                     if not ablocked:
                         actor.x = anx
                         actor.y = any_
                         steps += 1
                         current_dist = max(abs(actor.x - target_x), abs(actor.y - target_y))
                         moved = True
                         found_alt = True
                         break
                
                if not found_alt:
                    break # Truly blocked

        if moved: 
            self.session.add(actor)
            self.session.flush() # CRITICAL: Update 'x/y' in transaction so next actor sees it
        return moved
        
    def _check_victory_quiet(self, encounter):
        """Boolean check for victory (no events)."""
        alive_count = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).count()
        if alive_count == 0:
            encounter.is_active = False
            self.session.commit()
            return True
        return False

    def _check_victory(self, encounter):
        """Checks if all monsters are dead and ends combat if so."""
        # Query directly to ensure we aren't using stale 'encounter.monsters' list from memory
        try:
             alive_monsters = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).all()
        except:
             return False, []

        events = []
        if not alive_monsters:
            encounter.is_active = False
            
            events.append({"type": "text", "message": "<b>Combat Victory!</b>"})
            events.append({"type": "popup", "title": "VICTORY", "content": "Battle Won!", "color": "gold", "duration": 2000})

            # --- DUNGEON CLEAR CHECK ---
            # Check if ANY monsters remain in this dungeon (z=0)
            # Only check if we are actually in that dungeon context (simple check)
            try:
                remaining_monsters = self.session.query(Monster).filter_by(z=0, is_alive=True).count()
                if remaining_monsters == 0:
                     events.append({
                        "type": "popup",
                        "title": "DUNGEON CLEARED!",
                        "content": "The darkness lifts...",
                        "duration": 6000,
                        "color": "#00ff00"
                    })
                     events.append({"type": "text", "message": "<br><span style='color:#0f0; font-size:1.1em; font-weight:bold;'>DUNGEON CLEARED! The air feels lighter.</span>"})
            except: pass

            return True, events
        return False, events

    def _has_equipped_effect(self, effect_name):
        player = self.session.query(Player).first()
        if not player.inventory: return False
        for item in player.inventory:
            if item.is_equipped and item.properties and item.properties.get("effect") == effect_name:
                return True
        return False

    # --- ENEMY TURN ---
    def _enemy_turn(self, enemy):
        from .database import CombatEncounter # Ensure import
        events = []
        
        # 1. Check Stunned State
        if enemy.state == "stunned":
            events.append({"type": "text", "message": f"<span style='color:orange'>{enemy.name} is STUNNED and skips their turn!</span>"})
            events.append({"type": "popup", "title": "STUNNED", "content": "Turn Skipped", "duration": 1500, "color": "#fa0"})
            
            # Recover from stun
            enemy.state = "combat" 
            return events

        player = self.session.query(Player).first()
        dist = max(abs(enemy.x - player.x), abs(enemy.y - player.y))
        attack_range = 1.5

        # MOVEMENT
        if dist > attack_range:
             moved = self._move_actor_towards(enemy, player.x, player.y)
             if moved: events.append({"type": "text", "message": f"{enemy.name} moves closer."})
             dist = max(abs(enemy.x - player.x), abs(enemy.y - player.y)) # Recalc

        # ACTION
        if dist <= attack_range or (enemy.name == "Magma Weaver" and dist <= 4):
            # Advanced AI Checks
            executed_special = False
            
            # MAGMA WEAVER: Molten Web (Range 4, 30% Chance)
            if enemy.name == "Magma Weaver" and roll_dice(100) < 30:
                 events.append({"type": "text", "message": f"<b style='color:darkorange'>Magma Weaver</b> sprays a <span style='color:orangered'>Molten Web</span>!"})
                 events.append({"type": "anim", "actor": "enemy", "anim": "attack"}) # Need web anim?
                 player.hp_current = max(0, player.hp_current - 5)
                 events.append({"type": "popup", "title": "UNKINDLED", "content": "You are webbed!", "duration": 2000})
                 
                 encounter = self.session.query(CombatEncounter).filter_by(is_active=True).first()
                 if encounter:
                      encounter.moves_left = 0
                      events.append({"type": "text", "message": "The hardening lava prevents you from moving!"})
                 executed_special = True

            # CINDER HOUND: Burning Aura (Passive Trigger on Attack)
            if enemy.name == "Cinder-Hound" and dist <= 1.5:
                 if self._has_equipped_effect("fire_resist"):
                     events.append({"type": "text", "message": f"Your Phoenix Shield absorbs the Cinder-Hound's heat!"})
                 else:
                     burn_dmg = roll_dice(4)
                     player.hp_current = max(0, player.hp_current - burn_dmg)
                     events.append({"type": "text", "message": f"The <span style='color:orange'>Cinder-Hound's</span> heat burns you for {burn_dmg}!"})

            if not executed_special and dist <= 1.5:
                events.append({"type": "popup", "title": f"{enemy.name.upper()} ATTACKS", "content": "Prepare to defend!", "color": "#f88", "duration": 1000})
                events.append({"type": "anim", "actor": "enemy", "anim": "attack"})
                
                # Attack
                stats = enemy.stats or {}
                str_mod = self._get_modifier(stats.get("str", 10))
                total_hit = roll_dice(20) + str_mod
                
                if total_hit >= player.armor_class:
                    dmg = roll_dice(6) + str_mod
                    
                    # Rage Vulnerability
                    props = player.properties or {}
                    if props.get("rage_turns", 0) > 0:
                         dmg = int(dmg * 1.2)
                         events.append({"type": "text", "message": f"<span style='color:orange'>(Rage Vulnerability +20%)</span>"})

                    player.hp_current = max(0, player.hp_current - dmg)
                    events.append({"type": "text", "message": f"{enemy.name} hits you for <span style='color:red'>{dmg}</span> dmg!"})
                    events.append({"type": "popup", "title": "HIT", "content": f"Took {dmg} Damage!", "color": "#d00", "duration": 1200})
                    
                    if player.hp_current == 0:
                        # Player Death
                        events.append({"type": "popup", "title": "DEFEAT", "content": "You have fallen.", "duration": 4000})
                        self.dm.teleport_player(0,0,1)
                        player.hp_current = player.hp_max
                        # Reset Encounter
                        encounter = self.session.query(CombatEncounter).filter_by(is_active=True).first()
                        if encounter: encounter.is_active = False
                else:
                     events.append({"type": "text", "message": f"{enemy.name} misses you."})
                     events.append({"type": "popup", "title": "DODGED", "content": "Enemy missed!", "color": "#afa", "duration": 1000})
        else:
             # Fallback for far away or blocked enemies
             if not events:
                 action_msg = f"{enemy.name} roars!"
                 if dist > 8: action_msg = f"{enemy.name} is lurking in the shadows..."
                 else: action_msg = f"{enemy.name} is blocked."
                 events.append({"type": "text", "message": action_msg})
             elif moved and dist > attack_range:
                  # Moved but still out of range
                  pass 

        return events

    def _npc_turn(self, npc, encounter):
        """Automated turn for friendly NPCs."""
        events = []
        
        # 1. Target Selection
        targets = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).all()
        if not targets: return [{"type": "text", "message": f"{npc.name} waits."}]
        
        targets.sort(key=lambda m: max(abs(m.x - npc.x), abs(m.y - npc.y)))
        target = targets[0]

        is_mage = "Seraphina" in npc.name
        attack_range = 6 if is_mage else 1.5
        dist = max(abs(target.x - npc.x), abs(target.y - npc.y))
        
        # 2. Movement
        if dist > attack_range:
             moved = self._move_actor_towards(npc, target.x, target.y)
             if moved: events.append({"type": "text", "message": f"{npc.name} moves."})
             dist = max(abs(target.x - npc.x), abs(target.y - npc.y))
             
        # 3. Attack
        if dist <= attack_range:
             # Roll
             hit = roll_dice(20) + 3
             if hit >= target.armor_class:
                 dmg = roll_dice(8 if not is_mage else 10)
                 target.hp_current -= dmg
                 events.append({"type": "text", "message": f"{npc.name} hits {target.name} for {dmg}."})
                 if target.hp_current <= 0:
                     target.is_alive = False
                     target.state = "dead"
                     self._generate_loot(target)
                     events.append({"type": "text", "message": f"{target.name} dies!"})
                     # Victory Check
                     events.extend(self._check_victory(encounter))
             else:
                 events.append({"type": "text", "message": f"{npc.name} misses {target.name}."})
                 
        return events

    def _generate_loot(self, enemy):
        """Generates loot for a fresh corpse."""
        from .items import ITEM_TEMPLATES
        loot = []
        
        # Gold Scales with Level
        level = enemy.level or 1
        gold_base = roll_dice(10) + 5
        gold = gold_base + (level * 2) # Scale gold
        
        loot.append({"type": "gold", "qty": gold, "name": f"{gold} Gold Coins", "icon": "💰", "id": "gold"})
        
        # Item Drops
        # Base Roll d20 + Level/3
        roll = roll_dice(20) + (level // 3)
        code = None
        
        if roll >= 20: code = "chainmail" # Rare
        elif roll >= 15: code = "healing_potion" # Uncommon
        elif roll >= 10: code = "dagger" # Common
        elif roll >= 5: code = "torch" # Junk/Tool? We don't have torch valid item maybe? Let's check.
        
        # If no code or invalid, maybe fallback
        if roll >= 5 and not code: code = "healing_potion" # Fallback benefit
        
        # Specific Dungeon Loot (Priority)
        if enemy.z == 3: # Fire Dungeon
             f_roll = roll_dice(100)
             if f_roll > 92: code = "phoenix_shield" 
             elif f_roll > 75: code = "item_core" # Material
             elif f_roll > 60: code = "cryo_flask" 
        
        elif enemy.z == 4: # Ice Dungeon
             i_roll = roll_dice(100)
             if i_roll > 92: code = "frost_brand" # Hypothetical
             elif i_roll > 75: code = "item_frost_shard"
        
        # Add Item
        if code and code in ITEM_TEMPLATES:
            t = ITEM_TEMPLATES[code]
            loot.append({
                "type": "item", 
                "code": code, 
                "name": t['name'], 
                "icon": t['properties'].get('icon', '📦'),
                "id": f"loot_{random.randint(1000,9999)}"
            })
        
        # Bonus: Guaranteed 'Junk' or small item for high levels if nothing else
        if not code and level > 5 and roll_dice(10) > 5:
             loot.append({"type": "item", "code": "healing_potion", "name": "Healing Potion", "icon": "🧪", "id": f"loot_{random.randint(1000,9999)}"})

        enemy.loot = loot


