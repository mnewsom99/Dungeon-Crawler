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
            is_active=True
        )
        self.session.add(encounter)
        self.session.commit()
        
        # Link monsters
        for m in room_monsters:
            m.encounter_id = encounter.id
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
        """Execute player turn and then cycle queue."""
        encounter = self.session.query(CombatEncounter).filter_by(is_active=True).first()
        if not encounter:
            return {"events": [{"type": "text", "message": "No active combat."}]}

        order = encounter.turn_order
        idx = encounter.current_turn_index
        current_actor = order[idx]
        
        if current_actor["type"] != "player":
            return {"events": [{"type": "text", "message": "It is not your turn!"}]}

        events = []
        
        # --- PLAYER ACTION LOGIC ---
        # Resolve Target
        target = None
        if target_id:
            target = self.session.query(Monster).filter_by(id=target_id).first()
        else:
            # Default to first alive monster
            target = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).first()
            
        if not target and action_type == "attack":
             return {"events": [{"type": "text", "message": "No targets remaining!"}]}

        if action_type == "attack":
            events.extend(self._resolve_player_attack(target))
        elif action_type == "second_wind":
            events.extend(self._resolve_second_wind())
            
        elif action_type == "defend":
            # Temporary defense buff logic (simplified)
            # In a real system we'd set a 'defending' flag on the player for turn duration
            # For now, just a narrative event and maybe a small heal or just a message
            events.append({"type": "text", "message": "You raise your guard, preparing for the next attack."})
            events.append({"type": "popup", "title": "DEFENSE UP", "content": "Armor Class +2 (1 Turn)", "duration": 1500, "color": "rgba(50, 50, 200, 0.8)"})
            # TODO: Implement actual AC mod in database or temp state
            
        elif action_type == "use_potion":
            # Consumable Logic
            heal = roll_dice(4) + roll_dice(4) + 2
            self.dm.player.hp_current = min(self.dm.player.hp_max, self.dm.player.hp_current + heal)
            events.append({"type": "anim", "actor": "player", "anim": "heal"})
            events.append({"type": "text", "message": f"<span style='color:cyan'>Glug glug...</span> You drink a potion and recover <b>{heal} HP</b>."})
            # TODO: Consume item from inventory

        elif action_type == "flee":
             # End Encounter
             encounter.is_active = False
             for m in encounter.monsters:
                 m.state = "idle"
             self.session.commit()
             return {"events": [{"type": "text", "message": "You fled the battle!"}]}
        elif action_type == "move":
             events.append({"type": "text", "message": "You reposition in the chaos."})

        # --- END TURN & CYCLE ---
        # Advance index
        encounter.current_turn_index = (idx + 1) % len(order)
        self.session.commit()
        
        # Process AI Turns until Player
        events.extend(self._process_turn_queue(encounter))
        
        # Check Victory Condition (All monsters dead)
        alive_monsters = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).count()
        if alive_monsters == 0:
            encounter.is_active = False
            self.session.commit()
            events.append({"type": "popup", "title": "VICTORY", "content": "All enemies defeated!", "duration": 3000})
            
        return {"events": events}

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
            
            if monster and monster.is_alive:
                events.append({"type": "turn_switch", "actor": "enemy", "title": f"{monster.name}'s Turn", "content": "Attacking..."})
                events.extend(self._enemy_turn(monster))
            elif actor_data["type"] == "npc":
                from .database import NPC
                npc = self.session.query(NPC).filter_by(id=actor_data["id"]).first()
                if npc:
                    events.append({"type": "turn_switch", "actor": "npc", "title": f"{npc.name}'s Turn", "content": "Acting..."})
                    events.extend(self._npc_turn(npc, encounter))
            else:
                # Skip dead
                pass
                
            # 3. Advance Index
            encounter.current_turn_index = (idx + 1) % len(encounter.turn_order)
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

    def _enemy_turn(self, enemy):
        events = [{"type": "anim", "actor": "enemy", "anim": "attack"}]
        
        # Simple Attack Logic
        str_mod = self._get_modifier(enemy.stats.get("str", 10))
        roll = roll_dice(20)
        total_hit = roll + str_mod
        
        # Player AC
        player_ac = self.dm.player.armor_class
        
        if total_hit >= player_ac:
            dmg = roll_dice(6) + str_mod
            self.dm.player.hp_current -= dmg
            
            # Check for Player Death
            if self.dm.player.hp_current <= 0:
                self.dm.player.hp_current = 0
                
                # End Encounter
                encounter = self.session.query(CombatEncounter).filter_by(is_active=True).first()
                if encounter:
                    encounter.is_active = False
                    
                    # Reset all monsters to idle
                    for m in encounter.monsters:
                        m.state = "idle"
                
                # Respawn Mechanics
                self.dm.player.hp_current = self.dm.player.hp_max
                self.dm.teleport_player(0, 0, 1) # Town Plaza
                
                loss = int((self.dm.player.gold or 0) * 0.1)
                self.dm.player.gold = (self.dm.player.gold or 0) - loss
                
                events.append({"type": "text", "message": f"{enemy.name} attacks: <b>{total_hit}</b> <span style='color:red'>CRITIAL HIT!</span> ({dmg} dmg)"})
                events.append({
                    "type": "popup", 
                    "title": "☠️ YOU DIED ☠️", 
                    "content": f"You fall in battle... and wake up in town.<br>Lost {loss} gold.",
                    "duration": 5000,
                    "color": "rgba(100, 0, 0, 0.95)"
                })
                # Commit immediately to ensure position update propagates
                self.session.commit()
                return events

            # 1. Text Log
            events.append({"type": "text", "message": f"{enemy.name} attacks: <b>{total_hit}</b> <span style='color:red'>HITS!</span> ({dmg} dmg)"})
            
            # 2. Main Screen Popup
            events.append({
                "type": "popup", 
                "title": "HIT!", 
                "content": f"You take <b style='color:red; font-size: 1.5em;'>{dmg}</b> damage!",
                "duration": 2000
            })
        else:
            events.append({"type": "text", "message": f"{enemy.name} attacks and <span style='color:#888'>MISSES</span>."})
            events.append({
                "type": "popup", 
                "title": "MISS", 
                "content": "You dodged the attack!",
                "duration": 1500
            })
            
        return events

    def _npc_turn(self, npc, encounter):
        """Automated turn for friendly NPCs."""
        events = []
        
        # 1. Select Target (First alive monster)
        # Improvement: Select closest monster
        targets = self.session.query(Monster).filter_by(encounter_id=encounter.id, is_alive=True).all()
        if not targets:
             return [{"type": "text", "message": f"{npc.name} looks around, finding no targets."}]
        
        # Sort by distance
        targets.sort(key=lambda m: abs(m.x - npc.x) + abs(m.y - npc.y))
        target = targets[0]

        # 2. Determine Capabilities
        is_mage = "Seraphina" in npc.name
        attack_range = 6 if is_mage else 1
        
        # 3. Movement Logic
        dist = max(abs(target.x - npc.x), abs(target.y - npc.y)) # Chebyshev distance for tiles
        
        if dist > attack_range:
            # Move closer
            dx = 0
            dy = 0
            if npc.x < target.x: dx = 1
            elif npc.x > target.x: dx = -1
            
            if npc.y < target.y: dy = 1
            elif npc.y > target.y: dy = -1
            
            # Try X then Y, or diagonal
            # Simplified pathfinding: Just try the ideal step
            new_x = npc.x + dx
            new_y = npc.y + dy
            
            # Collision Check
            from .database import MapTile, NPC
            blocked = False
            
            # Wall
            tile = self.session.query(MapTile).filter_by(x=new_x, y=new_y, z=npc.z).first()
            if not tile or tile.tile_type in ["wall", "void", "water"]: blocked = True
            
            # Occupied
            if not blocked:
                if new_x == self.dm.player.x and new_y == self.dm.player.y: blocked = True
                elif self.session.query(NPC).filter_by(x=new_x, y=new_y, z=npc.z).first(): blocked = True
                elif self.session.query(Monster).filter_by(x=new_x, y=new_y, z=npc.z).first(): blocked = True
            
            if not blocked:
                npc.x = new_x
                npc.y = new_y
                events.append({"type": "text", "message": f"{npc.name} moves into position."})
                self.session.add(npc)
                # Recalculate dist
                dist = max(abs(target.x - npc.x), abs(target.y - npc.y))
            else:
                events.append({"type": "text", "message": f"{npc.name} tries to move but is blocked."})

        # 4. Attack Logic
        if dist <= attack_range:
            attack_roll = roll_dice(20) + 3 # +3 Proficiency/Stat assumed
            dmg_roll = 0
            action_name = "attacks"
            anim = "attack"
            
            if is_mage:
                action_name = "casts Firebolt at"
                anim = "magic" 
                dmg_roll = roll_dice(10) # 1d10
            else:
                dmg_roll = roll_dice(6) + 2 # 1d6+2 Mace
                
            events.append({"type": "anim", "actor": "npc", "anim": anim})
            
            if attack_roll >= target.armor_class:
                target.hp_current -= dmg_roll
                
                # Check Death
                if target.hp_current <= 0:
                    target.is_alive = False
                    target.state = "dead"
                    target.state = "dead"
                    self._generate_loot(target)
                    flag_modified(target, "state")
                    flag_modified(target, "loot")
                    self.dm.player.xp += 25 # Assist XP
                    events.append({"type": "text", "message": f"{npc.name} {action_name} {target.name} for <b>{dmg_roll}</b> damage. <span style='color:red'>It is destroyed!</span>"})
                else:
                    events.append({"type": "text", "message": f"{npc.name} {action_name} {target.name} for <b>{dmg_roll}</b> damage."})
            else:
                events.append({"type": "text", "message": f"{npc.name} {action_name} {target.name} but misses."})
        else:
             events.append({"type": "text", "message": f"{npc.name} is too far away to attack."})
            
        return events
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
