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
        elif action_type == "flee":
             # End Encounter
             encounter.is_active = False
             for m in encounter.monsters:
                 m.state = "idle"
             self.session.commit()
             return {"events": [{"type": "text", "message": "You fled the battle!"}]}

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
                from .items import ITEM_TEMPLATES
                loot = []
                # Gold
                gold = roll_dice(10) + 5
                loot.append({"type": "gold", "qty": gold, "name": f"{gold} Gold Coins", "icon": "💰", "id": "gold"})
                
                # Item
                roll = roll_dice(20)
                code = None
                if roll > 15: code = "chainmail"
                elif roll > 10: code = "healing_potion"
                elif roll > 5: code = "dagger"
                
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
                flag_modified(enemy, "loot")
                
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
                self.dm.player.x = 0
                self.dm.player.y = 0
                self.dm.player.z = 1 # Town Plaza
                
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
