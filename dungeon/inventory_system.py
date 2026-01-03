from .database import InventoryItem, WorldObject, Monster

from .items import ITEM_TEMPLATES
from .gamedata import RECIPES, SKILLS
from .rules import roll_dice, get_skill_level, award_skill_xp
from sqlalchemy.orm.attributes import flag_modified

class InventorySystem:
    def __init__(self, session):
        self.session = session

    def equip_item(self, player, item_id):
        """
        Equips an item for the player.
        1. Unequips any item in the same slot.
        2. Sets is_equipped = True.
        3. Recalculates stats.
        """
        item = self.session.query(InventoryItem).filter_by(id=item_id, player_id=player.id).first()
        if not item:
            return "Item not found."
        
        if not item.slot:
            return "This item cannot be equipped."

        if item.is_equipped:
            return "Item already equipped."

        # Unequip existing in slot
        current_equipped = self.session.query(InventoryItem).filter_by(
            player_id=player.id, 
            slot=item.slot, 
            is_equipped=True
        ).all()
        
        for old_item in current_equipped:
            old_item.is_equipped = False
            
        # Equip new
        item.is_equipped = True
        
        self.recalculate_stats(player)
        self.session.commit()
        
        return f"Equipped {item.name}."

    def unequip_item(self, player, item_id):
        """
        Unequips an item.
        """
        item = self.session.query(InventoryItem).filter_by(id=item_id, player_id=player.id).first()
        if not item or not item.is_equipped:
            return "Item not equipped."
            
        item.is_equipped = False
        
        self.recalculate_stats(player)
        self.session.commit()
        return f"Unequipped {item.name}."

    def recalculate_stats(self, player):
        """
        Re-sums Armor Class and other stats from equipped gear.
        """
        # Base Stats
        base_ac = 10
        
        # Dex Bonus
        stats = player.stats or {}
        # Support both casing just in case (though we standardized on lowercase)
        dex = stats.get('dex') or stats.get('DEX') or 10
        dex_mod = (dex - 10) // 2
        
        ac = base_ac + dex_mod
        
        # Helper to get current weapon damage
        weapon_damage = "1d4" # Fists
        
        equipped_items = [i for i in player.inventory if i.is_equipped]
        
        for item in equipped_items:
            props = item.properties or {}
            
            # Armor
            if 'defense' in props:
                try:
                    ac += int(props['defense'])
                except:
                    pass
            
            # Weapon
            if item.slot == 'main_hand' and 'damage' in props:
                weapon_damage = props['damage']
        
        # Update Player
        player.armor_class = ac
        
        # Store weapon damage in stats so Combat can read it
        stats_dict = dict(player.stats or {})
        stats_dict['weapon_damage'] = weapon_damage
        player.stats = stats_dict

    def use_item(self, player, item_id):
        item = self.session.query(InventoryItem).filter_by(id=item_id, player=player).first()
        if not item: return "Item not found."
        
        if item.item_type != "consumable":
            return "You cannot use this item."
            
        props = item.properties or {}
        msg = "You used the item."
        
        if "heal" in props:
            val = props["heal"]
            heal_amt = 0
            
            # Try simple int
            try:
                heal_amt = int(val)
            except:
                # Try Dice
                try:
                    heal_amt = roll_dice(str(val))
                except:
                    heal_amt = 5 # Fallback
            
            old_hp = player.hp_current
            player.hp_current = min(player.hp_max, player.hp_current + heal_amt)
            actual_heal = player.hp_current - old_hp
            msg = f"You drank the {item.name}. Recovered {actual_heal} HP."
            
        self.session.delete(item)
        self.session.commit()
        return msg

    def take_loot(self, player, corpse_id, loot_id):
        # Determine Source (Monster or WorldObject)
        source = None
        is_object = False
        
        if isinstance(corpse_id, str) and corpse_id.startswith("obj_"):
             oid = int(corpse_id.split("_")[1])
             source = self.session.query(WorldObject).filter_by(id=oid).first()
             is_object = True
        else:
             source = self.session.query(Monster).filter_by(id=corpse_id).first()
             
        if not source: return "Nothing left."
        
        loot_list = []
        if is_object: loot_list = (source.properties or {}).get("loot", [])
        else: loot_list = source.loot or []
        
        found = None
        new_loot_list = []
        for item in loot_list:
            # Check ID first, then Name (support both)
            if item.get('id') == loot_id or item.get('name') == loot_id:
                found = item
            else:
                new_loot_list.append(item)
                
        if not found: return "Item gone."
        
        # Transfer Logic
        if found.get('type') == 'gold':
            qty = found.get('qty', 1)
            player.gold = (player.gold or 0) + qty
            msg = f"Took {qty} gold."
        else:
            # Stacking Logic for Loot
            name = found.get('name')
            template = None
            
            # Find template for consistency if possible, or use found data
            # (found data is usually dict from JSON/properties)
            
            # Helper to add item with stacking
            added_new = True
            
            # If item is stackable (material/consumable)
            # Currently we simplified stacking logic in DM to only 'gathering' but we should apply it here too.
            # Let's verify 'item_type'
            itype = found.get('item_type') or found.get('type')
            
            # Simple check: Try to stack everything valid
            existing = self.session.query(InventoryItem).filter_by(
                 player=player, name=name, is_equipped=False
            ).first()
            
            if existing and existing.quantity < 50 and itype in ['material', 'consumable']:
                 existing.quantity += 1
                 flag_modified(existing, "quantity")
                 added_new = False
            else:
                 self.session.add(InventoryItem(
                    name=name, 
                    item_type=itype, 
                    slot=found.get('slot'), 
                    properties=found.get('properties', {}), 
                    player=player,
                    quantity=1
                 ))
                 
            msg = f"Took {name}."
            
        # Update Loot Source
        if is_object:
             props = source.properties or {}
             props["loot"] = new_loot_list
             source.properties = props
             flag_modified(source, "properties")
             
             if not new_loot_list:
                 self.session.delete(source)
                 msg = "Nothing left."

        else:
             source.loot = new_loot_list
             flag_modified(source, "loot")
             if not new_loot_list:
                 self.session.delete(source)
                 msg = "Corpse removed."
            
        self.session.commit()
        return {
            "message": msg,
            "corpse_removed": (not new_loot_list),
            "remaining": len(new_loot_list)
        }

    def craft_item(self, player, recipe_id):
        recipe = RECIPES.get(recipe_id)
        if not recipe: return "Unknown recipe."
        
        # Check Skills
        if "skill_req" in recipe:
            for skill, req_lvl in recipe["skill_req"].items():
                curr = get_skill_level(player, skill)
                if curr < req_lvl:
                    s_name = SKILLS.get(skill, {}).get("name", skill)
                    return f"Skill too low. Need {s_name} {req_lvl}."
        
        # Map Ingredient Codes to Names
        ingredients_needed = {} # Name -> Qty
        for code, qty in recipe["ingredients"].items():
            t = ITEM_TEMPLATES.get(code)
            if not t: return f"Error: Item {code} not defined."
            ingredients_needed[t['name']] = qty
            
        # Check Inventory
        player_items = list(player.inventory)
        to_consume = []
        
        for name, qty_needed in ingredients_needed.items():
            # Handle Stacks
            found_qty = 0
            # We need to find items and count their stack quantity
            candidates = [i for i in player_items if i.name == name]
            
            for i in candidates:
                found_qty += (i.quantity or 1)
                
            if found_qty < qty_needed:
                 return f"Missing: {name} ({found_qty}/{qty_needed})"
            
            # Calculate what to consume from which stacks
            remaining_needed = qty_needed
            for i in candidates:
                if remaining_needed <= 0: break
                
                avail = i.quantity or 1
                take = min(avail, remaining_needed)
                to_consume.append((i, take))
                remaining_needed -= take
            
        # Consume
        for item, amount in to_consume:
            if item.quantity > amount:
                item.quantity -= amount
                flag_modified(item, "quantity")
            else:
                self.session.delete(item)
            
        # Create Result
        res_code = recipe["result"]
        res_t = ITEM_TEMPLATES.get(res_code)
        if res_t:
            # Check Stacking for result
            existing = self.session.query(InventoryItem).filter_by(
                 player=player, name=res_t['name'], is_equipped=False
            ).first()
            
            if existing and existing.quantity < 50 and res_t['type'] in ['material', 'consumable']:
                existing.quantity += 1
                flag_modified(existing, "quantity")
            else:
                self.session.add(InventoryItem(
                    name=res_t['name'],
                    item_type=res_t['type'],
                    slot=res_t['slot'],
                    properties=res_t['properties'],
                    player=player,
                    quantity=1
                ))
        
        # XP
        msg = f"Crafted {res_t['name']}!"
        for skill in recipe.get("skill_req", {}):
            up, lvl = award_skill_xp(player, skill, 20)
            if up: msg += f" ({skill.title()} Up!)"
            
        self.session.commit()
        return msg

    def buy_item(self, player, template_id):
        if template_id not in ITEM_TEMPLATES:
            return "Unknown item."
            
        template = ITEM_TEMPLATES[template_id]
        cost = template['value']
        
        if (player.gold or 0) < cost:
            return "Not enough gold!"
            
        # Deduct Gold
        player.gold = (player.gold or 0) - cost
        
        # Add Item (Stacking?)
        # Generally shops sell 1 at a time, but we should stack if possible
        existing = self.session.query(InventoryItem).filter_by(
             player=player, name=template['name'], is_equipped=False
        ).first()
        
        if existing and existing.quantity < 50 and template['type'] in ['material', 'consumable']:
             existing.quantity += 1
             flag_modified(existing, "quantity")
        else:
            new_item = InventoryItem(
                name=template['name'],
                item_type=template['type'],
                slot=template['slot'],
                properties=template['properties'], # contains damage, defense, icon
                is_equipped=False,
                player=player,
                quantity=1
            )
            self.session.add(new_item)
            
        self.session.commit()
        
        return f"Bought {template['name']} for {cost}g."

    def remove_item(self, item_id, quantity=1):
        """Removes a specific quantity of an item by ID."""
        item = self.session.query(InventoryItem).filter_by(id=item_id).first()
        if not item: return False
        
        if item.quantity > quantity:
            item.quantity -= quantity
            flag_modified(item, "quantity")
        else:
            self.session.delete(item)
            
        self.session.commit()
        return True

    def remove_item_by_name(self, item_name, quantity=1):
        """Removes QTY of item by Name (handling stacks)."""
        # Find all instances
        items = self.session.query(InventoryItem).filter_by(name=item_name).all()
        if not items: return False
        
        remaining = quantity
        for item in items:
            if remaining <= 0: break
            
            avail = item.quantity or 1
            take = min(avail, remaining)
            
            if item.quantity > take:
                item.quantity -= take
                flag_modified(item, "quantity")
            else:
                self.session.delete(item)
            
            remaining -= take
            
        self.session.commit()
        return remaining == 0

    def sell_item(self, player, item_id):
        item = self.session.query(InventoryItem).filter_by(id=item_id, player=player).first()
        if not item: return "Item not found."
        
        if item.is_equipped:
            return "Unequip first!"
            
        # Determine Value (50% of base value, or default logic)
        # We need to map back to a template to know value, OR store value in item.
        # Currently value is in ITEM_TEMPLATES.
        # Try to find template by name
        value = 0
        from .items import ITEM_TEMPLATES
        # Ineffecient reverse lookup but works for small sets
        for k, v in ITEM_TEMPLATES.items():
            if v['name'] == item.name:
                value = v['value'] // 2
                break
        
        if value <= 0: value = 1 # Minimum 1g
        
        # Sell one from stack or all? 
        # Let's simple sell 1
        qty = 1
        gain = value * qty
        
        player.gold = (player.gold or 0) + gain
        
        if item.quantity > 1:
            item.quantity -= 1
            flag_modified(item, "quantity")
        else:
            self.session.delete(item)
            
        self.session.commit()
        return f"Sold {item.name} for {gain}g."
        return True
