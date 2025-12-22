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
