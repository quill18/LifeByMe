# ./models/game/character.py

from datetime import datetime
from typing import Dict, List, Optional, Set
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient
from config import Config
from .enums import LifeStage

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
characters = db.characters

@dataclass
class Character:
    life_id: ObjectId
    name: str
    age: int
    gender: str
    relationship_tags: List[str]  # e.g., ["friend", "classmate", "study_partner"]
    primary_role: str  # e.g., "parent", "teacher", "classmate", "friend"
    physical_descriptors: List[str]  # e.g., ["tall", "red hair", "glasses"]
    personality_descriptors: List[str]  # e.g., ["shy", "competitive", "artistic"]
    first_met_context: str
    first_met_life_stage: LifeStage
    custom_gender: Optional[str] = None
    friendship: int = 0  # 0-10
    romance: int = 0    # 0-10
    conflict: int = 0   # 0-10, represents active antagonism/rivalry
    memory_ids: List[ObjectId] = field(default_factory=list)  # Memories this character appears in
    is_alive: bool = True
    departure_reason: Optional[str] = None
    family_relations: Dict[str, ObjectId] = field(default_factory=dict)  # e.g., {"father": ObjectId(...)}
    connected_character_ids: Set[ObjectId] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    _id: ObjectId = field(default_factory=ObjectId)

    def to_dict(self) -> Dict:
        """Convert Character to dictionary for database storage"""
        return {
            '_id': self._id,
            'life_id': self.life_id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'custom_gender': self.custom_gender,
            'relationship_tags': self.relationship_tags,
            'primary_role': self.primary_role,
            'friendship': self.friendship,
            'romance': self.romance,
            'conflict': self.conflict,
            'physical_descriptors': self.physical_descriptors,
            'personality_descriptors': self.personality_descriptors,
            'first_met_context': self.first_met_context,
            'first_met_life_stage': self.first_met_life_stage.value,
            'memory_ids': [str(id) for id in self.memory_ids],
            'is_alive': self.is_alive,
            'departure_reason': self.departure_reason,
            'family_relations': {k: str(v) for k, v in self.family_relations.items()},
            'connected_character_ids': [str(id) for id in self.connected_character_ids],
            'created_at': self.created_at,
            'last_interaction': self.last_interaction
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Character':
        """Create Character object from dictionary"""
        # Convert string IDs back to ObjectId
        family_relations = {k: ObjectId(v) for k, v in data.get('family_relations', {}).items()}
        connected_ids = {ObjectId(id) for id in data.get('connected_character_ids', [])}
        memory_ids = [ObjectId(id) for id in data.get('memory_ids', [])]

        return cls(
            _id=data.get('_id', ObjectId()),
            life_id=data['life_id'],
            name=data['name'],
            age=data['age'],
            gender=data['gender'],
            custom_gender=data.get('custom_gender'),
            relationship_tags=data['relationship_tags'],
            primary_role=data['primary_role'],
            friendship=data.get('friendship', 0),
            romance=data.get('romance', 0),
            conflict=data.get('conflict', 0),
            physical_descriptors=data['physical_descriptors'],
            personality_descriptors=data['personality_descriptors'],
            first_met_context=data['first_met_context'],
            first_met_life_stage=LifeStage(data['first_met_life_stage']),
            memory_ids=memory_ids,
            is_alive=data.get('is_alive', True),
            departure_reason=data.get('departure_reason'),
            family_relations=family_relations,
            connected_character_ids=connected_ids,
            created_at=data.get('created_at', datetime.utcnow()),
            last_interaction=data.get('last_interaction', datetime.utcnow())
        )

    def save(self) -> None:
        """Save character to database"""
        self.last_interaction = datetime.utcnow()
        characters.update_one(
            {'_id': self._id},
            {'$set': self.to_dict()},
            upsert=True
        )

    @staticmethod
    def get_by_id(char_id: ObjectId) -> Optional['Character']:
        """Get character by ID"""
        char_data = characters.find_one({'_id': char_id})
        return Character.from_dict(char_data) if char_data else None

    @staticmethod
    def get_by_life_id(life_id: ObjectId) -> List['Character']:
        """Get all characters associated with a life"""
        char_data = characters.find({'life_id': life_id})
        return [Character.from_dict(data) for data in char_data]

    def update_relationship(self, friendship_change: int = 0, romance_change: int = 0, 
                          conflict_change: int = 0) -> None:
        """Update relationship values, ensuring they stay within bounds"""
        self.friendship = max(0, min(10, self.friendship + friendship_change))
        self.romance = max(0, min(10, self.romance + romance_change))
        self.conflict = max(0, min(10, self.conflict + conflict_change))
        self.save()

    def add_relationship_tag(self, tag: str) -> None:
        """Add a new relationship tag if it doesn't already exist"""
        if tag not in self.relationship_tags:
            self.relationship_tags.append(tag)
            self.save()

    def remove_relationship_tag(self, tag: str) -> None:
        """Remove a relationship tag if it exists"""
        if tag in self.relationship_tags:
            self.relationship_tags.remove(tag)
            self.save()

    def add_memory(self, memory_id: ObjectId) -> None:
        """Add a memory ID to this character's memory list"""
        if memory_id not in self.memory_ids:
            self.memory_ids.append(memory_id)
            self.save()

    def connect_character(self, other_character_id: ObjectId) -> None:
        """Connect this character to another character"""
        if other_character_id not in self.connected_character_ids:
            self.connected_character_ids.add(other_character_id)
            self.save()

    def add_family_relation(self, relation_type: str, character_id: ObjectId) -> None:
        """Add a family relation to this character"""
        self.family_relations[relation_type] = character_id
        self.save()

    def depart(self, reason: str) -> None:
        """Mark character as departed with reason"""
        self.departure_reason = reason
        self.save()

    def die(self, reason: str) -> None:
        """Mark character as deceased with reason"""
        self.is_alive = False
        self.departure_reason = f"Died: {reason}"
        self.save()