import math
import random
from sqlalchemy.orm.attributes import flag_modified
from .rules import roll_dice
from .database import Monster, Player, CombatEncounter

class CombatSystem:
    def __init__(self, dm_instance):
        self.dm = dm_instance
        self.session = dm_instance.session

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
        p_stats = self.dm.player.stats or {"dex": 10}
        p_init = roll_dice(20) + self._get_modifier(p_stats.get("dex", 10))
        participants.append({"type": "player", "id": self.dm.player.id, "init": p_init, "name": "You"})
        
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
        
        # Link monsters
        for m in room_monsters:
            m.encounter_id = encounter.id
            m.state = "combat" # Ensure state is updated so frontend sees them as targets
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

    def player_action(self, action_type, target_id=None):
        """Execute player turn phase-step."""
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
            events.append({"type": "text", "message": "Ending Turn..."})
            events.extend(self._cycle_turn(encounter))
            return {"events": events}

        # --- ACTION LOGIC ---
        if action_type == "move":
            if encounter.moves_left <= 0:
                return {"events": [{"type": "text", "message": "No movement remaining!"}]}
            
            encounter.moves_left -= 1
            # Note: Coordinate update is in DM.py
            pass 

        elif action_type in ["attack"]:
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
                self.dm.player.hp_current = min(self.dm.player.hp_max, self.dm.player.hp_current + heal)
                events.append({"type": "anim", "actor": "player", "anim": "heal"})
                events.append({"type": "text", "message": f"You drink a potion and recover <b>{heal} HP</b>."})
            elif action_type == "second_wind":
                events.extend(self._resolve_second_wind())

        elif action_type == "flee":
             active = self.session.query(CombatEncounter).filter_by(is_active=True).first()
             if active:
                 active.is_active = False
                 for m in active.monsters: m.state = "idle"
                 self.session.commit()
                 return {"events": [{"type": "text", "message": "You fled the battle!"}]}

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
        heal = roll_dice(10) + 1
        self.dm.player.hp_current = min(self.dm.player.hp_max, self.dm.player.hp_current + heal)
        return [
            {"type": "anim", "actor": "player", "anim": "heal"},
            {"type": "text", "message": f"<span style='color:gold'>Second Wind!</span> You recover <b>{heal} HP</b>."}
        ]

    def _resolve_player_attack(self, enemy):
        events = []
        # Stats
        p_stats = self.dm.player.stats or {"str": 10}
        str_mod = self._get_modifier(p_stats.get("str", 10))
        prof_bonus = 2
        
        # Attack Roll
        roll = roll_dice(20)
        hit_mod = str_mod + prof_bonus
        total_hit = roll + hit_mod
        
        events.append({"type": "anim", "actor": "player", "anim": "attack"})
        
        if total_hit >= enemy.armor_class:
            dmg = roll_dice(8) + str_mod
            enemy.hp_current -= dmg
            
            # Check Death
            if enemy.hp_current <= 0:
                enemy.is_alive = False
                enemy.state = "dead"
                self.dm.player.xp += 50
                
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
                
                events.append({"type": "text", "message": f"You slash the {enemy.name} for <b>{dmg}</b> damage. <span style='color:red'>It falls dead!</span>"})
                
                events.append({"type": "text", "message": f"You slash the {enemy.name} for <b>{dmg}</b> damage. <span style='color:red'>It falls dead!</span>"})
            else:
                events.append({"type": "text", "message": f"You hit {enemy.name} for <b>{dmg}</b> damage!"})
        else:
            events.append({"type": "text", "message": f"You swing at {enemy.name} but miss (Rolled {total_hit})."})
            
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
            if new_x == self.dm.player.x and new_y == self.dm.player.y: blocked = True
            
            if not blocked:
                actor.x = new_x
                actor.y = new_y
                moved = True
                steps += 1
                current_dist = max(abs(actor.x - target_x), abs(actor.y - target_y))
            else:
                # Try only ONE axis if diagonal blocked
                if dx != 0 and dy != 0:
                     # Try X only
                     new_x = actor.x + dx
                     new_y = actor.y
                     # Re-check (Simplified generic check)
                     if not (new_x == self.dm.player.x and new_y == self.dm.player.y):
                         actor.x = new_x 
                         steps += 1
                         current_dist = max(abs(actor.x - target_x), abs(actor.y - target_y))
                         moved = True
                     # Else Try Y...
                else:
                    break # Blocked

        if moved: 
            self.session.add(actor)
            self.session.flush() # CRITICAL: Update 'x/y' in transaction so next actor sees it
        return moved
        
    def _check_victory(self, encounter):
        """Checks if all monsters are dead and ends combat if so."""
        alive_monsters = [m for m in encounter.monsters if m.is_alive]
        events = []
        if not alive_monsters:
            encounter.is_active = False
            
            # --- XP CALCULATION ---
            total_xp = 0
            for m in encounter.monsters:
                 # Simple Formula: 4 XP per HP (so a 10 HP rat = 40 XP, Need 100 for Lvl 2)
                 total_xp += (m.hp_max or 10) * 4
            
            pl = self.dm.player
            old_level = pl.level or 1
            pl.xp = (pl.xp or 0) + total_xp
            
            # --- LEVEL UP CHECK ---
            # Threshold: Level * 150 (Level 1->2 needs 150 total XP)
            next_level_xp = old_level * 150
            leveled_up = False
            
            while pl.xp >= next_level_xp:
                pl.xp -= next_level_xp
                pl.level += 1
                leveled_up = True
                
                # Stat Growths
                hp_gain = 5 # Small fixed growth
                pl.hp_max += hp_gain
                pl.hp_current = pl.hp_max # Full Heal
                
                # Grant Stat Point
                # Ensure stats dict exists and is mutable
                stats = dict(pl.stats or {})
                if 'unspent_points' not in stats: stats['unspent_points'] = 0
                stats['unspent_points'] += 1
                pl.stats = stats
                
                # Flag modified for JSON
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(pl, "stats")
                
                next_level_xp = pl.level * 150
                
            self.session.commit()

            events.append({
                "type": "popup", 
                "title": "VICTORY!", 
                "content": f"Combat ended. Gained {total_xp} XP.",
                "duration": 3000,
                "color": "#d4af37" 
            })
            
            msg = f"<b>Victory!</b> You gained <span style='color:#0f0'>{total_xp} XP</span>."
            if leveled_up:
                msg += f"<br><span style='color:#ff0; font-size:1.2em;'>LEVEL UP! You are now Level {pl.level}!</span>"
                events.append({
                    "type": "popup",
                    "title": "LEVEL UP!",
                    "content": f"Reached Level {pl.level}!",
                    "duration": 5000,
                    "color": "#ffff00"
                })
                
            events.append({"type": "text", "message": msg})
            
        return events

    # --- ENEMY TURN ---
    def _enemy_turn(self, enemy):
        events = []
        player = self.dm.player
        dist = max(abs(enemy.x - player.x), abs(enemy.y - player.y))
        attack_range = 1.5

        # MOVEMENT
        if dist > attack_range:
             moved = self._move_actor_towards(enemy, player.x, player.y)
             if moved: events.append({"type": "text", "message": f"{enemy.name} moves closer."})
             dist = max(abs(enemy.x - player.x), abs(enemy.y - player.y)) # Recalc

        # ACTION
        if dist <= attack_range:
            events.append({"type": "anim", "actor": "enemy", "anim": "attack"})
            
            # Attack
            str_mod = self._get_modifier(enemy.stats.get("str", 10))
            total_hit = roll_dice(20) + str_mod
            
            if total_hit >= player.armor_class:
                dmg = roll_dice(6) + str_mod
                player.hp_current = max(0, player.hp_current - dmg)
                events.append({"type": "text", "message": f"{enemy.name} hits you for <span style='color:red'>{dmg}</span> dmg!"})
                events.append({"type": "popup", "title": "HIT", "content": f"-{dmg} HP", "duration": 1000})
                
                if player.hp_current == 0:
                    # Player Death
                    events.append({"type": "popup", "title": "DEFEAT", "content": "You have fallen.", "duration": 4000})
                    self.dm.teleport_player(0,0,1)
                    player.hp_current = player.hp_max
                    # Reset Encounter
                    encounter = self.session.query(CombatEncounter).filter_by(is_active=True).first()
                    if encounter: encounter.is_active = False
            else:
                 events.append({"type": "text", "message": f"{enemy.name} misses."})
        else:
             events.append({"type": "text", "message": f"{enemy.name} roars!"})

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
        # Gold
        gold = roll_dice(10) + 5
        loot.append({"type": "gold", "qty": gold, "name": f"{gold} Gold Coins", "icon": "💰", "id": "gold"})
        
        # Item (Boosted Rates)
        roll = roll_dice(20)
        code = None
        if roll > 10: code = "chainmail" # Was 15
        elif roll > 6: code = "healing_potion" # Was 10
        elif roll > 2: code = "dagger" # Was 5
        
        # Chance for second item
        if roll_dice(20) > 15:
             loot.append({"type": "item", "code": "healing_potion", "name": "Healing Potion", "icon": "🧪", "id": f"loot_{random.randint(1000,9999)}"})
        
        if code and code in ITEM_TEMPLATES:
            t = ITEM_TEMPLATES[code]
            loot.append({
                "type": "item", 
                "code": code, 
                "name": t['name'], 
                "icon": t['properties'].get('icon', '📦'),
                "id": f"loot_{random.randint(1000,9999)}"
            })
        
        enemy.loot = loot
