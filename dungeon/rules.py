import random
import re

def roll_dice(dice_str: str) -> int:
    """
    Parses a dice string (e.g., '1d20', '2d6+2') and rolls it.
    Also accepts an integer to treat as a 1d(int) roll.
    """
    if isinstance(dice_str, int):
        dice_str = f"1d{dice_str}"
        
    # Simple regex for xdy+z or xdy-z
    match = re.match(r'(\d+)d(\d+)([\+\-]\d+)?', dice_str)
    if not match:
        raise ValueError(f"Invalid dice string: {dice_str}")
    
    count, sides, modifier = match.groups()
    count = int(count)
    sides = int(sides)
    mod = int(modifier) if modifier else 0
    
    total = sum(random.randint(1, sides) for _ in range(count))
    return total + mod

def calculate_hit(roll: int, ac: int) -> bool:
    """
    Determines if a regular attack roll hits the target AC.
    Does not account for crits yet.
    """
    return roll >= ac

def calculate_damage(dice_str: str) -> int:
    """
    Rolls damage. separated for semantic clarity.
    """
    return roll_dice(dice_str)

def get_skill_level(player, skill):
    """Get the level of a specific skill for a player."""
    data = player.skills or {}
    if skill not in data: return 0
    if isinstance(data[skill], int): return data[skill] 
    return data[skill].get("level", 0)

def award_skill_xp(player, skill, amount):
    """Award XP to a skill and check for level up."""
    from sqlalchemy.orm.attributes import flag_modified
    
    data = player.skills or {}
    # Ensure dict structure
    new_data = dict(data)
    
    if skill not in new_data:
        new_data[skill] = {"level": 1, "xp": 0}
    elif isinstance(new_data[skill], int):
            new_data[skill] = {"level": new_data[skill], "xp": 0}
            
    s = new_data[skill]
    s["xp"] += amount
    
    # Level Up Logic
    threshold = s["level"] * 50
    leveled_up = False
    while s["xp"] >= threshold:
            s["xp"] -= threshold
            s["level"] += 1
            threshold = s["level"] * 50
            leveled_up = True
            
    player.skills = new_data
    flag_modified(player, "skills")
    
    return leveled_up, s["level"]
