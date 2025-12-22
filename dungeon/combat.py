from .rules import roll_dice
from .database import Monster, Player, MapTile

class CombatSystem:
    def __init__(self, dm_instance):
        self.dm = dm_instance
        self.session = dm_instance.session

    def check_engagement(self, player_pos):
        """Checks if player is adjacent to any ALIVE enemy."""
        px, py, pz = player_pos
        
        # Find enemies within 1 tile (Chebyshev distance)
        # Using a range query for efficiency
        enemy = self.session.query(Monster).filter(
            Monster.x.between(px-1, px+1),
            Monster.y.between(py-1, py+1),
            Monster.z == pz,
            Monster.is_alive == True
        ).first()

        # Don't engage if it's the player's own tile (unless overlap logic changes)
        # But wait, overlap is prevented in move_player.
        return enemy

    def start_combat(self, enemy):
        """Initializes combat state."""
        p_init = roll_dice(20)
        e_init = roll_dice(20)
        
        # Set enemy state to combat
        enemy.state = "combat"
        
        # Record combat state (For now, we just rely on Enemy state and maybe a temporary log)
        # Ideally, we'd have a 'Combat' table, but for now we'll return the message.
        # DM.move_player checks if any enemy is in 'combat' state.
        
        self.session.commit()
        
        msg = f"Combat started! Initiative: Player {p_init}, {enemy.name} {e_init}"
        return msg

    def player_action(self, action_type, direction=None):
        """Handles player combat actions."""
        # Find the active combat enemy
        enemy = self.session.query(Monster).filter_by(state="combat", is_alive=True).first()
        
        if not enemy:
            return "Combat is not active."

        msg = []

        if action_type == "attack":
            # Player Turn
            roll = roll_dice(20)
            ac = 12 # Default AC
            if roll >= ac:
                dmg = roll_dice(6) + 2 # Sword + Str
                enemy.hp_current -= dmg
                msg.append(f"You swing your sword and HIT! (Rolled {roll}). Dealt {dmg} damage.")
            else:
                msg.append(f"You swing your sword but MISS! (Rolled {roll}).")

        elif action_type == "unarmed":
            roll = roll_dice(20)
            ac = 12
            if roll >= ac:
                dmg = roll_dice(3) + 2 
                enemy.hp_current -= dmg
                msg.append(f"You kick the {enemy.name} and HIT! (Rolled {roll}). Dealt {dmg} damage.")
            else:
                msg.append(f"You try to kick the {enemy.name} but miss! (Rolled {roll}).")
        
        elif action_type == "flee":
             enemy.state = "idle" # Disengage
             self.session.commit()
             return "You flee from combat! (The enemy watches you run...)"

        # Check Enemy Death
        if enemy.hp_current <= 0:
            enemy.is_alive = False
            enemy.state = "dead"
            # No Corpse table yet, just leave 'dead' monster as a corpse marker
            
            self.session.commit()
            return " ".join(msg) + f" The {enemy.name} collapses! Victory."

        # Enemy Turn
        msg.append(self._enemy_turn(enemy))
        self.session.commit()
        
        return " ".join(msg)

    def _enemy_turn(self, enemy):
        roll = roll_dice(20)
        player_ac = 14
        
        if roll >= player_ac:
            dmg = roll_dice(4)
            self.dm.player.hp_current -= dmg
            return f"The {enemy.name} attacks you and HITS! Dealt {dmg} damage."
        else:
            return f"The {enemy.name} attacks you but MISSES!"
