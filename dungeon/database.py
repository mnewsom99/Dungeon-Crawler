from sqlalchemy import create_engine, Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from pathlib import Path

# Define the database path
DB_PATH = Path("dungeon.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Setup Engine and Session
engine = create_engine(DATABASE_URL, echo=False, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, default="Hero")
    character_class = Column(String, default="Adventurer")
    
    # Core Stats
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    gold = Column(Integer, default=0) # Currency
    hp_current = Column(Integer, default=20)
    hp_max = Column(Integer, default=20)
    mana_current = Column(Integer, default=10)
    mana_max = Column(Integer, default=10)
    stamina_current = Column(Integer, default=10)
    
    # Attributes (STR, DEX, etc.) stored as JSON
    stats = Column(JSON, default={})
    skills = Column(JSON, default={}) # Herbalism, Mining, etc.
    known_recipes = Column(JSON, default=[]) # List of Recipe IDs
    armor_class = Column(Integer, default=12) # 10 + 1 (Defense) + 1 (Generic Leather)
    
    # Position
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    z = Column(Integer, default=0)
    
    # Relationships
    inventory = relationship("InventoryItem", back_populates="player", cascade="all, delete-orphan")

class InventoryItem(Base):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    
    name = Column(String)
    item_type = Column(String) # weapon, armor, potion, material
    properties = Column(JSON, default={}) # damage: "1d6", defense: 2, etc.
    is_equipped = Column(Boolean, default=False)
    slot = Column(String, nullable=True) # main_hand, chest, head, legs, feet, hands, neck, off_hand
    quantity = Column(Integer, default=1)
    
    player = relationship("Player", back_populates="inventory")

class MapTile(Base):
    __tablename__ = 'map_tiles'
    
    id = Column(Integer, primary_key=True)
    x = Column(Integer, index=True)
    y = Column(Integer, index=True)
    z = Column(Integer, default=0)
    
    tile_type = Column(String) # floor, wall, void
    is_visited = Column(Boolean, default=False)
    
    # Allow storing extra data (e.g., "blood_stain": true)
    meta_data = Column(JSON, default={})

class WorldObject(Base):
    __tablename__ = 'world_objects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    obj_type = Column(String) # 'chest', 'door', 'lever'
    state = Column(String, default="closed") # 'closed', 'open', 'locked'
    
    x = Column(Integer)
    y = Column(Integer)
    z = Column(Integer, default=0)
    
    properties = Column(JSON, default={}) # {"loot": [], "key": "iron_key"}

class CombatEncounter(Base):
    __tablename__ = 'combat_encounters'
    
    id = Column(Integer, primary_key=True)
    turn_order = Column(JSON) # List of IDs/Types dicts e.g. [{"type": "player"}, {"type": "monster", "id": 1}]
    current_turn_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationship to monsters in this encounter
    monsters = relationship("Monster", back_populates="encounter")

class Monster(Base):
    __tablename__ = 'monsters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    monster_type = Column(String) # skeleton, goblin
    
    hp_current = Column(Integer)
    hp_max = Column(Integer)
    
    x = Column(Integer)
    y = Column(Integer)
    z = Column(Integer, default=0)
    
    is_alive = Column(Boolean, default=True)
    state = Column(String, default="idle") # idle, hunting, combat
    
    # Combat Stats
    level = Column(Integer, default=1)
    family = Column(String, default="monster") # undead, beast
    abilities = Column(JSON, default=[]) # ['fireball', 'stun']

    armor_class = Column(Integer, default=10)
    initiative = Column(Integer, default=0)
    stats = Column(JSON, default={"str":10, "dex":10, "con":10, "int":10, "wis":10, "cha":10})
    loot = Column(JSON, default=[]) # Loot dropped on death
    
    # Encounter Link
    encounter_id = Column(Integer, ForeignKey('combat_encounters.id'), nullable=True)
    encounter = relationship("CombatEncounter", back_populates="monsters")


# NPC Table for Oakhaven
class NPC(Base):
    __tablename__ = 'npcs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    persona_prompt = Column(String) # The system prompt for AI
    location = Column(String) # "Tavern", "Smithy"
    
    # Coordinates for Dungeon Encounters
    x = Column(Integer, nullable=True)
    y = Column(Integer, nullable=True)
    z = Column(Integer, default=0)

    quest_state = Column(JSON, default={}) # Tracks interactions

def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()
