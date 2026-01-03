from sqlalchemy import create_engine, Column, Integer, String, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

Base = declarative_base()

engine = None
Session = None



class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    # Vitality
    hp_current = Column(Integer, default=20)
    hp_max = Column(Integer, default=20)
    
    # Location
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    z = Column(Integer, default=1)
    
    # Stats
    stats = Column(JSON, default={}) # Str, Dex, etc.
    skills = Column(JSON, default={}) # Mining, Herbalism, etc.
    armor_class = Column(Integer, default=10)
    
    # Progression
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    gold = Column(Integer, default=0)
    
    quest_state = Column(JSON, default={"active_quests": []})
    
    # Relationships
    inventory = relationship("InventoryItem", back_populates="player", cascade="all, delete-orphan")

class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    
    name = Column(String)
    item_type = Column(String, default="misc") # weapon, armor, consumable, material
    slot = Column(String, nullable=True) # main_hand, chest, etc.
    quantity = Column(Integer, default=1)
    
    is_equipped = Column(Boolean, default=False)
    properties = Column(JSON, default={}) # {"damage": "1d6", "defense": 2}

    player = relationship("Player", back_populates="inventory")

class MapTile(Base):
    __tablename__ = 'map_tiles'
    
    # Composite Index for fast spatial lookups
    __table_args__ = (
        Index('idx_maptile_location', 'z', 'x', 'y'),
    )
    
    id = Column(Integer, primary_key=True)
    x = Column(Integer)
    y = Column(Integer)
    z = Column(Integer, default=0)
    
    tile_type = Column(String) # floor, wall, void
    is_visited = Column(Boolean, default=False)
    
    # Allow storing extra data (e.g., "blood_stain": true)
    meta_data = Column(JSON, default={})

class WorldObject(Base):
    __tablename__ = 'world_objects'

    __table_args__ = (
        Index('idx_wobj_location', 'z', 'x', 'y'),
    )
    
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
    
    # Turn Management
    phase = Column(String, default="move") # move, action, bonus
    moves_left = Column(Integer, default=0)
    actions_left = Column(Integer, default=0)
    bonus_actions_left = Column(Integer, default=0)

class Monster(Base):
    __tablename__ = 'monsters'

    __table_args__ = (
        Index('idx_monster_location', 'z', 'x', 'y'),
        Index('idx_monster_alive', 'is_alive'),
    )
    
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

    __table_args__ = (
        Index('idx_npc_location', 'z', 'x', 'y'),
    )
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    persona_prompt = Column(String) # The system prompt for AI
    location = Column(String) # "Tavern", "Smithy"
    asset = Column(String, default="player.png")
    
    # Coordinates for Dungeon Encounters
    x = Column(Integer, nullable=True)
    y = Column(Integer, nullable=True)
    z = Column(Integer, default=0)

    quest_state = Column(JSON, default={}) # Tracks interactions


# Database Initialization
from sqlalchemy.orm import scoped_session

engine = create_engine('sqlite:///dungeon.db', connect_args={'check_same_thread': False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_session():
    # Return the scoped_session registry/proxy directly.
    # This allows it to act as a thread-local proxy.
    return SessionLocal
